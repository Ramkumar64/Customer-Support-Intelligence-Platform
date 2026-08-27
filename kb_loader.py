from pathlib import Path


KB_DIR = Path("knowledge-base")


def load_knowledge_base():
    documents = []

    for path in KB_DIR.rglob("*.md"):
        content = path.read_text(encoding="utf-8")

        documents.append({
            "path": str(path),
            "filename": path.name,
            "content": content
        })

    return documents


if __name__ == "__main__":
    docs = load_knowledge_base()

    print(f"Loaded {len(docs)} knowledge-base documents\n")

    for doc in docs:
        print("-" * 60)
        print(doc["path"])
        print(f"Characters: {len(doc['content'])}")