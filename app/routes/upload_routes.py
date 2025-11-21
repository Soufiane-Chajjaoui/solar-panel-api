"""
Routes pour l'upload d'images vers Cloudinary.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from app.core.dependencies import get_current_user_email
from app.utils.cloudinary_storage import upload_image_to_cloudinary
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])


class ImageUploadRequest(BaseModel):
    """Schéma pour l'upload d'image."""
    panel_id: str
    image_base64: str
    filename: str = None


class ImageUploadResponse(BaseModel):
    """Réponse après upload d'image."""
    panel_id: str
    image_url: str
    message: str = "Image uploadée avec succès"


@router.post(
    "/image",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Uploader une image vers Cloudinary",
    responses={
        400: {"description": "Données invalides"},
        401: {"description": "Non authentifié"},
        500: {"description": "Erreur serveur"}
    }
)
def upload_image(
    request: ImageUploadRequest,
    email: str = Depends(get_current_user_email)
):
    """
    Upload une image vers Cloudinary.
    
    - **panel_id**: ID du panneau solaire
    - **image_base64**: Image encodée en base64
    - **filename**: Nom du fichier (optionnel)
    
    Retourne l'URL publique de l'image.
    """
    try:
        if not request.panel_id or not request.image_base64:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="panel_id et image_base64 sont requis"
            )
        
        image_url = upload_image_to_cloudinary(
            image_base64=request.image_base64,
            panel_id=request.panel_id,
            filename=request.filename
        )

        
        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Échec de l'upload de l'image"
            )
        
        logger.info(f"Image uploadée par {email} pour le panneau {request.panel_id}")
        
        return ImageUploadResponse(
            panel_id=request.panel_id,
            image_url=image_url,
            message="Image uploadée avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'upload: {str(e)}"
        )

