import logging
import re
import threading
import time
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

import jenkins_client
import settings
from auth import require_secret

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("webhook")

KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
app = FastAPI(title="Jira->Jenkins webhook", docs_url=None, redoc_url=None, openapi_url=None)

_recent: dict[str, float] = {}
_lock = threading.Lock()


class TriggerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # reject unknown parameters
    issue_key: str
    environment: Literal["QA"]
    tenant: Literal["DEMO"]
    retry: int = Field(default=1, ge=0, le=2)

    @field_validator("issue_key")
    @classmethod
    def known_key(cls, v: str) -> str:
        if not KEY_RE.match(v) or v not in settings.TAG_MAP:
            raise ValueError("unknown issue key")
        return v


def _claim(key: str) -> bool:
    """False if key was triggered within DEDUPE_SECONDS. ponytail: in-memory, lost on restart."""
    now = time.monotonic()
    with _lock:
        if now - _recent.get(key, -1e9) < settings.DEDUPE_SECONDS:
            return False
        _recent[key] = now
        return True


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/webhook/trigger", status_code=202, dependencies=[Depends(require_secret)])
def trigger(req: TriggerRequest):
    if not _claim(req.issue_key):
        raise HTTPException(status_code=409, detail="duplicate: build for this issue already triggered recently")
    try:
        queue = jenkins_client.trigger_build(
            {
                "TAGS": settings.TAG_MAP[req.issue_key],
                "ENV": req.environment,
                "TENANT": req.tenant,
                "RETRY": str(req.retry),
                "JIRA_KEY": req.issue_key,
            }
        )
    except jenkins_client.JenkinsError as e:
        with _lock:
            _recent.pop(req.issue_key, None)  # let the caller retry
        log.error("jenkins trigger failed issue=%s reason=%s", req.issue_key, e)
        raise HTTPException(status_code=502, detail="jenkins unavailable") from None
    log.info("triggered issue=%s tags=%s", req.issue_key, settings.TAG_MAP[req.issue_key])
    return {"status": "queued", "issue_key": req.issue_key, "queue_url": queue}
