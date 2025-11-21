"""
Client MQTT pour la communication avec les appareils IoT.
Gère la connexion, la publication et la souscription aux topics MQTT.
"""

import paho.mqtt.client as mqtt
import json
import logging
from typing import Callable, Optional, Dict, Any
from app.core.config import settings
from threading import Thread, Event
import time

logger = logging.getLogger(__name__)


class MQTTClient:
    """Client MQTT pour gérer la communication avec le broker."""

    def __init__(self):
        """Initialise le client MQTT."""
        self.client = mqtt.Client(
            client_id=settings.MQTT_CLIENT_ID,
            clean_session=True,
            protocol=mqtt.MQTTv311
        )

        # Configuration TLS pour HiveMQ Cloud
        if settings.MQTT_USE_TLS:
            import ssl
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.client.tls_set_context(context)
            logger.info("✅ TLS configuré pour HiveMQ Cloud")

        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe

        # État
        self.connected = False
        self.connection_event = Event()
        self.message_callbacks: Dict[str, Callable] = {}

        # Authentification
        if settings.MQTT_BROKER_USERNAME and settings.MQTT_BROKER_PASSWORD:
            self.client.username_pw_set(
                settings.MQTT_BROKER_USERNAME,
                settings.MQTT_BROKER_PASSWORD
            )
            logger.info("✅ Authentification MQTT configurée")
