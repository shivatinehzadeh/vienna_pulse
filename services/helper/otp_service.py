import logging
import random 
from setup import redis_setup
from fastapi import HTTPException, status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_otp(phone_number: str):
    try:
        redis_client = redis_setup.redis_info()
        if not redis_client:
            logger.warning("Redis is not working right now")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})  
        get_cached_phone = redis_client.get(phone_number)
        if get_cached_phone:
            logger.warning(f"otp request in 90 seconds for {phone_number}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail={"message":"You can not send two request in 90 seconds"})
        else:
            otp_length = 6
            otp_creation = ''.join([str(random.randint(0, 9)) for _ in range(otp_length)])
            redis_client.setex(phone_number, 90, otp_creation)
            return otp_creation
    except HTTPException:
        raise 
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={"message":"Internal Server Error"})
