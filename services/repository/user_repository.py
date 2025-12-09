from models.users import Users
from typing import Optional
from services.repository.base import BaseRepository


class UserRepository(BaseRepository):
    def find_user_by_field(self, field_name: str, field_value: str) -> Optional[Users]:
        return self.db.query(Users).filter(getattr(Users, field_name) == field_value).first()
    
class UserListRepository(BaseRepository):
    def get_all_users(self) -> list[Users]:
        return self.db.query(Users).all()