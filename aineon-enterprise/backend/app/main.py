from fastapi import FastAPI
from .db import engine, Base
from .api.v1.routes import auth, users, status, data, admin

# This will create the tables in the database
# In a production environment, you would use migrations (e.g., Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aineon Enterprise API", version="1.0.0")

app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(status.router, prefix="/api/v1", tags=["Status"])
app.include_router(data.router, prefix="/api/v1", tags=["Data"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Aineon Enterprise API"}

