from fastapi import APIRouter, Depends
import logging
from sqlalchemy.orm import Session
from pydantic_validation.user_validation import UserRead
from services.factory.users import UserFactory
from setup.database_setup import get_db
from async_lru import alru_cache
from functools import lru_cache

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@lru_cache(maxsize=10)
def get_user_service_cached(method: str, db: Session, param = None):
    return UserFactory.get_user_service(method=method, db=db,param=param)

@router.get("/users", response_model=list[UserRead])
@alru_cache(maxsize=120)
async def get_users(db: Session = Depends(get_db)):
    service = get_user_service_cached("all_users", db)
    logger.info("Fetching all users with caching")
    return await service.users()


@router.get("/user/{user_id}", response_model=UserRead)
@alru_cache(maxsize=120)
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    service = get_user_service_cached(method="by_id", db=db, param=user_id)
    return await service.users()

@router.get("/user_by_email/{email}", response_model=UserRead)
@alru_cache(maxsize=120)
async def get_user_by_email(email: str, db: Session = Depends(get_db)):
    service = get_user_service_cached(method="by_email", db=db, param=email)
    return await service.users()

@router.get("/user_by_phone/{phone_number}", response_model=UserRead)
@alru_cache(maxsize=120)
async def get_user_by_phone(phone_number: str, db: Session = Depends(get_db)):
    service = get_user_service_cached(method="by_phone", db=db, param=phone_number)
    return await service.users()