"""
Service MQTT pour gérer la communication avec les appareils IoT.
Traite les messages reçus et les stocke dans Firebase, avec upload des images vers Cloudinary.
"""

import json
import logging
from typing import Dict, Any, Optional
from app.core.mqtt_client import get_mqtt_client
from app.core.firebase_client import db
from app.core.config import settings
from app.services.ml_service import predict_cleaning_status
from app.services.dl_service import predict_from_image
from datetime import datetime

from app.utils.cloudinary_storage import upload_image_to_cloudinary

logger = logging.getLogger(__name__)


class MQTTService:
    """Service pour gérer les opérations MQTT."""
    
    @staticmethod
    def handle_panel_data(topic: str, data: Any):
        """
        Traite les données reçues des panneaux solaires.
        
        Args:
            topic: Le topic MQTT (ex: solar/panels/panel1/data)
            data: Les données reçues (dict ou str)
        """
        try:
            # Extraire l'ID du panneau du topic
            panel_id = topic.split('/')[2]
            
            # Convertir en dict si nécessaire
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning(f"Impossible de parser JSON: {data}")
                    return
            
            # Ajouter les métadonnées
            data['panel_id'] = panel_id
            data['timestamp'] = datetime.utcnow().isoformat()
            data['topic'] = topic
            
            # Stocker dans Firebase
            if db:
                db.collection("panel_data").add(data)
                logger.info(f"✅ Données du panneau {panel_id} stockées")
            else:
                logger.warning("⚠️ Firebase non disponible")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement des données du panneau: {e}")
    
    @staticmethod
    def handle_cleaning_status(topic: str, data: Any):
        """
        Traite les mises à jour d'état du nettoyage.
        
        Args:
            topic: Le topic MQTT (ex: solar/cleaning/device1/status)
            data: Les données reçues
        """
        try:
            # Extraire l'ID du dispositif
            device_id = topic.split('/')[2]
            
            # Convertir en dict si nécessaire
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    data = {"status": data}
            
            # Ajouter les métadonnées
            data['device_id'] = device_id
            data['timestamp'] = datetime.utcnow().isoformat()
            
            # Stocker dans Firebase
            if db:
                db.collection("cleaning_logs").add(data)
                logger.info(f"✅ État du nettoyage {device_id} enregistré")
            else:
                logger.warning("⚠️ Firebase non disponible")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de l'état du nettoyage: {e}")
    
    @staticmethod
    def handle_alert(topic: str, data: Any):
        """
        Traite les alertes reçues.

        Args:
            topic: Le topic MQTT (ex: solar/alerts/alert1/message)
            data: Les données reçues
        """
        try:
            # Extraire l'ID de l'alerte
            alert_id = topic.split('/')[2]

            # Convertir en dict si nécessaire
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    data = {"message": data}

            # Ajouter les métadonnées
            data['alert_id'] = alert_id
            data['timestamp'] = datetime.utcnow().isoformat()
            data['severity'] = data.get('severity', 'info')

            # Stocker dans Firebase
            if db:
                db.collection("alerts").add(data)
                logger.warning(f"⚠️ Alerte {alert_id} reçue: {data.get('message', 'N/A')}")
            else:
                logger.warning("⚠️ Firebase non disponible")

        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de l'alerte: {e}")

    @staticmethod
    def handle_solar_panel_data(topic: str, data: Any):
        """
        Traite les données reçues du topic solar/panel/#.
        C'est le handler principal qui écoute tous les panneaux solaires.
        Fait une prédiction ML et stocke les données avec la prédiction dans Firebase.

        Args:
            topic: Le topic MQTT (ex: solar/panel/panel1/data)
            data: Les données reçues (dict ou str)
        """
        try:
            # Afficher le message reçu dans la console
            print(f"\n{'='*60}")
            print(f"📨 MESSAGE REÇU - Topic: {topic}")
            print(f"{'='*60}")
            if isinstance(data, dict):
                print(json.dumps(data, indent=2))
            else:
                print(f"Données brutes: {data}")
            print(f"{'='*60}\n")
            
            logger.info(f"📨 Message reçu sur {topic}")

            # Convertir en dict si nécessaire
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    print(f"❌ ERREUR: Impossible de parser JSON: {data}")
                    logger.warning(f"Impossible de parser JSON: {data}")
                    return

            # Vérifier que les données nécessaires sont présentes
            required_fields = ["temperature", "humidity", "light", "R", "G", "B"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"⚠️ AVERTISSEMENT: Champs manquants dans les données: {missing_fields}")
                logger.warning(f"⚠️ Champs manquants dans les données: {missing_fields}")
                return
            
            # Extraire l'ID du panneau du topic
            # Format attendu: solar/panel/panel1/data -> panel1
            # Format alternatif: solar/panel/panel1 -> panel1
            try:
                topic_parts = topic.split('/')
                # Si le topic commence par "solar/panel/", prendre le 3ème élément
                if len(topic_parts) >= 3 and topic_parts[0] == "solar" and topic_parts[1] == "panel":
                    panel_id = topic_parts[2]
                # Sinon, essayer de trouver un ID dans le topic
                elif len(topic_parts) >= 2:
                    # Prendre le dernier élément comme ID si c'est un ID plausible
                    panel_id = topic_parts[-1] if topic_parts[-1] not in ["data", "status", "command"] else topic_parts[-2] if len(topic_parts) >= 3 else "unknown"
                else:
                    panel_id = "unknown"
            except Exception:
                panel_id = "unknown"
            
            # Extraire l'image si elle est fournie (pour validation DL)
            # L'image peut être fournie sous forme de:
            # - "image_path": chemin vers un fichier image
            # - "image_base64": string base64 encodée
            # - "image": chemin ou base64 (alias)
            image_data = data.get("image") or data.get("image_path") or data.get("image_base64")
            
            # Upload l'image vers Cloudinary si elle est fournie
            image_url = None
            if image_data:
                try:
                    print("📤 Upload de l'image vers Cloudinary...")
                    logger.info("📤 Upload de l'image vers Cloudinary...")
                    image_url = upload_image_to_cloudinary(image_data, panel_id)
                    if image_url:
                        data['image_url'] = image_url
                        print(f"✅ Image uploadée avec succès: {image_url}")
                        logger.info(f"✅ Image uploadée avec succès: {image_url}")
                    else:
                        print("⚠️ Échec de l'upload de l'image")
                        logger.warning("⚠️ Échec de l'upload de l'image")
                except Exception as upload_error:
                    print(f"❌ ERREUR lors de l'upload de l'image: {upload_error}")
                    logger.error(f"❌ Erreur lors de l'upload de l'image: {upload_error}", exc_info=True)

            # Faire la prédiction ML
            print("🤖 Prédiction ML en cours...")
            logger.info("🤖 Prédiction ML en cours...")
            prediction_result = predict_cleaning_status(data)
            
            if prediction_result:
                # Ajouter la prédiction ML aux données selon le format demandé
                ml_prediction = prediction_result.get('ml_prediction')
                data['ml_prediction'] = ml_prediction
                data['ml_confidence'] = prediction_result.get('ml_confidence')
                if prediction_result.get('ml_probability') is not None:
                    data['ml_probability'] = prediction_result.get('ml_probability')
                
                status_display = ml_prediction.upper() if ml_prediction else 'UNKNOWN'
                confidence_display = f" (confiance: {prediction_result.get('ml_confidence', 0):.2%})" if prediction_result.get('ml_confidence') is not None else ""
                print(f"✅ Prédiction ML: {status_display}{confidence_display}")
                logger.info(f"✅ Prédiction ML: {ml_prediction}")
                
                # Si ML détecte "dirty", déclencher le modèle DL pour validation
                if ml_prediction == "dirty" and image_data:
                    print(f"\n🔍 ML a détecté 'dirty' - Validation DL en cours...")
                    logger.info("🔍 ML a détecté 'dirty', déclenchement de la validation DL")
                    
                    try:
                        dl_prediction_result = predict_from_image(image_data)
                        
                        if dl_prediction_result:
                            # Ajouter les résultats DL aux données
                            data['dl_prediction'] = dl_prediction_result.get('dl_prediction')
                            data['dl_status'] = dl_prediction_result.get('dl_status')
                            data['dl_confidence'] = dl_prediction_result.get('dl_confidence')
                            data['dl_predicted_class'] = dl_prediction_result.get('dl_predicted_class')
                            
                            if dl_prediction_result.get('dl_probability') is not None:
                                data['dl_probability'] = dl_prediction_result.get('dl_probability')
                            if dl_prediction_result.get('dl_class_probabilities') is not None:
                                data['dl_class_probabilities'] = dl_prediction_result.get('dl_class_probabilities')
                            
                            dl_pred = dl_prediction_result.get('dl_prediction', 'unknown')
                            dl_conf = dl_prediction_result.get('dl_confidence', 0)
                            print(f"✅ Validation DL: {dl_pred} (confiance: {dl_conf:.2%})")
                            logger.info(f"✅ Validation DL: {dl_pred}")
                            
                            # Comparaison ML vs DL
                            if dl_prediction_result.get('dl_status') == 'clean':
                                print(f"⚠️ CONFLIT: ML=dirty mais DL=clean - La validation DL contredit ML")
                                logger.warning(f"⚠️ Conflit ML/DL: ML=dirty, DL=clean")
                        else:
                            print(f"⚠️ AVERTISSEMENT: Impossible d'obtenir une validation DL")
                            logger.warning("⚠️ Impossible d'obtenir une validation DL")
                            data['dl_prediction'] = None
                            data['dl_status'] = None
                            data['dl_confidence'] = None
                    except Exception as dl_error:
                        print(f"❌ ERREUR lors de la validation DL: {dl_error}")
                        logger.error(f"❌ Erreur lors de la validation DL: {dl_error}", exc_info=True)
                        data['dl_prediction'] = None
                        data['dl_status'] = None
                        data['dl_confidence'] = None
                elif ml_prediction == "dirty" and not image_data:
                    print(f"ℹ️  ML a détecté 'dirty' mais aucune image fournie - Validation DL ignorée")
                    logger.info("ℹ️  ML a détecté 'dirty' mais aucune image fournie pour validation DL")
                    data['dl_prediction'] = None
                    data['dl_status'] = None
                    data['dl_confidence'] = None
                else:
                    # ML détecte "clean", pas de validation DL nécessaire
                    print(f"✅ ML a détecté 'clean' - Validation DL non nécessaire")
                    logger.info("✅ ML a détecté 'clean', validation DL ignorée")
                    data['dl_prediction'] = None
                    data['dl_status'] = None
                    data['dl_confidence'] = None
            else:
                print("⚠️ AVERTISSEMENT: Impossible d'obtenir une prédiction ML")
                logger.warning("⚠️ Impossible d'obtenir une prédiction ML")
                data['ml_prediction'] = None
                data['ml_confidence'] = None
                data['ml_probability'] = None
                data['dl_prediction'] = None
                data['dl_status'] = None
                data['dl_confidence'] = None

            # Ajouter les métadonnées
            data['panel_id'] = panel_id
            data['timestamp'] = datetime.utcnow().isoformat()
            data['topic'] = topic

            # Stocker dans Firebase
            if db:
                try:
                    db.collection("solar_panel_data").add(data)
                    print(f"✅ Données du panneau {panel_id} stockées dans Firestore avec prédiction ML")
                    print(f"\n📊 Données complètes avec prédiction:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    print()
                    logger.info(f"✅ Données du panneau {panel_id} stockées dans Firestore avec prédiction ML")
                    logger.debug(f"   Données: {json.dumps(data, indent=2)}")
                except Exception as firebase_error:
                    print(f"❌ ERREUR Firestore: {firebase_error}")
                    logger.error(f"❌ Erreur Firestore: {firebase_error}")
            else:
                print("❌ ERREUR: Firebase non disponible - Les données ne sont pas stockées!")
                logger.error("❌ Firebase non disponible - Les données ne sont pas stockées!")

        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement des données du panneau solaire: {e}", exc_info=True)
    
    @staticmethod
    def publish_command(device_id: str, command: str, params: Optional[Dict] = None) -> bool:
        """
        Publie une commande à un appareil.
        
        Args:
            device_id: L'ID de l'appareil
            command: La commande à exécuter
            params: Les paramètres de la commande
            
        Returns:
            True si la publication est réussie
        """
        try:
            client = get_mqtt_client()
            
            # Construire le payload
            payload = {
                "command": command,
                "device_id": device_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if params:
                payload.update(params)
            
            # Publier sur le topic de commande
            topic = f"solar/commands/{device_id}"
            success = client.publish(topic, payload)
            
            if success:
                logger.info(f"✅ Commande '{command}' envoyée à {device_id}")
            else:
                logger.error(f"❌ Impossible d'envoyer la commande à {device_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la publication de la commande: {e}")
            return False
    
    @staticmethod
    def subscribe_to_topics():
        """S'abonne aux topics MQTT avec les callbacks appropriés."""
        try:
            client = get_mqtt_client()

            # S'abonner au topic principal solar/panel/#
            client.subscribe(
                settings.MQTT_TOPIC_SOLAR_PANEL,
                callback=MQTTService.handle_solar_panel_data
            )
            logger.info(f"✅ Abonné au topic: {settings.MQTT_TOPIC_SOLAR_PANEL}")

            logger.info("✅ Souscriptions MQTT configurées")

        except Exception as e:
            logger.error(f"❌ Erreur lors de la configuration des souscriptions: {e}")
    
    @staticmethod
    def get_panel_data(panel_id: str, limit: int = 10) -> list:
        """
        Récupère les dernières données d'un panneau.
        
        Args:
            panel_id: L'ID du panneau
            limit: Nombre de documents à récupérer
            
        Returns:
            Liste des données du panneau
        """
        try:
            if not db:
                logger.warning("⚠️ Firebase non disponible")
                return []
            
            docs = db.collection("panel_data")\
                .where("panel_id", "==", panel_id)\
                .order_by("timestamp", direction="DESCENDING")\
                .limit(limit)\
                .stream()
            
            return [doc.to_dict() for doc in docs]
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données: {e}")
            return []
    
    @staticmethod
    def get_recent_alerts(limit: int = 10) -> list:
        """
        Récupère les alertes récentes.
        
        Args:
            limit: Nombre d'alertes à récupérer
            
        Returns:
            Liste des alertes
        """
        try:
            if not db:
                logger.warning("⚠️ Firebase non disponible")
                return []
            
            docs = db.collection("alerts")\
                .order_by("timestamp", direction="DESCENDING")\
                .limit(limit)\
                .stream()
            
            return [doc.to_dict() for doc in docs]
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des alertes: {e}")
            return []

