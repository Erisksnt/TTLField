import logging
from typing import Any, Dict, List
import httpx

logger = logging.getLogger(__name__)

class OpenRouteServiceProvider:
    def __init__(self, base_url: str, api_key: str, profile: str = "driving-car"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.profile = profile

    async def match_route(self, points: List[Dict[str, Any]]) -> List[List[float]]:
        if not self.api_key:
            raise RuntimeError("ORS API key is not configured")

        if len(points) < 2:
            return []

        coordinates = [[p["longitude"], p["latitude"]] for p in points]
        payload = {
            "coordinates": coordinates,
            "instructions": False,
            "geometry_simplify": False,
            "units": "km",
            "preference": "fastest",
        }

        url = f"{self.base_url}/v2/directions/{self.profile}/geojson"
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                body = response.text[:500]
                raise RuntimeError(f"ORS request failed: {response.status_code} {body}")

            data = response.json()

        features = data.get("features") or []
        if not features:
            return []

        geometry = features[0].get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        if not coordinates:
            return []

        # Leaflet expects [lat, lng] coordinate order for Polyline positions.
        return [[coord[1], coord[0]] for coord in coordinates]
