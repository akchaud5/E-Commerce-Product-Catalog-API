import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "E-Commerce Product Catalog API"
    
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/ecommerce")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret_key_for_dev_only_please_change_in_production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
