from fastapi import APIRouter, HTTPException, status
from app.core.firebase_client import db
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/panels", tags=["Panels"])





@router.get(
    "",
    response_model=List[List[Dict[str, Any]]],
    summary="Récupérer tous les panneaux",
    responses={200: {"description": "Liste des panneaux avec données détaillées"}}
)
def get_panels(limit: int = 50, offset: int = 0):
    """
    Récupère tous les panneaux et leurs dernières données depuis Firestore.
    Retourne un tableau où chaque panneau est représenté par un tableau contenant
    les données DL et capteurs séparées.

    - **limit**: Nombre maximum de panneaux à retourner (défaut: 50)
    - **offset**: Nombre de panneaux à sauter (défaut: 0)
    """
    try:
        if db is None:
            logger.warning("⚠️ Firestore non disponible")
            return []

        # Fetch latest sensor data from solar_panel_data with limit
        sensor_docs = db.collection("solar_panel_data").order_by("timestamp", direction="DESCENDING").limit(limit * 2).stream()

        # Group sensor data by panel_id and keep latest
        sensor_data = {}
        for doc in sensor_docs:
            data = doc.to_dict()
            panel_id = data.get("panel_id")
            if panel_id:
                if panel_id not in sensor_data:
                    sensor_data[panel_id] = data

        # Fetch latest DL predictions from dl_predictions with limit
        dl_docs = db.collection("dl_predictions").order_by("timestamp", direction="DESCENDING").limit(limit * 2).stream()

        # Group DL data by panel_id and keep latest
        dl_data = {}
        for doc in dl_docs:
            data = doc.to_dict()
            panel_id = data.get("panel_id")
            if panel_id:
                if panel_id not in dl_data:
                    dl_data[panel_id] = data

        # Build response array for each panel
        all_panels = []
        for panel_id in set(sensor_data.keys()) | set(dl_data.keys()):
            panel_response = []

            # Add DL prediction data if available
            dl = dl_data.get(panel_id)
            if dl:
                dl_object = {
                    "all_classes_sorted": dl.get("all_classes_sorted", []),
                    "class_probabilities": dl.get("class_probabilities", {}),
                    "confidence": dl.get("confidence"),
                    "confidence_level": dl.get("confidence_level"),
                    "created_at": dl.get("created_at"),
                    "image_url": dl.get("image_url"),
                    "panel_id": dl.get("panel_id"),
                    "predicted_class": dl.get("predicted_class"),
                    "predicted_class_index": dl.get("predicted_class_index"),
                    "probability": dl.get("probability", {}),
                    "processing_time_ms": dl.get("processing_time_ms"),
                    "status": dl.get("status"),
                    "timestamp": dl.get("timestamp")
                }
                panel_response.append(dl_object)

            # Add sensor data if available
            sensor = sensor_data.get(panel_id)
            if sensor:
                sensor_object = {
                    "B": sensor.get("B"),
                    "G": sensor.get("G"),
                    "R": sensor.get("R"),
                    "battery_level": sensor.get("battery_level"),
                    "device_status": sensor.get("device_status"),
                    "dl_confidence": None,
                    "dl_prediction": None,
                    "dl_status": None,
                    "humidity": sensor.get("humidity"),
                    "last_maintenance": sensor.get("last_maintenance"),
                    "light": sensor.get("light"),
                    "ml_confidence": sensor.get("ml_confidence"),
                    "ml_prediction": sensor.get("ml_prediction"),
                    "ml_probability": sensor.get("ml_probability", {}),
                    "panel_id": sensor.get("panel_id"),
                    "temperature": sensor.get("temperature"),
                    "timestamp": sensor.get("timestamp"),
                    "topic": sensor.get("topic"),
                    "water_level": sensor.get("water_level")
                }
                panel_response.append(sensor_object)

            # Only add panels that have at least some data
            if panel_response:
                all_panels.append(panel_response)

        # Apply offset and limit
        panels = all_panels[offset:offset + limit]

        logger.info(f"✅ Returned {len(panels)} panels (offset: {offset}, limit: {limit}) with detailed merged data from Firestore")
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
