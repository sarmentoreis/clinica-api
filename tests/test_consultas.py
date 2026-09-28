import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from auth import security
from models.models import User
from database.connection import settings

@pytest.fixture(autouse=True)
async def init_banco():
    await settings.initialize_database()

async def override_get_current_user():
    return User(
        username="dr_leo", 
        hashed_password="hashed_pwd", 
        role="profissional", 
        mfa_enabled=False
    )

@pytest.mark.asyncio
async def test_criar_consulta_com_sucesso():
    app.dependency_overrides[security.get_current_user] = override_get_current_user
    
    payload = {
        "paciente_nome": "Maria Souza",
        "data_hora": "2026-11-10T09:00:00"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/consultas/", json=payload)
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 201
    dados_retornados = response.json()
    assert dados_retornados["paciente_nome"] == "Maria Souza"
    assert dados_retornados["profissional_nome"] == "dr_leo"
    assert "id" in dados_retornados