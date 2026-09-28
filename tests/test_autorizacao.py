import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from auth import security
from models.models import User, Consulta
from database.connection import settings

@pytest.fixture(autouse=True)
async def init_banco():
    await settings.initialize_database()

async def mock_medico_atacante():
    return User(username="dr_hacker", hashed_password="pwd", role="profissional", mfa_enabled=False)

async def mock_laboratorio_m2m():
    return User(username="lab_parceiro", hashed_password="", role="laboratorio", mfa_enabled=False)

@pytest.mark.asyncio
async def test_mitigacao_bola_medico_nao_pode_ler_consulta_alheia():
    """
    Vetor: BOLA (IDOR) do Exercício 4 e 8.
    Garante que um médico logado não consiga ler uma consulta que não lhe pertence.
    """
    consulta_real = Consulta(
        paciente_nome="João Silva",
        profissional_nome="dr_leo",
        data_hora="2026-12-01T10:00:00"
    )
    await consulta_real.insert()

    app.dependency_overrides[security.get_current_user] = mock_medico_atacante
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/consultas/{consulta_real.id}")
        
    app.dependency_overrides.clear()
    
    assert response.status_code == 403
    assert "Acesso negado" in response.json()["detail"]

@pytest.mark.asyncio
async def test_mitigacao_escopo_m2m_laboratorio_nao_pode_escrever():
    """
    Vetor: Abuso de privilégios.
    Garante que o laboratório (que só tem escopo de leitura) não pode criar consultas.
    """
    app.dependency_overrides[security.get_current_user] = mock_laboratorio_m2m
    
    payload_malicioso = {
        "paciente_nome": "Invasão Teste",
        "data_hora": "2026-12-01T10:00:00"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/consultas/", json=payload_malicioso)
        
    app.dependency_overrides.clear()
    
    assert response.status_code == 403