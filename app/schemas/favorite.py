from .base import LoweredStripedSchema
from typing import Optional
from datetime import datetime


class FavoriteCityCreate(LoweredStripedSchema):
    city_name: str
    country_code: str | None= None
    latitude: float | None= None
    longitude: float | None= None
    is_default: bool= False


class FavoriteCityResponse(FavoriteCityCreate):
    id: int
    is_default: bool
    created_at: datetime



class CurrentWeatherResponse(LoweredStripedSchema):
    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: float
    visibility: float
    wind_speed: float
    wind_direction: int
    description: str
    icon: str
    sunrise: str | None= None
    sunset: str | None= None
    unit: str= "metric"