import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def autenticar(usuario: str, senha: str) -> bool:
    # compare_digest evita ataque de timing na comparação
    return secrets.compare_digest(usuario, settings.usuario_demo) and secrets.compare_digest(
        senha, settings.senha_demo
    )


def criar_token(usuario: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expira_minutos)
    return jwt.encode(
        {"sub": usuario, "exp": expira}, settings.jwt_secret, algorithm=settings.jwt_algoritmo
    )


def usuario_atual(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algoritmo])
        return payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
