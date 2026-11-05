# Evidence of real runs

All runs were executed against a real Jenkins (Docker) and a real Jira Cloud Free site. Trimmed console output is in `docs/evidence/`.

| Build | Trigger | Ticket / tag | Result | Ticket afterwards |
|---|---|---|---|---|
| #5 | manual API trigger | KAN-1 `@TODO-ADD` | PASSED (1/1) | comment + PDF (earlier comment-based format) |
| #6 | manual, `FORCE_FAIL` | KAN-2 `@TODO-COMPLETE` | **FAILED** (0/1), build FAILURE | comment + PDF, Jira still updated |
| #7 | webhook service (`202`) | KAN-3 `@TODO-FILTER` | PASSED | comment + PDF, KAN-1/KAN-2 untouched |
| #8 | **poller** (label `run-automation` added) | KAN-2 `@TODO-COMPLETE` | PASSED | comment + PDF, label consumed |
| #9 | **poller** | KAN-3 `@TODO-FILTER` | PASSED | label `automation-passed`, link "#9 - PASSED (1/1 passed)", 2 attachments, comments unchanged |
| #10 | manual, `FORCE_FAIL` | KAN-3 `@TODO-FILTER` | **FAILED**, build FAILURE | label `automation-failed`, link "#10 - FAILED (0/1 passed)", 3 attachments, comments unchanged |

## Webhook negative tests (curl against the running service)

| Request | Expected | Got |
|---|---|---|
| no secret | 401 | 401 |
| wrong secret | 401 | 401 |
| malformed issue key | 422 | 422 |
| key not in tag map | 422 | 422 |
| environment `PROD` | 422 | 422 |
| extra field `tags` | 422 | 422 |
| valid request | 202 | 202 with queue URL |
| same request again | 409 | 409 |
| `/docs` | 404 | 404 |
| secret present in service logs | 0 | 0 |

## Other checks

- Only the tagged scenario ran (`1 scenario`) for every build.
- A failing test still produced a Jira update and kept the build FAILURE (reporting never overrides the test result).
- Other tickets were never modified by a run for a different ticket.
- Anonymous access to Jenkins returns 403; the `webhook` user can read the job but gets 403 on the admin page.
