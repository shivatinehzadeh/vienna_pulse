from enum import Enum
from models.users import Users
from typing import Optional
from services.repository.base import BaseRepository
from async_lru import alru_cache

class UserRepository(BaseRepository):
    @alru_cache(maxsize=120)
    async def find_user_by_field(self, field_name: str, field_value: str) -> Optional[Users]:
        return self.db.query(Users).filter(getattr(Users, field_name) == field_value).first()
    
    @alru_cache(maxsize=120)
    async def get_all_users(self) -> list[Users]:
        return self.db.query(Users).all()

class InvalidCacheMethod(str, Enum):
        BY_PARAM = "by_param"
        ALL_USERS = "all_users"