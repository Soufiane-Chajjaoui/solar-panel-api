"""
Utilitaires pour le traitement d'images.
"""

import base64
import io
from typing import Optional, Union
from pathlib import Path
from PIL import Image
import numpy as np


def image_to_base64(image_path: Union[str, Path]) -> Optional[str]:
    """
    Convertit une image en string base64.
    
    Args:
        image_path: Chemin vers l'image
    
    Returns:
        String base64 ou None en cas d'erreur
    """
    try:
        with open(image_path, 'rb') as img_file:
            img_bytes = img_file.read()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return img_base64
    except Exception as e:
        print(f"Erreur lors de la conversion en base64: {e}")
        return None


def base64_to_image(base64_string: str) -> Optional[Image.Image]:
    """
    Convertit une string base64 en image PIL.
    
    Args:
        base64_string: String base64 encodée
    
    Returns:
        Image PIL ou None en cas d'erreur
    """
    try:
        image_bytes = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_bytes))
        return image
    except Exception as e:
        print(f"Erreur lors de la conversion depuis base64: {e}")
        return None


def save_image_from_base64(base64_string: str, output_path: Union[str, Path]) -> bool:
    """
    Sauvegarde une image depuis une string base64.
    
    Args:
        base64_string: String base64 encodée
        output_path: Chemin où sauvegarder l'image
    
    Returns:
        True si succès, False sinon
    """
    try:
        image = base64_to_image(base64_string)
        if image:
            image.save(output_path)
            return True
        return False
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        return False

