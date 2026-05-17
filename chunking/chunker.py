class Chunker:
    def chunk(self, parsed_data):
        chunks = []
        for item in parsed_data:
            if item["type"] not in [
                "paragraph",
                "subparagraph",
                "definition"
            ]:
                continue

            metadata = {
                "type": item.get("type"),
                "section": item.get("section"),
                "section_title": item.get("section_title"),
                "item": item.get("item"),
                "subitem": item.get("subitem"),
                "page": item.get("page")
            }

            if item["type"] == "definition":
                metadata["term"] = item.get("term")
            chunks.append({
                "text": item["text"],
                "metadata": metadata
            })
        return chunks
