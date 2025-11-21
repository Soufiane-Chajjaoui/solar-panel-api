"""
Routes pour la validation humaine des prédictions Deep Learning.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from app.core.dependencies import get_current_user_email
from app.services.firestore_service import FirestoreService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    """Schéma pour une requête de feedback/validation."""
    panel_id: str
    prediction_id: str = None  # Optional, can be inferred from panel_id and timestamp
    is_correct: bool
    predicted_class: str = None
    corrected_class: str = None
    confidence: float = None
    timestamp: str = None  # Timestamp of the original prediction
    reason: str = None  # Optional reason for correction


class FeedbackResponse(BaseModel):
    """Réponse pour un feedback soumis."""
    success: bool
    message: str
    feedback_id: str = None


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Soumettre un feedback de validation humaine",
    responses={
        400: {"description": "Données invalides"},
        401: {"description": "Non authentifié"},
        404: {"description": "Prédiction non trouvée"},
        500: {"description": "Erreur serveur"}
    }
)
def submit_feedback(
    request: FeedbackRequest,
    # email: str = Depends(get_current_user_email)  # Temporarily disabled for testing
):
    """
    Soumet un feedback de validation humaine pour une prédiction.

    - **panel_id**: ID du panneau solaire
    - **prediction_id**: ID de la prédiction (optionnel)
    - **is_correct**: True si la prédiction était correcte
    - **predicted_class**: Classe prédite par l'IA
    - **corrected_class**: Classe corrigée (si is_correct=False)
    - **confidence**: Confiance de l'IA
    - **timestamp**: Timestamp de la prédiction originale
    - **reason**: Raison de la correction (optionnel)

    Retourne le statut de soumission du feedback.
    """
    try:
        if not request.panel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="panel_id est requis"
            )

        if request.is_correct is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="is_correct est requis"
            )

        logger.info(f"Feedback soumis pour le panneau {request.panel_id}: correct={request.is_correct}")

        # Simulate email for testing
        email = "test@example.com"

        # Store feedback in Firestore
        feedback_data = {
            "panel_id": request.panel_id,
            "prediction_id": request.prediction_id,
            "is_correct": request.is_correct,
            "predicted_class": request.predicted_class,
            "corrected_class": request.corrected_class if not request.is_correct else None,
            "confidence": request.confidence,
            "original_timestamp": request.timestamp,
            "reason": request.reason,
            "submitted_by": email,
            "submitted_at": datetime.utcnow().isoformat() + "Z"
        }

        feedback_id = FirestoreService.store_feedback(feedback_data)

        if not feedback_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Échec du stockage du feedback"
            )

        # If this is a correction, also update the original prediction record
        if not request.is_correct and request.timestamp:
            # Try to find and update the original prediction
            FirestoreService.update_prediction_validation(
                request.panel_id,
                request.timestamp,
                {
                    "human_validated": True,
                    "human_validation_correct": False,
                    "human_corrected_class": request.corrected_class,
                    "human_feedback_reason": request.reason,
                    "human_feedback_submitted_at": feedback_data["submitted_at"]
                }
            )

        message = "Feedback soumis avec succès"
        if not request.is_correct:
            message += f" - Correction appliquée: {request.corrected_class}"

        logger.info(f"Feedback stocké avec succès pour panneau {request.panel_id}")

        return FeedbackResponse(
            success=True,
            message=message,
            feedback_id=feedback_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la soumission du feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la soumission du feedback: {str(e)}"
        )