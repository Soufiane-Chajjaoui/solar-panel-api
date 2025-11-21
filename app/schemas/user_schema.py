"""
Schémas Pydantic pour les utilisateurs.
Valide les données d'entrée et de sortie.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import re


def validate_email(email: str) -> str:
    """Valide le format d'un email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Email invalide")
    return email


class UserCreate(BaseModel):
    """Schéma pour la création d'un nouvel utilisateur."""
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        example="Soufiane",
        description="Prénom de l'utilisateur"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        example="Chajjaoui",
        description="Nom de l'utilisateur"
    )
    email: str = Field(
        ...,
        example="soufiane@example.com",
        description="Email unique de l'utilisateur"
    )
    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        example="+212600000000",
        description="Numéro de téléphone de l'utilisateur"
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        example="StrongPassword123!",
        description="Mot de passe (min 6 caractères)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Soufiane",
                "last_name": "Chajjaoui",
                "email": "soufiane@example.com",
                "phone": "+212600000000",
                "password": "StrongPassword123!"
            }
        }


class UserLogin(BaseModel):
    """Schéma pour la connexion utilisateur."""
    email: str = Field(
        ...,
        example="soufiane@example.com",
        description="Email de l'utilisateur"
    )
    password: str = Field(
        ...,
        example="StrongPassword123!",
        description="Mot de passe de l'utilisateur"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "soufiane@example.com",
                "password": "StrongPassword123!"
            }
        }


class UserUpdate(BaseModel):
    """Schéma pour la mise à jour des informations utilisateur."""
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Prénom de l'utilisateur"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Nom de l'utilisateur"
    )
    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=15,
        description="Numéro de téléphone de l'utilisateur"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Soufiane",
                "last_name": "Chajjaoui",
                "phone": "+212600000000"
            }
        }


class UserResponse(BaseModel):
    """Schéma pour la réponse utilisateur (sans mot de passe)."""
    first_name: Optional[str] = Field(None, description="Prénom de l'utilisateur")
    last_name: Optional[str] = Field(None, description="Nom de l'utilisateur")
    email: str = Field(..., description="Email de l'utilisateur")
    phone: Optional[str] = Field(None, description="Numéro de téléphone de l'utilisateur")
    created_at: Optional[str] = Field(None, description="Date de création")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "first_name": "Soufiane",
                "last_name": "Chajjaoui",
                "email": "soufiane@example.com",
                "phone": "+212600000000",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
