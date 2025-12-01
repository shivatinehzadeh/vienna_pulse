from fastapi import APIRouter
from passlib.context import CryptContext
from models.users import Users
from pydantic_validation.user_validation import UserCreate
from starlette.responses import JSONResponse
from setup.database_setup import get_db
from sqlalchemy.exc import IntegrityError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
router = APIRouter()


db =  next(get_db())

@router.post("/register")
def register_user(data: UserCreate):
    try:
        data = dict(data)
        logger.info(f"Starting user registration process.with data: {data}")
        
        # Hash the password
        password = pwd_context.hash(data.get("password"))
        
        #prepare user info for registration
        registeration_info = {
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "username": data.get("username"),
            "email": data.get("email"),
            "phone_number": data.get("phone_number"),
            "password": password,
            "active_status": True,
        }
        # Create user instance and add to the database
        create_user = Users(**registeration_info)
        db.add(create_user)
        db.commit()
        db.refresh(create_user)
        
        logger.info(f"User registered successfully with username: {data.get('username')}")
        
        if create_user:
            return JSONResponse(
                status_code=201,
                content={"message": "User registered successfully."},
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"message": "User registration is failed."},
            )
    except IntegrityError:
        logger.error("User registration failed due to integrity error (duplicate entry) for data:(email or username or phone number)")
        return JSONResponse(
            status_code=400,
            content={"message": "User with this info:(email or username or phone number) already exists."},
        )
    except Exception as e:
        logger.error(f"User registration failed due to an unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"An error occurred: {str(e)}"},
        )