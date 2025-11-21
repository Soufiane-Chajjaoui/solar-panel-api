"""
Service Firestore pour stocker et récupérer les prédictions Deep Learning.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.core.firebase_client import db
import firebase_admin.firestore as firestore

logger = logging.getLogger(__name__)

COLLECTION_NAME = "dl_predictions"


class FirestoreService:
    """Service pour gérer les prédictions DL dans Firestore."""

    @staticmethod
    def store_prediction(prediction_data: Dict[str, Any]) -> bool:
        """
        Stocke une prédiction DL dans Firestore.

        Args:
            prediction_data: Données de la prédiction à stocker

        Returns:
            True si succès, False sinon
        """
        if db is None:
            logger.warning("⚠️ Firestore non disponible - prédiction non stockée")
            return False

        try:
            # Créer le document avec un ID basé sur panel_id et timestamp
            doc_id = f"{prediction_data['panel_id']}_{prediction_data['timestamp'].replace(':', '').replace('-', '').replace('.', '_')}"

            # Préparer les données pour Firestore
            doc_data = {
                "panel_id": prediction_data["panel_id"],
                "image_url": prediction_data["image_url"],
                "predicted_class": prediction_data["predicted_class"],
                "confidence": prediction_data["confidence"],
                "status": prediction_data["status"],
                "confidence_level": prediction_data["confidence_level"],
                "probability": prediction_data["probability"],
                "class_probabilities": prediction_data["class_probabilities"],
                "all_classes_sorted": prediction_data["all_classes_sorted"],
                "predicted_class_index": prediction_data["predicted_class_index"],
                "processing_time_ms": prediction_data["processing_time_ms"],
                "timestamp": prediction_data["timestamp"],
                "created_at": datetime.utcnow()
            }

            # Stocker dans Firestore
            db.collection(COLLECTION_NAME).document(doc_id).set(doc_data)
            logger.info(f"✅ Prédiction stockée pour panneau {prediction_data['panel_id']}")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur lors du stockage de la prédiction: {e}")
            return False

    @staticmethod
    def get_predictions(
        panel_id: Optional[str] = None,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère les prédictions depuis Firestore.

        Args:
            panel_id: ID du panneau (optionnel, pour filtrer)
            limit: Nombre maximum de résultats
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)

        Returns:
            Liste des prédictions
        """
        if db is None:
            logger.warning("⚠️ Firestore non disponible - retour liste vide")
            return []

        try:
            # For now, fetch all predictions and filter in memory due to composite index requirement
            # TODO: Create composite index in Firestore for better performance
            query = db.collection(COLLECTION_NAME).order_by("timestamp", direction="DESCENDING")

            # If we have date filters, apply them in the query
            if start_date or end_date:
                docs = query.stream()
                predictions = []

                for doc in docs:
                    data = doc.to_dict()
                    pred_timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", ""))

                    if start_date and pred_timestamp < start_date:
                        continue
                    if end_date and pred_timestamp > end_date:
                        continue

                    predictions.append(data)

                # Apply panel_id filter in memory
                if panel_id:
                    predictions = [p for p in predictions if p.get("panel_id") == panel_id]

                return predictions[:limit]

            # No date filters - fetch and filter in memory
            docs = query.limit(limit * 2).stream()  # Fetch more to account for filtering
            all_predictions = [doc.to_dict() for doc in docs]

            # Apply panel_id filter in memory
            if panel_id:
                predictions = [p for p in all_predictions if p.get("panel_id") == panel_id]
            else:
                predictions = all_predictions

            logger.info(f"✅ {len(predictions)} prédictions récupérées (panel_id filter: {panel_id})")
            return predictions[:limit]

        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des prédictions: {e}")
            # Return empty list on quota or other errors to prevent crashes
            return []

    @staticmethod
    def get_prediction_stats(
        days: int = 30,
        panel_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calcule des statistiques sur les prédictions.

        Args:
            days: Nombre de jours à analyser
            panel_id: ID du panneau (optionnel)

        Returns:
            Dictionnaire avec les statistiques
        """
        if db is None:
            return {"error": "Firestore non disponible"}

        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Reduce limit to avoid quota issues
            predictions = FirestoreService.get_predictions(
                panel_id=panel_id,
                limit=1000,  # Reduced from 10000 to avoid quota limits
                start_date=start_date,
                end_date=end_date
            )

            if not predictions:
                return {
                    "total_predictions": 0,
                    "period_days": days,
                    "class_distribution": {},
                    "status_distribution": {"clean": 0, "dirty": 0},
                    "confidence_levels": {"high": 0, "medium": 0, "low": 0},
                    "daily_trend": [],
                    "avg_confidence": 0,
                    "avg_processing_time": 0,
                    "message": "Aucune prédiction trouvée"
                }

            # Calculer les statistiques
            total_predictions = len(predictions)

            # Distribution des classes prédites
            class_distribution = {}
            status_distribution = {"clean": 0, "dirty": 0}
            confidence_levels = {"high": 0, "medium": 0, "low": 0}

            for pred in predictions:
                # Classes
                pred_class = pred.get("predicted_class", "Unknown")
                class_distribution[pred_class] = class_distribution.get(pred_class, 0) + 1

                # Status
                status = pred.get("status", "unknown")
                if status in status_distribution:
                    status_distribution[status] += 1

                # Niveaux de confiance
                conf_level = pred.get("confidence_level", "unknown")
                if conf_level in confidence_levels:
                    confidence_levels[conf_level] += 1

            # Statistiques temporelles (par jour)
            daily_stats = {}
            for pred in predictions:
                pred_date = datetime.fromisoformat(pred["timestamp"].replace("Z", "")).date()
                date_str = pred_date.isoformat()

                if date_str not in daily_stats:
                    daily_stats[date_str] = {"total": 0, "clean": 0, "dirty": 0}

                daily_stats[date_str]["total"] += 1
                status = pred.get("status", "unknown")
                if status in ["clean", "dirty"]:
                    daily_stats[date_str][status] += 1

            # Convertir en liste triée pour les graphiques
            daily_trend = [
                {"date": date, **stats}
                for date, stats in sorted(daily_stats.items())
            ]

            return {
                "total_predictions": total_predictions,
                "period_days": days,
                "class_distribution": class_distribution,
                "status_distribution": status_distribution,
                "confidence_levels": confidence_levels,
                "daily_trend": daily_trend,
                "avg_confidence": sum(p.get("confidence", 0) for p in predictions) / total_predictions if predictions else 0,
                "avg_processing_time": sum(p.get("processing_time_ms", 0) for p in predictions) / total_predictions if predictions else 0
            }

        except Exception as e:
            logger.error(f"❌ Erreur lors du calcul des statistiques: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_panel_history(panel_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des prédictions pour un panneau spécifique.

        Args:
            panel_id: ID du panneau
            limit: Nombre maximum de résultats

        Returns:
            Liste des prédictions pour ce panneau
        """
        return FirestoreService.get_predictions(panel_id=panel_id, limit=limit)

    @staticmethod
    def store_feedback(feedback_data: Dict[str, Any]) -> str:
        """
        Stocke un feedback de validation humaine dans Firestore.

        Args:
            feedback_data: Données du feedback à stocker

        Returns:
            ID du document créé, ou None en cas d'échec
        """
        if db is None:
            logger.warning("⚠️ Firestore non disponible - feedback non stocké")
            return None

        try:
            # Créer le document avec un ID basé sur panel_id et timestamp
            doc_id = f"feedback_{feedback_data['panel_id']}_{feedback_data['submitted_at'].replace(':', '').replace('-', '').replace('.', '_')}"

            # Stocker dans Firestore
            db.collection("feedback").document(doc_id).set(feedback_data)
            logger.info(f"✅ Feedback stocké pour panneau {feedback_data['panel_id']}")
            return doc_id

        except Exception as e:
            logger.error(f"❌ Erreur lors du stockage du feedback: {e}")
            return None

    @staticmethod
    def update_prediction_validation(
        panel_id: str,
        prediction_timestamp: str,
        validation_data: Dict[str, Any]
    ) -> bool:
        """
        Met à jour une prédiction avec des données de validation humaine.

        Args:
            panel_id: ID du panneau
            prediction_timestamp: Timestamp de la prédiction originale
            validation_data: Données de validation à ajouter

        Returns:
            True si succès, False sinon
        """
        if db is None:
            logger.warning("⚠️ Firestore non disponible - validation non mise à jour")
            return False

        try:
            # Rechercher la prédiction par panel_id et timestamp approximatif
            predictions_ref = db.collection(COLLECTION_NAME)
            query = predictions_ref.where("panel_id", "==", panel_id).order_by("timestamp", direction="DESCENDING").limit(10)

            docs = query.stream()
            target_doc = None

            for doc in docs:
                data = doc.to_dict()
                # Comparer les timestamps (avec une tolérance de quelques secondes)
                if abs((datetime.fromisoformat(data["timestamp"].replace("Z", "")) -
                       datetime.fromisoformat(prediction_timestamp.replace("Z", ""))).total_seconds()) < 60:
                    target_doc = doc
                    break

            if target_doc:
                # Mettre à jour le document
                target_doc.reference.update(validation_data)
                logger.info(f"✅ Validation mise à jour pour prédiction {panel_id}")
                return True
            else:
                logger.warning(f"⚠️ Prédiction non trouvée pour mise à jour de validation: {panel_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour de la validation: {e}")
            return False