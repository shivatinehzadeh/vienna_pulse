import fastapi
from app import auth,users

app = fastapi.FastAPI()


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
