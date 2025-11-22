"""
Service Deep Learning pour prédire l'état de propreté des panneaux solaires via images.
Utilise un modèle MobileNet entraîné pour la classification d'images.
"""

import tensorflow as tf
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)

# Chemin vers le modèle DL
MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "dl"
MODEL_PATH = MODEL_DIR / "mobilenet_solar_final.keras"

# Variable globale pour le modèle
_dl_model = None

# Taille d'image attendue par MobileNet (224x224 est standard pour MobileNet)
IMAGE_SIZE = (224, 224)

# Mapping des classes du modèle
DL_CLASS_NAMES = {
    0: "Bird-drop",
    1: "Clean",
    2: "Dusty",
    3: "Electrical-damage",
    4: "Physical-Damage",
    5: "Snow-Covered"
}

# Mapping des classes vers clean/dirty pour compatibilité
# Classes considérées comme "clean": Clean
# Classes considérées comme "dirty": Bird-drop, Dusty, Electrical-damage, Physical-Damage, Snow-Covered
DL_CLASS_TO_STATUS = {
    0: "dirty",   # Bird-drop
    1: "clean",   # Clean
    2: "Dusty",   # Dusty
    3: "Electrical-damage",   # Electrical-damage
    4: "Physical-damage",   # Physical-Damage
    5: "Snow-Covered"    # Snow-Covered
}


def load_dl_model() -> Optional[tf.keras.Model]:
    """
    Charge le modèle Deep Learning MobileNet depuis le fichier.
    
    Returns:
        Modèle Keras chargé ou None en cas d'erreur
    """
    global _dl_model
    
    if _dl_model is not None:
        return _dl_model
    
    try:
        if not MODEL_PATH.exists():
            logger.error(f"❌ Fichier modèle DL introuvable: {MODEL_PATH}")
            return None
        
        logger.info(f"📦 Chargement du modèle DL depuis {MODEL_PATH}")
        _dl_model = tf.keras.models.load_model(str(MODEL_PATH))
        logger.info("✅ Modèle DL chargé avec succès")
        
        # Vérifier la taille d'image attendue
        input_shape = _dl_model.input_shape
        if input_shape and len(input_shape) >= 3:
            global IMAGE_SIZE
            IMAGE_SIZE = (input_shape[1], input_shape[2]) if input_shape[1] and input_shape[2] else (224, 224)
            logger.info(f"📐 Taille d'image attendue par le modèle: {IMAGE_SIZE}")
        
        return _dl_model
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du modèle DL: {e}", exc_info=True)
        return None


