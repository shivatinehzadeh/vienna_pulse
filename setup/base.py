import fastapi
from app import register,auth,users

app = fastapi.FastAPI()


app.include_router(register.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
