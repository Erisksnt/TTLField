import pytest
from datetime import datetime, timedelta
from app.services.report_service import ReportService, Journey


class TestReportService:
    """Testes do serviço de relatórios melhorado"""
    
    @staticmethod
    def create_position(
        latitude: float,
        longitude: float,
        timestamp: datetime,
        speed: float = 0.0
    ) -> dict:
        """Helper para criar um dicionário de posição"""
        return {
            "latitude": latitude,
            "longitude": longitude,
            "fixTime": timestamp.isoformat() + "Z",
            "speed": speed,  # m/s
        }
    
    def test_velocidade_media_corrigida(self):
        """
        Teste cenário descrito pelo usuário:
        - 30 min a 60 km/h (30 km)
        - 3 horas parado
        - 30 min a 60 km/h (30 km)
        
        Esperado: velocidade média = 60 km/h (não 6 km/h)
        """
        # Preparar dados
        base_time = datetime(2026, 6, 22, 8, 0, 0)
        positions = []
        
        # Primeira viagem: 30 km em 30 min
        current_time = base_time
        # Simular ~15 pontos durante 30 min a 60 km/h (~1.67 m/s)
        for i in range(15):
            lat = -23.5505 + (i * 0.01)  # Simular movimento ao norte
            lon = -46.6333
            pos_time = current_time + timedelta(minutes=i*2)
            positions.append(self.create_position(lat, lon, pos_time, speed=16.7))
        
        # Parada de 3 horas (nenhuma posição registrada - gap temporal)
        current_time = current_time + timedelta(hours=3.5)
        
        # Segunda viagem: 30 km em 30 min
        for i in range(15):
            lat = -23.5505 + 0.15 + (i * 0.01)
            lon = -46.6333
            pos_time = current_time + timedelta(minutes=i*2)
            positions.append(self.create_position(lat, lon, pos_time, speed=16.7))
        
        # Calcular métricas
        metrics = ReportService.calculate_report_metrics(positions)
        
        # Validações
        assert metrics['journeys_count'] == 2, f"Esperado 2 viagens, obteve {metrics['journeys_count']}"
        assert abs(metrics['total_distance_km'] - 60) < 1, \
            f"Distância esperada ~60 km, obteve {metrics['total_distance_km']}"
        assert abs(metrics['total_time_minutes'] - 60) < 2, \
            f"Tempo esperado ~60 min, obteve {metrics['total_time_minutes']}"
        assert metrics['average_speed_kmh'] > 50, \
            f"Velocidade média esperada > 50 km/h, obteve {metrics['average_speed_kmh']}"
        print(f"✅ Teste velocidade média: {metrics['average_speed_kmh']} km/h (CORRETO!)")
    
    def test_identificacao_viagens_por_inatividade(self):
        """
        Testa se viagens são corretamente separadas por períodos de inatividade
        """
        base_time = datetime(2026, 6, 22, 8, 0, 0)
        positions = []
        
        # Viagem 1: 15 min
        for i in range(8):
            pos_time = base_time + timedelta(minutes=i*2)
            positions.append(self.create_position(-23.5505, -46.6333 + (i*0.001), pos_time, 10))
        
        # GAP: 40 minutos sem movimentação (deve separar viagens)
        base_time = base_time + timedelta(minutes=30 + 40)
        
        # Viagem 2: 15 min
        for i in range(8):
            pos_time = base_time + timedelta(minutes=i*2)
            positions.append(self.create_position(-23.5505, -46.6333 + 0.01 + (i*0.001), pos_time, 10))
        
        # Identificar viagens
        journeys = ReportService.identify_journeys(positions)
        
        assert len(journeys) == 2, f"Esperado 2 viagens, obteve {len(journeys)}"
        assert journeys[0].duration_minutes < 20, "Primeira viagem deve ter ~15 min"
        assert journeys[1].duration_minutes < 20, "Segunda viagem deve ter ~15 min"
        print(f"✅ Teste separação de viagens: {len(journeys)} viagens identificadas corretamente")
    
    def test_filtragem_gps_jitter(self):
        """
        Testa se pequenos deslocamentos (GPS jitter) não são contados como movimento
        """
        base_time = datetime(2026, 6, 22, 10, 0, 0)
        positions = []
        
        # Simular parada com GPS jitter (deslocamentos < 30m)
        lat_base = -23.5505
        lon_base = -46.6333
        
        for i in range(20):
            # Pequeníssimas variações (~5-10 metros)
            lat = lat_base + (i % 2) * 0.0001  # ~10m de variação
            lon = lon_base + (i % 3) * 0.00005  # ~5m de variação
            pos_time = base_time + timedelta(minutes=i)
            positions.append(self.create_position(lat, lon, pos_time, speed=0.5))
        
        # Calcular métricas
        metrics = ReportService.calculate_report_metrics(positions)
        
        # Validações: não deve contar como movimento real
        assert metrics['total_distance_km'] < 0.5, \
            f"Distância deveria ser ~0, obteve {metrics['total_distance_km']} km"
        print(f"✅ Teste GPS jitter: {metrics['total_distance_km']} km (corretamente ignorado)")
    
    def test_parada_curta_nao_separa_viagem(self):
        """
        Testa se paradas curtas (< 30 min) não encerram a viagem
        Exemplo: semáforo, trânsito
        """
        base_time = datetime(2026, 6, 22, 9, 0, 0)
        positions = []
        
        # Movimento por 15 min
        for i in range(8):
            pos_time = base_time + timedelta(minutes=i*2)
            positions.append(self.create_position(-23.5505, -46.6333 + (i*0.01), pos_time, 15))
        
        # Parada curta: 2 min (semáforo)
        current_time = base_time + timedelta(minutes=15)
        for i in range(2):
            pos_time = current_time + timedelta(minutes=i)
            positions.append(self.create_position(-23.5505 + 0.15, -46.6333 + 0.08, pos_time, 0))
        
        # Continua movimento por mais 15 min
        current_time = current_time + timedelta(minutes=2)
        for i in range(8):
            pos_time = current_time + timedelta(minutes=i*2)
            positions.append(self.create_position(-23.5505 + 0.15, -46.6333 + 0.08 + (i*0.01), pos_time, 15))
        
        # Identificar viagens
        journeys = ReportService.identify_journeys(positions)
        
        assert len(journeys) == 1, f"Esperado 1 viagem (parada curta não separa), obteve {len(journeys)}"
        print(f"✅ Teste parada curta: {len(journeys)} viagem (corretamente continuada)")
    
    def test_calculo_paradas(self):
        """
        Testa identificação de pontos de parada
        """
        base_time = datetime(2026, 6, 22, 10, 0, 0)
        positions = []
        
        # Movimento por 10 min
        for i in range(5):
            pos_time = base_time + timedelta(minutes=i*2)
            positions.append(self.create_position(-23.5505, -46.6333, pos_time, 15))
        
        # Parada de 5 min
        current_time = base_time + timedelta(minutes=10)
        for i in range(5):
            pos_time = current_time + timedelta(minutes=i)
            positions.append(self.create_position(-23.5505 + 0.01, -46.6333 + 0.01, pos_time, 0))
        
        # Movimento novamente por 10 min
        current_time = current_time + timedelta(minutes=5)
        for i in range(5):
            pos_time = current_time + timedelta(minutes=i*2)
            positions.append(self.create_position(-23.5505, -46.6333 + 0.01, pos_time, 15))
        
        # Identificar paradas
        stops = ReportService.identify_stops(positions, min_stop_duration_minutes=2)
        
        assert len(stops) >= 1, f"Esperado pelo menos 1 parada, obteve {len(stops)}"
        if stops:
            assert stops[0]['duration_minutes'] >= 4, \
                f"Parada deveria ter ~5 min, obteve {stops[0]['duration_minutes']}"
        print(f"✅ Teste paradas: {len(stops)} parada(s) identificada(s)")
    
    def test_velocidade_media_com_parada_curta(self):
        """
        Cenário: 30 min a 60 km/h + 5 min parado + 30 min a 60 km/h
        Esperado: velocidade média = 60 km/h (parada curta não reduz média)
        """
        base_time = datetime(2026, 6, 22, 8, 0, 0)
        positions = []
        
        # Primeira metade: 30 min a 60 km/h (~30 km)
        for i in range(15):
            pos_time = base_time + timedelta(minutes=i*2)
            positions.append(self.create_position(
                -23.5505 + (i*0.01), -46.6333, pos_time, speed=16.7
            ))
        
        # Parada: 5 min
        current_time = base_time + timedelta(minutes=30)
        for i in range(5):
            pos_time = current_time + timedelta(minutes=i)
            positions.append(self.create_position(
                -23.5505 + 0.15, -46.6333, pos_time, speed=0
            ))
        
        # Segunda metade: 30 min a 60 km/h (~30 km)
        current_time = current_time + timedelta(minutes=5)
        for i in range(15):
            pos_time = current_time + timedelta(minutes=i*2)
            positions.append(self.create_position(
                -23.5505 + 0.15, -46.6333 + (i*0.01), pos_time, speed=16.7
            ))
        
        # Calcular métricas
        metrics = ReportService.calculate_report_metrics(positions)
        
        # Validações
        assert metrics['journeys_count'] == 1, "Parada curta não deve separar viagens"
        assert abs(metrics['average_speed_kmh'] - 60) < 5, \
            f"Velocidade média esperada ~60 km/h, obteve {metrics['average_speed_kmh']}"
        print(f"✅ Teste vel. média com parada curta: {metrics['average_speed_kmh']} km/h (CORRETO!)")
    
    def test_caso_vazio(self):
        """
        Testa comportamento com dados vazios ou insuficientes
        """
        # Lista vazia
        metrics = ReportService.calculate_report_metrics([])
        assert metrics['total_distance_km'] == 0
        assert metrics['journeys_count'] == 0
        
        # Apenas 1 ponto
        base_time = datetime(2026, 6, 22, 10, 0, 0)
        single = [self.create_position(-23.5505, -46.6333, base_time, 10)]
        metrics = ReportService.calculate_report_metrics(single)
        assert metrics['journeys_count'] == 0
        print(f"✅ Teste casos vazios: tratados corretamente")


# ============================================================================
# SCRIPT DE VALIDAÇÃO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TESTES DO NOVO REPORT SERVICE - TTLField")
    print("=" * 70)
    print()
    
    test_service = TestReportService()
    
    try:
        test_service.test_velocidade_media_corrigida()
        test_service.test_identificacao_viagens_por_inatividade()
        test_service.test_filtragem_gps_jitter()
        test_service.test_parada_curta_nao_separa_viagem()
        test_service.test_calculo_paradas()
        test_service.test_velocidade_media_com_parada_curta()
        test_service.test_caso_vazio()
        
        print()
        print("=" * 70)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 70)
        
    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"❌ TESTE FALHOU: {e}")
        print("=" * 70)
        raise
