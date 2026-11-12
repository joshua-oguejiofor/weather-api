from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FavoriteCity(Base):
    __tablename__ = "favorite_cities"
    
    id: Mapped[int]= mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int]= mapped_column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    city_name: Mapped[str]= mapped_column(sa.String(100), nullable=False)
    country_code: Mapped[str]= mapped_column(sa.String(10), nullable=True)
    latitude: Mapped[float]= mapped_column(sa.Float, nullable=True)
    longitude: Mapped[float]= mapped_column(sa.Float, nullable=True)
    is_default: Mapped[bool]= mapped_column(sa.Boolean, default=False)
    created_at: Mapped[datetime]= mapped_column(sa.DateTime(timezone=True), server_default= sa.func.now())
    
    user: Mapped["User"]= relationship(back_populates="favorites")