from services.repository.factory import RepositoryFactory
from fastapi import HTTPException, status
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_repo = RepositoryFactory.get_repository("user")

async def get_user(param_name=None,param_value=None):
    if param_name and param_value:    
        user = await user_repo.find_user_by_field(param_name,param_value)
    else:
        user = await user_repo.get_all_users()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

async def update_user(data, user_id):
    update_data = await user_repo.update_user(data, user_id)
    if not update_data:
        logger.error(f"User with id: {user_id} updated is failed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "update is failed."},
        )
    return update_data