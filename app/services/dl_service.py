"""
Service Deep Learning pour prédire l'état de propreté des panneaux solaires via images.
Utilise un modèle MobileNet converti en ONNX pour les prédictions.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from PIL import Image
import numpy as np
import io

import onnxruntime as ort

logger = logging.getLogger(__name__)

# Chemin vers le modèle ONNX
MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "dl"
MODEL_PATH = MODEL_DIR / "mobilenet_solar_final.onnx"

# Taille d'image attendue par MobileNet
IMAGE_SIZE = (224, 224)

# Mapping des classes
DL_CLASS_NAMES = {
    0: "Bird-drop",
    1: "Clean",
    2: "Dusty",
    3: "Electrical-damage",
    4: "Physical-Damage",
    5: "Snow-Covered"
}

DL_CLASS_TO_STATUS = {
    0: "dirty",
    1: "clean",
    2: "dirty",
    3: "dirty",
    4: "dirty",
    5: "dirty"
}

# Session ONNX globale
_onnx_session: Optional[ort.InferenceSession] = None
_onnx_input_name: Optional[str] = None

def load_onnx_model() -> Optional[ort.InferenceSession]:
    """Charge le modèle ONNX et initialise la session."""
    global _onnx_session, _onnx_input_name
    if _onnx_session is not None:
        return _onnx_session

    if not MODEL_PATH.exists():
        logger.error(f"❌ Fichier ONNX introuvable: {MODEL_PATH}")
        return None

    try:
        _onnx_session = ort.InferenceSession(str(MODEL_PATH))
        _onnx_input_name = _onnx_session.get_inputs()[0].name
        logger.info(f"✅ Modèle ONNX chargé avec succès: {MODEL_PATH}")
        return _onnx_session
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du modèle ONNX: {e}", exc_info=True)
        return None

def preprocess_image(image: Union[str, Path, Image.Image, bytes]) -> Optional[np.ndarray]:
    """Prépare l'image pour la prédiction ONNX au format [N, H, W, C]."""
    try:
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        elif isinstance(image, Image.Image):
            img = image
        elif isinstance(image, bytes):
            img = Image.open(io.BytesIO(image))
        else:
            logger.error(f"❌ Type d'image non supporté: {type(image)}")
            return None

        # Convertir en RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Redimensionner
        img_resized = img.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)

        # Convertir en numpy et Normalisation simple [0,1]
        img_array = np.array(img_resized, dtype=np.float32) / 255.0

        # Le tenseur est déjà au format [H, W, C] (224, 224, 3)
        # Ajouter uniquement la dimension du batch
        img_array = np.expand_dims(img_array, axis=0) # Ajoute N (Batch) -> [1, 224, 224, 3]

        # Le tenseur est maintenant au format [1, 224, 224, 3]
        return img_array
    except Exception as e:
        logger.error(f"❌ Erreur lors du prétraitement de l'image: {e}", exc_info=True)
        return None

def predict_from_image(image: Union[str, Path, Image.Image, bytes]) -> Optional[Dict[str, Any]]:
    """Prédit l'état de propreté d'un panneau solaire à partir d'une image avec ONNX."""
    try:
        session = load_onnx_model()
        if session is None:
            return None

        img_array = preprocess_image(image)
        if img_array is None:
            return None

        # Run inference
        outputs = session.run(None, { _onnx_input_name: img_array })
        predictions = outputs[0]  # normalement shape [1, 6]

        if predictions.shape[0] != 1:
            logger.error(f"❌ Format de sortie inattendu: {predictions.shape}")
            return None

        prediction_probs = predictions[0]
        predicted_class = int(np.argmax(prediction_probs))
        confidence = float(prediction_probs[predicted_class])
        predicted_class_name = DL_CLASS_NAMES.get(predicted_class, f"Class-{predicted_class}")

        # Calculer clean/dirty
        probability_clean = sum(
            float(prediction_probs[i]) for i in range(len(prediction_probs))
            if DL_CLASS_TO_STATUS.get(i, "dirty") == "clean"
        )
        probability_dirty = sum(
            float(prediction_probs[i]) for i in range(len(prediction_probs))
            if DL_CLASS_TO_STATUS.get(i, "dirty") == "dirty"
        )
        total_prob = probability_clean + probability_dirty
        if abs(total_prob - 1.0) > 0.01 and total_prob > 0:
            probability_clean /= total_prob
            probability_dirty /= total_prob

        dl_status = DL_CLASS_TO_STATUS.get(predicted_class, "dirty")

        result = {
            "dl_prediction": predicted_class_name,
            "dl_status": dl_status,
            "dl_confidence": confidence,
            "dl_probability": {
                "clean": probability_clean,
                "dirty": probability_dirty
            },
            "dl_class_probabilities": {
                DL_CLASS_NAMES[i]: float(prediction_probs[i]) for i in range(len(prediction_probs))
            },
            "dl_predicted_class": predicted_class
        }

        logger.info(f"✅ Prédiction DL via ONNX: {predicted_class_name} ({dl_status}, confiance: {confidence:.2%})")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur lors de la prédiction DL avec ONNX: {e}", exc_info=True)
        return None

def is_dl_model_loaded() -> bool:
    return _onnx_session is not None

async def initialize_dl_model():
    """
    Initialise le modèle DL au démarrage de l'application.
    À appeler dans le lifespan de FastAPI.
    """
    try:
        logger.info("🚀 Initialisation du modèle DL...")
        model = load_onnx_model()
        if model is not None:
            logger.info("✅ Modèle DL initialisé avec succès")
        else:
            logger.warning("⚠️ Échec de l'initialisation du modèle DL")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation du modèle DL: {e}")