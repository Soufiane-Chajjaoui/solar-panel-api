"""
Routes pour les prédictions Deep Learning.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from app.core.dependencies import get_current_user_email
from app.services.dl_service import predict_from_image
from app.services.firestore_service import FirestoreService
import logging
import requests
import time
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["Prediction"])


class PredictRequest(BaseModel):
    """Schéma pour une requête de prédiction."""
    panel_id: str
    image_url: str


class PredictResponse(BaseModel):
    """Réponse d'une prédiction."""
    panel_id: str
    image_url: str  # Add image_url to response
    predicted_class: str
    confidence: float
    status: str
    probability: dict
    class_probabilities: dict
    predicted_class_index: int
    confidence_level: str  # "high", "medium", "low"
    all_classes_sorted: list  # List of dicts with class_name and probability, sorted by probability
    processing_time_ms: float
    timestamp: str


@router.post(
    "",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Prédire l'état d'un panneau solaire",
    responses={
        400: {"description": "Données invalides"},
        401: {"description": "Non authentifié"},
        500: {"description": "Erreur serveur"}
    }
)
def predict_panel_condition(
    request: PredictRequest,
    # email: str = Depends(get_current_user_email)  # Temporarily disabled for testing
):
    """
    Prédit l'état de propreté d'un panneau solaire à partir d'une image.

    - **panel_id**: ID du panneau solaire
    - **image_url**: URL de l'image à analyser

    Retourne la prédiction du modèle Deep Learning.
    """
    try:
        if not request.panel_id or not request.image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="panel_id et image_url sont requis"
            )

        logger.info(f"Prédiction demandée pour le panneau {request.panel_id}")
        start_time = time.time()


        # Télécharger l'image depuis l'URL
        try:
            response = requests.get(request.image_url, timeout=30)
            response.raise_for_status()
            image_bytes = response.content
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement de l'image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossible de télécharger l'image depuis l'URL: {str(e)}"
            )

        # Faire la prédiction
        prediction_result = predict_from_image(image_bytes)

        if prediction_result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Échec de la prédiction"
            )

        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Determine confidence level
        confidence = prediction_result["dl_confidence"]
        if confidence >= 0.8:
            confidence_level = "high"
        elif confidence >= 0.6:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Sort all classes by probability (descending)
        all_classes_sorted = [
            {"class_name": class_name, "probability": prob}
            for class_name, prob in sorted(
                prediction_result["dl_class_probabilities"].items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]

        # Créer le timestamp
        prediction_timestamp = datetime.utcnow().isoformat() + "Z"

        # Formater la réponse
        response_data = PredictResponse(
            panel_id=request.panel_id,
            image_url=request.image_url,  # Include image_url in response
            predicted_class=prediction_result["dl_prediction"],
            confidence=prediction_result["dl_confidence"],
            status=prediction_result["dl_status"],
            probability=prediction_result["dl_probability"],
            class_probabilities=prediction_result["dl_class_probabilities"],
            predicted_class_index=prediction_result["dl_predicted_class"],
            confidence_level=confidence_level,
            all_classes_sorted=all_classes_sorted,
            processing_time_ms=round(processing_time, 2),
            timestamp=prediction_timestamp
        )

        # Stocker la prédiction dans Firestore (en arrière-plan, ne pas bloquer la réponse)
        try:
            prediction_for_storage = {
                "panel_id": request.panel_id,
                "image_url": request.image_url,
                "predicted_class": prediction_result["dl_prediction"],
                "confidence": prediction_result["dl_confidence"],
                "status": prediction_result["dl_status"],
                "confidence_level": confidence_level,
                "probability": prediction_result["dl_probability"],
                "class_probabilities": prediction_result["dl_class_probabilities"],
                "all_classes_sorted": all_classes_sorted,
                "predicted_class_index": prediction_result["dl_predicted_class"],
                "processing_time_ms": round(processing_time, 2),
                "timestamp": prediction_timestamp
            }

            # Stocker de manière asynchrone (ne pas attendre)
            import threading
            threading.Thread(
                target=FirestoreService.store_prediction,
                args=(prediction_for_storage,),
                daemon=True
            ).start()

        except Exception as storage_error:
            logger.warning(f"⚠️ Échec du stockage en arrière-plan: {storage_error}")
            # Ne pas échouer la prédiction si le stockage échoue

        logger.info(f"Prédiction réussie pour le panneau {request.panel_id}: {prediction_result['dl_prediction']} (confiance: {confidence:.2%}, niveau: {confidence_level})")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la prédiction: {str(e)}"
        )