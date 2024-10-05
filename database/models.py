from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
)

from database.database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    path = Column(String, unique=True, nullable=False)
    edit_date = Column(DateTime, nullable=False)
