import json
import os
from pathlib import Path

# Config comes from env only. Secrets are never logged or returned.
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
JENKINS_URL = os.environ.get("JENKINS_URL", "http://jenkins:8080").rstrip("/")
JENKINS_USER = os.environ.get("JENKINS_USER", "webhook")
JENKINS_PASSWORD = os.environ.get("JENKINS_PASSWORD", "")
JOB_NAME = "automation-run"  # hardcoded: this service can only ever start this job
DEDUPE_SECONDS = int(os.environ.get("DEDUPE_SECONDS", "60"))

# Jira key -> Cucumber tag. Client never supplies tags.
# ponytail: copy of automation-standard-poc/config/jira-tag-map.json; single source via fetch/CI sync in enterprise.
TAG_MAP: dict[str, str] = json.loads(
    Path(os.environ.get("TAG_MAP_FILE", Path(__file__).with_name("tag_map.json"))).read_text()
)
