import json
import logging

import httpx
from fastapi import HTTPException

from app.celery_server import celery_tasks
from app.core.config import settings
from app.core.redis_server import get_cache, set_cache
from app.models import user

from .history_service import HistoryService

logger = logging.getLogger(__name__)

OWM_BASE= "https://api.openweathermap.org/data/2.5"
OWM_AIR_BASE= "https://api.openweathermap.org/data/2.5/air_pollution"
OWM_GEO_BASE= "http://api.openweathermap.org/geo/1.0"
WEATHERAPI_BASE= "https://api.weatherapi.com/v1/forecast.json"

AQI_LABELS = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}


def _unit_param(unit: str) -> str:
    return unit if unit  else "metric"


class WeatherService:
    def __init__(self, history_service: HistoryService= None):
        self.weather_key= settings.WEATHERAPI_KEY.get_secret_value()
        self.owm_key= settings.OPENWEATHERMAP_API_KEY.get_secret_value()
        self.history_service= history_service
    # ------------------------------------------------------------------ #
    #  Current Weather
    # ------------------------------------------------------------------ #
    """weather using city"""
    async def get_current_weather(self, city: str, current_user: user.User, unit: str | None = None) -> dict:
                
        cache_key = f"weather:current:{city}:{_unit_param(unit)}"
        cached = await get_cache(cache_key)
        if cached:
            return json.loads(cached)


        data = await self._owm_current(city= city, unit= _unit_param(unit))
        await set_cache(cache_key, json.dumps(data), expire=settings.WEATHER_CACHE_TTL)
        
        await self.history_service.record_search(
                user_id=current_user.id,
                query= city,
                query_type= "city",
                result_city= data.get("city"),
                result_country= data.get("country"),
                weather_snapshot= {"temp": data.get("temperature"), "desc": data.get("description")},
            )
        return data


    """weather using longitude and latitude"""
    async def get_current_by_coords(
        self, 
        lat: float, 
        lon: float, 
        unit: str,
        current_user: user.User
        ) -> dict:
        
        
        cache_key = f"weather:current:{lat:.2f}:{lon:.2f}:{_unit_param(unit)}"
        cached = await get_cache(cache_key)
        if cached:
            return json.loads(cached)

        data= await self._owm_current(lat=lat, lon=lon, unit= _unit_param(unit))
        
        #This is a forecasted response up to 5 days, caching it up to 6 hours keep data longer
        await set_cache(cache_key, json.dumps(data), expire= 21600)
        
        await self.history_service.record_search(
            lat= lat,
            lon= lon,
            user_id= current_user.id,
            query= f"{lat},{lon}",
            query_type= "coordinates",
            result_city= data.get("city"),
            result_country= data.get("country"),
            weather_snapshot={"temp": data.get("temperature"), "desc": data.get("description")},
        )
        return data

    
    
    async def get_forecast(self, city: str, unit: str, current_user: user.User) -> dict:
                
        cache_key= f"weather:forecast:{city}:{_unit_param(unit)}"
        cached= await get_cache(cache_key)
        if cached:
            return json.loads(cached)
        
        data= await self._owm_forecast(city, _unit_param(unit))
        
        await set_cache(cache_key, json.dumps(data), expire=settings.WEATHER_CACHE_TTL)

        return data


    async def get_air_quality(self, city: str) -> dict:
        
        cache_key = f"weather:air:{city}"
        cached = await get_cache(cache_key)
        if cached:
            return json.loads(cached)

        data= await self._fetch_air_quality(city)
        await set_cache(cache_key, json.dumps(data), expire=settings.WEATHER_CACHE_TTL)
        return data


    async def get_weather_alerts(self, city: str, current_user: user.User) -> dict:
        
        cache_key = f"weather:alerts:{city}"
        cached = await get_cache(cache_key)
        if cached:
            return json.loads(cached)
        
        result= {}
        
        result= await self._fetch_weather_alerts(city)
        await set_cache(cache_key, json.dumps(result), expire=settings.WEATHER_CACHE_TTL)
        
        if result.get("alerts"):
            first_alert= result["alerts"][0]
            
            # celery sends the email as background job
            celery_tasks.send_severe_weather_alert_task.delay(
                current_user.email, 
                city, 
                first_alert["event"], 
                first_alert["description"],
                current_user.first_name
                )
            
        # Extracts the response from the helper function
            return {
                "msg": f"{result.get('msg')}",
                "city": result.get("city"),
                "alerts": result.get("alerts"),
                "amount": result.get("count")
                } 
         
        return {"msg": f"No active alerts for {city}."}
        

    
    # Dosen't need async because it's a simple calculation and doesn't involve I/O operations.
    def convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        
        result= {
            "original": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "symbol": "°C" if to_unit == "metric" else "°F",
            }
        
        if from_unit == to_unit:
            result.update({"converted": round(value, 2)})
            return result
        
        if from_unit == "metric" and to_unit == "imperial":
            result.update({"converted": round(value * 9 / 5 + 32, 2)}) 
            return result
        
        if from_unit == "imperial" and to_unit == "metric":
            result.update({"converted": round((value - 32) * 5 / 9, 2)}) 
            return result
        # if no conditions are met, raise an exception for invalid unit conversion
        raise HTTPException(status_code=400, detail="Invalid unit conversion")

   
    async def _owm_current(self, unit: str, city: str | None = None, lat: float | None = None, lon: float | None = None) -> dict:
        #Params is
        
        params = {"appid": self.owm_key, "units": unit}
        if city:
            params["q"] = city
        else:
            params.update({"lat": lat, "lon": lon})

        async with httpx.AsyncClient(timeout=10) as client:
            for attempt in range(3):
                try:
                    r = await client.get(f"{OWM_BASE}/weather", params=params)
                    if r.status_code == 404:
                        raise HTTPException(status_code=404, detail="City not found")
                    r.raise_for_status()
                    d = r.json()
                    
                    return {
                        "city": d["name"],
                        "country": d["sys"]["country"],
                        "temperature": d["main"]["temp"],
                        "feels_like": d["main"]["feels_like"],
                        "humidity": d["main"]["humidity"],
                        "pressure": d["main"]["pressure"],
                        "visibility": d.get("visibility", 0) / 1000,
                        "wind_speed": d["wind"]["speed"],
                        "wind_direction": d["wind"].get("deg", 0),
                        "description": d["weather"][0]["description"].title(),
                        "icon": f"https://openweathermap.org/img/wn/{d['weather'][0]['icon']}@2x.png",
                        "sunrise": str(d["sys"].get("sunrise", "")),
                        "sunset": str(d["sys"].get("sunset", "")),
                        "unit": unit,
                    }
                except httpx.TimeoutException:
                    if attempt == 2: # 2 mathing the last attempt (0,1,2)
                        raise HTTPException(status_code= 503, detail= "Weather service timeout")


    async def _owm_forecast(self, city: str, unit: str) -> dict:
        
        params = {"q": city, "appid": self.owm_key, "units": unit, "cnt": 40}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{OWM_BASE}/forecast", params=params)
            if r.status_code == 404:
                raise HTTPException(status_code=404, detail="City not found")
            r.raise_for_status()
            d = r.json()

        # Aggregate into daily buckets
        days: dict = {}
        for item in d["list"]:
            date = item["dt_txt"].split(" ")[0]
            if date not in days:
                days[date] = {"temps": [], "humidity": [], "descriptions": [], "icons": [], "wind": [], "pop": []}
            days[date]["temps"].append(item["main"]["temp"])
            days[date]["humidity"].append(item["main"]["humidity"])
            days[date]["descriptions"].append(item["weather"][0]["description"].title())
            days[date]["icons"].append(item["weather"][0]["icon"])
            days[date]["wind"].append(item["wind"]["speed"])
            days[date]["pop"].append(item.get("pop", 0))

        forecast= []
        for date, v in list(days.items())[:5]:
            forecast.append({
                "date": date,
                "temp_min": round(min(v["temps"]), 1),
                "temp_max": round(max(v["temps"]), 1),
                "humidity": int(sum(v["humidity"]) / len(v["humidity"])),
                "description": max(set(v["descriptions"]), key=v["descriptions"].count),
                "icon": f"https://openweathermap.org/img/wn/{v['icons'][0]}@2x.png",
                "wind_speed": round(sum(v["wind"]) / len(v["wind"]), 1),
                "precipitation_chance": round(max(v["pop"]) * 100, 1),
            })

        return {"city": d["city"]["name"], "country": d["city"]["country"], "forecast": forecast, "unit": unit}
    
    
    async def _geocode_city(self, city: str):
        async with httpx.AsyncClient(timeout=10) as client:
            geo= await client.get(f"{OWM_GEO_BASE}/direct", params={"q": city, "limit": 1, "appid": self.owm_key})
            geo.raise_for_status()
            locations= geo.json()
            if not locations:
                raise HTTPException(status_code=404, detail="City not found")
            
            return {"lat": locations[0]["lat"], "lon": locations[0]["lon"]}
    
    

    async def _fetch_air_quality(self, city: str) -> dict:
        # First geocode the city
        
        async with httpx.AsyncClient(timeout=10) as client:
            gecoded_city= await self._geocode_city(city)
        
            r = await client.get(OWM_AIR_BASE, params={"lat": gecoded_city.get("lat"), "lon": gecoded_city.get("lon"), "appid": self.owm_key})
            r.raise_for_status()
            d = r.json()
            print("Air quality data: ", d)
        comp = d["list"][0]["components"]
        aqi = d["list"][0]["main"]["aqi"]
        return {
            "city": city,
            "aqi": aqi,
            "aqi_label": AQI_LABELS.get(aqi, "Unknown"),
            "pm2_5": comp.get("pm2_5"),
            "pm10": comp.get("pm10"),
            "co": comp.get("co"),
            "no2": comp.get("no2"),
            "o3": comp.get("o3"),
        }


    """Fetch active government weather alerts for a given location using WeatherAPI.com."""
    async def _fetch_weather_alerts(self, city: str):
        
        async with httpx.AsyncClient(timeout=10) as client:
            gecoded_city= await self._geocode_city(city)
               
            q = f"{gecoded_city.get("lat")},{gecoded_city.get("lon")}"
            params = {"key": self.weather_key, "q": q, "days": 1, "alerts": "yes"}

            response = await client.get(WEATHERAPI_BASE, params=params, timeout=10)
            response.raise_for_status()
            data= response.json()
    
        #  Validate location data returned
        if "location" not in data:
            raise HTTPException(status_code= 400, detail= "Invalid response recieved")
            
        location_info= data["location"]
        location_name= location_info.get('name')

        #Check if 'alerts' container exists in the payload
        alerts_data= data.get("alerts", {}).get("alert", [])

        if not alerts_data:
            return {"msg": f"No active severe weather alerts for {location_name}."}
                
        # Process alerts into structured format
        alerts= []
        
        for alert in alerts_data:
            alerts.append({
                "event": alert.get("event", "General Alert"),
                "severity": alert.get("severity", "Unknown Severity"),
                "start": alert.get("effective", "N/A"),
                "end": alert.get("expires", "N/A"),
                "description": alert.get("desc", "No detailed description provided.")
            })
            
        return{
            "msg": f"Found {len(alerts_data)} active weather alert(s) for {location_name}.",
            "city": location_name, 
            "alerts": alerts, 
            "count": len(alerts_data)
            }
    
   