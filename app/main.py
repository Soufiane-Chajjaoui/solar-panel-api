"""
Application FastAPI principale pour le système de nettoyage de panneaux solaires.
Intègre l'authentification, les routes et la configuration de sécurité.
"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.firebase_client import db
from app.core.config import settings, validate_settings
from app.core.mqtt_client import init_mqtt, close_mqtt, get_mqtt_client
from app.routes import panel_routes, cleaning_routes, user_routes, auth_routes, mqtt_routes, upload_routes, predict_routes, history_routes, feedback_routes
from app.services.dl_service import initialize_dl_model
from app.services.mqtt_service import MQTTService
import logging
from prometheus_fastapi_instrumentator import Instrumentator

# ============ Configuration du logging ============
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger('fastapi_app')

# ============ Validation des paramètres ============
try:
    validate_settings()
    logger.info("✅ Configuration validée avec succès")
except Exception as e:
    logger.error(f"❌ Erreur de configuration: {e}")
    raise

# ============ Création de l'application ============
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API pour la gestion intelligente du nettoyage de panneaux solaires",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

Instrumentator().instrument(app).expose(app)
logger.info("📊 Monitoring Prometheus ACTIVÉ")

# ============ Configuration CORS ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

MAX_REQUEST_SIZE = 100_000_000  # 100 MB

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    body = await request.body()
    if len(body) > MAX_REQUEST_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Request too large"
        )
    return await call_next(request)

logger.info("✅ CORS configuré")

# ============ Routes ============

@app.get(
    "/",
    tags=["Health"],
    summary="Vérifier l'état de l'API",
    responses={200: {"description": "API en fonctionnement"}}
)
def root():
    """Endpoint de santé pour vérifier que l'API est en fonctionnement."""
    return {
        "message": "🌞 Smart Solar Panel Cleaner API Running",
        "version": settings.API_VERSION,
        "status": "healthy"
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Vérifier la santé de l'API",
    responses={200: {"description": "API saine"}}
)
def health_check():
    """Endpoint de santé détaillé."""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "debug": settings.DEBUG
    }


@app.get(
    "/test-firebase",
    tags=["Debug"],
    summary="Tester la connexion Firebase"
)
def test_firebase():
    """Teste la connexion à Firebase Firestore."""
    if db is None:
        return {
            "connected": False,
            "message": "⚠️ Firebase n'est pas configuré",
            "details": "Veuillez configurer FIREBASE_CREDENTIALS_PATH dans .env et placer le fichier serviceAccountKey.json",
            "status": "NOT_CONFIGURED"
        }

    try:
        doc = db.collection("test").document("12").get()
        return {
            "connected": True,
            "message": "✅ Connexion Firebase réussie",
            "document_exists": doc.exists,
            "status": "CONNECTED"
        }
    except Exception as e:
        logger.error(f"Erreur Firebase: {e}")
        return {
            "connected": False,
            "error": str(e),
            "status": "ERROR"
        }


@app.get(
    "/test-mqtt",
    tags=["Debug"],
    summary="Tester la connexion MQTT"
)
def test_mqtt():
    """Teste la connexion au broker MQTT."""
    try:
        client = get_mqtt_client()
        return {
            "connected": client.is_connected(),
            "broker": f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}",
            "client_id": settings.MQTT_CLIENT_ID,
            "message": "✅ Connexion MQTT réussie" if client.is_connected() else "⚠️ Non connecté au broker MQTT",
            "status": "CONNECTED" if client.is_connected() else "DISCONNECTED"
        }
    except Exception as e:
        logger.error(f"Erreur MQTT: {e}")
        return {
            "connected": False,
            "error": str(e),
            "status": "ERROR"
        }


# ============ Enregistrement des routes ============
app.include_router(auth_routes.router)
app.include_router(mqtt_routes.router)

# Enregistrer les autres routes si elles existent
if hasattr(panel_routes, 'router'):
    app.include_router(panel_routes.router)
if hasattr(cleaning_routes, 'router'):
    app.include_router(cleaning_routes.router)
if hasattr(user_routes, 'router'):
    app.include_router(user_routes.router)
if hasattr(upload_routes, 'router'):
    app.include_router(upload_routes.router)
if hasattr(predict_routes, 'router'):
    app.include_router(predict_routes.router)
if hasattr(history_routes, 'router'):
    app.include_router(history_routes.router)
if hasattr(feedback_routes, 'router'):
    app.include_router(feedback_routes.router)

logger.info("✅ Routes enregistrées avec succès")


# ============ Gestion des erreurs globales ============
@app.exception_handler(Exception)
async def global_exception_handler(_, exc):
    """Gestionnaire global des exceptions."""
    logger.error(f"Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erreur interne du serveur"}
    )


# ============ Événements de démarrage/arrêt ============
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Gestionnaire du cycle de vie de l'application."""
    # Démarrage
    logger.info("🚀 Application démarrée")

    # Initialiser le modèle DL
    logger.info("🤖 Initialisation du modèle DL...")
    await initialize_dl_model()

    # Initialiser MQTT
    logger.info("🔗 Initialisation du client MQTT...")
    if init_mqtt():
        logger.info("✅ Client MQTT initialisé avec succès")

        # S'abonner aux topics MQTT
        logger.info("📡 Configuration des abonnements MQTT...")
        MQTTService.subscribe_to_topics()
        logger.info("✅ Abonnements MQTT configurés")
    else:
        logger.warning("⚠️ Impossible de connecter le client MQTT (mode dégradé)")

    yield
    # Arrêt
    logger.info("🛑 Arrêt de l'application...")
    close_mqtt()
    logger.info("✅ Application arrêtée")
    
# Appliquer le lifespan
app.router.lifespan_context = lifespan
