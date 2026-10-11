import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from pydantic import BaseModel
from functools import lru_cache

# ──────────────────────────────────────────────
# 1. Config — loaded once from .env
# ──────────────────────────────────────────────
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
AUTH0_ALGORITHMS = [os.getenv("AUTH0_ALGORITHMS", "RS256")]
CLAIM_NAMESPACE = os.getenv("AUTH0_CLAIM_NAMESPACE", "https://knowledge-copilot.local/")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

# FastAPI security scheme — auto_error=False so we can handle missing tokens ourselves
security = HTTPBearer(auto_error=False)

LOCAL_JWT_SECRET = os.getenv("JWT_SECRET", "copilot-local-secret-key-2026")


def create_access_token(data: dict) -> str:
    """Creates a local JWT signed with HS256."""
    to_encode = data.copy()
    return jwt.encode(to_encode, LOCAL_JWT_SECRET, algorithm="HS256")



# ──────────────────────────────────────────────
# 2. Pydantic model for the authenticated user
# ──────────────────────────────────────────────
class CurrentUser(BaseModel):
    """Represents the authenticated user extracted from a validated JWT."""
    sub: str                    # Auth0 user ID (e.g., "auth0|abc123")
    email: Optional[str] = None
    role: str = "viewer"        # Default: most restrictive
    department: str = "general" # Default: general access


# ──────────────────────────────────────────────
# 3. JWKS fetching (cached) — Auth0's public keys
# ──────────────────────────────────────────────
@lru_cache()
def _get_jwks() -> dict:
    """
    Fetch Auth0's JSON Web Key Set (public keys used to verify JWT signatures).
    Cached because these keys rarely rotate.
    """
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = httpx.get(jwks_url)
    response.raise_for_status()
    return response.json()


def _get_signing_key(token: str) -> dict:
    """
    Match the 'kid' (Key ID) in the JWT header to the correct
    public key from Auth0's JWKS endpoint.
    """
    jwks = _get_jwks()
    unverified_header = jwt.get_unverified_header(token)

    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find appropriate signing key",
    )


# ──────────────────────────────────────────────
# 4. Core JWT validation + user extraction
# ──────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    FastAPI dependency that:
    1. Extracts the Bearer token
    2. Validates against Local JWT (HS256) or Auth0 (RS256)
    3. Returns CurrentUser with user ID (sub), role, and department
    """
    if credentials is not None:
        token = credentials.credentials

        # 1. Try Local JWT first (HS256)
        try:
            payload = jwt.decode(
                token,
                LOCAL_JWT_SECRET,
                algorithms=["HS256"],
            )
            return CurrentUser(
                sub=payload.get("sub", "anonymous"),
                email=payload.get("email"),
                role=payload.get("role", "viewer"),
                department=payload.get("department", "general"),
            )
        except JWTError:
            pass

        # 2. Try Auth0 RSA JWT
        if AUTH0_DOMAIN:
            try:
                signing_key = _get_signing_key(token)
                payload = jwt.decode(
                    token,
                    signing_key,
                    algorithms=AUTH0_ALGORITHMS,
                    audience=AUTH0_AUDIENCE,
                    issuer=f"https://{AUTH0_DOMAIN}/",
                )
                return CurrentUser(
                    sub=payload.get("sub", ""),
                    email=payload.get(f"{CLAIM_NAMESPACE}email", payload.get("email")),
                    role=payload.get(f"{CLAIM_NAMESPACE}role", "viewer"),
                    department=payload.get(f"{CLAIM_NAMESPACE}department", "general"),
                )
            except Exception:
                pass

    # DEV_MODE bypass ONLY if no token was passed
    if DEV_MODE and credentials is None:
        return CurrentUser(
            sub="dev-admin",
            email="dev@localhost",
            role="admin",
            department="general",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated or invalid token",
    )



# ──────────────────────────────────────────────
# 5. Role-based access control (RBAC) helpers
# ──────────────────────────────────────────────
ROLE_HIERARCHY = {"viewer": 0, "editor": 1, "admin": 2}


def require_role(minimum_role: str):
    """
    Returns a dependency that enforces a minimum role level.
    
    Usage:
        @router.post("/upload", dependencies=[Depends(require_role("editor"))])
    """
    async def _check(user: CurrentUser = Depends(get_current_user)):
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' lacks permission. Minimum required: '{minimum_role}'",
            )
        return user
    return _check
