import sqlalchemy as sa
from datetime import datetime
from app.core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column, Mapped


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int]= mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    email: Mapped[str]= mapped_column(sa.String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str]= mapped_column(sa.String(255), nullable=False)
    role: Mapped[str]= mapped_column(sa.String(10), default="user")
    first_name: Mapped[str]= mapped_column(sa.String(100), nullable=False)
    last_name: Mapped[str]= mapped_column(sa.String(100), nullable=False)
    is_active: Mapped[bool]= mapped_column(sa.Boolean, default=True)
    is_verified: Mapped[bool]= mapped_column(sa.Boolean, default=False)
    preferred_unit: Mapped[str]= mapped_column(sa.String(10), default="metric")
    created_at: Mapped[datetime]= mapped_column(sa.DateTime(timezone=True), server_default= sa.func.now())
    updated_at: Mapped[datetime]= mapped_column(sa.DateTime(timezone=True), server_default= sa.func.now(), onupdate= sa.func.now())
    
    favorites: Mapped[list["FavoriteCity"]]= relationship(back_populates= "user", cascade= "all, delete-orphan")
    search_history: Mapped[list["SearchHistory"]]= relationship(back_populates= "user", cascade= "all, delete-orphan")
