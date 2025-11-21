"""
Routes pour récupérer l'historique des prédictions DL.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.dependencies import get_current_user_email
from app.services.firestore_service import FirestoreService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["History"])


class PredictionHistoryResponse(BaseModel):
    """Réponse pour l'historique des prédictions."""
    predictions: List[Dict[str, Any]]
    total_count: int
    has_more: bool


class PredictionStatsResponse(BaseModel):
    """Réponse pour les statistiques des prédictions."""
    total_predictions: int
    period_days: int
    class_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    confidence_levels: Dict[str, int]
    daily_trend: List[Dict[str, Any]]
    avg_confidence: float
    avg_processing_time: float


@router.get(
    "/predictions",
    response_model=PredictionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Récupérer l'historique des prédictions",
    responses={
        400: {"description": "Paramètres invalides"},
        401: {"description": "Non authentifié"},
        500: {"description": "Erreur serveur"}
    }
)
def get_prediction_history(
    panel_id: Optional[str] = Query(None, description="ID du panneau pour filtrer"),
    limit: int = Query(50, description="Nombre maximum de résultats", ge=1, le=500),
    offset: int = Query(0, description="Décalage pour la pagination", ge=0),
    days: Optional[int] = Query(None, description="Nombre de jours à remonter", ge=1, le=365),
    # email: str = Depends(get_current_user_email)  # Temporarily disabled for testing
):
    """
    Récupère l'historique des prédictions DL.

    - **panel_id**: ID du panneau (optionnel)
    - **limit**: Nombre maximum de résultats (1-500)
    - **offset**: Décalage pour la pagination
    - **days**: Nombre de jours à remonter (optionnel)

    Retourne la liste des prédictions avec pagination.
    """
    try:
        # Simulate email for testing
        email = "test@example.com"

        # Calculer les dates si spécifié
        start_date = None
        if days:
            start_date = datetime.utcnow() - timedelta(days=days)

        # Récupérer les prédictions
        predictions = FirestoreService.get_predictions(
            panel_id=panel_id,
            limit=limit + 1,  # +1 pour vérifier s'il y a plus de résultats
            start_date=start_date
        )

        # Appliquer l'offset et vérifier s'il y a plus de résultats
        has_more = len(predictions) > limit
        predictions = predictions[offset:offset + limit] if offset > 0 else predictions[:limit]

        # Compter le total (approximatif pour la pagination)
        total_count = len(predictions) + (offset if offset > 0 else 0)
        if has_more:
            total_count += 1  # Au moins un de plus

        response = PredictionHistoryResponse(
            predictions=predictions,
            total_count=total_count,
            has_more=has_more
        )

        logger.info(f"Historique récupéré: {len(predictions)} prédictions (panel: {panel_id or 'all'}, limit: {limit})")

        return response

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=PredictionStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Récupérer les statistiques des prédictions",
    responses={
        400: {"description": "Paramètres invalides"},
        401: {"description": "Non authentifié"},
        500: {"description": "Erreur serveur"}
    }
)
def get_prediction_stats(
    days: int = Query(30, description="Nombre de jours d'analyse", ge=1, le=365),
    panel_id: Optional[str] = Query(None, description="ID du panneau pour filtrer"),
    # email: str = Depends(get_current_user_email)  # Temporarily disabled for testing
):
    """
    Calcule et retourne les statistiques des prédictions DL.

    - **days**: Nombre de jours à analyser (1-365)
    - **panel_id**: ID du panneau (optionnel)

    Retourne diverses statistiques et tendances.
    """
    try:
        # Simulate email for testing
        email = "test@example.com"

        # Récupérer les statistiques
        stats = FirestoreService.get_prediction_stats(days=days, panel_id=panel_id)

        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors du calcul des statistiques: {stats['error']}"
            )

        response = PredictionStatsResponse(**stats)

        logger.info(f"Statistiques calculées pour {days} jours (panel: {panel_id or 'all'})")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )


@router.get(
    "/panel/{panel_id}",
    response_model=PredictionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Récupérer l'historique d'un panneau spécifique",
    responses={
        400: {"description": "Paramètres invalides"},
        401: {"description": "Non authentifié"},
        404: {"description": "Panneau non trouvé"},
        500: {"description": "Erreur serveur"}
    }
)
def get_panel_history(
    panel_id: str,
    limit: int = Query(20, description="Nombre maximum de résultats", ge=1, le=100),
    # email: str = Depends(get_current_user_email)  # Temporarily disabled for testing
):
    """
    Récupère l'historique des prédictions pour un panneau spécifique.

    - **panel_id**: ID du panneau
    - **limit**: Nombre maximum de résultats (1-100)

    Retourne l'historique récent du panneau.
    """
    try:
        # Simulate email for testing
        email = "test@example.com"

        # Mock prediction history data
        mock_predictions = {
            "panel1": [
                {
                    "id": "pred-1",
                    "panel_id": "panel1",
                    "predicted_class": "clean",
                    "confidence": 0.95,
                    "status": "clean",
                    "confidence_level": "high",
                    "processing_time_ms": 245,
                    "image_url": "https://via.placeholder.com/400x300?text=panel1",
                    "timestamp": "2025-11-21T07:42:00.000Z",
                    "all_classes_sorted": [
                        {"class_name": "clean", "probability": 0.95},
                        {"class_name": "dirty", "probability": 0.05}
                    ]
                },
                {
                    "id": "pred-2",
                    "panel_id": "panel1",
                    "predicted_class": "clean",
                    "confidence": 0.92,
                    "status": "clean",
                    "confidence_level": "high",
                    "processing_time_ms": 238,
                    "image_url": "https://via.placeholder.com/400x300?text=panel1",
                    "timestamp": "2025-11-21T07:35:00.000Z",
                    "all_classes_sorted": [
                        {"class_name": "clean", "probability": 0.92},
                        {"class_name": "dirty", "probability": 0.08}
                    ]
                }
            ],
            "P-TEST-8": [
                {
                    "id": "pred-3",
                    "panel_id": "P-TEST-8",
                    "predicted_class": "dirty",
                    "confidence": 0.88,
                    "status": "dirty",
                    "confidence_level": "high",
                    "processing_time_ms": 252,
                    "image_url": "https://via.placeholder.com/400x300?text=P-TEST-8",
                    "timestamp": "2025-11-21T07:40:00.000Z",
                    "all_classes_sorted": [
                        {"class_name": "dirty", "probability": 0.88},
                        {"class_name": "clean", "probability": 0.12}
                    ]
                }
            ],
            "P-TEST-10": [
                {
                    "id": "pred-4",
                    "panel_id": "P-TEST-10",
                    "predicted_class": "clean",
                    "confidence": 0.92,
                    "status": "clean",
                    "confidence_level": "high",
                    "processing_time_ms": 241,
                    "image_url": "https://via.placeholder.com/400x300?text=P-TEST-10",
                    "timestamp": "2025-11-21T07:38:00.000Z",
                    "all_classes_sorted": [
                        {"class_name": "clean", "probability": 0.92},
                        {"class_name": "dirty", "probability": 0.08}
                    ]
                }
            ]
        }

        predictions = mock_predictions.get(panel_id, [])[:limit]

        response = PredictionHistoryResponse(
            predictions=predictions,
            total_count=len(predictions),
            has_more=len(predictions) >= limit
        )

        logger.info(f"Mock historique du panneau {panel_id} récupéré: {len(predictions)} prédictions")

        return response

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique du panneau {panel_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )