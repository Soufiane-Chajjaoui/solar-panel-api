"""
Dépendances FastAPI pour l'authentification et l'autorisation.
Utilisées avec Depends() pour protéger les routes.
"""

from fastapi import Depends, HTTPException, status, Header
from typing import Optional, Dict, Any
from app.core.security import verify_token, get_token_from_header
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Extrait et valide le token JWT du header Authorization.
    Utilisé comme dépendance pour protéger les routes.
    
    Args:
        authorization: Le header Authorization
        
    Returns:
        Le payload du token contenant les données de l'utilisateur
        
    Raises:
        HTTPException: Si le token est invalide ou expiré
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = get_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format d'Authorization header invalide. Utilisez: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide: email manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user_email(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    Extrait l'email de l'utilisateur courant.
    
    Args:
        current_user: Le payload du token (injecté par get_current_user)
        
    Returns:
        L'email de l'utilisateur
    """
    return current_user.get("sub")


async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Extrait le token JWT s'il est présent, mais ne lève pas d'erreur s'il est absent.
    Utilisé pour les routes optionnellement authentifiées.
    
    Args:
        authorization: Le header Authorization
        
    Returns:
        Le payload du token ou None si absent/invalide
    """
    if not authorization:
        return None
    
    token = get_token_from_header(authorization)
    if not token:
        return None
    
    return verify_token(token, token_type="access")

