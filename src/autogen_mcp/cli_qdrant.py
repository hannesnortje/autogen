import sys
from autogen_mcp.qdrant_client import QdrantWrapper


def main():
    q = QdrantWrapper()
    is_up = q.health()
    print(f"Qdrant health: {'OK' if is_up else 'DOWN'}")
    if is_up:
        try:
            cols = q.list_collections()
            print("Collections:", ", ".join(cols) if cols else "<none>")
        except Exception as e:
            print("Error listing collections:", e)
    return 0 if is_up else 1


if __name__ == "__main__":
    sys.exit(main())
