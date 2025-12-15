from abc import ABC,abstractmethod
import datetime
from enum import Enum
from fastapi import HTTPException, status
from pydantic import ValidationError
from services.helper.user_functions import get_user
from pydantic_validation.user_validation import UserRead
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FetchUserMethod(str, Enum):
    BY_ID = "by_id"
    BY_PHONE = "by_phone"
    BY_EMAIL = "by_email"
    ALL_USERS = "all_users"

class Users(ABC):
    def __init__(self, db, param = None):
         self.param = param
         self.db = db
         
    def log_info(self, message: str):
        logger.info(f"{datetime.datetime.now()}:{self.__class__.__name__}:{message}")
    
    def log_error(self, message: str):
        logger.error(f"{datetime.datetime.now()}:{self.__class__.__name__}:{message}") 
        
    async def users(self):
        try:
            return await self._get_users()
        except ValidationError as ve:
            self.log_error(f"Response validation failed for UserLoginResponse: {ve}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "Authentication service returned invalid response"}
            )
        except HTTPException:
            raise
        except Exception as e:
            self.log_error(f"Internal Server Error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail={"message": "Internal Server Error"})
    
    @abstractmethod
    async def _get_users(self):
        pass
 
 
class UserFactory:
    @staticmethod
    def get_user_service(method: str, db, param = None):
        if method == FetchUserMethod.BY_ID:
            return UserByIdService(db, param)
        elif method == FetchUserMethod.BY_PHONE:
            return UserByPhoneService(db, param)
        elif method == FetchUserMethod.BY_EMAIL:
            return UserByEmailService(db, param)
        elif method == FetchUserMethod.ALL_USERS:
            return AllUsersService(db)
        else:
            raise ValueError("Invalid user retrieval method")
          
class UserByIdService(Users):
    async def _get_users(self):
        self.log_info(f"Fetching user by id: {self.param}")
        user = await get_user(self.db, "id",self.param)
        return UserRead.model_validate(user)
    
    
class UserByPhoneService(Users):
    async def _get_users(self):
        self.log_info(f"Fetching user by phone number: {self.param}")
        user = await get_user(self.db, "phone_number",self.param)
        return UserRead.model_validate(user)
    
    
class UserByEmailService(Users):
    async def _get_users(self):
        self.log_info(f"Fetching user by email: {self.param}")
        user = await get_user(self.db, "email",self.param)
        return UserRead.model_validate(user)
    
class AllUsersService(Users):
    async def _get_users(self):
        self.log_info("Fetching all users")
        users = await get_user(self.db)
        return [UserRead.model_validate(user) for user in users]