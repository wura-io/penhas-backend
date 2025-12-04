"""
Geolocation / Geocoding services
Port from Perl Penhas::Helpers::Geolocation and Penhas::Helpers::GeolocationCached
Integrates with Google Maps and HERE Maps APIs
"""
import httpx
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.config import settings
from app.models.geo import GeoCache
from app.core.redis_client import redis_client


class GeolocationService:
    """
    Geocoding service with multiple providers and caching
    Matches Perl's Penhas::Helpers::Geolocation
    """
    
    def __init__(self):
        self.google_api_key = settings.GOOGLE_MAPS_API_KEY
        self.here_api_key = settings.HERE_API_KEY
        self.timeout = 30
    
    async def geocode_address(
        self,
        db: AsyncSession,
        street: str,
        number: str,
        city: str,
        state: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Geocode address using Google Maps or HERE
        With caching support
        """
        # Build address string
        address = f"{street}, {number}, {city}, {state}, Brazil"
        
        if use_cache:
            # Check cache first
            cached = await self._get_cached(db, address)
            if cached:
                return cached
        
        # Try Google Maps first
        result = await self._geocode_google(address)
        
        # Fallback to HERE Maps
        if not result:
            result = await self._geocode_here(address)
        
        # Store in cache
        if result and use_cache:
            await self._store_cache(db, address, result)
        
        return result
    
    async def _geocode_google(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Geocode using Google Maps Geocoding API
        Matches Perl's Google Maps integration
        """
        if not self.google_api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={
                        "address": address,
                        "key": self.google_api_key,
                        "language": "pt-BR",
                        "region": "br"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "OK" and data.get("results"):
                    location = data["results"][0]["geometry"]["location"]
                    return {
                        "latitude": str(location["lat"]),
                        "longitude": str(location["lng"]),
                        "provider": "google",
                        "formatted_address": data["results"][0].get("formatted_address")
                    }
                
                return None
                
        except httpx.HTTPStatusError as e:
            print(f"Google Maps HTTP error: {e}")
            return None
        except httpx.RequestError as e:
            print(f"Google Maps request error: {e}")
            return None
        except Exception as e:
            print(f"Google Maps unexpected error: {e}")
            return None
    
    async def _geocode_here(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Geocode using HERE Maps Geocoding API
        Matches Perl's HERE Maps integration
        """
        if not self.here_api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://geocode.search.hereapi.com/v1/geocode",
                    params={
                        "q": address,
                        "apiKey": self.here_api_key,
                        "lang": "pt-BR",
                        "in": "countryCode:BRA"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("items") and len(data["items"]) > 0:
                    item = data["items"][0]
                    position = item["position"]
                    return {
                        "latitude": str(position["lat"]),
                        "longitude": str(position["lng"]),
                        "provider": "here",
                        "formatted_address": item.get("title")
                    }
                
                return None
                
        except httpx.HTTPStatusError as e:
            print(f"HERE Maps HTTP error: {e}")
            return None
        except httpx.RequestError as e:
            print(f"HERE Maps request error: {e}")
            return None
        except Exception as e:
            print(f"HERE Maps unexpected error: {e}")
            return None
    
    async def _get_cached(
        self,
        db: AsyncSession,
        address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get geocoded result from cache
        Matches Perl's GeolocationCached
        """
        # Try Redis first
        cache_key = f"geocode:{address}"
        cached_value = await redis_client.get(cache_key)
        
        if cached_value:
            import json
            return json.loads(cached_value)
        
        # Try database cache
        result = await db.execute(
            select(GeoCache)
            .where(GeoCache.address == address)
        )
        geo_cache = result.scalar_one_or_none()
        
        if geo_cache:
            cached_data = {
                "latitude": geo_cache.latitude,
                "longitude": geo_cache.longitude,
                "provider": geo_cache.provider,
                "formatted_address": geo_cache.formatted_address
            }
            
            # Store back in Redis for faster access next time
            import json
            await redis_client.setex(
                cache_key,
                86400 * 30,  # 30 days
                json.dumps(cached_data)
            )
            
            return cached_data
        
        return None
    
    async def _store_cache(
        self,
        db: AsyncSession,
        address: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Store geocoded result in cache
        """
        # Store in database
        geo_cache = GeoCache(
            address=address,
            latitude=result["latitude"],
            longitude=result["longitude"],
            provider=result.get("provider"),
            formatted_address=result.get("formatted_address"),
            created_at=datetime.utcnow()
        )
        db.add(geo_cache)
        await db.commit()
        
        # Store in Redis
        cache_key = f"geocode:{address}"
        import json
        await redis_client.setex(
            cache_key,
            86400 * 30,  # 30 days
            json.dumps(result)
        )
    
    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates to address
        """
        # Try Google Maps first
        result = await self._reverse_geocode_google(latitude, longitude)
        
        # Fallback to HERE Maps
        if not result:
            result = await self._reverse_geocode_here(latitude, longitude)
        
        return result
    
    async def _reverse_geocode_google(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """Reverse geocode using Google Maps"""
        if not self.google_api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={
                        "latlng": f"{latitude},{longitude}",
                        "key": self.google_api_key,
                        "language": "pt-BR"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "OK" and data.get("results"):
                    return {
                        "formatted_address": data["results"][0].get("formatted_address"),
                        "provider": "google"
                    }
                
                return None
                
        except Exception as e:
            print(f"Google Maps reverse geocode error: {e}")
            return None
    
    async def _reverse_geocode_here(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """Reverse geocode using HERE Maps"""
        if not self.here_api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://revgeocode.search.hereapi.com/v1/revgeocode",
                    params={
                        "at": f"{latitude},{longitude}",
                        "apiKey": self.here_api_key,
                        "lang": "pt-BR"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("items") and len(data["items"]) > 0:
                    return {
                        "formatted_address": data["items"][0].get("title"),
                        "provider": "here"
                    }
                
                return None
                
        except Exception as e:
            print(f"HERE Maps reverse geocode error: {e}")
            return None


# Singleton instance
geolocation_service = GeolocationService()

