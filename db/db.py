from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, sessionmaker
from sqlalchemy import create_engine
from typing import Optional


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[Optional[int]]
    name: Mapped[Optional[str]]
    sheet_id: Mapped[Optional[str]]
    execise: Mapped[Optional[str]]
    weight: Mapped[Optional[int]]
    repeats: Mapped[Optional[int]]


engine = create_engine("sqlite:///database.db")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
