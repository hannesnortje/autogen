"""
Minimal CLI dashboard for AutoGen MCP
Lists objectives, todos, and recent artifacts from Qdrant memory.
"""

import argparse
from autogen_mcp.memory import MemoryService


def list_objectives(mem):
    print("Objectives:")
    points = mem.q.scroll(
        mem.collection,
        must=[{"key": "scope", "match": {"value": "objective"}}],
        limit=100,
        with_payload=True,
    )["result"]["points"]
    for p in points:
        obj = p["payload"].get("text")
        tid = p["payload"].get("thread_id")
        print(f"- [{tid}] {obj}")
    if not points:
        print("(none)")


def list_todos(mem):
    print("Todos:")
    points = mem.q.scroll(
        mem.collection,
        must=[{"key": "scope", "match": {"value": "todo"}}],
        limit=100,
        with_payload=True,
    )["result"]["points"]
    for p in points:
        todo = p["payload"].get("text")
        tid = p["payload"].get("thread_id")
        print(f"- [{tid}] {todo}")
    if not points:
        print("(none)")


def list_artifacts(mem):
    print("Artifacts:")
    points = mem.q.scroll(
        mem.collection,
        must=[{"key": "scope", "match": {"value": "artifact"}}],
        limit=100,
        with_payload=True,
    )["result"]["points"]
    for p in points:
        art = p["payload"].get("text")
        tid = p["payload"].get("thread_id")
        print(f"- [{tid}] {art}")
    if not points:
        print("(none)")


def main():
    parser = argparse.ArgumentParser(description="AutoGen MCP CLI Dashboard")
    parser.add_argument(
        "--collection", default="memory_default", help="Qdrant collection name"
    )
    parser.add_argument("--objectives", action="store_true", help="List objectives")
    parser.add_argument("--todos", action="store_true", help="List todos")
    parser.add_argument("--artifacts", action="store_true", help="List artifacts")
    args = parser.parse_args()

    mem = MemoryService(collection=args.collection)
    if args.objectives:
        list_objectives(mem)
    if args.todos:
        list_todos(mem)
    if args.artifacts:
        list_artifacts(mem)
    if not (args.objectives or args.todos or args.artifacts):
        list_objectives(mem)
        print()
        list_todos(mem)
        print()
        list_artifacts(mem)


if __name__ == "__main__":
    main()
