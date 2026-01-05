from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.core.config import settings

# Create a new SQLAlchemy engine instance
# Fix casing: Settings uses `database_url` (pydantic v2 style)
engine = create_engine(settings.database_url)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a scoped session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()