import jwt
import datetime
import os
import logging
from dotenv import load_dotenv
from fastapi import HTTPException, status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
jwt_secret = os.getenv("SECRET")
jwt_algorithm = os.getenv("ALGORITHM")

async def token_creation(user_id):
    try:
        payload= {
            "sub": str(user_id),
            "exp": datetime.datetime.now() + datetime.timedelta(seconds=90),
            "iat": datetime.datetime.now(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)
        
        if not token:
            logger.error(f"Token creation failed for user ID: {user_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 detail={"Authentication service temporarily unavailable"})
        return {
                "token": token,
                "token_type": "bearer",  
                "user_id": user_id    
            }
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error In Token Creation"})
