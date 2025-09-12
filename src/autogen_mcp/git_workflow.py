import argparse
import subprocess
import sys


def run(cmd, dry_run=False):
    print(f"$ {cmd}")
    if not dry_run:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr)
            sys.exit(result.returncode)
        return result.stdout.strip()
    return None


def create_branch(branch: str, dry_run=False):
    run(f"git checkout -b {branch}", dry_run)


def commit_all(message: str, dry_run=False):
    run("git add .", dry_run)
    run(f"git commit -m '{message}'", dry_run)


def push_branch(branch: str, dry_run=False):
    run(f"git push --set-upstream origin {branch}", dry_run)


def main():
    parser = argparse.ArgumentParser(description="Agent Git workflow automation.")
    parser.add_argument(
        "--branch", required=True, help="Branch name to create and push."
    )
    parser.add_argument("--message", required=True, help="Commit message.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no changes)."
    )
    args = parser.parse_args()

    create_branch(args.branch, args.dry_run)
    commit_all(args.message, args.dry_run)
    push_branch(args.branch, args.dry_run)
    print("Workflow complete.")


if __name__ == "__main__":
    main()
