import httpx

import settings


class JenkinsError(Exception):
    pass


def trigger_build(params: dict[str, str]) -> str:
    """Start the one allowed job; return queue URL. Basic auth + CSRF crumb (same session)."""
    base = settings.JENKINS_URL
    try:
        with httpx.Client(auth=(settings.JENKINS_USER, settings.JENKINS_PASSWORD), timeout=10) as c:
            crumb = c.get(f"{base}/crumbIssuer/api/json")
            crumb.raise_for_status()
            j = crumb.json()
            r = c.post(
                f"{base}/job/{settings.JOB_NAME}/buildWithParameters",
                params=params,
                headers={j["crumbRequestField"]: j["crumb"]},
            )
            r.raise_for_status()
            return r.headers.get("Location", "")
    except (httpx.HTTPError, KeyError) as e:
        # Never include request details (auth) in the error text.
        raise JenkinsError(type(e).__name__) from None
