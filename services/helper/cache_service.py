from cachetools import TTLCache
from cachetools.keys import hashkey
import logging

from setup.database_setup import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create cache
user_cache = TTLCache(maxsize=120, ttl=60)

def get_cache_key(method):
    if method == "all_users":
        return hashkey("users", "all")

async def get_cached_users(method):
    cache_key = get_cache_key(method)
    
    # Check cache
    if cache_key in user_cache:
        logger.info("CACHE HIT (cachetools)")
        return user_cache[cache_key]
    
    else: 
        return None