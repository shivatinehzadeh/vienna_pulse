import uuid
from fastapi import APIRouter, Depends
import logging
from sqlalchemy.orm import Session
from pydantic_validation.user_validation import UserCreate, UserRead
from services.factory.users import UserFactory
from services.helper.cache_service import user_cache
from models.users import Users
from setup.database_setup import get_db
from functools import lru_cache
from services.helper import cache_service
from passlib.context import CryptContext
from starlette.responses import JSONResponse
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")



@lru_cache(maxsize=10)
def get_user_service_cached(method: str, param = None):
    return UserFactory.get_user_service(method=method,param=param)


@router.post("/register")
def register_user(data: UserCreate,  db: Session = Depends(get_db)):
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

        user_cache.clear()
        logger.info(f"User registered successfully with username: {data.get('username')}")
        
        if create_user:
            return JSONResponse(
                status_code=201,
                content={"message": "User registered successfully."},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "User registration is failed."},
            )
    except IntegrityError:
        db.rollback()
        logger.error("User registration failed due to integrity error (duplicate entry) for data:(email or username or phone number)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "User with this info:(email or username or phone number) already exists."},
        )
    except Exception as e:
        logger.error(f"User registration failed due to an unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"An error occurred: {str(e)}"},
        )


@router.get("/users", response_model=list[UserRead])
async def get_users():
    method = "all_users"
    get_cached_data = await  cache_service.get_cached_users(method)
    if get_cached_data:
        return get_cached_data 
    logger.info("CACHE MISS (cachetools)")
    db = next(get_db())
    service = UserFactory.get_user_service(method=method, db=db)
    result = await service.users()
    db.close()
    
    # Store in cache
    cache_key = cache_service.get_cache_key(method)
    cache_service.user_cache[cache_key] = result
    return result

@router.get("/user/{user_id}", response_model=UserRead)
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    service = get_user_service_cached(method="by_id", db=db, param=user_id)
    return await service.users()

@router.get("/user_by_email/{email}", response_model=UserRead)
async def get_user_by_email(email: str, db: Session = Depends(get_db)):
    service = get_user_service_cached(method="by_email", db=db, param=email)
    return await service.users()

@router.get("/user_by_phone/{phone_number}", response_model=UserRead)
async def get_user_by_phone(phone_number: str, db: Session = Depends(get_db)):
    service = get_user_service_cached(method="by_phone", db=db, param=phone_number)
    return await service.users()

