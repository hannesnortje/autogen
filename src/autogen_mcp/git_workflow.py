import argparse
import subprocess
import sys
import uuid
from autogen_mcp.observability import get_logger


def run(cmd, dry_run=False, logger=None, correlation_id=None):
    if logger:
        logger.info(
            "Running shell command",
            extra={"extra": {"cmd": cmd, "dry_run": dry_run}},
        )
    else:
        print(f"$ {cmd}")
    if not dry_run:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            if logger:
                logger.error(
                    "Command failed",
                    extra={
                        "extra": {
                            "cmd": cmd,
                            "stderr": result.stderr,
                            "returncode": result.returncode,
                        }
                    },
                )
            else:
                print(result.stderr)
            sys.exit(result.returncode)
        return result.stdout.strip()
    return None


def create_branch(branch: str, dry_run=False, logger=None, correlation_id=None):
    if logger:
        logger.info(
            "Creating branch",
            extra={"extra": {"branch": branch, "dry_run": dry_run}},
        )
    run(f"git checkout -b {branch}", dry_run, logger, correlation_id)


def commit_all(message: str, dry_run=False, logger=None, correlation_id=None):
    if logger:
        logger.info(
            "Committing all changes",
            extra={"extra": {"message": message, "dry_run": dry_run}},
        )
    run("git add .", dry_run, logger, correlation_id)
    run(f"git commit -m '{message}'", dry_run, logger, correlation_id)


def push_branch(branch: str, dry_run=False, logger=None, correlation_id=None):
    if logger:
        logger.info(
            "Pushing branch",
            extra={"extra": {"branch": branch, "dry_run": dry_run}},
        )
    run(
        f"git push --set-upstream origin {branch}",
        dry_run,
        logger,
        correlation_id,
    )


def main():
    parser = argparse.ArgumentParser(description="Agent Git workflow automation.")
    parser.add_argument(
        "--branch", required=True, help="Branch name to create and push."
    )
    parser.add_argument("--message", required=True, help="Commit message.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no changes)."
    )
    parser.add_argument(
        "--correlation-id", default=None, help="Correlation ID for tracing/logging."
    )
    args = parser.parse_args()
    correlation_id = args.correlation_id or str(uuid.uuid4())
    logger = get_logger("autogen.git_workflow", correlation_id=correlation_id)
    logger.info(
        "Starting git workflow",
        extra={"extra": {"branch": args.branch, "dry_run": args.dry_run}},
    )
    create_branch(args.branch, args.dry_run, logger, correlation_id)
    commit_all(args.message, args.dry_run, logger, correlation_id)
    push_branch(args.branch, args.dry_run, logger, correlation_id)
    logger.info("Workflow complete.")


if __name__ == "__main__":
    main()
