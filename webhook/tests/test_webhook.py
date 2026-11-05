import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["WEBHOOK_SECRET"] = "s3cret"

from fastapi.testclient import TestClient  # noqa: E402

import jenkins_client  # noqa: E402
import main  # noqa: E402

H = {"X-Webhook-Secret": "s3cret"}
OK = {"issue_key": "KAN-1", "environment": "QA", "tenant": "DEMO", "retry": 1}
calls = []


def fake(params):
    calls.append(params)
    return "http://jenkins/queue/item/1/"


def setup_function():
    main._recent.clear()
    calls.clear()
    jenkins_client.trigger_build = fake


c = TestClient(main.app)


def test_happy_path_derives_tag_server_side():
    r = c.post("/webhook/trigger", json=OK, headers=H)
    assert r.status_code == 202 and r.json()["queue_url"].endswith("/1/")
    assert calls[0] == {"TAGS": "@TODO-ADD", "ENV": "QA", "TENANT": "DEMO", "RETRY": "1", "JIRA_KEY": "KAN-1"}


def test_bad_or_missing_secret_rejected():
    assert c.post("/webhook/trigger", json=OK).status_code == 401
    assert c.post("/webhook/trigger", json=OK, headers={"X-Webhook-Secret": "nope"}).status_code == 401
    assert not calls


def test_invalid_input_rejected():
    for bad in (
        {**OK, "issue_key": "bad"},
        {**OK, "issue_key": "KAN-999"},
        {**OK, "issue_key": "KAN-1; rm"},
        {**OK, "environment": "PROD"},
        {**OK, "tenant": "ACME"},
        {**OK, "retry": 9},
        {**OK, "tags": "@Regression"},  # client-supplied tags forbidden
    ):
        assert c.post("/webhook/trigger", json=bad, headers=H).status_code == 422, bad
    assert not calls


def test_duplicate_is_409_and_other_key_ok():
    assert c.post("/webhook/trigger", json=OK, headers=H).status_code == 202
    assert c.post("/webhook/trigger", json=OK, headers=H).status_code == 409
    assert c.post("/webhook/trigger", json={**OK, "issue_key": "KAN-2"}, headers=H).status_code == 202
    assert len(calls) == 2


def test_jenkins_failure_is_502_and_retryable():
    def boom(_):
        raise jenkins_client.JenkinsError("ConnectError")

    jenkins_client.trigger_build = boom
    assert c.post("/webhook/trigger", json=OK, headers=H).status_code == 502
    jenkins_client.trigger_build = fake
    assert c.post("/webhook/trigger", json=OK, headers=H).status_code == 202