def preprocess_image(image: Union[str, Path, Image.Image, np.ndarray, bytes]) -> Optional[np.ndarray]:
    """
    Prépare une image pour la prédiction.
    
    Args:
        image: Peut être:
            - Chemin vers un fichier image (str ou Path)
            - Image PIL
            - Array numpy
            - Bytes d'une image
            - Base64 string encodée
    
    Returns:
        Array numpy préprocessé pour le modèle ou None en cas d'erreur
    """
    try:
        # Charger l'image selon le type d'entrée
        if isinstance(image, (str, Path)):
            # Chemin de fichier
            img_path = Path(image)
            if not img_path.exists():
                logger.error(f"❌ Fichier image introuvable: {img_path}")
                return None
            logger.debug(f"📷 Chargement de l'image: {img_path}")
            img = Image.open(img_path)
            logger.debug(f"   Taille originale: {img.size}, Mode: {img.mode}")
            
        elif isinstance(image, Image.Image):
            # Image PIL déjà chargée
            img = image
            logger.debug(f"📷 Image PIL reçue, Taille: {img.size}, Mode: {img.mode}")
            
        elif isinstance(image, np.ndarray):
            # Array numpy - convertir en Image PIL
            img = Image.fromarray(image)
            logger.debug(f"📷 Conversion numpy -> PIL, Taille: {img.size}")
            
        elif isinstance(image, bytes):
            # Bytes d'une image
            img = Image.open(io.BytesIO(image))
            logger.debug(f"📷 Image depuis bytes, Taille: {img.size}")
            
        elif isinstance(image, str):
            # Peut être du base64
            try:
                # Essayer de décoder en base64
                image_bytes = base64.b64decode(image)
                img = Image.open(io.BytesIO(image_bytes))
                logger.debug(f"📷 Image depuis base64, Taille: {img.size}")
            except Exception:
                logger.error("❌ Format d'image non reconnu (attendu: chemin de fichier, PIL Image, numpy array, bytes, ou base64)")
                return None
        else:
            logger.error(f"❌ Type d'image non supporté: {type(image)}")
            return None
        
        # Convertir en RGB si nécessaire
        if img.mode != 'RGB':
            logger.debug(f"   Conversion de {img.mode} vers RGB")
            img = img.convert('RGB')
        
        # Redimensionner à la taille attendue
        img_resized = img.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
        logger.debug(f"   Image redimensionnée à: {IMAGE_SIZE}")
        
        # Convertir en array numpy
        img_array = np.array(img_resized, dtype=np.float32)
        
        # Normalisation: le modèle pourrait avoir été entraîné avec ou sans normalisation ImageNet
        # Par défaut, on essaie SANS normalisation ImageNet (juste [0,1])
        # Si les prédictions sont incorrectes, essayez avec USE_IMAGENET_NORMALIZATION = True
        
        USE_IMAGENET_NORMALIZATION = False  # Changez en True si le modèle le nécessite
        
        if USE_IMAGENET_NORMALIZATION:
            # Normaliser [0, 1] puis appliquer ImageNet normalization
            img_array = img_array / 255.0
            # Valeurs moyennes ImageNet pour chaque canal RGB
            imagenet_mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            imagenet_std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            # Normaliser avec les valeurs ImageNet par canal
            for i in range(3):
                img_array[:, :, i] = (img_array[:, :, i] - imagenet_mean[i]) / imagenet_std[i]
            logger.debug(f"   Normalisation ImageNet appliquée")
        else:
            # Normaliser simplement [0, 1]
            img_array = img_array / 255.0
            logger.debug(f"   Normalisation simple [0,1] appliquée")
        
        # Vérifier les valeurs min/max pour debugging
        logger.debug(f"   Valeurs min/max du array: {img_array.min():.4f} / {img_array.max():.4f}")
        
        # Ajouter la dimension du batch
        img_array = np.expand_dims(img_array, axis=0)
        
        logger.debug(f"   Shape final: {img_array.shape}")
        
        return img_array
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du prétraitement de l'image: {e}", exc_info=True)
        return None


