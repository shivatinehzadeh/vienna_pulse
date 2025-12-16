import uuid
from fastapi import APIRouter, Depends
import logging
from sqlalchemy.orm import Session
from pydantic_validation.user_validation import UserRead
from services.factory.users import UserFactory
from setup.database_setup import get_db
from async_lru import alru_cache
from functools import lru_cache
from cachetools import TTLCache
from cachetools.keys import hashkey
router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@lru_cache(maxsize=10)
def get_user_service_cached(method: str, param = None):
    return UserFactory.get_user_service(method=method,param=param)


# Create cache
user_cache = TTLCache(maxsize=120, ttl=60)

def get_cache_key():
    return hashkey("users", "all")

async def get_cached_users():
    cache_key = get_cache_key()
    
    # Check cache
    if cache_key in user_cache:
        logger.info("CACHE HIT (cachetools)")
        return user_cache[cache_key]
    
    logger.info("CACHE MISS (cachetools)")
    db = next(get_db())
    service = UserFactory.get_user_service(method="all_users", db=db)
    result = await service.users()
    db.close()
    
    # Store in cache
    user_cache[cache_key] = result
    return result

@router.get("/users", response_model=list[UserRead])
async def get_users():
    return await get_cached_users()

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

