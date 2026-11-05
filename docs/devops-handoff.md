# DevOps hand-off: from POC to enterprise

The POC proves the flow works. This list is what to change to run it at scale. Items are ordered by priority.

## 1. Trigger path (decide first)

| Option | Inbound access | Pros | Cons |
|---|---|---|---|
| **A. Polling** (built) | none | no exposure, simplest security review | up to N s latency, API calls per interval |
| B. Inbound webhook behind gateway/WAF | yes, from Atlassian egress IPs only | instant | needs public endpoint, IP allowlist, secret rotation, WAF |
| C. Queue in the middle (webhook -> SQS/PubSub -> Jenkins) | small public receiver | buffering, retries, audit | one more component |
| D. Marketplace app (Xray / Zephyr Scale / Jenkins-for-Jira) | vendor managed | supported UI, test management | licence cost, less control |
| E. Cloudflare/ngrok tunnel | yes | fine for a demo | not for production |

Recommendation: start with A (already works), move to B or C only if latency matters.

## 2. Jenkins

- Controller runs **no builds** (`numExecutors: 0`). Use ephemeral agents (Kubernetes pods or Docker agents) with an image that has Node 20 and Playwright browsers pre-installed.
- SSO (OIDC/SAML/LDAP) + role-based authorization instead of local users.
- Keep `jenkins/casc.yaml` and `plugins.txt` in Git, pin plugin versions, back up `JENKINS_HOME`.
- Secrets from a secret manager (Vault / cloud secret store / Jenkins credentials provider), not environment variables.
- Folders per team, build retention policies, artifact retention, disk quotas.
- Use Lockable Resources (or equivalent) so two runs cannot hit the same tenant/environment at once.
- Make the shared reporting logic a **Jenkins shared library** step instead of copying scripts per repo.

## 3. Jira

- Use a **dedicated service account**, not a person. Minimum project permissions: Browse, Edit issues (labels), Add attachments, Link issues. No admin.
- Prefer scoped / short-lived tokens and put rotation on a calendar.
- Check Jira Cloud API rate limits and Automation rule quotas for your plan before choosing polling interval or the Automation-webhook approach.
- Create the manual "Run automation" button as a project (or global) automation rule; document it as code (export the rule JSON).
- Labels used: `run-automation` (request), `automation-queued` (claimed), `automation-passed|failed|error` (result). Reserve them so nobody reuses them.
- Optional upgrade: replace labels with custom fields ("Automation status", "Last run") for a proper panel.

## 4. Mapping tickets to tests

POC uses `config/jira-tag-map.json`. Options at scale:

1. **Convention**: ticket `PM-1234` runs tag `@PM-1234` (the real framework already tags scenarios this way). Validate the tag exists with a `cucumber-js --dry-run` before running.
2. Central mapping (config repo / small service) when tags differ from keys.
3. A Jira custom field "Automation tag" owned by QA.

Keep **one source of truth**. The POC webhook currently holds a second copy.

## 5. Webhook service (only if route B/C)

- Deploy with 2+ replicas behind an ingress/WAF with Atlassian IP allowlist and rate limiting.
- Move duplicate protection from memory to Redis (or check the Jenkins queue / use idempotency keys).
- Secret from the secret manager; support rotation (accept old + new during a window). Jira Automation "Send web request" cannot sign payloads (HMAC), so keep the secret in a custom header and restrict by IP, or use a Forge/Connect app for signed (JWT) requests.
- Structured logs, metrics (accepted/rejected/duplicate), alerts on 401 spikes.
- Never log headers, tokens or full bodies.

## 6. Test execution

- Per-environment credentials via the existing Jenkins file/credential provider; never in the repo.
- Network paths from agents to QA environments (VPN, proxies, firewall rules).
- Parallelism / sharding by feature once the suite grows; keep `@flaky` retry policy explicit.
- Image pinning: Node, Playwright and base images by digest; scan images.
- Corporate TLS inspection: bake the corporate root CA into agent images (OS, Java, Node, Chromium NSS). Never disable certificate verification.
- Use the internal package registry/proxy for npm and pip; keep lockfiles free of private URLs when sharing outside the company.

## 7. Reporting

- Keep: PDF attachment, result label, build link. Comment is opt-in (`JIRA_COMMENT=true`).
- Add: publish Allure / Cucumber HTML on the Jenkins job, link it instead of attaching large files.
- Optional: push results to Xray/Zephyr if the organization uses a test-management tool.

## 8. Operations

- Alert when `jira-poller` fails repeatedly or when a claimed ticket has no matching build.
- Dashboards: runs per day, pass rate, queue time, run duration.
- Runbook for: expired Jira token, revoked GitHub token, Jenkins down, QA environment down.
- Disaster recovery: Jenkins config is code; only build history needs backup.

## 9. Security checklist

- [ ] Jenkins never directly internet-facing
- [ ] SSO + roles, no shared admin password
- [ ] Service accounts + least privilege (Jira, GitHub, Jenkins)
- [ ] Secrets in a manager, rotated, never in URLs, logs or repos
- [ ] Inbound endpoint (if any) behind WAF, IP allowlist, rate limits
- [ ] Pinned and scanned images, pinned plugins
- [ ] Audit logging enabled
- [ ] Wrong-ticket guard kept (tag that ran must match the ticket's mapped tag)

## 10. Suggested rollout

1. Pilot one project and one test suite with polling.
2. Move Jenkins config into the company platform repo; agents on Kubernetes.
3. Switch credentials to the secret manager and a Jira service account.
4. Add monitoring/alerts; document runbooks.
5. Roll out to more projects; decide on webhook/queue if latency matters.
