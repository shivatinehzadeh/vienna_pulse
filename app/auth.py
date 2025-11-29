from fastapi import APIRouter, Depends, HTTPException, status
import logging
from fastapi.responses import JSONResponse
from models.users import Users
import jwt
import os
import time
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from setup.database_setup import get_db
from app import auth_validation
import random 
from setup import redis_setup
from providers.mock_provider import MockMessageProvider

jwt_secret = os.getenv("SECRET")
jwt_algorithm = os.getenv("ALGORITHM")

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/login")
async def login_user(payload: dict, db: Session = Depends(get_db)):
    try:
        data = dict(payload)
        username = data.get("username", "")
        password = data.get("password", "")
        
        validation_messages = await auth_validation.login_validation({"username":username,"password":password})
        if validation_messages:
            logger.error(f"Validation errors: {validation_messages}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"messages":validation_messages})
        
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
        return JSONResponse(status_code=200,content=get_token)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal Server Error during login: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})
    

@router.post("/login/email")
async def login_with_email(payload:dict, db: Session= Depends(get_db) ):
    try:
        data = dict(payload)
        email = data.get("email")
        password = data.get("password")
        validation_check = await auth_validation.login_validation({"email":email,"password":password})
        if validation_check:
            logger.error(f"validation error : {validation_check}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail={"message":validation_check})
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
        return JSONResponse(status_code=200, content=get_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal Server Error during login: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})
    
    
@router.post("/login/otp")
async def login_otp(payload:dict, db: Session = Depends(get_db)):
    try:
        data = dict(payload)
        phone_number = data.get("phone_number")
        validation_check = await auth_validation.login_validation({"phone_number":phone_number})
        if validation_check:
            logger.error(f"validation error : {validation_check}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail={"message":validation_check})
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

@router.post("/login/phone")
async def login_with_phone(payload:dict, db: Session = Depends(get_db)):
    try:
        data = dict(payload)
        phone_number = data.get("phone_number")
        otp = data.get("otp")
        
        validation_check = await auth_validation.login_validation({"phone_number":phone_number,"otp":otp})
        if validation_check:
            logger.error(f"validation error : {validation_check}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail={"message":validation_check})
        
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
    

async def token_creation(user_id):
    try:
        payload= {
            "user_id" : user_id,
            "expires" : time.time() + 900
        }
        token = jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)
        
        if not token:
            logger.error(f"Token creation failed for user ID: {user_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 detail={"Authentication service temporarily unavailable"})
        return {
                "token": token,
                "token_type": "bearer",  
                "user_id": user_id    
            }
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error In Token Creation"})

async def send_otp(phone_number: str):
    try:
        redis_client = redis_setup.redis_info()
        if not redis_client:
            logger.warning("Redis is not working right now")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})  
        get_cached_phone = redis_client.get(phone_number)
        if get_cached_phone:
            logger.warning(f"otp request in 90 seconds for {phone_number}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail={"message":"You can not send two request in 90 seconds"})
        else:
            otp_length = 6
            otp_creation = ''.join([str(random.randint(0, 9)) for _ in range(otp_length)])
            redis_client.setex(phone_number, 90, otp_creation)
            return otp_creation
    except HTTPException:
        raise 
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})
