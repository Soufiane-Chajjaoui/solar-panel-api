from fastapi import APIRouter, HTTPException, status
from app.core.firebase_client import db
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/panels", tags=["Panels"])


class PanelResponse(BaseModel):
    panel_id: str
    last_status: str
    last_confidence: float
    thumbnail: Optional[str] = None
    last_update: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[float] = None


@router.get(
    "",
    response_model=List[PanelResponse],
    summary="Récupérer tous les panneaux",
    responses={200: {"description": "Liste des panneaux"}}
)
def get_panels():
    """
    Récupère tous les panneaux et leurs dernières données depuis Firestore.
    """
    try:
        if db is None:
            logger.warning("⚠️ Firestore non disponible")
            return []

        # Fetch the most recent documents
        docs = db.collection("solar_panel_data").order_by("timestamp", direction="DESCENDING").limit(500).stream()

        # Keep only the latest entry per panel
        panels_data = {}
        for doc in docs:
            data = doc.to_dict()
            panel_id = data.get("panel_id")
            if panel_id and panel_id not in panels_data:
                panels_data[panel_id] = data

        # Convert to PanelResponse format
        panels = []
        for panel_id, data in panels_data.items():
            panels.append(
                PanelResponse(
                    panel_id=panel_id,
                    last_status=data.get("ml_prediction") or "unknown",
                    last_confidence=float(data.get("ml_confidence") or 0.0),
                    thumbnail=data.get("image_url") or f"https://via.placeholder.com/400x300?text={panel_id}",
                    last_update=data.get("timestamp", ""),
                    temperature=data.get("temperature"),
                    humidity=data.get("humidity"),
                    light=data.get("light")
                )
            )

        logger.info(f"✅ Returned {len(panels)} panels from Firestore")
        return panels

    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des panneaux: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des panneaux"
        )


@router.get(
    "/{panel_id}",
    response_model=Dict[str, Any],
    summary="Récupérer les détails d'un panneau",
    responses={
        200: {"description": "Détails du panneau"},
        404: {"description": "Panneau non trouvé"}
    }
)
def get_panel(panel_id: str):
    """
    Récupère les détails complets d'un panneau spécifique depuis Firestore.
    """
    try:
        if db is None:
            logger.warning("⚠️ Firestore non disponible")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service de base de données non disponible"
            )

        # Fetch the latest document for this panel
        docs = db.collection("solar_panel_data") \
            .where("panel_id", "==", panel_id) \
            .order_by("timestamp", direction="DESCENDING") \
            .limit(1).stream()

        panel_data = None
        for doc in docs:
            panel_data = doc.to_dict()
            break

        if not panel_data:
            logger.warning(f"⚠️ Panneau non trouvé: {panel_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Panneau {panel_id} non trouvé"
            )

        response = {
            "panel_id": panel_id,
            "last_status": panel_data.get("ml_prediction") or "unknown",
            "last_confidence": float(panel_data.get("ml_confidence") or 0.0),
            "last_update": panel_data.get("timestamp", ""),
            "thumbnail": panel_data.get("image_url") or f"https://via.placeholder.com/400x300?text={panel_id}",
            "temperature": panel_data.get("temperature"),
            "humidity": panel_data.get("humidity"),
            "light": panel_data.get("light"),
            "ml_prediction": panel_data.get("ml_prediction"),
            "ml_confidence": float(panel_data.get("ml_confidence") or 0.0),
            "ml_probability": panel_data.get("ml_probability", {}),
            "dl_prediction": panel_data.get("dl_prediction"),
            "dl_confidence": float(panel_data.get("dl_confidence") or 0.0),
            "dl_status": panel_data.get("dl_status"),
            "color_data": {
                "R": panel_data.get("R"),
                "G": panel_data.get("G"),
                "B": panel_data.get("B")
            },
            "raw_data": {
                "panel_id": panel_id,
                "temperature": panel_data.get("temperature"),
                "humidity": panel_data.get("humidity"),
                "light": panel_data.get("light"),
                "timestamp": panel_data.get("timestamp")
            }
        }

        logger.info(f"✅ Returned details for panel: {panel_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du panneau {panel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du panneau"
        )
