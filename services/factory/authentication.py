from abc import ABC, abstractmethod
import datetime
from fastapi import HTTPException, status
import logging

from fastapi.responses import JSONResponse
from pydantic import ValidationError

from pydantic_validation.authentication import UserLogin, UserLoginEmail, UserLoginResponse, UserSendOtp, UserVerifyOtp
from services.helper import auth_validation
from services.helper.otp_service import send_otp
from services.helper.token_service import token_creation
from services.providers.mock_provider import MockMessageProvider
from setup import redis_setup
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthMethod(str, Enum):
    LOGIN_CREDENTIALS = "login_credentials"
    LOGIN_PHONE_OTP = "login_phone_otp"
    AUTHENTICATE_PHONE = "authenticate_phone"

class AuthenticationService(ABC):
    def __init__(self, input):
        self.input = input
        
    def log_info(self, message: str):
        logger.info(f"{datetime.datetime.now()}:{self.__class__.__name__}:{message}")
    
    def log_warning(self, message: str):
        logger.warning(f"{datetime.datetime.now()}:{self.__class__.__name__}:{message}")
    
    def log_error(self, message: str):
        logger.error(f"{datetime.datetime.now()}:{self.__class__.__name__}:{message}")
        
    async def authenticate(self):
        try:
            return await self._run()
        
        except ValidationError as ve:
                self.log_error("Response validation failed for UserLoginResponse: %s", ve)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={"message": "Authentication service returned invalid response"}
                )
        except HTTPException:
            raise
        except Exception as e:
            self.log_error(str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail={"message": "Internal Server Error"})
    
    @abstractmethod
    async def _run(self):
        pass
    
    

class AuthenticationFactory:
    @staticmethod
    def get_authentication_service(method: AuthMethod,input):
        if method == AuthMethod.LOGIN_CREDENTIALS:
            return LoginCredentialsService(input)
        elif method == AuthMethod.LOGIN_PHONE_OTP:
            return LoginPhoneOtpService(input)
        elif method == AuthMethod.AUTHENTICATE_PHONE:
            return AuthenticationPhoneService(input)
        else:
            raise ValueError("Invalid authentication method")

class LoginCredentialsService(AuthenticationService):
    def __init__(self, payload, user_checker=auth_validation.user_check,
                 password_checker=auth_validation.password_check_validation, token_creator=token_creation):
        super().__init__(payload)
        self.user_checker = user_checker
        self.password_checker = password_checker
        self.token_creator = token_creator
        
    async def _run(self):
        self.log_info(f"Starting login with credentials process:{self.input}, type:{type(self.input)},{self.input.email if hasattr(self.input,'email') else 'no email field'}")
        if self.input.key == "email":
            data : UserLoginEmail = self.input
            self.log_info("Logging in with email")
            email = data.email
            user = await self.user_checker({"email":email})
        else:
            data : UserLogin = self.input
            self.log_info("Logging in with username")
            username = data.username
            user = await self.user_checker({"username":username})
        
        password_validation = await self.password_checker(data.password, user)
        if not password_validation:
            self.log_warning(f"password for user_id:{user.id} is invalid")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={"message":"Invalid credentials."})
    
        get_token = await self.token_creator(user.id)
        self.log_info("token is created successfully")
        return UserLoginResponse(**get_token)


class LoginPhoneOtpService(AuthenticationService):
    
    def __init__(self, payload, otp_sender=send_otp, message_provider=MockMessageProvider()):
        super().__init__(payload)
        self.otp_sender = otp_sender
        self.message_provider = message_provider
        
    async def _run(self):
        data : UserSendOtp = self.input
        phone_number = data.phone_number
        otp = await self.otp_sender(phone_number)
        if otp:
            mock_message = await self.message_provider.send_message(to=phone_number, message=f"Your OTP is {otp}")
            self.log_info(f"OTP is send successfully:{mock_message}")
            return JSONResponse(status_code=200, content={"message":f"OTP is send successfully"})


class AuthenticationPhoneService(AuthenticationService):
    def __init__(self, payload, user_checker=auth_validation.user_check, token_creator=token_creation):
        super().__init__(payload)
        self.user_checker = user_checker
        self.token_creator = token_creator
    
    async def _run(self):
        data :UserVerifyOtp = self.input
        phone_number = data.phone_number
        otp = data.otp
        
        redis_client = redis_setup.redis_info()
        if not redis_client:
            self.log_warning("Redis is not working right now")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})
        
        cached_otp = redis_client.get(phone_number)
        self.log_info(f"cached_otp retrieved for phone number {phone_number}:{cached_otp},type:{type(cached_otp)}")
        if not cached_otp or cached_otp != otp:
            self.log_warning(f"Invalid OTP for phone number: {phone_number}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={"message":"Invalid OTP"})
        
        user = await self.user_checker({"phone_number":phone_number})
        get_token = await self.token_creator(user.id)
        self.log_info("token is created successfully")
        
        redis_client.delete(phone_number)
        self.log_info(f"cached otp deleted for phone number {phone_number}")
        return UserLoginResponse(**get_token)
        