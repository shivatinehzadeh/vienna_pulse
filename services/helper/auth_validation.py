from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import logging
from passlib.context import CryptContext

from models.users import Users
from services.repository.factory import RepositoryFactory


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def password_check_validation(password, user):
    try:
        password_check = pwd_context.verify(password, user.password)
        if not password_check:
            return False
        return True
    except Exception as e:
        logger.error(f"Error during password validation: {str(e)}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error during password validation"})
    
async def user_check(data:dict, db):
    try:
        key_list = ["username", "email", "phone_number"]
        field_name = next((key for key in key_list if key in data), None)
        repo = RepositoryFactory.get_repository("user", db)
        user = repo.find_user_by_field(field_name=field_name, field_value=data[field_name])
        if not user:
            logger.warning("User not found.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail={"message":"Invalid credentials."})
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user check: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error during user check"})