from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_async_engine("sqlite+aiosqlite:///database/database.db", echo=False)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    async with async_session() as session:
        yield session
