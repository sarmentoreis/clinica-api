import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from auth import security
from models.models import User

async def mock_medico_autorizado():
    return User(username="dr_akira", hashed_password="", role="profissional", mfa_enabled=False)

@pytest.mark.asyncio
async def test_rejeicao_entrada_maliciosa_mass_assignment():
    """Valida bloqueio de campos não declarados e injeção (OWASP API3 e API8)"""
    app.dependency_overrides[security.get_current_user] = mock_medico_autorizado
    
    payload_invalido = {
        "paciente_nome": "<script>alert('XSS')</script>",
        "data_hora": "2026-12-01T10:00:00",
        "role_override": "admin" #
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/consultas/", json=payload_invalido)
        
    app.dependency_overrides.clear()
    
    assert response.status_code == 422
    erros = response.json()["detail"]
    assert any("String should match pattern" in err["msg"] for err in erros)
    assert any("Extra inputs are not permitted" in err["msg"] for err in erros)