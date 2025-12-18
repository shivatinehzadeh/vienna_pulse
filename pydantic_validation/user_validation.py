from typing import Annotated
from pydantic import BaseModel, EmailStr, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=4)]
NonEmptyStrPhone = Annotated[str, StringConstraints(strip_whitespace=True, min_length=11)]


class UserUpdate(BaseModel):
    first_name: NonEmptyStr | None
    last_name: NonEmptyStr | None
    email: EmailStr | None
    username: NonEmptyStr
    phone_number: NonEmptyStrPhone | None


class UserCreate(BaseModel):
    first_name: NonEmptyStr
    last_name: NonEmptyStr
    email: EmailStr | None
    username: NonEmptyStr
    password: NonEmptyStr
    phone_number: NonEmptyStrPhone | None


class UserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    username: str
    phone_number: str | None

    model_config = {"from_attributes": True}
