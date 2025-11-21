# 🌞 Smart Solar Panel Cleaner API

API FastAPI pour la gestion intelligente du nettoyage de panneaux solaires avec authentification sécurisée.

## ✨ Fonctionnalités

- 🔐 **Authentification JWT** - Tokens d'accès et de rafraîchissement
- 🔒 **Sécurité** - Hachage bcrypt, validation des données, gestion des erreurs
- 📊 **Configuration Centralisée** - Gestion sécurisée des variables d'environnement
- 🚀 **FastAPI** - Framework moderne et performant
- 📚 **Documentation** - Swagger UI et ReDoc intégrés
- 🔥 **Firebase** - Intégration Firestore pour la base de données

## 🚀 Démarrage Rapide

### Installation
```bash
# Cloner le projet
cd /media/soufian-ch/P1/projects/iot-project/solar-panel-api

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Mettre la clé générée dans .env
```

### Démarrage
```bash
./run.sh
```

L'API sera disponible à: **http://localhost:8000**

## 📚 Documentation

- 📚 **Documentation** - Disponible à: **http://localhost:8000/docs**
- 📚 **ReDoc** - Disponible à: **http://localhost:8000/redoc**

### Guides Détaillés
- 🔐 [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md) - Détails des améliorations de sécurité

## 🔐 Authentification

### Endpoints
```
POST   /auth/register    Enregistrement d'un nouvel utilisateur
POST   /auth/login       Connexion et obtention des tokens
POST   /auth/refresh     Rafraîchissement des tokens
POST   /auth/logout      Déconnexion
```

### Exemple d'Utilisation
```bash
# Enregistrement
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Soufiane",
    "last_name": "Chajjaoui",
    "email": "soufiane@example.com",
    "password": "StrongPassword123!"
  }'

# Connexion
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "soufiane@example.com",
    "password": "StrongPassword123!"
  }'

# Utiliser le token
curl -X GET "http://localhost:8000/health" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🛡️ Sécurité

### Implémentée
- ✅ Hachage bcrypt avec 12 rounds
- ✅ JWT avec expiration courte (15 min)
- ✅ Refresh tokens révocables (7 jours)
- ✅ Validation stricte des données
- ✅ Messages d'erreur génériques
- ✅ Logging détaillé
- ✅ Configuration sécurisée
- ✅ CORS configurable

### À Implémenter
- ⏳ Rate limiting
- ⏳ Authentification à deux facteurs (2FA)
- ⏳ Audit logging
- ⏳ Permissions et rôles
- ⏳ OAuth2/OpenID Connect

## 📦 Dépendances

```
fastapi>=0.100.0                    Framework web
uvicorn[standard]>=0.23.0           Serveur ASGI
python-jose[cryptography]>=3.3.0    Gestion JWT
passlib[bcrypt]>=1.7.4              Hachage de mots de passe
bcrypt>=4.0.0                       Algorithme bcrypt
pydantic-settings>=2.0.0            Configuration
email-validator>=2.0.0              Validation d'email
firebase-admin>=6.0.0               Client Firebase
slowapi>=0.1.8                      Rate limiting
python-json-logger>=2.0.0           Logging JSON
```

## 🗂️ Structure du Projet

```
app/
├── core/
│   ├── config.py              Configuration centralisée
│   ├── security.py            Fonctions de sécurité
│   ├── dependencies.py        Dépendances FastAPI
│   └── firebase_client.py     Client Firebase
├── routes/
│   ├── auth_routes.py         Routes d'authentification
│   ├── panel_routes.py        Routes des panneaux
│   ├── cleaning_routes.py     Routes de nettoyage
│   └── user_routes.py         Routes utilisateur
├── schemas/
│   ├── user_schema.py         Schémas utilisateur
│   └── token_schema.py        Schémas tokens
└── main.py                    Application principale

.env.example                   Exemple de configuration
requirements.txt               Dépendances Python
```

## 🧪 Tests

### Avec Swagger UI
```
http://localhost:8000/docs
```

### Avec cURL
Voir [TESTING_GUIDE.md](TESTING_GUIDE.md)

### Avec Python
```python
import requests

response = requests.post(
    "http://localhost:8000/auth/login",
    json={"email": "test@example.com", "password": "password"}
)
tokens = response.json()
```

## 🔧 Configuration

### Variables d'Environnement
```env
# Authentification JWT
JWT_SECRET_KEY=votre-clé-secrète-forte
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Firebase
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

Voir `.env.example` pour la configuration complète.

## 📖 Protéger une Route

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user_email

router = APIRouter()

@router.get("/my-profile")
def get_profile(email: str = Depends(get_current_user_email)):
    """Route protégée - nécessite un token valide."""
    return {"email": email, "message": "Votre profil"}
```

## 🚀 Production

### Checklist
- [ ] Générer une clé JWT forte
- [ ] Configurer DEBUG=False
- [ ] Configurer CORS correctement
- [ ] Utiliser HTTPS
- [ ] Configurer les variables d'environnement
- [ ] Mettre en place le rate limiting
- [ ] Configurer le logging
- [ ] Tester tous les endpoints
- [ ] Mettre en place le monitoring

Voir [BEST_PRACTICES.md](BEST_PRACTICES.md) pour plus de détails.

## 📞 Support

- 📚 **Documentation**: `/docs` (Swagger UI)
- 📖 **Guides**: Voir les fichiers `.md` du projet
- 🐛 **Problèmes**: Voir [QUICK_START.md](QUICK_START.md#9️⃣-dépannage)

## 📝 Licence

Ce projet est sous licence MIT.

## 👨‍💻 Auteur

Améliorations d'authentification par **Augment Agent** - 2024-10-22

---

**Version**: 1.0.0
**Status**: ✅ Production Ready

