from fastapi import APIRouter, HTTPException, status
from app.core.firebase_client import db
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/panels", tags=["Panels"])


def merge_panel_data(sensor_data: Dict[str, Any], dl_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge sensor data and DL prediction data for a panel.

    Args:
        sensor_data: Latest sensor data from solar_panel_data collection
        dl_data: Latest DL prediction data from dl_predictions collection

    Returns:
        Merged data dictionary
    """
    merged = dict(sensor_data)  # Start with sensor data

    # Add DL prediction data
    if dl_data:
        merged.update({
            "dl_prediction": dl_data.get("predicted_class"),
            "dl_confidence": dl_data.get("confidence"),
            "dl_status": dl_data.get("status"),
            "dl_probability": dl_data.get("probability", {}),
            "dl_class_probabilities": dl_data.get("class_probabilities", {}),
            "dl_predicted_class_index": dl_data.get("predicted_class_index"),
            "dl_confidence_level": dl_data.get("confidence_level"),
            "dl_all_classes_sorted": dl_data.get("all_classes_sorted", []),
            "dl_processing_time_ms": dl_data.get("processing_time_ms"),
            "dl_timestamp": dl_data.get("timestamp"),
            "image_url": dl_data.get("image_url"),  # Use DL image URL if available
        })

    return merged


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
    Combine les données des capteurs (solar_panel_data) et les prédictions DL (dl_predictions).
    """
    try:
        if db is None:
            logger.warning("⚠️ Firestore non disponible")
            return []

        # Fetch latest sensor data from solar_panel_data
        sensor_docs = db.collection("solar_panel_data").stream()

        # Group sensor data by panel_id and keep latest
        sensor_data = {}
        for doc in sensor_docs:
            data = doc.to_dict()
            panel_id = data.get("panel_id")
            if panel_id:
                current_timestamp = data.get("timestamp", "")
                if panel_id not in sensor_data or current_timestamp > sensor_data[panel_id].get("timestamp", ""):
                    sensor_data[panel_id] = data

        # Fetch latest DL predictions from dl_predictions
        dl_docs = db.collection("dl_predictions").stream()

        # Group DL data by panel_id and keep latest
        dl_data = {}
        for doc in dl_docs:
            data = doc.to_dict()
            panel_id = data.get("panel_id")
            if panel_id:
                current_timestamp = data.get("timestamp", "")
                if panel_id not in dl_data or current_timestamp > dl_data[panel_id].get("timestamp", ""):
                    dl_data[panel_id] = data

        # Merge data for each panel
        merged_panels = {}
        for panel_id in set(sensor_data.keys()) | set(dl_data.keys()):
            sensor = sensor_data.get(panel_id, {})
            dl = dl_data.get(panel_id, {})
            merged_panels[panel_id] = merge_panel_data(sensor, dl)

        # Convert to PanelResponse format
        panels = []
        for panel_id, data in merged_panels.items():
            # Determine the best status to show (prefer DL if available, fallback to ML)
            status = data.get("dl_status") or data.get("ml_prediction") or "unknown"
            confidence = data.get("dl_confidence") or data.get("ml_confidence") or 0.0

            panels.append(
                PanelResponse(
                    panel_id=panel_id,
                    last_status=status,
                    last_confidence=float(confidence),
                    thumbnail=data.get("image_url") or f"https://via.placeholder.com/400x300?text={panel_id}",
                    last_update=data.get("dl_timestamp") or data.get("timestamp", ""),
                    temperature=data.get("temperature"),
                    humidity=data.get("humidity"),
                    light=data.get("light")
                )
            )

        logger.info(f"✅ Returned {len(panels)} panels with merged data from Firestore")
        return panels

    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des panneaux: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des panneaux"
        )


@router.get(
    "/{panel_id}",
    response_model=List[Dict[str, Any]],
    summary="Récupérer les détails d'un panneau",
    responses={
        200: {"description": "Détails du panneau"},
        404: {"description": "Panneau non trouvé"}
    }
)
def get_panel(panel_id: str):
    """
    Récupère les détails complets d'un panneau spécifique depuis Firestore.
    Retourne un tableau avec les données DL et capteurs séparées.
    """
    try:
        if db is None:
            logger.warning("⚠️ Firestore non disponible")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service de base de données non disponible"
            )

        # Fetch latest sensor data for this panel
        sensor_docs = db.collection("solar_panel_data") \
            .where("panel_id", "==", panel_id) \
            .stream()

        # Find the latest sensor data
        sensor_data = None
        latest_sensor_timestamp = None
        for doc in sensor_docs:
            doc_data = doc.to_dict()
            doc_timestamp = doc_data.get("timestamp")
            if doc_timestamp and (latest_sensor_timestamp is None or doc_timestamp > latest_sensor_timestamp):
                latest_sensor_timestamp = doc_timestamp
                sensor_data = doc_data

        # Fetch latest DL predictions for this panel
        dl_docs = db.collection("dl_predictions") \
            .where("panel_id", "==", panel_id) \
            .stream()

        # Find the latest DL data
        dl_data = None
        latest_dl_timestamp = None
        for doc in dl_docs:
            doc_data = doc.to_dict()
            doc_timestamp = doc_data.get("timestamp")
            if doc_timestamp and (latest_dl_timestamp is None or doc_timestamp > latest_dl_timestamp):
                latest_dl_timestamp = doc_timestamp
                dl_data = doc_data

        # Check if we have any data for this panel
        if not sensor_data and not dl_data:
            logger.warning(f"⚠️ Panneau non trouvé: {panel_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Panneau {panel_id} non trouvé"
            )

        # Build response array with separate objects
        response = []

        # Add DL prediction data if available
        if dl_data:
            dl_object = {
                "all_classes_sorted": dl_data.get("all_classes_sorted", []),
                "class_probabilities": dl_data.get("class_probabilities", {}),
                "confidence": dl_data.get("confidence"),
                "confidence_level": dl_data.get("confidence_level"),
                "created_at": dl_data.get("created_at"),
                "image_url": dl_data.get("image_url"),
                "panel_id": dl_data.get("panel_id"),
                "predicted_class": dl_data.get("predicted_class"),
                "predicted_class_index": dl_data.get("predicted_class_index"),
                "probability": dl_data.get("probability", {}),
                "processing_time_ms": dl_data.get("processing_time_ms"),
                "status": dl_data.get("status"),
                "timestamp": dl_data.get("timestamp")
            }
            response.append(dl_object)

        # Add sensor data if available
        if sensor_data:
            sensor_object = {
                "B": sensor_data.get("B"),
                "G": sensor_data.get("G"),
                "R": sensor_data.get("R"),
                "battery_level": sensor_data.get("battery_level"),
                "device_status": sensor_data.get("device_status"),
                "dl_confidence": None,
                "dl_prediction": None,
                "dl_status": None,
                "humidity": sensor_data.get("humidity"),
                "last_maintenance": sensor_data.get("last_maintenance"),
                "light": sensor_data.get("light"),
                "ml_confidence": sensor_data.get("ml_confidence"),
                "ml_prediction": sensor_data.get("ml_prediction"),
                "ml_probability": sensor_data.get("ml_probability", {}),
                "panel_id": sensor_data.get("panel_id"),
                "temperature": sensor_data.get("temperature"),
                "timestamp": sensor_data.get("timestamp"),
                "topic": sensor_data.get("topic"),
                "water_level": sensor_data.get("water_level")
            }
            response.append(sensor_object)

        logger.info(f"✅ Returned separate data objects for panel: {panel_id} (sensor: {sensor_data is not None}, dl: {dl_data is not None})")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du panneau {panel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du panneau"
        )
