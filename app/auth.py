from fastapi import APIRouter, Depends, HTTPException, status
import logging
from fastapi.responses import JSONResponse
from models.users import Users

from sqlalchemy.orm import Session
from setup.database_setup import get_db
from services.authentication_services import auth_validation
from setup import redis_setup
from services.providers.mock_provider import MockMessageProvider
from pydantic_validation.authentication import UserLogin, UserLoginEmail, UserSendOtp, UserVerifyOtp, UserLoginResponse
from services.authentication_services.token_service import token_creation
from services.authentication_services.otp_service import send_otp

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/login", response_model=UserLoginResponse)
async def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    try:
        data = dict(payload)
        username = data.get("username", "")
        password = data.get("password", "")
        
        user = db.query(Users).filter(Users.username == username).first()
        if not user:
            logger.warning(f"username is invalid:{username}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail={"message":"Invalid credentials."})
        
        password_validation = await auth_validation.password_check_validation(password, user)
        if not password_validation:
            logger.warning(f"password is incorrect for username:{user.username}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail={"message":"Invalid credentials."})
        get_token = await token_creation(user.id)
        
        logger.info(f"Successful login for user: {user.username}")
        return UserLoginResponse(**get_token)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal Server Error during login: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})
    

@router.post("/login/email", response_model=UserLoginResponse)
async def login_with_email(payload:UserLoginEmail, db: Session= Depends(get_db) ):
    try:
        data = dict(payload)
        email = data.get("email")
        password = data.get("password")
        
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            logger.warning(f"user with email {email} not found")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={"message":"Invalid credentials."})
        
        password_validation = await auth_validation.password_check_validation(password, user)
        if not password_validation:
            logger.warning(f"password for user_id:{user.id} is invalid")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={"message":"Invalid credentials."})
        
        get_token = await token_creation(user.id)
        logger.info("token is created successfully")
        return UserLoginResponse(**get_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal Server Error during login: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})
    
    
@router.post("/login/otp", response_model=UserLoginResponse)
async def login_otp(payload:UserSendOtp, db: Session = Depends(get_db)):
    try:
        data = dict(payload)
        phone_number = data.get("phone_number")
        otp = await send_otp(phone_number)
        if otp:
            mock_message = await MockMessageProvider().send_message(to=phone_number, message=f"Your OTP is {otp}")
            logger.info(f"OTP is send successfully:{mock_message}")
            return JSONResponse(status_code=200, content={"message":f"OTP is send successfully"})
    except HTTPException:
        raise 
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})

@router.post("/login/phone", response_model=UserLoginResponse)
async def login_with_phone(payload:UserVerifyOtp, db: Session = Depends(get_db)):
    try:
        data = dict(payload)
        phone_number = data.get("phone_number")
        otp = data.get("otp")
        
        redis_client = redis_setup.redis_info()
        if not redis_client:
            logger.warning("Redis is not working right now")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})
        
        cached_otp = redis_client.get(phone_number)
        logger.info(f"cached_otp retrieved for phone number {phone_number}:{cached_otp},type:{type(cached_otp)}")
        if not cached_otp or cached_otp != otp:
            logger.warning(f"Invalid OTP for phone number: {phone_number}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={"message":"Invalid OTP"})
        
        user = db.query(Users).filter(Users.phone_number == phone_number).first()
        if not user:
            logger.warning(f"user with phone number {phone_number} not found")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={"message":"Invalid credentials."})
        
        get_token = await token_creation(user.id)
        logger.info("token is created successfully")
        redis_client.delete(phone_number)
        logger.info(f"cached otp deleted for phone number {phone_number}")
        return JSONResponse(status_code=200, content=get_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal Server Error during login: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})
 