from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import logging
from passlib.context import CryptContext


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def login_validation(validation_dict):
    try:
        message = []
        for item in validation_dict:            
            if not validation_dict[item]:
                logger.error(f"Login failed: {item} is empty.")
                message.append(f"{item} is required.")
                
            elif not isinstance(validation_dict[item], str):
                logger.error(f"Login failed: {item} must be string.")
                message.append(f"{item} must be string.")
                
            elif validation_dict[item].strip() == "":
                logger.error(f"Login failed: {item} is empty.")
                message.append(f"{item} is required.")
                
        return message
    except Exception as e:
        logger.error(f"Error during login validation: {str(e)}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error during validation"})

async def password_check_validation(password, user):
    try:
        password_check = pwd_context.verify(password, user.password)
        if not password_check:
            return False
        return True
    except Exception as e:
        logger.error(f"Error during password validation: {str(e)}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error during password validation"})