def predict_from_image(image: Union[str, Path, Image.Image, np.ndarray, bytes]) -> Optional[Dict[str, Any]]:
    """
    Prédit l'état de propreté d'un panneau solaire à partir d'une image.

    Args:
        image: Image à analyser (peut être chemin de fichier, PIL Image, numpy array, bytes, ou base64)

    Returns:
        Dictionnaire avec:
            - dl_prediction: str (nom de la classe prédite, ex: "Physical-Damage")
            - dl_status: str ("clean" ou "dirty")
            - dl_confidence: float (probabilité de la classe prédite)
            - dl_probability: dict avec "clean" et "dirty" comme clés
            - dl_class_probabilities: dict avec les probabilités de chaque classe par nom
            - dl_predicted_class: int (index de la classe prédite, 0-5)
        ou None en cas d'erreur
    """
    try:
        # Charger le modèle si nécessaire
        model = load_dl_model()

        if model is None:
            logger.error("❌ Modèle DL non disponible - fichier modèle manquant ou corrompu")
            return None
        
        # Préprocesser l'image
        processed_image = preprocess_image(image)
        if processed_image is None:
            return None
        
        # Faire la prédiction
        logger.debug(f"🤖 Prédiction en cours avec le modèle...")
        predictions = model.predict(processed_image, verbose=0)
        
        # Gérer différentes configurations de sortie
        if len(predictions.shape) != 2:
            logger.error(f"❌ Format de prédiction non attendu: {predictions.shape}")
            return None
        
        num_classes = predictions.shape[1]
        prediction_probs = predictions[0]
        
        # Afficher toutes les probabilités pour debugging
        logger.debug(f"📊 Probabilités brutes: {prediction_probs}")
        
        # Trouver la classe prédite (celle avec la probabilité la plus élevée)
        prediction_class = int(np.argmax(prediction_probs))
        confidence = float(prediction_probs[prediction_class])
        
        logger.debug(f"   Classe prédite (index): {prediction_class}, Confiance: {confidence:.4f}")
        
        # Obtenir le nom de la classe prédite
        predicted_class_name = DL_CLASS_NAMES.get(prediction_class, f"Class-{prediction_class}")
        
        # Créer un dictionnaire avec les probabilités de chaque classe par nom
        class_probabilities = {}
        for class_idx in range(num_classes):
            class_name = DL_CLASS_NAMES.get(class_idx, f"Class-{class_idx}")
            class_probabilities[class_name] = float(prediction_probs[class_idx])
        
        # Calculer clean/dirty basé sur le mapping des classes
        if num_classes == 6:
            # Modèle avec 6 classes - utiliser le mapping défini
            probability_clean = sum(
                float(prediction_probs[i]) 
                for i in range(num_classes) 
                if DL_CLASS_TO_STATUS.get(i, "dirty") == "clean"
            )
            probability_dirty = sum(
                float(prediction_probs[i]) 
                for i in range(num_classes) 
                if DL_CLASS_TO_STATUS.get(i, "dirty") == "dirty"
            )
            
            # Déterminer le statut basé sur la classe prédite
            dl_status = DL_CLASS_TO_STATUS.get(prediction_class, "dirty")
            
            logger.debug(f"📊 6 classes détectées:")
            for class_idx, class_name in DL_CLASS_NAMES.items():
                logger.debug(f"   {class_name} (class {class_idx}): {prediction_probs[class_idx]:.4f}")
            logger.debug(f"   Classe prédite: {prediction_class} ({predicted_class_name}) -> {dl_status}")
        elif num_classes == 2:
            # Cas binaire classique
            probability_clean = float(prediction_probs[0])
            probability_dirty = float(prediction_probs[1])
            dl_status = "dirty" if prediction_class == 1 else "clean"
            predicted_class_name = "Clean" if prediction_class == 0 else "Dirty"
        elif num_classes == 1:
            # Cas sigmoid (une seule probabilité)
            probability_dirty = float(prediction_probs[0])
            probability_clean = 1.0 - probability_dirty
            dl_status = "dirty" if probability_dirty > 0.5 else "clean"
            predicted_class_name = "Dirty" if dl_status == "dirty" else "Clean"
        else:
            # Cas générique pour n'importe quel nombre de classes
            split_point = num_classes // 2
            probability_clean = float(np.sum(prediction_probs[:split_point]))
            probability_dirty = float(np.sum(prediction_probs[split_point:]))
            dl_status = "dirty" if prediction_class >= split_point else "clean"
            predicted_class_name = DL_CLASS_NAMES.get(prediction_class, f"Class-{prediction_class}")
            logger.warning(f"⚠️ Nombre de classes non standard ({num_classes}), utilisation de mapping générique")
        
        # S'assurer que les probabilités totalisent 1.0 (normalisation)
        total_prob = probability_clean + probability_dirty
        if abs(total_prob - 1.0) > 0.01:  # Tolérance pour erreurs d'arrondi
            # Renormaliser si nécessaire
            probability_clean = probability_clean / total_prob if total_prob > 0 else 0.5
            probability_dirty = probability_dirty / total_prob if total_prob > 0 else 0.5
        
        result = {
            "dl_prediction": predicted_class_name,  # Nom de la classe prédite (ex: "Physical-Damage")
            "dl_status": dl_status,  # Statut clean/dirty
            "dl_confidence": confidence,  # Probabilité de la classe prédite
            "dl_probability": {
                "clean": probability_clean,
                "dirty": probability_dirty
            },
            "dl_class_probabilities": class_probabilities,  # Probabilités de chaque classe par nom
            "dl_predicted_class": int(prediction_class)  # Index de la classe prédite (0-5)
        }
        
        logger.info(f"✅ Prédiction DL: {predicted_class_name} ({dl_status}, confiance: {confidence:.2%})")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la prédiction DL: {e}", exc_info=True)
        return None


def is_dl_model_loaded() -> bool:
    """Vérifie si le modèle DL est chargé."""
    global _dl_model
    return _dl_model is not None

