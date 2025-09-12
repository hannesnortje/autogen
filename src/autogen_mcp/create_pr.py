import argparse
import os
import requests


def create_github_pr(
    repo: str, branch: str, base: str, title: str, body: str, token: str, dry_run=False
):
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"title": title, "head": branch, "base": base, "body": body}
    print(f"POST {url}\n{data}")
    if not dry_run:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code != 201:
            print(f"Error creating PR: {resp.status_code} {resp.text}")
            return None
        pr_url = resp.json()["html_url"]
        print(f"PR created: {pr_url}")
        return pr_url
    return None


def main():
    parser = argparse.ArgumentParser(description="Create a GitHub PR via API.")
    parser.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    parser.add_argument("--branch", required=True, help="Branch to PR from")
    parser.add_argument("--base", default="main", help="Base branch (default: main)")
    parser.add_argument("--title", required=True, help="PR title")
    parser.add_argument("--body", default="", help="PR body")
    parser.add_argument(
        "--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    args = parser.parse_args()

    if not args.token:
        print("GitHub token required (set --token or GITHUB_TOKEN env var)")
        exit(1)
    create_github_pr(
        repo=args.repo,
        branch=args.branch,
        base=args.base,
        title=args.title,
        body=args.body,
        token=args.token,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
