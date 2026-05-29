import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
shared_path = project_root / "shared"

if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from parser.popatkus_parser import PopatkusParser
from chunking.chunker import Chunker
from vectorstore.qdrant_store import QdrantStore
from utils.config import Config


def main():
    parser = PopatkusParser(Config.PDF_PATH)
    parsed = parser.parse()

    os.makedirs(os.path.dirname(Config.PARSED_PATH), exist_ok=True)
    with open(Config.PARSED_PATH, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    chunker = Chunker()
    chunks = chunker.chunk(parsed)
    vector_store = QdrantStore()
    vector_store.clear_collection()
    vector_store.add_documents(chunks)


if __name__ == "__main__":
    main()
