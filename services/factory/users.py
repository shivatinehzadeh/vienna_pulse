from abc import ABC,abstractmethod
import datetime
from enum import Enum
from fastapi import HTTPException, status
from pydantic import ValidationError
from services.helper.auth_validation import password_check_validation
from services.helper.user_functions import get_user, update_user
from pydantic_validation.user_validation import UserRead
from services.helper.cache_service import user_cache
import logging
from starlette.responses import JSONResponse
from passlib.context import CryptContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class UserMethod(str, Enum):
    BY_ID = "by_id"
    BY_PHONE = "by_phone"
    BY_EMAIL = "by_email"
    ALL_USERS = "all_users"
    BY_USERNAME = "by_username"
    UPDATE_USER = "update_user"
    CHANGE_PASSWORD = "change_password"

class Users(ABC):
    def __init__(self, param = None, user_id = None):
         self.param = param
         self.user_id = user_id
         
    def log_info(self, message: str):
        logger.info(f"{datetime.datetime.now()}:{self.__class__.__name__}:{message}")
    
    def log_error(self, message: str):
        logger.error(f"{datetime.datetime.now()}:{self.__class__.__name__}:{message}") 
        
    async def users(self):
        try:
            return await self._run()
        except ValidationError as ve:
            self.log_error(f"Response validation failed for UserLoginResponse: {ve}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "Authentication service returned invalid response"}
            )
        except HTTPException:
            raise
        except Exception as e:
            self.log_error(f"Internal Server Error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail={"message": "Internal Server Error"})
    
    @abstractmethod
    async def _run(self):
        pass
 
 
class UserFactory:
    @staticmethod
    def get_user_service(method: str, param = None, user_id = None):
        if method == UserMethod.BY_ID:
            return UserByIdService(user_id)
        elif method == UserMethod.BY_PHONE:
            return UserByPhoneService(param)
        elif method == UserMethod.BY_EMAIL:
            return UserMethod(param)
        elif method == UserMethod.BY_USERNAME:
            return UserByUsernameService(param)
        elif method == UserMethod.ALL_USERS:
            return AllUsersService()
        elif method == UserMethod.BY_USERNAME:
            return UserByUsernameService(param)
        elif method == UserMethod.UPDATE_USER:
            return UpdateUserService(param,user_id)
        elif method == UserMethod.CHANGE_PASSWORD:
            return ChangePasswordService(param,user_id)
        else:
            raise ValueError("Invalid user retrieval method")
          
class UserByIdService(Users):
    
    async def _run(self):
        self.log_info(f"Fetching user by id: {self.param}")
        user = await get_user("id",self.user_id)
        return UserRead.model_validate(user)
    
    
class UserByPhoneService(Users):
    async def _run(self):
        self.log_info(f"Fetching user by phone number: {self.param}")
        user = await get_user("phone_number",self.param)
        return UserRead.model_validate(user)
    
    
class UserByEmailService(Users):
    async def _run(self):
        self.log_info(f"Fetching user by email: {self.param}")
        user = await get_user("email",self.param)
        return UserRead.model_validate(user)
    
class UserByUsernameService(Users):
    async def _run(self):
        self.log_info(f"Fetching user by username: {self.param}")
        user = await get_user("username",self.param)
        return UserRead.model_validate(user)
    
class AllUsersService(Users):
    async def _run(self):
        self.log_info("Fetching all users")
        users = await get_user()
        return [UserRead.model_validate(user) for user in users]
    
class UpdateUserService(Users):
    async def _run(self):
        self.log_info(f"Updating user with data: {self.param}")
        data = self.param
        if "password" in data and data["password"] is not None:
            #remove password from update data
            data.pop("password")
            
        self.log_info(f"Starting user update process for user id: {self.user_id} with data: {data}")
        
        user = await get_user("id",self.user_id)
        if not user:
            self.log_error(f"User with id: {self.user_id} not found for update.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "User not found."},
            )
        update_data = await update_user(data, self.user_id)
        if update_data:
            user_cache.clear()
        self.log_info(f"User with id: {self.user_id} updated successfully.")
        return UserRead.model_validate(user)
    
class ChangePasswordService(Users):
    async def _run(self):
        self.log_info(f"Updating password with data: {self.param}")
        data = self.param
        password = data.get("password")
            
        self.log_info(f"Starting user update process for user id: {self.user_id} with data: {data}")
        
        user = await get_user("id",self.user_id)
        if not user:
            self.log_error(f"User with id: {self.user_id} not found for update.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "User not found."},
            )
        chacked_password = password_check_validation(password, user)
        if not chacked_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password validation failed."},
            )
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        data = {"password": pwd_context.hash(password)}
        await update_user(data, self.user_id)
        self.log_info(f"User with id: {self.user_id} is changed password successfully.")
        return JSONResponse(content={"message": "Password changed successfully."}, status_code=status.HTTP_200_OK)
    
