"""
Authentication Module v4.0 - JWT com chave persistente
Fabrica de Agentes - Nova Arquitetura MVP
"""
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

# Arquivo para persistir a secret key
SECRET_KEY_FILE = Path(__file__).parent.parent / ".jwt_secret"


def get_or_create_secret_key() -> str:
    """
    Obtem ou cria secret key persistente

    A chave eh salva em arquivo para persistir entre restarts.
    Em producao, use variavel de ambiente JWT_SECRET_KEY.
    """
    # Primeiro, tentar variavel de ambiente
    env_key = os.getenv("JWT_SECRET_KEY")
    if env_key and env_key != "your-super-secret-key-change-this-in-production":
        return env_key

    # Se nao, tentar arquivo
    if SECRET_KEY_FILE.exists():
        return SECRET_KEY_FILE.read_text().strip()

    # Se nao existe, criar nova chave
    key = secrets.token_urlsafe(32)
    try:
        SECRET_KEY_FILE.write_text(key)
        SECRET_KEY_FILE.chmod(0o600)  # Apenas owner pode ler
        print(f"[Auth] Nova JWT secret key gerada e salva em {SECRET_KEY_FILE}")
    except Exception as e:
        print(f"[Auth] Aviso: Nao foi possivel salvar secret key: {e}")

    return key


# Configuracoes JWT
SECRET_KEY = get_or_create_secret_key()
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer(auto_error=False)


# =============================================================================
# MODELS
# =============================================================================

class Token(BaseModel):
    """Token de acesso"""
    access_token: str
    token_type: str = "bearer"
    expires_at: str


class TokenData(BaseModel):
    """Dados extraidos do token"""
    username: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None


class UserCreate(BaseModel):
    """Dados para criar usuario"""
    username: str
    password: str
    email: Optional[str] = None
    role: str = "VIEWER"


class UserLogin(BaseModel):
    """Dados para login"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Response do usuario"""
    username: str
    email: Optional[str]
    role: str
    active: bool


# =============================================================================
# PASSWORD FUNCTIONS
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se senha corresponde ao hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera hash da senha"""
    return pwd_context.hash(password)


# =============================================================================
# TOKEN FUNCTIONS
# =============================================================================

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Cria JWT token

    Args:
        data: Dados para incluir no token (sub=username, role=role)
        expires_delta: Tempo de expiracao customizado

    Returns:
        Token JWT encoded
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decodifica e valida JWT token

    Args:
        token: Token JWT

    Returns:
        TokenData com dados do usuario

    Raises:
        HTTPException: Se token invalido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        exp = payload.get("exp")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing username"
            )

        return TokenData(
            username=username,
            role=role,
            exp=datetime.fromtimestamp(exp) if exp else None
        )

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


# =============================================================================
# DEPENDENCIES
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency para obter usuario atual do token

    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user": user.username}
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    return decode_token(credentials.credentials)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenData]:
    """
    Dependency para obter usuario atual (opcional)

    Retorna None se nao autenticado ao inves de erro.
    """
    if credentials is None:
        return None

    try:
        return decode_token(credentials.credentials)
    except HTTPException:
        return None


async def require_role(required_role: str):
    """
    Factory para dependency que requer role especifica

    Usage:
        @app.get("/admin")
        async def admin_route(user: TokenData = Depends(require_role("ADMIN"))):
            return {"admin": user.username}
    """
    async def role_checker(user: TokenData = Depends(get_current_user)) -> TokenData:
        if user.role != required_role and user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}"
            )
        return user

    return role_checker


# =============================================================================
# AUTH ROUTES (para incluir no app)
# =============================================================================

from fastapi import APIRouter

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@auth_router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Autentica usuario e retorna token JWT

    Para desenvolvimento, aceita:
    - admin/admin123 (role: ADMIN)
    """
    # Em producao, buscar usuario do banco
    # Por agora, usuario admin hardcoded para dev
    if credentials.username == "admin" and credentials.password == "admin123":
        token = create_access_token(
            data={"sub": "admin", "role": "ADMIN"}
        )
        expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        return Token(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at.isoformat()
        )

    # Tentar buscar do banco
    try:
        from factory.database.connection import SessionLocal
        from factory.database.models import User

        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.username == credentials.username,
                User.active == True
            ).first()

            if user and verify_password(credentials.password, user.password_hash):
                token = create_access_token(
                    data={"sub": user.username, "role": user.role}
                )
                expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

                # Atualizar last_login
                user.last_login = datetime.utcnow()
                db.commit()

                return Token(
                    access_token=token,
                    token_type="bearer",
                    expires_at=expires_at.isoformat()
                )
        finally:
            db.close()
    except Exception as e:
        print(f"[Auth] Erro ao buscar usuario: {e}")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )


@auth_router.get("/me", response_model=UserResponse)
async def get_me(user: TokenData = Depends(get_current_user)):
    """Retorna dados do usuario atual"""
    return UserResponse(
        username=user.username,
        email=None,
        role=user.role,
        active=True
    )


@auth_router.post("/refresh", response_model=Token)
async def refresh_token(user: TokenData = Depends(get_current_user)):
    """Renova token JWT"""
    new_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    return Token(
        access_token=new_token,
        token_type="bearer",
        expires_at=expires_at.isoformat()
    )
