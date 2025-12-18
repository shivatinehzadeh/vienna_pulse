from services.repository.factory import RepositoryFactory
from fastapi import HTTPException, status

async def get_user(param_name=None,param_value=None):
    user_repo = RepositoryFactory.get_repository("user")
    if param_name and param_value:    
        user = await user_repo.find_user_by_field(param_name,param_value)
    else:
        user = await user_repo.get_all_users()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
