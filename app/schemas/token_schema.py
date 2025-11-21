"""
Schémas Pydantic pour les tokens JWT.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Token(BaseModel):
    """Schéma pour la réponse de login / refresh."""
    access_token: str = Field(
        ...,
        description="Token d'accès JWT (valide 15 minutes)"
    )
    refresh_token: str = Field(
        ...,
        description="Token de rafraîchissement JWT (valide 7 jours)"
    )
    token_type: str = Field(
        default="bearer",
        description="Type de token (toujours 'bearer')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenData(BaseModel):
    """Schéma pour les données contenues dans le token."""
    email: Optional[str] = Field(
        None,
        description="Email de l'utilisateur"
    )
    exp: Optional[int] = Field(
        None,
        description="Timestamp d'expiration du token"
    )
    type: Optional[str] = Field(
        None,
        description="Type de token (access ou refresh)"
    )
