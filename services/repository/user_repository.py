from enum import Enum
from models.users import Users
from typing import Optional
from services.repository.base import BaseRepository
from async_lru import alru_cache
from setup.database_setup import get_db
from sqlalchemy.exc import IntegrityError
import logging
from fastapi import HTTPException, status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRepository(BaseRepository):
    def __init__(self):
        self.db = next(get_db())
        
    async def add_user(self,data):
        try:
            self.db.add(Users(**data))
            self.db.commit()
            return True
        except IntegrityError:
            self.db.rollback()
            logger.error("User registration failed due to integrity error (duplicate entry) for data:(email or username or phone number)")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "User with this info:(email or username or phone number) already exists."},
            )  
        
    async def update_user(self,data,user_id: int):
        try:
            logger.info(f"Updating user with ID: {user_id}")

            # Update user fields
            self.db.query(Users).filter(Users.id == user_id).update(data)
            self.db.commit()
            return True
        except IntegrityError:
            self.db.rollback()
            logger.error("User update failed due to integrity error (duplicate entry) for data:(email or username or phone number)")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "User with this info:(email or username or phone number) already exists."},
            )
            
    @alru_cache(maxsize=120)
    async def find_user_by_field(self, field_name: str, field_value: str) -> Optional[Users]:
        logger.warning(f"Finding user by {field_name} with value: {field_value}")
        return self.db.query(Users).filter(getattr(Users, field_name) == field_value).first()
    
    @alru_cache(maxsize=120)
    async def get_all_users(self) -> list[Users]:
        return self.db.query(Users).all()
    
    

class InvalidCacheMethod(str, Enum):
        BY_PARAM = "by_param"
        ALL_USERS = "all_users"