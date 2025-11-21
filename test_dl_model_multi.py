"""
Script de test pour tester le modèle DL avec plusieurs images.
Vérifie que le modèle fait des prédictions différentes pour différentes images.
"""

import sys
import json
from pathlib import Path
from app.services.dl_service import predict_from_image, load_dl_model
import logging

# Configurer le logging pour voir les détails
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_multiple_images(image_paths):
    """
    Teste la prédiction sur plusieurs images.
    
    Args:
        image_paths: Liste de chemins vers les images à tester
    """
    print(f"\n{'='*60}")
    print(f"🧪 TEST MULTI-IMAGES DU MODÈLE DEEP LEARNING")
    print(f"{'='*60}\n")
    
    # Charger le modèle une seule fois
    print("📦 Chargement du modèle DL...")
    model = load_dl_model()
    
    if model is None:
        print("❌ ERREUR: Impossible de charger le modèle DL")
        return
    
    print("✅ Modèle DL chargé avec succès\n")
    
    results = []
    
    for i, image_path in enumerate(image_paths, 1):
        image_file = Path(image_path)
        if not image_file.exists():
            print(f"❌ Image {i}: Fichier introuvable: {image_path}")
            continue
        
        print(f"\n{'='*60}")
        print(f"🖼️  Image {i}/{len(image_paths)}: {image_file.name}")
        print(f"{'='*60}")
        
        # Faire la prédiction
        result = predict_from_image(image_path)
        
        if result:
            results.append({
                "image": str(image_file),
                "prediction": result['dl_prediction'],
                "status": result.get('dl_status', 'unknown'),
                "confidence": result['dl_confidence'],
                "class_index": result.get('dl_predicted_class', -1),
                "all_probs": result.get('dl_class_probabilities', {})
            })
            
            print(f"✅ Prédiction: {result['dl_prediction']}")
            print(f"   Statut: {result.get('dl_status', 'unknown')}")
            print(f"   Confiance: {result['dl_confidence']:.2%}")
            print(f"   Classe (index): {result.get('dl_predicted_class', -1)}")
            
            # Afficher les 3 meilleures prédictions
            class_probs = result.get('dl_class_probabilities', {})
            if class_probs:
                sorted_classes = sorted(class_probs.items(), key=lambda x: x[1], reverse=True)
                print(f"\n   Top 3 prédictions:")
                for j, (class_name, prob) in enumerate(sorted_classes[:3], 1):
                    print(f"   {j}. {class_name:25s}: {prob:.4%}")
        else:
            print(f"❌ ERREUR: Impossible d'obtenir une prédiction pour {image_file.name}")
    
    # Résumé final
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ")
    print(f"{'='*60}")
    if results:
        unique_predictions = set(r['prediction'] for r in results)
        print(f"Nombre d'images testées: {len(results)}")
        print(f"Prédictions uniques: {len(unique_predictions)}")
        print(f"Classes prédites: {', '.join(sorted(unique_predictions))}")
        
        if len(unique_predictions) == 1:
            print(f"\n⚠️  ATTENTION: Toutes les images ont la même prédiction: {list(unique_predictions)[0]}")
            print(f"   Cela peut indiquer un problème avec le modèle ou les images.")
        else:
            print(f"\n✅ Les images produisent des prédictions différentes.")
    else:
        print("❌ Aucun résultat à afficher")


if __name__ == "__main__":
    # Images par défaut à tester
    default_images = [
        r"C:\Users\SAMSUNG\Desktop\M2 ADIA\IoT\nettoyant intelligentes pour panneau solaire\images\SC.jpg"
        r"C:\Users\SAMSUNG\Desktop\M2 ADIA\IoT\nettoyant intelligentes pour panneau solaire\images\PD.jpg"
        r"C:\Users\SAMSUNG\Desktop\M2 ADIA\IoT\nettoyant intelligentes pour panneau solaire\images\DS.jpg"
    ]
    
    if len(sys.argv) > 1:
        # Utiliser les images fournies en argument
        image_paths = sys.argv[1:]
    else:
        # Utiliser les images par défaut
        print("ℹ️  Aucune image spécifiée, utilisation de l'image par défaut")
        print("   Usage: python test_dl_model_multi.py image1.jpg image2.jpg ...")
        image_paths = default_images
    
    test_multiple_images(image_paths)

