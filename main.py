import uvicorn
from database.connection import settings
from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from auth import security
from models.models import User
from routers import consultas
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from middleware import security

limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    await settings.initialize_database()
    yield

app = FastAPI(lifespan=lifespan, title="Clínica Médica API - Agendamentos")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(security.SecurityHeadersMiddleware)
app.include_router(consultas.router)

@app.post("/token", tags=["Autenticação Humana"])
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.username == form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    escopos_selecionados = form_data.scopes if form_data.scopes else ["consultas:read"]
    
    token = security.create_access_token(
        data={
            "sub": user.username, 
            "role": user.role, 
            "mfa_enabled": user.mfa_enabled,
            "scopes": escopos_selecionados
        },
        mfa_code="123456"
    )

    return {"access_token": token, "token_type": "bearer"}

@app.post("/token/b2b", tags=["Autenticação M2M"])
@limiter.limit("20/minute")
async def login_b2b(request: Request, grant_type: str = Form(...), client_id: str = Form(...), client_secret: str = Form(...)):   
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="Grant type não suportado para B2B")
        
    if client_id != "lab_parceiro" or client_secret != "senha_super_secreta_b2b":
        raise HTTPException(status_code=401, detail="Credenciais de cliente B2B inválidas")

    token = security.create_access_token(
        data={
            "sub": client_id, 
            "role": "laboratorio", 
            "scopes": ["consultas:read"]
        }
    )
    return {"access_token": token, "token_type": "bearer"}

if __name__ == "__main__":
    print("Iniciando o Projeto Clínica Médica API...")
    uvicorn.run("main:app", host="localhost", port=8080, reload=True)