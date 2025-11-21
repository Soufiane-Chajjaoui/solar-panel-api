# Frontend-Backend Integration Guide

## Overview
The Next.js frontend is now linked with the FastAPI backend using Firebase authentication and JWT tokens.

## Architecture

```
Frontend (Next.js)
    ↓
Firebase Auth (Client-side authentication)
    ↓
getBackendTokens() → /auth/sync-firebase → Backend
    ↓
Firebase ID Token → Verified → Create/Update User → JWT Tokens
    ↓
Store JWT tokens in localStorage
    ↓
Use JWT tokens for all API calls
```

## Setup

### 1. Backend Configuration

The backend now supports Firebase token verification. Ensure:
- `serviceAccountKey.json` is in the root directory
- Firebase credentials are properly configured
- The backend is running on `http://localhost:8000`

### 2. Frontend Configuration

Update `.env.local`:
```
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
```

## Usage in Components

### Sign In with Firebase

```javascript
import { signIn, getBackendTokens, storeBackendTokens } from '@/lib/auth'
import { syncFirebaseAndGetTokens } from '@/lib/backendAuth'

async function handleSignIn(email, password) {
  try {
    // 1. Sign in with Firebase
    const userCredential = await signIn(email, password)
    
    // 2. Sync with backend and get JWT tokens
    const tokens = await syncFirebaseAndGetTokens()
    
    // Tokens are automatically stored in localStorage
    console.log('Successfully signed in and synced with backend')
  } catch (error) {
    console.error('Sign in failed:', error)
  }
}
```

### Sign Up with Firebase

```javascript
import { signUp, getBackendTokens, storeBackendTokens } from '@/lib/auth'

async function handleSignUp(email, password, firstName, lastName) {
  try {
    // 1. Create account with Firebase
    const userCredential = await signUp(email, password)
    
    // 2. Sync with backend (creates user in Firestore)
    const tokens = await syncFirebaseAndGetTokens()
    
    console.log('Account created and synced with backend')
  } catch (error) {
    console.error('Sign up failed:', error)
  }
}
```

### Making API Calls

```javascript
import { callFastAPI } from '@/lib/fastapi'

async function fetchUserData() {
  try {
    // The JWT token is automatically added to the Authorization header
    const response = await callFastAPI('/auth/me', {}, 'GET')
    console.log('User data:', response)
  } catch (error) {
    console.error('Failed to fetch user data:', error)
  }
}
```

### Using Backend Auth Functions

```javascript
import { getCurrentUser, logoutBackendUser } from '@/lib/backendAuth'

async function getUserInfo() {
  try {
    const user = await getCurrentUser()
    console.log('Current user:', user)
  } catch (error) {
    console.error('Failed to get user info:', error)
  }
}

async function handleLogout() {
  try {
    await logoutBackendUser()
    console.log('Logged out successfully')
  } catch (error) {
    console.error('Logout failed:', error)
  }
}
```

## Available API Endpoints

### Authentication
- `POST /auth/register` - Register new user (email/password)
- `POST /auth/login` - Login user (email/password)
- `POST /auth/sync-firebase` - Sync Firebase token and get JWT tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout user

### Health Check
- `GET /` - API health check
- `GET /health` - Detailed health check
- `GET /test-firebase` - Test Firebase connection
- `GET /test-mqtt` - Test MQTT connection

## Authentication Flow

1. User signs in with Firebase (email/password)
2. Frontend retrieves Firebase ID token
3. Frontend sends Firebase ID token to `/auth/sync-firebase`
4. Backend verifies Firebase token:
   - If user doesn't exist: creates new user in Firestore
   - If user exists: updates last login timestamp
5. Backend returns JWT tokens (access + refresh)
6. Frontend stores tokens in localStorage
7. All subsequent API calls use JWT tokens in Authorization header

## Token Refresh

When access token expires, use the refresh token:

```javascript
import { refreshAccessToken, storeBackendTokens } from '@/lib/backendAuth'

async function refreshToken() {
  try {
    const tokens = getStoredBackendTokens()
    const newTokens = await refreshAccessToken(tokens.refresh_token)
    await storeBackendTokens(newTokens)
  } catch (error) {
    // Handle refresh failure - may need to redirect to login
    console.error('Token refresh failed:', error)
  }
}
```

## CORS Configuration

Backend CORS is configured to accept requests from:
- `http://localhost:3000` (Next.js dev server)
- `http://localhost:8000` (Backend itself)

Update `.env` on the backend if needed:
```
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

## Troubleshooting

### "Firebase token invalid" error
- Ensure user is authenticated with Firebase before calling backend
- Check Firebase configuration in `Frontend/lib/Firebase.js`
- Verify Firebase service account credentials on backend

### CORS errors
- Check that `NEXT_PUBLIC_FASTAPI_URL` is set correctly
- Verify backend CORS configuration includes frontend URL
- Check browser console for detailed CORS errors

### No Authorization header sent
- Verify tokens are stored in localStorage
- Check that `callFastAPI` is being used for requests
- Ensure token storage didn't fail during sync

### Backend returns 401 Unauthorized
- Check token expiration
- Try refreshing token with refresh token
- Re-authenticate if refresh fails

## File Structure

```
Frontend/
├── lib/
│   ├── auth.js              # Firebase auth + backend token management
│   ├── backendAuth.js       # Backend API auth functions
│   ├── fastapi.js           # Axios client with auto-auth
│   ├── Firebase.js          # Firebase config
│   └── ...
```

## Next Steps

1. Create protected pages using Next.js middleware
2. Add user context for app-wide authentication state
3. Implement token refresh interceptor for expired tokens
4. Add logout functionality on all pages
