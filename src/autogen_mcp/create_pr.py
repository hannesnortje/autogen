import argparse
import os
import uuid
import requests
from autogen_mcp.observability import get_logger


def create_github_pr(
    repo: str,
    branch: str,
    base: str,
    title: str,
    body: str,
    token: str,
    dry_run=False,
    logger=None,
    correlation_id=None,
):
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"title": title, "head": branch, "base": base, "body": body}
    if logger:
        logger.info(
            "Creating GitHub PR",
            extra={
                "extra": {
                    "repo": repo,
                    "branch": branch,
                    "base": base,
                    "title": title,
                    "dry_run": dry_run,
                }
            },
        )
    else:
        print(f"POST {url}\n{data}")
    if not dry_run:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code != 201:
            if logger:
                logger.error(
                    "Error creating PR",
                    extra={
                        "extra": {
                            "status_code": resp.status_code,
                            "response": resp.text,
                        }
                    },
                )
            else:
                print(f"Error creating PR: {resp.status_code} {resp.text}")
            return None
        pr_url = resp.json()["html_url"]
        if logger:
            logger.info(
                "PR created",
                extra={"extra": {"pr_url": pr_url}},
            )
        else:
            print(f"PR created: {pr_url}")
        return pr_url
    return None


def main():
    parser = argparse.ArgumentParser(description="Create a GitHub PR via API.")
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repo (owner/name)",
    )
    parser.add_argument("--branch", required=True, help="Branch to PR from")
    parser.add_argument("--base", default="main", help="Base branch (default: main)")
    parser.add_argument("--title", required=True, help="PR title")
    parser.add_argument("--body", default="", help="PR body")
    parser.add_argument(
        "--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument(
        "--correlation-id", default=None, help="Correlation ID for tracing/logging."
    )
    args = parser.parse_args()

    if not args.token:
        print("GitHub token required (set --token or GITHUB_TOKEN env var)")
        exit(1)
    correlation_id = args.correlation_id or str(uuid.uuid4())
    logger = get_logger("autogen.create_pr", correlation_id=correlation_id)
    create_github_pr(
        repo=args.repo,
        branch=args.branch,
        base=args.base,
        title=args.title,
        body=args.body,
        token=args.token,
        dry_run=args.dry_run,
        logger=logger,
        correlation_id=correlation_id,
    )


if __name__ == "__main__":
    main()
