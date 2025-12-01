from typing import Annotated
from pydantic import BaseModel, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class UserLogin(BaseModel):
    username: NonEmptyStr
    password: NonEmptyStr
    
class UserLoginEmail(BaseModel):
    email: NonEmptyStr
    password: NonEmptyStr

class UserSendOtp(BaseModel):
    phone_number: NonEmptyStr
    
class UserVerifyOtp(BaseModel):
    phone_number: NonEmptyStr
    otp: NonEmptyStr

class UserLoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user_id: int