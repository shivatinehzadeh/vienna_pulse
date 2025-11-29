
import os
import redis
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

def redis_info():
    try:
        redis_client = redis.Redis(
            host='host.docker.internal',  # For Windows Docker Desktop
            port=6379,
            db=0,
            decode_responses=True
        )
        redis_client.ping()
        logger.info("Connected to Redis successfully")
        return redis_client
    except redis.ConnectionError:
        logger.warning("Redis not available")
        redis_client = None
        return redis_client