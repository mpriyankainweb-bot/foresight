import json
import os
import sys
import urllib.error
import urllib.request


def main():
    api_url = os.getenv("FORESIGHT_API_URL", "http://localhost:8000").rstrip("/")
    api_key = os.getenv("FORESIGHT_API_KEY", "foresight-secret-key-123")
    service = os.getenv("FORESIGHT_SERVICE", "payments-gateway")
    fail_on_hold = os.getenv("FORESIGHT_FAIL_ON_HOLD", "true").lower() == "true"

    pr_title = os.getenv("PR_TITLE") or "Deploy Safety Check PR"
    pr_body = os.getenv("PR_BODY") or ""
    pr_number = os.getenv("PR_NUMBER")
    github_repo = os.getenv("GITHUB_REPOSITORY")
    github_token = os.getenv("GITHUB_TOKEN")

    payload = {
        "service": service,
        "title": pr_title,
        "description": pr_body,
        "memory_enabled": True,
    }

    req_url = f"{api_url}/api/v1/deploys/check"
    req_headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }

    req = urllib.request.Request(
        req_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=req_headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"::error::Failed to connect to Foresight API at {req_url}: {e}", file=sys.stderr)
        sys.exit(1)

    verdict = data.get("verdict", "HOLD")
    risk_score = data.get("risk_score", 100)
    summary = data.get("summary", "")
    reasons = data.get("reasons", [])
    similar_incidents = data.get("similar_incidents", [])
    citations = data.get("memory_citations", [])

    # Badge formatting
    badge_color = "red" if verdict == "HOLD" else ("yellow" if verdict == "CANARY" else "green")
    verdict_emoji = "🚨" if verdict == "HOLD" else ("⚠️" if verdict == "CANARY" else "✅")

    reasons_md = "\n".join([f"- {r}" for r in reasons]) if reasons else "No specific risk factors flagged."

    similar_md = ""
    if similar_incidents:
        similar_md = "\n".join([
            f"- **[{inc.get('id')}] {inc.get('title')}**: {inc.get('similarity_reason')} *(Fix that worked: {inc.get('fix_that_worked', 'N/A')})*"
            for inc in similar_incidents
        ])

    citations_md = ""
    if citations:
        citations_md = "\n".join([
            f"- `{cit.get('id')}` (Relevance {(cit.get('score', 0.9) * 100):.0f}%): {cit.get('text')[:120]}..."
            for cit in citations[:3]
        ])

    comment_body = f"""## {verdict_emoji} Foresight Deploy Safety Check

| Field | Value |
| --- | --- |
| **Service** | `{service}` |
| **Verdict** | `[{verdict}]` |
| **Risk Score** | `{risk_score}/100` |

### 📝 Summary
{summary}

### ⚠️ Identified Risk Factors
{reasons_md}

{f"### 🔁 Similar Recalled Incidents\n{similar_md}\n" if similar_md else ""}
{f"### 🧠 Hindsight Memory Citations\n{citations_md}\n" if citations_md else ""}

---
*Hindsight remembers. Foresight prevents.*
"""

    print(comment_body)

    # Post PR comment if GitHub context is present
    if github_token and github_repo and pr_number:
        comment_url = f"https://api.github.com/repos/{github_repo}/issues/{pr_number}/comments"
        comment_req = urllib.request.Request(
            comment_url,
            data=json.dumps({"body": comment_body}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {github_token}",
                "Content-Type": "application/json",
                "User-Agent": "Foresight-GitHub-Action",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(comment_req) as c_resp:
                print(f"Posted PR comment successfully (HTTP {c_resp.status})")
        except Exception as ce:
            print(f"::warning::Failed to post PR comment: {ce}", file=sys.stderr)

    if verdict == "HOLD" and fail_on_hold:
        print("::error::Foresight check returned HOLD verdict. Blocking PR merge.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
