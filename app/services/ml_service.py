"""
Service ML pour prédire l'état de propreté des panneaux solaires.
Utilise un modèle ONNX optimisé pour les performances et la taille réduite.
"""

import numpy as np
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("⚠️ ONNX Runtime non disponible, fonctionnalités ML limitées")

logger = logging.getLogger(__name__)

# Chemin vers les modèles
MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "ml"
MODEL_PATH = MODEL_DIR / "best_model.onnx"

# Variable globale pour la session ONNX
_session = None


def load_model() -> Optional[Any]:
    """
    Charge le modèle ONNX depuis le fichier.

    Returns:
        Session ONNX ou None en cas d'erreur
    """
    global _session

    if _session is not None:
        return _session

    if not ONNX_AVAILABLE:
        logger.error("❌ ONNX Runtime non disponible")
        return None

    try:
        if not MODEL_PATH.exists():
            logger.error(f"❌ Fichier modèle ONNX introuvable: {MODEL_PATH}")
            return None

        logger.info(f"📦 Chargement du modèle ONNX depuis {MODEL_PATH}")
        _session = ort.InferenceSession(str(MODEL_PATH))

        logger.info("✅ Modèle ONNX chargé avec succès")
        return _session

    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du modèle ONNX: {e}")
        return None


def prepare_features(data: Dict[str, Any]) -> Optional[np.ndarray]:
    """
    Prépare les features à partir des données brutes.
    
    Args:
        data: Dictionnaire contenant temperature, humidity, light, R, G, B
        
    Returns:
        Array numpy avec les features préparées ou None en cas d'erreur
    """
    try:
        # Extraire les valeurs
        temperature = float(data.get("temperature", 0))
        humidity = float(data.get("humidity", 0))
        light = float(data.get("light", 0))
        R = float(data.get("R", 0))
        G = float(data.get("G", 0))
        B = float(data.get("B", 0))
        
        # Calculer les features dérivées
        RGB_mean = (R + G + B) / 3.0
        RGB_std = np.std([R, G, B])
        G_over_R = G / (R + 1e-6)  # Éviter la division par zéro
        B_over_R = B / (R + 1e-6)
        
        # Construire le vecteur de features dans l'ordre correct
        # [temperature, humidity, light, R, G, B, RGB_mean, RGB_std, G_over_R, B_over_R]
        features = np.array([[
            temperature,
            humidity,
            light,
            R,
            G,
            B,
            RGB_mean,
            RGB_std,
            G_over_R,
            B_over_R
        ]])
        
        return features
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la préparation des features: {e}")
        return None


def predict_cleaning_status(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Prédit l'état de propreté d'un panneau solaire en utilisant ONNX.

    Args:
        data: Dictionnaire contenant les données du capteur:
            - temperature: float
            - humidity: float
            - light: float
            - R: int (valeur RGB rouge)
            - G: int (valeur RGB vert)
            - B: int (valeur RGB bleu)

    Returns:
        Dictionnaire avec:
            - ml_prediction: str ("clean" ou "dirty")
            - ml_confidence: float (probabilité de la classe prédite)
            - ml_probability: dict avec "clean" et "dirty" comme clés
        ou None en cas d'erreur
    """
    try:
        # Charger le modèle ONNX si nécessaire
        session = load_model()

        if session is None:
            logger.error("❌ Modèle ONNX non disponible")
            return None

        # Préparer les features
        features = prepare_features(data)
        if features is None:
            return None

        # Convertir en float32 pour ONNX
        features = features.astype(np.float32)

        # Faire l'inférence ONNX
        input_name = session.get_inputs()[0].name
        inputs = {input_name: features}
        outputs = session.run(None, inputs)

        # outputs[0] = prédictions, outputs[1] = probabilités
        prediction = int(outputs[0][0])

        # Extraire les probabilités
        probability_clean = None
        probability_dirty = None
        confidence = None

        if len(outputs) > 1:
            # Les probabilités sont dans outputs[1]
            probas = outputs[1][0]
            if isinstance(probas, dict):
                # Format dictionnaire
                probability_clean = float(probas.get(0, probas.get('0', 0)))
                probability_dirty = float(probas.get(1, probas.get('1', 0)))
            else:
                # Format array
                probability_clean = float(probas[0])
                probability_dirty = float(probas[1])

            # La confiance est la probabilité de la classe prédite
            confidence = probability_dirty if prediction == 1 else probability_clean

        # Convertir en statut lisible
        ml_prediction = "dirty" if prediction == 1 else "clean"

        result = {
            "ml_prediction": ml_prediction,
            "ml_confidence": confidence,
            "ml_probability": {
                "clean": probability_clean,
                "dirty": probability_dirty
            } if probability_clean is not None and probability_dirty is not None else None
        }

        if confidence is not None:
            logger.info(f"✅ Prédiction ONNX: {ml_prediction} (confiance: {confidence:.2%})")
        else:
            logger.info(f"✅ Prédiction ONNX: {ml_prediction}")

        return result

    except Exception as e:
        logger.error(f"❌ Erreur lors de la prédiction ONNX: {e}")
        return None


def is_model_loaded() -> bool:
    """Vérifie si le modèle ONNX est chargé."""
    global _session
    return _session is not None

