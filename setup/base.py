import fastapi
from app import register,auth
app = fastapi.FastAPI()

app.include_router(register.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
