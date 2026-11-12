from fastapi import APIRouter, Depends, Query

from app.models.user import User
from app.schemas import weather
from app.services.weather_service import WeatherService
from app.utils.dependencies import get_current_user, get_weather_service

router= APIRouter()






"""Get real-time current weather for a city."""
@router.get("/current", status_code= 200, response_model= weather.CurrentWeatherResponse)
async def get_current_weather(
    city: str,
    unit: str | None= Query(None, pattern= "^(metric|imperial)$", description="metric or imperial"),
    current_user: User= Depends(get_current_user),
    service: WeatherService= Depends(get_weather_service),
):
    
    return await service.get_current_weather(city= city, current_user= current_user, unit= unit)


"""Get current weather by geographic coordinates."""
@router.get("/current/coordinates", status_code= 200, response_model= weather.CurrentWeatherResponse)
async def get_weather_by_coords(
    latitude: float= Query(..., description="Latitude"),
    longitude: float= Query(..., description="Longitude"),
    unit: str | None= Query(None, pattern= "^(metric|imperial)$", description="metric or imperial"),
    current_user: User= Depends(get_current_user),
    service: WeatherService= Depends(get_weather_service),
):
    return await service.get_current_by_coords(lat= latitude, lon= longitude, unit= unit, current_user= current_user)
    

"""Get 5-day weather forecast for a city."""
@router.get("/forecast", status_code= 200, response_model= weather.ForecastResponse)
async def get_forecast(
    city: str,
    unit: str | None= Query(None, pattern= "^(metric|imperial)$", description="metric or imperial"),
    current_user: User= Depends(get_current_user),
    service: WeatherService= Depends(get_weather_service),
):
    
    return await service.get_forecast(city= city, unit= unit, current_user= current_user)


"""Get air quality index (AQI) and pollutant levels for a city."""
@router.get("/air-quality", status_code= 200, response_model= weather.AirQualityResponse)
async def get_air_quality(
    city: str,
    current_user: User= Depends(get_current_user),
    service: WeatherService= Depends(get_weather_service),
):
    return await service.get_air_quality(city)


"""Convert temperature between Celsius (metric) and Fahrenheit (imperial)."""
@router.post("/convert", status_code= 200, response_model= weather.ConvertResponse)
async def convert_temperature(
    value: float,
    from_unit: str= Query(..., pattern= "^(metric|imperial)$", description="Source unit: metric or imperial"),
    to_unit: str= Query(..., pattern= "^(metric|imperial)$", description="Target unit: metric or imperial"),
    current_user: User= Depends(get_current_user),
    service: WeatherService= Depends(get_weather_service),
):
    
    return service.convert_temperature(value, from_unit, to_unit)
   

"""Get active severe weather alerts for a city."""
@router.get("/alerts", status_code= 200)
async def get_weather_alerts(
    city: str,
    current_user: User = Depends(get_current_user),
    service: WeatherService= Depends(get_weather_service)
):
    return await service.get_weather_alerts(city= city, current_user= current_user)

