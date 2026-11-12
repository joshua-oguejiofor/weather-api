from __future__ import annotations
from .base import LoweredStripedSchema




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
    unit: str


class _ForecastDay(LoweredStripedSchema):
    date: str
    temp_min: float
    temp_max: float
    humidity: int
    description: str
    icon: str
    wind_speed: float
    precipitation_chance: float | None= None


class ForecastResponse(LoweredStripedSchema):
    city: str
    country: str
    forecast: list[_ForecastDay]
    unit: str


class AirQualityResponse(LoweredStripedSchema):
    city: str
    aqi: int
    aqi_label: str
    pm2_5: float | None= None
    pm10: float | None= None
    co: float | None= None
    no2: float | None= None
    o3: float | None= None


class ConvertResponse(LoweredStripedSchema):
    original: float
    from_unit: str
    to_unit: str
    symbol: str
    converted: float
    

