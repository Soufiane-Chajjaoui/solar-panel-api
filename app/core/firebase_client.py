import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage
import logging

logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis .env
load_dotenv()

# Lire le chemin du fichier JSON depuis la variable d'environnement
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")

# Initialiser Firebase
db = None
bucket = None

try:
    if os.path.exists(firebase_cred_path):
        logger.info(f"✅ Fichier Firebase trouvé: {firebase_cred_path}")
        cred = credentials.Certificate(firebase_cred_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        # Initialize Firebase Storage bucket
        # Only initialize if storage bucket is explicitly configured
        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        if bucket_name:
            try:
                bucket = storage.bucket(bucket_name)
                logger.info("✅ Firebase Storage initialisé avec succès")
            except Exception as storage_error:
                logger.warning(f"⚠️ Firebase Storage non disponible: {storage_error}")
                bucket = None
        else:
            # If no bucket name configured, skip Firebase Storage (using Cloudinary instead)
            logger.info("ℹ️ Firebase Storage non configuré (utilisation de Cloudinary)")
            bucket = None
        
        logger.info("✅ Firebase initialisé avec succès")
    else:
        logger.warning(f"⚠️ Fichier Firebase introuvable: {firebase_cred_path}")
        logger.warning("⚠️ Firebase ne sera pas disponible. Utilisez le mode mock pour les tests.")
        db = None
        bucket = None
except Exception as e:
    logger.error(f"❌ Erreur lors de l'initialisation de Firebase: {e}")
    logger.warning("⚠️ Firebase ne sera pas disponible. Utilisez le mode mock pour les tests.")
    db = None
    bucket = None
