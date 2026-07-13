import logging
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.services.openrouteservice_provider import OpenRouteServiceProvider

logger = logging.getLogger(__name__)

class RouteMatchingProvider(ABC):
    @abstractmethod
    async def match_route(self, points: List[Dict[str, Any]]) -> List[List[float]]:
        pass

class RouteMatchingService:
    def __init__(self, provider_name: Optional[str] = None):
        settings = get_settings()
        self.provider_name = provider_name or settings.route_matching_provider
        self.cache_size = settings.route_matching_cache_size
        self.cache: "OrderedDict[str, List[List[float]]]" = OrderedDict()
        self.provider = self._resolve_provider(settings)

    def _resolve_provider(self, settings: Any) -> RouteMatchingProvider:
        provider_key = (self.provider_name or "openrouteservice").lower()
        if provider_key == "openrouteservice":
            return OpenRouteServiceProvider(settings.ors_url, settings.ors_api_key, settings.ors_profile)
        raise ValueError(f"Unsupported route matching provider: {self.provider_name}")

    def _cache_key(self, points: List[Dict[str, Any]]) -> str:
        return ";".join(f"{p['latitude']:.6f},{p['longitude']:.6f}" for p in points)

    def _get_cached(self, key: str) -> Optional[List[List[float]]]:
        return self.cache.get(key)

    def _set_cached(self, key: str, value: List[List[float]]) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cache_size:
            self.cache.popitem(last=False)

    async def match_route(self, points: List[Dict[str, Any]]) -> List[List[float]]:
        if len(points) < 2:
            return []

        cache_key = self._cache_key(points)
        cached = self._get_cached(cache_key)
        if cached is not None:
            logger.debug("RouteMatchingService cache hit")
            return cached

        try:
            matched = await self.provider.match_route(points)
            self._set_cached(cache_key, matched)
            return matched
        except Exception as e:
            logger.warning("Route matching provider failed: %s", e)
            return []
