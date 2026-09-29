import argparse
import os
import sys

import httpx


def check_deploy(args):
    api_url = args.api_url or os.getenv("FORESIGHT_API_URL", "http://localhost:8000")
    api_key = args.api_key or os.getenv("FORESIGHT_API_KEY", "foresight-secret-key-123")

    diff_content = ""
    if args.diff:
        if os.path.exists(args.diff):
            with open(args.diff, "r", encoding="utf-8") as f:
                diff_content = f.read()
        else:
            diff_content = args.diff

    config_changes = []
    if args.config_changes:
        config_changes = [c.strip() for c in args.config_changes.split(",") if c.strip()]

    payload = {
        "service": args.service,
        "title": args.title,
        "description": args.description or "",
        "diff": diff_content,
        "config_changes": config_changes,
        "environment": args.environment,
        "author": args.author,
        "memory_enabled": not args.no_memory,
    }

    endpoint = f"{api_url.rstrip('/')}/api/v1/deploys/check"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(endpoint, json=payload, headers=headers)
            if resp.status_code != 200:
                print(f"Error: API returned HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
                sys.exit(3)
            data = resp.json()
    except Exception as e:
        print(f"Error connecting to Foresight API at {endpoint}: {e}", file=sys.stderr)
        sys.exit(3)

    verdict = data.get("verdict", "HOLD")
    risk_score = data.get("risk_score", 100)
    summary = data.get("summary", "")
    reasons = data.get("reasons", [])
    similar_incidents = data.get("similar_incidents", [])
    memory_citations = data.get("memory_citations", [])

    print("\n" + "=" * 60)
    print(" FORESIGHT DEPLOY SAFETY CHECK")
    print("=" * 60)
    print(f" Service:      {args.service}")
    print(f" Change Title: {args.title}")
    print(f" Environment:  {args.environment}")
    print(f" Verdict:      [{verdict}] (Risk Score: {risk_score}/100)")
    print("-" * 60)
    print(f" Summary: {summary}\n")

    if reasons:
        print(" Reasons:")
        for r in reasons:
            print(f"  • {r}")
        print()

    if similar_incidents:
        print(" Similar Past Incidents Recalled:")
        for inc in similar_incidents:
            print(f"  • [{inc.get('id')}] {inc.get('title')} ({inc.get('date')})")
            print(f"    Similarity: {inc.get('similarity_reason')}")
            if inc.get("fix_that_worked"):
                print(f"    Fix That Worked: {inc.get('fix_that_worked')}")
            if inc.get("fix_that_failed"):
                print(f"    Fix That Failed: {inc.get('fix_that_failed')}")
        print()

    if memory_citations:
        print(f" Hindsight Memory Citations ({len(memory_citations)} items):")
        for cit in memory_citations[:3]:
            print(f"  • [{cit.get('id')}] {cit.get('text')[:120]}...")
        print()

    print("=" * 60 + "\n")

    if verdict == "SHIP":
        sys.exit(0)
    elif verdict == "CANARY":
        sys.exit(1)
    elif verdict == "HOLD":
        sys.exit(2)
    else:
        sys.exit(2)


def cli():
    parser = argparse.ArgumentParser(prog="foresight", description="Foresight Deploy-Safety CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Run a deploy safety check")
    check_parser.add_argument("--service", required=True, help="Target service name (e.g. payments-gateway)")
    check_parser.add_argument("--title", required=True, help="Pull request or change title")
    check_parser.add_argument("--description", default="", help="Detailed description of change")
    check_parser.add_argument("--diff", default="", help="Path to diff file or raw diff string")
    check_parser.add_argument("--config-changes", default="", help="Comma-separated list of config keys touched")
    check_parser.add_argument("--environment", default="production", help="Deployment environment")
    check_parser.add_argument("--author", default="Arjun", help="Author of the change")
    check_parser.add_argument("--api-url", default="", help="Foresight API base URL")
    check_parser.add_argument("--api-key", default="", help="Foresight API Key")
    check_parser.add_argument("--no-memory", action="store_true", help="Disable Hindsight memory recall")

    args = parser.parse_args()

    if args.command == "check":
        check_deploy(args)


if __name__ == "__main__":
    cli()
