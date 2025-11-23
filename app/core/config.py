"""
Configuration centralisée pour l'application.
Gère toutes les variables d'environnement de manière sécurisée.
"""

from typing import List
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()


class Settings:
    """Configuration de l'application."""

    # ============ Application ============
    PROJECT_NAME: str = "Smart Solar Panel Cleaner API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    API_VERSION: str = "1.0.0"

    # ============ Serveur ============
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "False").lower() == "true"

    # ============ JWT & Authentification ============
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ============ Firebase ============
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")

    # ============ Cloudinary ============
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

    # ============ Sécurité ============
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # secondes

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ============ Logging ============
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json ou text

    # ============ MQTT ============
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_BROKER_USERNAME: str = os.getenv("MQTT_BROKER_USERNAME", "")
    MQTT_BROKER_PASSWORD: str = os.getenv("MQTT_BROKER_PASSWORD", "")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "solar-panel-api")
    MQTT_KEEPALIVE: int = int(os.getenv("MQTT_KEEPALIVE", "60"))
    MQTT_QOS: int = int(os.getenv("MQTT_QOS", "1"))
    MQTT_RETAIN: bool = os.getenv("MQTT_RETAIN", "false").lower() == "true"
    MQTT_USE_TLS: bool = os.getenv("MQTT_USE_TLS", "false").lower() == "true"

    # Topics MQTT
    MQTT_TOPIC_SOLAR_PANEL: str = os.getenv("MQTT_TOPIC_SOLAR_PANEL", "solar/panel/#")  # Recevoir les données des panneaux
    MQTT_TOPIC_SOLAR_COMMAND: str = os.getenv("MQTT_TOPIC_SOLAR_COMMAND", "solar/command")  # Publier les événements


# Instance globale des settings
settings = Settings()


def validate_settings():
    """Valide les paramètres critiques au démarrage."""
    if settings.JWT_SECRET_KEY == "your-secret-key-change-in-production":
        raise ValueError(
            "⚠️ ERREUR: JWT_SECRET_KEY n'est pas configurée! "
            "Définissez JWT_SECRET_KEY dans votre fichier .env"
        )

    if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        raise FileNotFoundError(
            f"⚠️ ERREUR: Fichier Firebase introuvable à {settings.FIREBASE_CREDENTIALS_PATH}"
        )

    return True

