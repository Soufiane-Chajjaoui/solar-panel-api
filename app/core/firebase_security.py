import firebase_admin
from firebase_admin import auth as firebase_auth
from app.core.security import create_access_token, create_refresh_token
from app.core.firebase_client import db, firestore
import logging

logger = logging.getLogger(__name__)


def verify_firebase_token(id_token: str):
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except firebase_auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase ID token")
        return None
    except firebase_auth.ExpiredIdTokenError:
        logger.warning("Expired Firebase ID token")
        return None
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        return None


def sync_firebase_user(id_token: str):
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return None
    
    email = decoded_token.get('email')
    if not email:
        logger.warning("Firebase token missing email")
        return None
    
    try:
        doc = db.collection("users").document(email).get()
        
        if not doc.exists:
            db.collection("users").document(email).set({
                "email": email,
                "first_name": decoded_token.get('name', '').split()[0] if decoded_token.get('name') else '',
                "last_name": decoded_token.get('name', '').split()[1] if len(decoded_token.get('name', '').split()) > 1 else '',
                "firebase_uid": decoded_token.get('uid'),
                "refresh_tokens": [],
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Created new user from Firebase: {email}")
        else:
            db.collection("users").document(email).update({
                "updated_at": firestore.SERVER_TIMESTAMP,
                "firebase_uid": decoded_token.get('uid')
            })
            logger.info(f"Updated existing user from Firebase: {email}")
        
        access_token = create_access_token({"sub": email})
        refresh_token = create_refresh_token({"sub": email})
        
        db.collection("users").document(email).update({
            "refresh_tokens": firestore.ArrayUnion([refresh_token]),
            "last_login": firestore.SERVER_TIMESTAMP
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "email": email
        }
    
    except Exception as e:
        logger.error(f"Error syncing Firebase user: {e}")
        return None
