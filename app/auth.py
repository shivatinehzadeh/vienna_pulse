from fastapi import APIRouter, Depends, HTTPException, status
import logging
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from services.factory.authentication import AuthenticationFactory
from services.helper import auth_validation
from setup import redis_setup
from services.providers.mock_provider import MockMessageProvider
from pydantic_validation.authentication import UserLogin, UserLoginEmail, UserSendOtp, UserVerifyOtp, UserLoginResponse
from services.helper.token_service import token_creation
from services.helper.otp_service import send_otp
from pydantic import ValidationError


router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/login", response_model=UserLoginResponse)
async def login_user(payload: UserLogin):
        payload = payload.model_copy(update={"key": "username"})
        return await AuthenticationFactory.get_authentication_service(method="login_credentials", input= payload).authenticate()


@router.post("/login/email", response_model=UserLoginResponse)
async def login_with_email(payload:UserLoginEmail):
        payload = payload.model_copy(update={"key": "email"})
        return await AuthenticationFactory.get_authentication_service(method="login_credentials", input= payload).authenticate()

@router.post("/login/phone", response_model=UserLoginResponse)
async def login_with_phone(payload:UserVerifyOtp):
        return await AuthenticationFactory.get_authentication_service(method="authenticate_phone", input= payload).authenticate()
    
@router.post("/login/otp")
async def login_otp(payload:UserSendOtp):
    return await AuthenticationFactory.get_authentication_service(method="login_phone_otp", input= payload).authenticate()