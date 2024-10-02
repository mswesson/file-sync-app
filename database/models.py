from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    select,
    DateTime
)

from database.database import Base

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    path = Column(String, unique=True, nullable=False)
    edit_data = Column(DateTime, nullable=False)
    