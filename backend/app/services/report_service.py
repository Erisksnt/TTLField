import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from app.services.tracking_service import TrackingService

logger = logging.getLogger(__name__)


@dataclass
class Journey:
    """Representa uma viagem contínua (sem pausas longas)"""
    start_time: datetime
    end_time: datetime
    points: List[Dict]  # Lista de pontos da viagem
    total_distance_km: float = 0.0
    total_time_seconds: float = 0.0
    max_speed_kmh: float = 0.0
    
    @property
    def average_speed_kmh(self) -> float:
        """Calcula velocidade média corretamente: distância / tempo"""
        if self.total_time_seconds <= 0:
            return 0.0
        return (self.total_distance_km / (self.total_time_seconds / 3600))
    
    @property
    def duration_minutes(self) -> float:
        return self.total_time_seconds / 60


class ReportService:
    LONG_INACTIVITY_THRESHOLD_MINUTES = 30  # Parada que encerra uma viagem
    SHORT_STOP_THRESHOLD_MINUTES = 2  # Parada dentro de uma viagem
    MIN_MOVEMENT_DISTANCE_M = 60  # Distância mínima para considerar movimento (evita GPS jitter)
    MIN_SPEED_KMH = 1.0  # Velocidade mínima para contar movimento
    
    @staticmethod
    def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """Calcula distância em metros entre dois pontos"""
        return TrackingService.haversine(lon1, lat1, lon2, lat2)
    
    @classmethod
    def identify_journeys(
        cls,
        positions_data: List[Dict],
        inactivity_threshold_minutes: Optional[int] = None,
    ) -> List[Journey]:
        """
        Identifica viagens separando-as por períodos de inatividade longa.
        
        Args:
            positions_data: Lista de dicts com posições (deve ter 'fixTime', 'latitude', 'longitude')
            inactivity_threshold_minutes: Minutos sem movimento para encerrar viagem (default: 30)
        
        Returns:
            Lista de Journey objects
        """
        if inactivity_threshold_minutes is None:
            inactivity_threshold_minutes = cls.LONG_INACTIVITY_THRESHOLD_MINUTES
        
        if not positions_data or len(positions_data) < 2:
            return []
        
        # Ordenar por timestamp
        sorted_positions = sorted(
            positions_data,
            key=lambda p: p.get("fixTime") or p.get("serverTime") or ""
        )
        
        journeys = []
        current_journey_points = [sorted_positions[0]]
        journey_start_time = cls._parse_datetime(sorted_positions[0].get("fixTime") or sorted_positions[0].get("serverTime"))
        
        for i in range(1, len(sorted_positions)):
            prev = sorted_positions[i - 1]
            curr = sorted_positions[i]
            
            prev_time = cls._parse_datetime(prev.get("fixTime") or prev.get("serverTime"))
            curr_time = cls._parse_datetime(curr.get("fixTime") or curr.get("serverTime"))
            
            if not prev_time or not curr_time:
                continue
            
            time_diff_minutes = (curr_time - prev_time).total_seconds() / 60
            
            # Verificar se houve inatividade longa
            if time_diff_minutes >= inactivity_threshold_minutes:
                # Finalizar viagem atual
                if len(current_journey_points) > 1:
                    journey = cls._build_journey(current_journey_points)
                    if journey:
                        journeys.append(journey)
                
                # Iniciar nova viagem
                current_journey_points = [curr]
                journey_start_time = curr_time
            else:
                # Continuar mesma viagem
                current_journey_points.append(curr)
        
        # Finalizar última viagem
        if len(current_journey_points) > 1:
            journey = cls._build_journey(current_journey_points)
            if journey:
                journeys.append(journey)
        
        logger.info(f"🚗 Identificadas {len(journeys)} viagens em {len(positions_data)} pontos")
        return journeys
    
    @classmethod
    def _build_journey(cls, points: List[Dict]) -> Optional[Journey]:
        """Constrói objeto Journey a partir de pontos"""
        if len(points) < 2:
            return None
        
        start_time = cls._parse_datetime(points[0].get("fixTime") or points[0].get("serverTime"))
        end_time = cls._parse_datetime(points[-1].get("fixTime") or points[-1].get("serverTime"))
        
        if not start_time or not end_time:
            return None
        
        total_distance = 0.0
        max_speed = 0.0
        
        for i in range(1, len(points)):
            prev = points[i - 1]
            curr = points[i]
            
            # Validar coordenadas
            if not all(key in prev and prev[key] is not None for key in ["latitude", "longitude"]):
                continue
            if not all(key in curr and curr[key] is not None for key in ["latitude", "longitude"]):
                continue
            
            # Calcular distância
            dist_m = cls.haversine(
                prev.get("longitude"), prev.get("latitude"),
                curr.get("longitude"), curr.get("latitude")
            )
            total_distance += dist_m
            
            # Velocidade máxima
            if curr.get("speed") is not None:
                speed_kmh = curr["speed"] * 3.6
                if speed_kmh > max_speed:
                    max_speed = speed_kmh
        
        total_time_seconds = (end_time - start_time).total_seconds()
        
        journey = Journey(
            start_time=start_time,
            end_time=end_time,
            points=points,
            total_distance_km=total_distance / 1000,
            total_time_seconds=total_time_seconds,
            max_speed_kmh=round(max_speed, 1)
        )
        
        logger.debug(
            f"Viagem: {journey.duration_minutes:.1f}min, "
            f"{journey.total_distance_km:.2f}km, "
            f"{journey.average_speed_kmh:.1f}km/h"
        )
        
        return journey
    
    @classmethod
    def calculate_report_metrics(
        cls,
        positions_data: List[Dict],
        inactivity_threshold_minutes: Optional[int] = None,
    ) -> Dict:
        """
        Calcula métricas do relatório baseado em viagens identificadas.
        
        Returns:
            Dict com métricas agregadas
        """
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
        
        # Agregar métricas
        total_distance = sum(j.total_distance_km for j in journeys)
        total_time_seconds = sum(j.total_time_seconds for j in journeys)
        max_speed = max((j.max_speed_kmh for j in journeys), default=0.0)
        
        # Velocidade média correta: distância total / tempo total em movimento
        avg_speed = (total_distance / (total_time_seconds / 3600)) if total_time_seconds > 0 else 0.0
        
        logger.info(
            f"Relatório Final: "
            f"distância={total_distance:.2f}km, "
            f"tempo={total_time_seconds/60:.1f}min, "
            f"vel_média={avg_speed:.1f}km/h, "
            f"viagens={len(journeys)}"
        )
        
        return {
            "total_distance_km": round(total_distance, 2),
            "total_time_minutes": round(total_time_seconds / 60, 1),
            "average_speed_kmh": round(avg_speed, 1),
            "max_speed_kmh": round(max_speed, 1),
            "journeys_count": len(journeys),
            "journeys": [
                {
                    "start_time": j.start_time,
                    "end_time": j.end_time,
                    "duration_minutes": round(j.duration_minutes, 1),
                    "distance_km": round(j.total_distance_km, 2),
                    "average_speed_kmh": round(j.average_speed_kmh, 1),
                    "max_speed_kmh": j.max_speed_kmh,
                }
                for j in journeys
            ]
        }
    
    @classmethod
    def identify_stops(
        cls,
        positions_data: List[Dict],
        min_stop_duration_minutes: int = 2,
    ) -> List[Dict]:
        """
        Identifica pontos de parada dentro das viagens.
        
        Args:
            positions_data: Lista de posições
            min_stop_duration_minutes: Duração mínima para considerar parada
        
        Returns:
            Lista de paradas com informações de localização e duração
        """
        if not positions_data or len(positions_data) < 2:
            return []
        
        sorted_positions = sorted(
            positions_data,
            key=lambda p: p.get("fixTime") or p.get("serverTime") or ""
        )
        
        stops = []
        i = 0
        
        while i < len(sorted_positions):
            curr = sorted_positions[i]
            
            if i + 1 >= len(sorted_positions):
                break
            
            next_pos = sorted_positions[i + 1]
            
            curr_time = cls._parse_datetime(curr.get("fixTime") or curr.get("serverTime"))
            next_time = cls._parse_datetime(next_pos.get("fixTime") or next_pos.get("serverTime"))
            
            if not curr_time or not next_time:
                i += 1
                continue
            
            time_diff_seconds = (next_time - curr_time).total_seconds()
            
            # Verificar se é uma parada (pouca distância e tempo mínimo)
            dist_m = cls.haversine(
                curr.get("longitude"), curr.get("latitude"),
                next_pos.get("longitude"), next_pos.get("latitude")
            )
            
            # Se movimento é pequeno (possível parada), coletar sequência e verificar duração total
            if dist_m < cls.MIN_MOVEMENT_DISTANCE_M:
                stop_start = curr
                stop_start_time = curr_time
                # inicializar stop_end com o próximo ponto
                stop_end = next_pos
                stop_end_time = next_time
                j = i + 1

                # Estender parada enquanto continuar com movimento pequeno
                while j < len(sorted_positions):
                    check_pos = sorted_positions[j]
                    check_time = cls._parse_datetime(check_pos.get("fixTime") or check_pos.get("serverTime"))

                    if not check_time:
                        j += 1
                        continue

                    d = cls.haversine(
                        stop_start.get("longitude"), stop_start.get("latitude"),
                        check_pos.get("longitude"), check_pos.get("latitude")
                    )

                    if d > cls.MIN_MOVEMENT_DISTANCE_M:
                        break

                    stop_end = check_pos
                    stop_end_time = check_time
                    j += 1

                # Calcular duração total da parada
                stop_duration_seconds = (stop_end_time - stop_start_time).total_seconds()
                stop_duration_minutes = stop_duration_seconds / 60

                if stop_duration_minutes >= min_stop_duration_minutes:
                    stops.append({
                        "latitude": stop_start.get("latitude"),
                        "longitude": stop_start.get("longitude"),
                        "start_time": stop_start_time,
                        "end_time": stop_end_time,
                        "duration_minutes": round(stop_duration_minutes, 1),
                    })

                i = j
            else:
                i += 1
        
        logger.info(f"Identificadas {len(stops)} paradas")
        return stops
    
    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string em formato ISO 8601"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00')).replace(tzinfo=None)
        except (ValueError, AttributeError):
            return None