# fonction pour liée le backend avec Mosquitto
    def _on_connect(self, client, userdata, flags, rc):
        """Callback appelé lors de la connexion au broker."""
        if rc == 0:
            self.connected = True
            self.connection_event.set()
            logger.info("✅ Connecté au broker MQTT")

            # S'abonner aux topics par défaut
            self._subscribe_default_topics()
        else:
            self.connected = False
            logger.error(f"❌ Erreur de connexion MQTT: code {rc}")
            self._log_connection_error(rc)

    def _on_disconnect(self, client, userdata, rc):
        """Callback appelé lors de la déconnexion."""
        self.connected = False
        self.connection_event.clear()

        if rc != 0:
            logger.warning(f"⚠️ Déconnexion inattendue du broker MQTT: code {rc}")
        else:
            logger.info("✅ Déconnecté du broker MQTT")

    def _on_message(self, client, userdata, msg):
        """Callback appelé à la réception d'un message."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            logger.debug(f"📨 Message reçu sur {topic}: {payload}")

            # Essayer de parser en JSON
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload

            # Appeler le callback si enregistré
            if topic in self.message_callbacks:
                callback = self.message_callbacks[topic]
                callback(topic, data)

            # Appeler les callbacks wildcard
            for registered_topic, callback in self.message_callbacks.items():
                if self._topic_matches(topic, registered_topic):
                    callback(topic, data)

        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement du message: {e}")

    def _on_publish(self, client, userdata, mid):
        """Callback appelé après la publication d'un message."""
        logger.debug(f"✅ Message publié (ID: {mid})")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback appelé après la souscription."""
        logger.debug(f"✅ Souscription confirmée (ID: {mid}, QoS: {granted_qos})")

    def connect(self) -> bool:
        """
        Établit la connexion au broker MQTT.

        Returns:
            True si la connexion est réussie, False sinon
        """
        try:
            logger.info(f"🔗 Connexion au broker MQTT: {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")

            self.client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                keepalive=settings.MQTT_KEEPALIVE
            )

            # Démarrer la boucle de traitement
            self.client.loop_start()

            # Attendre la connexion (timeout 5 secondes)
            if self.connection_event.wait(timeout=5):
                return True
            else:
                logger.error("❌ Timeout lors de la connexion MQTT")
                return False

        except Exception as e:
            logger.error(f"❌ Erreur lors de la connexion MQTT: {e}")
            return False

    def disconnect(self):
        """Déconnecte du broker MQTT."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("✅ Déconnexion MQTT réussie")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la déconnexion MQTT: {e}")

    def publish(
        self,
        topic: str,
        payload: Any,
        qos: Optional[int] = None,
        retain: Optional[bool] = None
    ) -> bool:
        """
        Publie un message sur un topic MQTT.

        Args:
            topic: Le topic MQTT
            payload: Le message (dict, str, ou bytes)
            qos: Niveau de qualité de service (0, 1, ou 2)
            retain: Si le message doit être conservé

        Returns:
            True si la publication est réussie, False sinon
        """
        try:
            if not self.connected:
                logger.warning("⚠️ Non connecté au broker MQTT")
                return False

            # Convertir le payload en JSON si c'est un dict
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            elif not isinstance(payload, (str, bytes)):
                payload = str(payload)

            # Utiliser les valeurs par défaut si non spécifiées
            qos = qos if qos is not None else settings.MQTT_QOS
            retain = retain if retain is not None else settings.MQTT_RETAIN

            result = self.client.publish(
                topic,
                payload,
                qos=qos,
                retain=retain
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📤 Message publié sur {topic}")
                return True
            else:
                logger.error(f"❌ Erreur lors de la publication: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"❌ Erreur lors de la publication: {e}")
            return False

    def subscribe(
        self,
        topic: str,
        callback: Optional[Callable] = None,
        qos: Optional[int] = None
    ) -> bool:
        """
        S'abonne à un topic MQTT.

        Args:
            topic: Le topic MQTT (peut contenir des wildcards)
            callback: Fonction appelée à la réception d'un message
            qos: Niveau de qualité de service

        Returns:
            True si la souscription est réussie, False sinon
        """
        try:
            if not self.connected:
                logger.warning("⚠️ Non connecté au broker MQTT")
                return False

            qos = qos if qos is not None else settings.MQTT_QOS

            result = self.client.subscribe(topic, qos=qos)

            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📥 Souscription au topic: {topic}")

                # Enregistrer le callback
                if callback:
                    self.message_callbacks[topic] = callback

                return True
            else:
                logger.error(f"❌ Erreur lors de la souscription: {result[0]}")
                return False

        except Exception as e:
            logger.error(f"❌ Erreur lors de la souscription: {e}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """
        Se désabonne d'un topic MQTT.

        Args:
            topic: Le topic MQTT

        Returns:
            True si la désouscription est réussie, False sinon
        """
        try:
            if not self.connected:
                logger.warning("⚠️ Non connecté au broker MQTT")
                return False

            result = self.client.unsubscribe(topic)

            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📭 Désouscription du topic: {topic}")

                # Supprimer le callback
                if topic in self.message_callbacks:
                    del self.message_callbacks[topic]

                return True
            else:
                logger.error(f"❌ Erreur lors de la désouscription: {result[0]}")
                return False

        except Exception as e:
            logger.error(f"❌ Erreur lors de la désouscription: {e}")
            return False

    def _subscribe_default_topics(self):
        """S'abonne aux topics par défaut."""
        default_topics = [
            settings.MQTT_TOPIC_SOLAR_PANEL,
        ]

        for topic in default_topics:
            self.subscribe(topic)

    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """
        Vérifie si un topic correspond à un pattern avec wildcards.

        Args:
            topic: Le topic reçu
            pattern: Le pattern avec wildcards (+ ou #)

        Returns:
            True si le topic correspond au pattern
        """
        topic_parts = topic.split('/')
        pattern_parts = pattern.split('/')

        for i, pattern_part in enumerate(pattern_parts):
            if i >= len(topic_parts):
                return False

            if pattern_part == '#':
                return True
            elif pattern_part != '+' and pattern_part != topic_parts[i]:
                return False

        return len(topic_parts) == len(pattern_parts)

    def _log_connection_error(self, rc: int):
        """Affiche le message d'erreur correspondant au code de retour."""
        error_messages = {
            1: "Protocole MQTT incorrect",
            2: "Identifiant client rejeté",
            3: "Serveur indisponible",
            4: "Identifiants incorrects",
            5: "Non autorisé"
        }

        message = error_messages.get(rc, f"Erreur inconnue (code {rc})")
        logger.error(f"❌ {message}")

    def is_connected(self) -> bool:
        """Retourne l'état de la connexion."""
        return self.connected


# Instance globale du client MQTT
mqtt_client: Optional[MQTTClient] = None


def get_mqtt_client() -> MQTTClient:
    """Retourne l'instance globale du client MQTT."""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = MQTTClient()
    return mqtt_client


def init_mqtt() -> bool:
    """Initialise la connexion MQTT au démarrage."""
    try:
        client = get_mqtt_client()
        if client.connect():
            logger.info("✅ Client MQTT initialisé avec succès")
            return True
        else:
            logger.error("❌ Impossible de connecter le client MQTT")
            return False
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation MQTT: {e}")
        return False


def close_mqtt():
    """Ferme la connexion MQTT à l'arrêt."""
    global mqtt_client
    if mqtt_client:
        mqtt_client.disconnect()
        mqtt_client = None
        logger.info("✅ Client MQTT fermé")
