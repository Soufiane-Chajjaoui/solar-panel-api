"""
Script de test pour le modèle Deep Learning MobileNet.
Teste la prédiction d'images de panneaux solaires.
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from app.services.dl_service import predict_from_image, load_dl_model, is_dl_model_loaded

# Activer le logging pour debug (optionnel)
logging.basicConfig(
    level=logging.INFO,  # Changez en logging.DEBUG pour plus de détails
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_image_prediction(image_path: str):
    """
    Teste la prédiction sur une image.
    
    Args:
        image_path: Chemin vers l'image à tester
    """
    print(f"\n{'='*60}")
    print(f"🧪 TEST DU MODÈLE DEEP LEARNING")
    print(f"{'='*60}")
    print(f"Image: {image_path}")
    print(f"{'='*60}\n")
    
    # Vérifier que le fichier existe
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"❌ ERREUR: Fichier image introuvable: {image_path}")
        return
    
    # Charger le modèle
    print("📦 Chargement du modèle DL...")
    model = load_dl_model()
    
    if model is None:
        print("❌ ERREUR: Impossible de charger le modèle DL")
        return
    
    print("✅ Modèle DL chargé avec succès\n")
    
    # Faire la prédiction
    print("🤖 Prédiction en cours...")
    result = predict_from_image(image_path)
    
    if result:
        # Afficher le résultat JSON complet (optionnel, peut être commenté)
        # print(f"\n{'='*60}")
        # print("✅ RÉSULTAT JSON COMPLET")
        # print(f"{'='*60}")
        # print(json.dumps(result, indent=2))
        # print(f"{'='*60}\n")
        
        # Affichage lisible
        prediction = result['dl_prediction']
        status = result.get('dl_status', 'unknown')
        confidence = result['dl_confidence']
        prob_clean = result['dl_probability']['clean']
        prob_dirty = result['dl_probability']['dirty']
        class_probs = result.get('dl_class_probabilities', {})
        predicted_class_idx = result.get('dl_predicted_class', -1)
        
        print(f"\n{'='*60}")
        print(f"📊 RÉSUMÉ DE LA PRÉDICTION")
        print(f"{'='*60}")
        print(f"   Classe prédite    : {prediction}")
        print(f"   Statut            : {status.upper()}")
        print(f"   Confiance         : {confidence:.2%}")
        print(f"   Index de classe   : {predicted_class_idx}")
        print(f"\n   Probabilités agrégées:")
        print(f"   - Clean           : {prob_clean:.2%}")
        print(f"   - Dirty           : {prob_dirty:.2%}")
        print(f"\n{'='*60}")
        print(f"📋 PROBABILITÉS PAR CLASSE")
        print(f"{'='*60}")
        
        # Afficher les probabilités de chaque classe
        if class_probs:
            # Trier par probabilité décroissante
            sorted_classes = sorted(class_probs.items(), key=lambda x: x[1], reverse=True)
            for class_name, prob in sorted_classes:
                marker = " ⭐ PRÉDIT" if class_name == prediction else ""
                bar_length = int(prob * 50)  # Barre visuelle de 50 caractères max
                bar = "█" * bar_length
                print(f"   {class_name:20s}: {prob:7.4%} │{bar:<50s}│ {marker}")
        print(f"{'='*60}\n")
    else:
        print("❌ ERREUR: Impossible d'obtenir une prédiction")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Teste le modèle Deep Learning MobileNet avec une image"
    )
    parser.add_argument(
        "image_path",
        type=str,
        nargs='?',  # Make it optional
        default=r"C:\Users\SAMSUNG\Desktop\M2 ADIA\IoT\nettoyant intelligentes pour panneau solaire\images\SC.jpg",
        help="Chemin vers l'image à tester (optionnel, utilise une image par défaut si non spécifié)"
    )
    
    args = parser.parse_args()
    
    try:
        test_image_prediction(args.image_path)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

