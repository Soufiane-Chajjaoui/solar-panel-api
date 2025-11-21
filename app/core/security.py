"""
Module de sécurité pour l'authentification et le hachage des mots de passe.
Implémente les bonnes pratiques de sécurité avec JWT et bcrypt.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ============ Configuration ============
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto", # Utiliser bcrypt par défaut (Gestion automatique des anciens algos)
    bcrypt__rounds=12  # Nombre de rounds pour bcrypt (sécurité accrue)
)


# ============ Hachage de mot de passe ============
def hash_password(password: str) -> str:
    """
    Hache un mot de passe en utilisant bcrypt.

    Note: Bcrypt a une limite de 72 bytes. Les mots de passe plus longs
    sont tronqués automatiquement.

    Args:
        password: Le mot de passe en clair

    Returns:
        Le mot de passe haché
    """
    if not password or len(password) < 6:
        raise ValueError("Le mot de passe doit contenir au moins 6 caractères")

    # Bcrypt a une limite de 72 bytes
    # Tronquer le mot de passe s'il est trop long
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
        logger.warning("Mot de passe tronqué à 72 bytes (limite bcrypt)")

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe correspond à son hash.

    Note: Bcrypt a une limite de 72 bytes. Les mots de passe plus longs
    sont tronqués automatiquement pour la vérification.

    Args:
        plain_password: Le mot de passe en clair
        hashed_password: Le mot de passe haché

    Returns:
        True si le mot de passe est correct, False sinon
    """
    try:
        # Tronquer le mot de passe s'il est trop long (même limite que hash_password)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            plain_password = password_bytes[:72].decode('utf-8', errors='ignore')

        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
        return False


# ============ Génération de tokens JWT ============
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un token d'accès JWT.

    Args:
        data: Les données à encoder dans le token
        expires_delta: Durée d'expiration personnalisée

    Returns:
        Le token JWT encodé
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Erreur lors de la création du token d'accès: {e}")
        raise


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Crée un token de rafraîchissement JWT.

    Args:
        data: Les données à encoder dans le token

    Returns:
        Le token JWT encodé
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    to_encode.update({"exp": expire, "type": "refresh"})

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Erreur lors de la création du token de rafraîchissement: {e}")
        raise


# ============ Vérification de tokens ============
def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Vérifie et décode un token JWT.

    Args:
        token: Le token à vérifier
        token_type: Le type de token attendu ("access" ou "refresh")

    Returns:
        Le payload du token si valide, None sinon
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Vérifier le type de token
        if payload.get("type") != token_type:
            logger.warning(f"Type de token incorrect: {payload.get('type')}")
            return None

        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expiré")
        return None
    except jwt.JWTClaimsError:
        logger.warning("Revendications JWT invalides")
        return None
    except JWTError as e:
        logger.warning(f"Erreur JWT: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la vérification du token: {e}")
        return None


def get_token_from_header(auth_header: Optional[str]) -> Optional[str]:
    """
    Extrait le token du header Authorization.

    Args:
        auth_header: La valeur du header Authorization

    Returns:
        Le token si valide, None sinon
    """
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Format d'Authorization header invalide")
        return None

    return parts[1]
