from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, PydanticObjectId
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from models.models import User, Consulta

class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = "mongodb://localhost:27017"
    SECRET_KEY: Optional[str] = "sua_chave_secreta_super_segura"

    model_config = SettingsConfigDict(env_file=".env")

    async def initialize_database(self):
        client = AsyncIOMotorClient(self.DATABASE_URL)
        await init_beanie(
            database=client.clinica_db,
            document_models=[User, Consulta]
        )

settings = Settings()

class Database:
    def __init__(self, model):
        self.model = model

    async def save(self, document):
        await document.create()
        return document

    async def get(self, id: PydanticObjectId):
        doc = await self.model.get(id)
        if doc:
            return doc
        return False

    async def find_one(self, query: dict):
        doc = await self.model.find_one(query)
        return doc

    async def get_all(self):
        docs = await self.model.find_all().to_list()
        return docs

    async def update(self, id: PydanticObjectId, body: BaseModel):
        doc_id = id
        des_body = body.model_dump(exclude_unset=True) 
        
        update_query = {"$set": {
            field: value for field, value in des_body.items()
        }}

        doc = await self.get(doc_id)
        if not doc:
            return False
        
        await doc.update(update_query)
        return doc

    async def delete(self, id: PydanticObjectId):
        doc = await self.get(id)
        if not doc:
            return False
        await doc.delete()
        return True