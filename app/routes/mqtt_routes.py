"""
Routes pour la gestion MQTT et les appareils IoT.
Permet de publier des commandes et récupérer les données.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.core.dependencies import get_current_user_email
from app.services.mqtt_service import MQTTService
from app.core.mqtt_client import get_mqtt_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mqtt", tags=["MQTT"])


# ============ Schémas Pydantic ============

class PublishMessageRequest(BaseModel):
    """Schéma pour publier un message MQTT."""
    topic: str = Field(..., description="Topic MQTT")
    payload: Dict[str, Any] = Field(..., description="Payload du message")
    qos: Optional[int] = Field(1, description="Niveau de QoS (0, 1, ou 2)")
    retain: Optional[bool] = Field(False, description="Conserver le message")


class PublishCommandRequest(BaseModel):
    """Schéma pour publier une commande."""
    device_id: str = Field(..., description="ID de l'appareil")
    command: str = Field(..., description="Commande à exécuter")
    params: Optional[Dict[str, Any]] = Field(None, description="Paramètres de la commande")


class SubscribeTopicRequest(BaseModel):
    """Schéma pour s'abonner à un topic."""
    topic: str = Field(..., description="Topic MQTT (peut contenir des wildcards)")
    qos: Optional[int] = Field(1, description="Niveau de QoS")


class PanelDataResponse(BaseModel):
    """Schéma pour les données d'un panneau."""
    panel_id: str
    temperature: Optional[float]
    irradiance: Optional[float]
    efficiency: Optional[float]
    timestamp: str


class AlertResponse(BaseModel):
    """Schéma pour une alerte."""
    alert_id: str
    message: str
    severity: str
    timestamp: str


# ============ Endpoints ============

@router.get(
    "/status",
    summary="Vérifier l'état de la connexion MQTT",
    responses={200: {"description": "État de la connexion"}}
)
def mqtt_status(email: str = Depends(get_current_user_email)):
    """
    Vérifie l'état de la connexion MQTT.
    Nécessite une authentification.
    """
    try:
        client = get_mqtt_client()
        return {
            "connected": client.is_connected(),
            "status": "CONNECTED" if client.is_connected() else "DISCONNECTED",
            "user": email
        }
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut MQTT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la vérification du statut MQTT"
        )


@router.post(
    "/publish",
    summary="Publier un message MQTT",
    responses={
        200: {"description": "Message publié avec succès"},
        401: {"description": "Non authentifié"},
        500: {"description": "Erreur serveur"}
    }
)
def publish_message(
    request: PublishMessageRequest,
    email: str = Depends(get_current_user_email)
):
    """
    Publie un message sur un topic MQTT.
    
    - **topic**: Le topic MQTT
    - **payload**: Les données à publier
    - **qos**: Niveau de qualité de service (0, 1, ou 2)
    - **retain**: Si le message doit être conservé
    """
    try:
        client = get_mqtt_client()
        
        if not client.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Broker MQTT non disponible"
            )
        
        success = client.publish(
            request.topic,
            request.payload,
            qos=request.qos,
            retain=request.retain
        )
        
        if success:
            logger.info(f"Message publié par {email} sur {request.topic}")
            return {
                "success": True,
                "message": "Message publié avec succès",
                "topic": request.topic
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Impossible de publier le message"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la publication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la publication du message"
        )


@router.post(
    "/command",
    summary="Envoyer une commande à un appareil",
    responses={
        200: {"description": "Commande envoyée"},
        401: {"description": "Non authentifié"},
        503: {"description": "Broker MQTT non disponible"}
    }
)
def send_command(
    request: PublishCommandRequest,
    email: str = Depends(get_current_user_email)
):
    """
    Envoie une commande à un appareil IoT.
    
    - **device_id**: L'ID de l'appareil
    - **command**: La commande à exécuter
    - **params**: Les paramètres optionnels
    """
    try:
        success = MQTTService.publish_command(
            request.device_id,
            request.command,
            request.params
        )
        
        if success:
            logger.info(f"Commande '{request.command}' envoyée par {email} à {request.device_id}")
            return {
                "success": True,
                "message": f"Commande '{request.command}' envoyée",
                "device_id": request.device_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Impossible d'envoyer la commande"
            )
            
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la commande: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'envoi de la commande"
        )


@router.get(
    "/panels/{panel_id}/data",
    response_model=List[PanelDataResponse],
    summary="Récupérer les données d'un panneau",
    responses={
        200: {"description": "Données du panneau"},
        401: {"description": "Non authentifié"}
    }
)
def get_panel_data(
    panel_id: str,
    limit: int = 10,
    email: str = Depends(get_current_user_email)
):
    """
    Récupère les dernières données d'un panneau solaire.
    
    - **panel_id**: L'ID du panneau
    - **limit**: Nombre de documents à récupérer (max 100)
    """
    try:
        if limit > 100:
            limit = 100
        
        data = MQTTService.get_panel_data(panel_id, limit)
        
        logger.info(f"Données du panneau {panel_id} récupérées par {email}")
        
        return data
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des données"
        )


@router.get(
    "/alerts",
    response_model=List[AlertResponse],
    summary="Récupérer les alertes récentes",
    responses={
        200: {"description": "Alertes récentes"},
        401: {"description": "Non authentifié"}
    }
)
def get_alerts(
    limit: int = 10,
    email: str = Depends(get_current_user_email)
):
    """
    Récupère les alertes récentes.
    
    - **limit**: Nombre d'alertes à récupérer (max 100)
    """
    try:
        if limit > 100:
            limit = 100
        
        alerts = MQTTService.get_recent_alerts(limit)
        
        logger.info(f"Alertes récupérées par {email}")
        
        return alerts
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des alertes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des alertes"
        )


@router.post(
    "/subscribe",
    summary="S'abonner à un topic MQTT",
    responses={
        200: {"description": "Abonnement réussi"},
        401: {"description": "Non authentifié"}
    }
)
def subscribe_topic(
    request: SubscribeTopicRequest,
    email: str = Depends(get_current_user_email)
):
    """
    S'abonne à un topic MQTT.
    
    - **topic**: Le topic MQTT (peut contenir des wildcards + et #)
    - **qos**: Niveau de qualité de service
    """
    try:
        client = get_mqtt_client()
        
        if not client.is_connected():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Broker MQTT non disponible"
            )
        
        success = client.subscribe(request.topic, qos=request.qos)
        
        if success:
            logger.info(f"Abonnement au topic {request.topic} par {email}")
            return {
                "success": True,
                "message": "Abonnement réussi",
                "topic": request.topic
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Impossible de s'abonner au topic"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'abonnement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'abonnement"
        )

