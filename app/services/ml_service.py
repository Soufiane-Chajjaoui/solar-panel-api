"""
Service ML pour prédire l'état de propreté des panneaux solaires.
Utilise un modèle Gradient Boosting entraîné.
"""

import joblib
import numpy as np
import logging
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Chemin vers les modèles
MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "ml"
SCALER_PATH = MODEL_DIR / "scaler.joblib"
MODEL_PATH = MODEL_DIR / "best_model.joblib"

# Variables globales pour le modèle et le scaler
_model = None
_scaler = None


def load_model() -> Tuple[Optional[Any], Optional[Any]]:
    """
    Charge le modèle ML et le scaler depuis les fichiers.
    
    Returns:
        Tuple (model, scaler) ou (None, None) en cas d'erreur
    """
    global _model, _scaler
    
    if _model is not None and _scaler is not None:
        return _model, _scaler
    
    try:
        if not SCALER_PATH.exists():
            logger.error(f"❌ Fichier scaler introuvable: {SCALER_PATH}")
            return None, None
        
        if not MODEL_PATH.exists():
            logger.error(f"❌ Fichier modèle introuvable: {MODEL_PATH}")
            return None, None
        
        logger.info(f"📦 Chargement du scaler depuis {SCALER_PATH}")
        _scaler = joblib.load(SCALER_PATH)
        
        logger.info(f"📦 Chargement du modèle depuis {MODEL_PATH}")
        _model = joblib.load(MODEL_PATH)
        
        logger.info("✅ Modèle ML chargé avec succès")
        return _model, _scaler
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du modèle ML: {e}")
        return None, None


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
    Prédit l'état de propreté d'un panneau solaire.
    
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
        # Charger le modèle si nécessaire
        model, scaler = load_model()
        
        if model is None or scaler is None:
            logger.error("❌ Modèle ML non disponible")
            return None
        
        # Préparer les features
        features = prepare_features(data)
        if features is None:
            return None
        
        # Normaliser les features
        features_scaled = scaler.transform(features)
        
        # Faire la prédiction
        prediction = model.predict(features_scaled)[0]
        
        # Obtenir les probabilités pour les deux classes
        probability_clean = None
        probability_dirty = None
        confidence = None
        
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(features_scaled)[0]
            # proba[0] = clean (classe 0), proba[1] = dirty (classe 1)
            probability_clean = float(proba[0])
            probability_dirty = float(proba[1])
            # La confiance est la probabilité de la classe prédite
            confidence = float(proba[int(prediction)])
        
        # Convertir en statut lisible
        ml_prediction = "dirty" if int(prediction) == 1 else "clean"
        
        result = {
            "ml_prediction": ml_prediction,
            "ml_confidence": confidence,
            "ml_probability": {
                "clean": probability_clean,
                "dirty": probability_dirty
            } if probability_clean is not None and probability_dirty is not None else None
        }
        
        if confidence is not None:
            logger.info(f"✅ Prédiction ML: {ml_prediction} (confiance: {confidence:.2%})")
        else:
            logger.info(f"✅ Prédiction ML: {ml_prediction}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la prédiction ML: {e}")
        return None


def is_model_loaded() -> bool:
    """Vérifie si le modèle est chargé."""
    global _model, _scaler
    return _model is not None and _scaler is not None

