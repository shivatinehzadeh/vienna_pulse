from .user_repository import UserListRepository, UserRepository

class RepositoryFactory:

    @staticmethod
    def get_repository(name: str, db):

        repositories = {
            "user": UserRepository,
            "user_list": UserListRepository
        }

        repo_class = repositories.get(name)

        if not repo_class:
            raise ValueError(f"Repository '{name}' not found")

        return repo_class(db)