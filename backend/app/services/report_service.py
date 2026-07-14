import asyncio
import logging
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx

from app.services.tracking_service import TrackingService

logger = logging.getLogger(__name__)


@dataclass
class Journey:
    """Continuous trip built from moving GPS segments only."""
    start_time: datetime
    end_time: datetime
    points: List[Dict]
    total_distance_km: float = 0.0
    total_time_seconds: float = 0.0
    max_speed_kmh: float = 0.0
    segments: Optional[List[Dict]] = None

    @property
    def average_speed_kmh(self) -> float:
        if self.total_time_seconds <= 0:
            return 0.0
        return self.total_distance_km / (self.total_time_seconds / 3600)

    @property
    def duration_minutes(self) -> float:
        return self.total_time_seconds / 60


class ReportService:
    LONG_INACTIVITY_THRESHOLD_MINUTES = 30
    SHORT_STOP_THRESHOLD_MINUTES = 2
    MIN_MOVEMENT_DISTANCE_M = 60
    MIN_SPEED_KMH = 1.0

    @staticmethod
    def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        return TrackingService.haversine(lon1, lat1, lon2, lat2)

    @classmethod
    def identify_journeys(
        cls,
        positions_data: List[Dict],
        inactivity_threshold_minutes: Optional[int] = None,
    ) -> List[Journey]:
        if inactivity_threshold_minutes is None:
            inactivity_threshold_minutes = cls.LONG_INACTIVITY_THRESHOLD_MINUTES

        segments = cls._build_segments(positions_data)
        if not segments:
            return []

        journeys: List[Journey] = []
        current_segments: List[Dict] = []
        stopped_seconds = 0.0

        for segment in segments:
            if segment["is_moving"]:
                if current_segments and stopped_seconds / 60 >= inactivity_threshold_minutes:
                    journey = cls._build_journey_from_segments(current_segments)
                    if journey:
                        journeys.append(journey)
                    current_segments = []

                current_segments.append(segment)
                stopped_seconds = 0.0
            elif current_segments:
                stopped_seconds += segment["time_seconds"]

        if current_segments:
            journey = cls._build_journey_from_segments(current_segments)
            if journey:
                journeys.append(journey)

        logger.info("Identificadas %s viagens em %s pontos", len(journeys), len(positions_data))
        return journeys

    @classmethod
    def calculate_report_metrics(
        cls,
        positions_data: List[Dict],
        inactivity_threshold_minutes: Optional[int] = None,
    ) -> Dict:
        journeys = cls.identify_journeys(positions_data, inactivity_threshold_minutes)

        if not journeys:
            return {
                "total_distance_km": 0.0,
                "total_time_minutes": 0.0,
                "average_speed_kmh": 0.0,
                "max_speed_kmh": 0.0,
                "journeys_count": 0,
                "journeys": [],
            }

        total_distance = sum(journey.total_distance_km for journey in journeys)
        total_time_seconds = sum(journey.total_time_seconds for journey in journeys)
        max_speed = max((journey.max_speed_kmh for journey in journeys), default=0.0)
        avg_speed = (total_distance / (total_time_seconds / 3600)) if total_time_seconds > 0 else 0.0

        return {
            "total_distance_km": round(total_distance, 2),
            "total_time_minutes": round(total_time_seconds / 60, 1),
            "average_speed_kmh": round(avg_speed, 1),
            "max_speed_kmh": round(max_speed, 1),
            "journeys_count": len(journeys),
            "journeys": [
                {
                    "start_time": journey.start_time,
                    "end_time": journey.end_time,
                    "duration_minutes": round(journey.duration_minutes, 1),
                    "distance_km": round(journey.total_distance_km, 2),
                    "average_speed_kmh": round(journey.average_speed_kmh, 1),
                    "max_speed_kmh": journey.max_speed_kmh,
                }
                for journey in journeys
            ],
        }

    @classmethod
    def identify_stops(
        cls,
        positions_data: List[Dict],
        min_stop_duration_minutes: int = 2,
    ) -> List[Dict]:
        segments = cls._build_segments(positions_data)
        if not segments:
            return []

        stops: List[Dict] = []
        current_stop_segments: List[Dict] = []

        for segment in segments:
            if segment["is_moving"]:
                cls._append_stop(stops, current_stop_segments, min_stop_duration_minutes)
                current_stop_segments = []
            else:
                current_stop_segments.append(segment)

        cls._append_stop(stops, current_stop_segments, min_stop_duration_minutes)
        logger.info("Identificadas %s paradas", len(stops))
        return stops

    @classmethod
    def enrich_route_points(cls, positions_data: List[Dict]) -> List[Dict]:
        journeys = cls.identify_journeys(positions_data)
        enriched = []

        for journey_index, journey in enumerate(journeys, start=1):
            journey_segments = cls._segments_for_journey(journey)
            if not journey_segments:
                continue

            enriched.append({
                "position": journey_segments[0]["prev"],
                "journey_index": journey_index,
                "is_journey_start": True,
                "is_journey_end": False,
                "segment_distance_km": 0.0,
                "segment_time_seconds": 0.0,
                "segment_speed_kmh": 0.0,
            })

            for segment_index, segment in enumerate(journey_segments):
                enriched.append({
                    "position": segment["curr"],
                    "journey_index": journey_index,
                    "is_journey_start": False,
                    "is_journey_end": segment_index == len(journey_segments) - 1,
                    "segment_distance_km": segment["distance_m"] / 1000,
                    "segment_time_seconds": segment["time_seconds"],
                    "segment_speed_kmh": segment["speed_kmh"],
                })

        if enriched:
            return enriched

        return [
            {
                "position": position,
                "journey_index": None,
                "is_journey_start": False,
                "is_journey_end": False,
                "segment_distance_km": 0.0,
                "segment_time_seconds": 0.0,
                "segment_speed_kmh": 0.0,
            }
            for position in cls._sorted_positions(positions_data)
        ]

    @classmethod
    def _segments_for_journey(cls, journey: Journey) -> List[Dict]:
        if journey.segments is not None:
            return journey.segments

        journey_start = journey.start_time
        journey_end = journey.end_time
        return [
            segment
            for segment in cls._build_segments(journey.points)
            if segment["is_moving"]
            and segment["prev_time"] >= journey_start
            and segment["curr_time"] <= journey_end
        ]

    @classmethod
    def _build_segments(cls, positions_data: List[Dict]) -> List[Dict]:
        sorted_positions = cls._sorted_positions(positions_data)
        segments = []

        for index in range(1, len(sorted_positions)):
            prev = sorted_positions[index - 1]
            curr = sorted_positions[index]
            prev_time = cls._position_time(prev)
            curr_time = cls._position_time(curr)

            if not prev_time or not curr_time:
                continue

            time_seconds = (curr_time - prev_time).total_seconds()
            if time_seconds <= 0:
                continue

            if not cls._has_coordinates(prev) or not cls._has_coordinates(curr):
                continue

            distance_m = cls.haversine(
                prev.get("longitude"),
                prev.get("latitude"),
                curr.get("longitude"),
                curr.get("latitude"),
            )
            inferred_speed_kmh = (distance_m / 1000) / (time_seconds / 3600)
            gps_speed_kmh = cls._speed_kmh(curr)
            speed_kmh = max(inferred_speed_kmh, gps_speed_kmh or 0.0)
            is_moving = (
                distance_m >= cls.MIN_MOVEMENT_DISTANCE_M
                and speed_kmh >= cls.MIN_SPEED_KMH
            )

            segments.append({
                "prev": prev,
                "curr": curr,
                "prev_time": prev_time,
                "curr_time": curr_time,
                "time_seconds": time_seconds,
                "distance_m": distance_m,
                "speed_kmh": speed_kmh,
                "is_moving": is_moving,
            })

        return segments

    @classmethod
    def _build_journey_from_segments(cls, segments: List[Dict]) -> Optional[Journey]:
        if not segments:
            return None

        points = [segments[0]["prev"]]
        points.extend(segment["curr"] for segment in segments)
        total_distance_m = sum(segment["distance_m"] for segment in segments)
        total_time_seconds = sum(segment["time_seconds"] for segment in segments)
        max_speed = max((segment["speed_kmh"] for segment in segments), default=0.0)

        return Journey(
            start_time=segments[0]["prev_time"],
            end_time=segments[-1]["curr_time"],
            points=points,
            total_distance_km=total_distance_m / 1000,
            total_time_seconds=total_time_seconds,
            max_speed_kmh=round(max_speed, 1),
            segments=segments,
        )

    _reverse_geocode_cache: "OrderedDict[Tuple[float, float], Optional[str]]" = OrderedDict()
    REVERSE_GEOCODING_CACHE_SIZE = 256
    REVERSE_GEOCODING_URL = "https://nominatim.openstreetmap.org/reverse"

    @classmethod
    def _append_stop(cls, stops: List[Dict], stop_segments: List[Dict], min_stop_duration_minutes: int):
        if not stop_segments:
            return

        duration_minutes = sum(segment["time_seconds"] for segment in stop_segments) / 60
        if duration_minutes < min_stop_duration_minutes:
            return

        positions = [stop_segments[0]["prev"]]
        positions.extend(segment["curr"] for segment in stop_segments)
        latitude = sum(position.get("latitude") for position in positions) / len(positions)
        longitude = sum(position.get("longitude") for position in positions) / len(positions)
        middle_position = positions[len(positions) // 2]

        stops.append({
            "latitude": latitude,
            "longitude": longitude,
            "start_time": stop_segments[0]["prev_time"],
            "end_time": stop_segments[-1]["curr_time"],
            "duration_minutes": round(duration_minutes, 1),
            "address": cls._position_address(middle_position),
        })

    @classmethod
    def _reverse_geocode_cache_key(cls, latitude: float, longitude: float) -> Tuple[float, float]:
        return (round(latitude, 6), round(longitude, 6))

    @classmethod
    async def reverse_geocode_coordinates(cls, latitude: float, longitude: float) -> Optional[str]:
        key = cls._reverse_geocode_cache_key(latitude, longitude)
        if key in cls._reverse_geocode_cache:
            cls._reverse_geocode_cache.move_to_end(key)
            return cls._reverse_geocode_cache[key]

        params = {
            "format": "json",
            "lat": latitude,
            "lon": longitude,
            "zoom": 18,
            "addressdetails": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(cls.REVERSE_GEOCODING_URL, params=params, headers={"User-Agent": "TTLField/1.0"})
                if response.status_code != 200:
                    logger.warning("Reverse geocoding failed for %s,%s: HTTP %s", latitude, longitude, response.status_code)
                    address = None
                else:
                    data = response.json()
                    address = data.get("display_name") if isinstance(data, dict) else None
        except Exception as exc:
            logger.warning("Reverse geocoding error for %s,%s: %s", latitude, longitude, exc)
            address = None

        cls._reverse_geocode_cache[key] = address
        if len(cls._reverse_geocode_cache) > cls.REVERSE_GEOCODING_CACHE_SIZE:
            cls._reverse_geocode_cache.popitem(last=False)
        return address

    @classmethod
    async def ensure_stop_addresses(cls, stops: List[Dict]) -> None:
        if not stops:
            return

        coords_to_task: Dict[Tuple[float, float], asyncio.Task] = {}
        for stop in stops:
            if stop.get("address"):
                continue
            coord_key = cls._reverse_geocode_cache_key(stop["latitude"], stop["longitude"])
            if coord_key not in coords_to_task:
                coords_to_task[coord_key] = asyncio.create_task(
                    cls.reverse_geocode_coordinates(stop["latitude"], stop["longitude"])
                )

        if not coords_to_task:
            return

        await asyncio.gather(*coords_to_task.values())

        for stop in stops:
            if stop.get("address"):
                continue
            coord_key = cls._reverse_geocode_cache_key(stop["latitude"], stop["longitude"])
            stop["address"] = coords_to_task[coord_key].result()

    @classmethod
    def _sorted_positions(cls, positions_data: List[Dict]) -> List[Dict]:
        return sorted(positions_data, key=lambda position: cls._position_time(position) or datetime.min)

    @classmethod
    def _position_time(cls, position: Dict) -> Optional[datetime]:
        return cls._parse_datetime(
            position.get("fixTime") or position.get("serverTime") or position.get("timestamp")
        )

    @staticmethod
    def _has_coordinates(position: Dict) -> bool:
        return all(position.get(key) is not None for key in ["latitude", "longitude"])

    @staticmethod
    def _speed_kmh(position: Dict) -> Optional[float]:
        speed = position.get("speed")
        if speed is None:
            return None
        return float(speed) * 3.6

    @staticmethod
    def _position_address(position: Dict) -> Optional[str]:
        return position.get("address") or position.get("attributes", {}).get("address")

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        if not value:
            return None
        try:
            if isinstance(value, datetime):
                return value.replace(tzinfo=None)
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, AttributeError):
            return None
