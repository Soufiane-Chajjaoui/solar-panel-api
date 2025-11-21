"""
Routes d'authentification avec les bonnes pratiques de sécurité.
Gère l'enregistrement, la connexion, le rafraîchissement et la déconnexion.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from app.core.firebase_client import db, firestore
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.firebase_security import sync_firebase_user
from app.core.dependencies import get_current_user_email
from app.schemas.user_schema import UserCreate, UserLogin, UserResponse, UserUpdate
from app.schemas.token_schema import Token
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


def format_timestamp(dt: datetime) -> str:
    """Format a datetime object to a human-readable string."""
    return dt.strftime("%B %d, %Y at %I:%M:%S %p UTC+1")

# --- Register ---
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer un nouvel utilisateur",
    responses={
        400: {"description": "Email déjà enregistré"},
        422: {"description": "Données invalides"}
    }
)
def register_user(user: UserCreate):
    """
    Enregistre un nouvel utilisateur.

    - **first_name**: Prénom de l'utilisateur
    - **last_name**: Nom de l'utilisateur
    - **email**: Email unique de l'utilisateur
    - **phone**: Numéro de téléphone de l'utilisateur
    - **password**: Mot de passe (min 6 caractères)
    """
    try:
        doc_ref = db.collection("users").document(user.email)
        if doc_ref.get().exists:
            logger.warning(f"Tentative d'enregistrement avec email existant: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà enregistré"
            )

        # Hacher le mot de passe
        hashed = hash_password(user.password)

        # Créer l'utilisateur
        now = datetime.now(timezone.utc)
        doc_ref.set({
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "password": hashed,
            "refresh_tokens": [],
            "created_at": format_timestamp(now),
            "updated_at": format_timestamp(now)
        })

        logger.info(f"Nouvel utilisateur enregistré: {user.email}")

        return UserResponse(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'enregistrement"
        )

# --- Login ---
@router.post(
    "/login",
    response_model=Token,
    summary="Connexion utilisateur",
    responses={
        401: {"description": "Identifiants invalides"},
        422: {"description": "Données invalides"}
    }
)
def login_user(user: UserLogin):
    """
    Authentifie un utilisateur et retourne les tokens JWT.

    - **email**: Email de l'utilisateur
    - **password**: Mot de passe de l'utilisateur

    Retourne:
    - **access_token**: Token d'accès (15 minutes)
    - **refresh_token**: Token de rafraîchissement (7 jours)
    """
    try:
        doc = db.collection("users").document(user.email).get()
        if not doc.exists:
            logger.warning(f"Tentative de connexion avec email inexistant: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect"
            )

        user_data = doc.to_dict()
        if not verify_password(user.password, user_data.get("password", "")):
            logger.warning(f"Tentative de connexion avec mauvais mot de passe: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect"
            )

        # Créer les tokens
        access_token = create_access_token({"sub": user.email})
        refresh_token = create_refresh_token({"sub": user.email})

        # Stocker le refresh_token
        now = datetime.now(timezone.utc)
        db.collection("users").document(user.email).update({
            "refresh_tokens": firestore.ArrayUnion([refresh_token]),
            "last_login": format_timestamp(now)
        })

        logger.info(f"Connexion réussie: {user.email}")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la connexion"
        )

# --- Refresh Token ---
class RefreshTokenRequest(BaseModel):
    refresh_token: str = BaseModel.model_fields.get("refresh_token", None)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Rafraîchir les tokens",
    responses={
        401: {"description": "Refresh token invalide ou expiré"}
    }
)
def refresh_token(request: RefreshTokenRequest):
    """
    Rafraîchit les tokens JWT en utilisant un refresh token valide.

    - **refresh_token**: Le refresh token obtenu lors de la connexion

    Retourne:
    - **access_token**: Nouveau token d'accès
    - **refresh_token**: Nouveau token de rafraîchissement
    """
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
        if not payload or "sub" not in payload:
            logger.warning("Tentative de rafraîchissement avec refresh token invalide")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalide ou expiré"
            )

        email = payload["sub"]
        doc = db.collection("users").document(email).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )

        user_data = doc.to_dict()
        if "refresh_tokens" not in user_data or request.refresh_token not in user_data["refresh_tokens"]:
            logger.warning(f"Tentative de rafraîchissement avec token révoqué: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token révoqué"
            )

        # Générer nouveaux tokens
        access_token = create_access_token({"sub": email})
        new_refresh_token = create_refresh_token({"sub": email})

        # Remplacer ancien refresh token par le nouveau
        db.collection("users").document(email).update({
            "refresh_tokens": firestore.ArrayRemove([request.refresh_token])
        })
        db.collection("users").document(email).update({
            "refresh_tokens": firestore.ArrayUnion([new_refresh_token])
        })

        logger.info(f"Tokens rafraîchis pour: {email}")

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du rafraîchissement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du rafraîchissement"
        )


# --- Get Current User ---
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Récupérer les informations de l'utilisateur connecté",
    responses={
        401: {"description": "Non authentifié"}
    }
)
def get_current_user(email: str = Depends(get_current_user_email)):
    """
    Récupère les informations de l'utilisateur actuellement connecté.
    Nécessite un token d'accès valide.

    Retourne:
    - **email**: Email de l'utilisateur
    - **first_name**: Prénom de l'utilisateur
    - **last_name**: Nom de l'utilisateur
    """
    try:
        doc = db.collection("users").document(email).get()
        if not doc.exists:
            logger.warning(f"Utilisateur non trouvé: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )

        user_data = doc.to_dict()
        logger.info(f"Récupération des infos utilisateur: {email}")

        return UserResponse(
            email=user_data.get("email"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            phone=user_data.get("phone"),
            created_at=user_data.get("created_at") if isinstance(user_data.get("created_at"), str) else str(user_data.get("created_at"))
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos utilisateur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des infos utilisateur"
        )


# --- Update Current User ---
@router.put(
    "/me",
    response_model=UserResponse,
    summary="Mettre à jour les informations de l'utilisateur connecté",
    responses={
        401: {"description": "Non authentifié"},
        422: {"description": "Données invalides"}
    }
)
def update_current_user(user_update: UserUpdate, email: str = Depends(get_current_user_email)):
    """
    Met à jour les informations de l'utilisateur actuellement connecté.
    Nécessite un token d'accès valide.

    - **first_name**: Prénom de l'utilisateur (optionnel)
    - **last_name**: Nom de l'utilisateur (optionnel)
    - **phone**: Numéro de téléphone de l'utilisateur (optionnel)

    Retourne les informations mises à jour de l'utilisateur.
    """
    try:
        doc_ref = db.collection("users").document(email)
        doc = doc_ref.get()
        if not doc.exists:
            logger.warning(f"Utilisateur non trouvé pour mise à jour: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )

        # Préparer les données à mettre à jour
        update_data = {}
        if user_update.first_name is not None:
            update_data["first_name"] = user_update.first_name
        if user_update.last_name is not None:
            update_data["last_name"] = user_update.last_name
        if user_update.phone is not None:
            update_data["phone"] = user_update.phone

        # Ajouter la date de mise à jour
        now = datetime.now(timezone.utc)
        update_data["updated_at"] = format_timestamp(now)

        # Mettre à jour l'utilisateur
        doc_ref.update(update_data)

        # Récupérer les données mises à jour
        updated_doc = doc_ref.get()
        updated_user_data = updated_doc.to_dict()

        logger.info(f"Informations utilisateur mises à jour: {email}")

        return UserResponse(
            email=updated_user_data.get("email"),
            first_name=updated_user_data.get("first_name"),
            last_name=updated_user_data.get("last_name"),
            phone=updated_user_data.get("phone"),
            created_at=updated_user_data.get("created_at") if isinstance(updated_user_data.get("created_at"), str) else str(updated_user_data.get("created_at"))
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des infos utilisateur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour des infos utilisateur"
        )


# --- Firebase Sync ---
class FirebaseTokenRequest(BaseModel):
    id_token: str


@router.post(
    "/sync-firebase",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Synchroniser avec Firebase et obtenir les tokens JWT",
    responses={
        401: {"description": "Firebase token invalide ou expiré"}
    }
)
def sync_firebase(request: FirebaseTokenRequest):
    """
    Synchronise avec Firebase en utilisant un ID token valide.
    Crée ou met à jour l'utilisateur et retourne les tokens JWT.

    - **id_token**: Le Firebase ID token obtenu après authentification Firebase

    Retourne:
    - **access_token**: Token d'accès JWT (15 minutes)
    - **refresh_token**: Token de rafraîchissement JWT (7 jours)
    """
    try:
        # Verify Firebase token and sync user
        result = sync_firebase_user(request.id_token)
        if not result:
            logger.warning("Failed to sync Firebase user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firebase token invalide ou expiré"
            )

        logger.info(f"Firebase sync successful for: {result['email']}")

        return Token(
            access_token=result['access_token'],
            refresh_token=result['refresh_token'],
            token_type=result['token_type']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during Firebase sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la synchronisation Firebase"
        )


# --- Logout ---
@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Déconnexion utilisateur",
    responses={
        401: {"description": "Non authentifié"}
    }
)
def logout_user(email: str = Depends(get_current_user_email)):
    """
    Déconnecte l'utilisateur en révoquant tous ses refresh tokens.
    Nécessite un token d'accès valide.
    """
    try:
        db.collection("users").document(email).update({
            "refresh_tokens": []
        })

        logger.info(f"Déconnexion: {email}")

        return {"message": "Déconnexion réussie"}
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la déconnexion"
        )
