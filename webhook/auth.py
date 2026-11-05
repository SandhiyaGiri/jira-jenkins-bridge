import hmac

from fastapi import Header, HTTPException

import settings


def require_secret(x_webhook_secret: str = Header(default="")) -> None:
    # Constant-time compare; empty configured secret fails closed.
    if not settings.WEBHOOK_SECRET or not hmac.compare_digest(
        x_webhook_secret.encode(), settings.WEBHOOK_SECRET.encode()
    ):
        raise HTTPException(status_code=401, detail="unauthorized")
