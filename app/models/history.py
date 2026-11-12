from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id: Mapped[int]= mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int]= mapped_column(sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query: Mapped[str]= mapped_column(sa.String(200), nullable=False)
    query_type: Mapped[str]= mapped_column(sa.String(50), default="city")
    latitude: Mapped[float]= mapped_column(sa.Float, nullable=True)
    longitude: Mapped[float]= mapped_column(sa.Float, nullable=True)
    result_city: Mapped[str]= mapped_column(sa.String(100), nullable=True)
    result_country: Mapped[str]= mapped_column(sa.String(10), nullable=True)
    weather_snapshot: Mapped[dict]= mapped_column(sa.JSON, nullable=True)
    searched_at: Mapped[datetime]= mapped_column(sa.DateTime(timezone=True), server_default= sa.func.now())
    
    user: Mapped["User"]= relationship(back_populates="search_history")