from beanie import Document, PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class User(Document):
    username: str
    hashed_password: str
    role: str = "profissional"
    mfa_enabled: bool = False
    
    class Settings:
        name = "users"

class Consulta(Document):
    paciente_nome: str
    profissional_nome: str
    data_hora: datetime
    status: str = "agendada"
    token_auditoria: str
    notas_medicas: Optional[str] = None
    
    class Settings:
        name = "consultas"

class ConsultaCreate(BaseModel):
    paciente_nome: str = Field(
        min_length=2,
        max_length=100,
        pattern=r"^[A-Za-zÀ-ÖØ-öø-ÿ\s'-]+$"
    )
    data_hora: datetime
    model_config = ConfigDict(extra="forbid")

class ConsultaResponse(BaseModel):
    id: PydanticObjectId = Field(validation_alias="_id", serialization_alias="id")
    paciente_nome: str
    profissional_nome: str
    data_hora: datetime
    status: str
    model_config = ConfigDict(extra="ignore", populate_by_name=True, from_attributes=True)