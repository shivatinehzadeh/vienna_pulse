from fastapi import APIRouter, Depends, HTTPException, status
import logging
from sqlalchemy.orm import Session
from pydantic_validation.user_validation import UserRead
from services.repository.factory import RepositoryFactory
from setup.database_setup import get_db


router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/users", response_model=list[UserRead])
async def get_users(db: Session = Depends(get_db)):
    user_repo = RepositoryFactory.get_repository("user", db)
    users = user_repo.get_all_users()
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return [UserRead.model_validate(user) for user in users]

@router.get("/user/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user_repo = RepositoryFactory.get_repository("user", db)
    user = user_repo.find_user_by_field("id",user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)