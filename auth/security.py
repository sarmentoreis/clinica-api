from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import (
    OAuth2PasswordBearer, 
    HTTPBearer, 
    HTTPAuthorizationCredentials, 
    SecurityScopes
)

from database.connection import Settings
from models.models import User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

settings = Settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "consultas:read": "Permite leitura de consultas",
        "consultas:write": "Permite criação e gestão de consultas",
    },
    auto_error=False
)

bearer_scheme = HTTPBearer(auto_error=False)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, mfa_code: str = None):
    to_encode = data.copy()
    
    if to_encode.get("mfa_enabled") and mfa_code != "123456":
        raise HTTPException(status_code=401, detail="Código MFA inválido")
        
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "mfa_verified": True})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    security_scopes: SecurityScopes,
    token_oauth2: str = Depends(oauth2_scheme),
    auth_bearer: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = token_oauth2 or (auth_bearer.credentials if auth_bearer else None)

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token ausente/expirado",
        headers={"WWW-Authenticate": authenticate_value},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_scopes = payload.get("scopes", [])
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão negada. Escopo exigido: '{scope}'",
                headers={"WWW-Authenticate": authenticate_value},
            )

    if username == "lab_parceiro":
        user = User(username="lab_parceiro", hashed_password="", role="laboratorio")
    else:
        user = await User.find_one({"username": username})

    if user is None:
        raise credentials_exception

    return user

async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Operação restrita a administradores."
        )
    return current_user