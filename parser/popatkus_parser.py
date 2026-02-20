import pdfplumber
import re
import json


class PopatkusParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.structures = []

    def parse(self):
        self.structures = []
        current = {"section": None, "section_title": None, "item": None, "subitem": None}
        in_glossary = False
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                if page_num == 2:
                    continue
                text = page.extract_text()
                if not text:
                    continue
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                for line in lines:
                    if re.fullmatch(r"\d+", line):
                        continue
                    if len(line) < 4:
                        continue
                    if re.fullmatch(r"Используемые понятия и сокращения", line):
                        in_glossary = True
                        self.structures.append({"type": "glossary_title", "text": line, "page": page_num})
                        continue
                    sec_match = re.match(r"^([IVXLCDM]+)\.\s+(.*)", line)
                    if sec_match:
                        current["section"] = sec_match.group(1)
                        current["section_title"] = sec_match.group(2)
                        current["item"] = None
                        current["subitem"] = None
                        in_glossary = False
                        self.structures.append({"type": "section", "section": current["section"], "section_title": current["section_title"], "text": line, "page": page_num})
                        continue
                    sub_match = re.match(r"^(\d+\.\d+(?:\.\d+)*)\.\s+(.*)", line)
                    if sub_match:
                        current["subitem"] = sub_match.group(1)
                        self.structures.append({"type": "subparagraph", "section": current["section"], "section_title": current["section_title"], "item": current["item"], "subitem": current["subitem"], "text": line, "page": page_num})
                        continue
                    par_match = re.match(r"^(\d+)\.\s+(.*)", line)
                    if par_match:
                        current["item"] = par_match.group(1)
                        current["subitem"] = None
                        self.structures.append({"type": "paragraph", "section": current["section"], "section_title": current["section_title"], "item": current["item"], "subitem": None, "text": line, "page": page_num})
                        continue
                    if in_glossary:
                        if re.search(r"\s–\s", line):
                            term, definition = re.split(r"\s–\s", line, 1)
                            self.structures.append({
                                "type": "definition",
                                "term": term.strip(),
                                "text": line,
                                "page": page_num
                            })
                        else:
                            if self.structures and self.structures[-1]["type"] == "definition":
                                self.structures[-1]["text"] += " " + line
                        continue
                    if self.structures:
                        last = self.structures[-1]
                        if last["type"] in {"paragraph", "subparagraph"}:
                            last["text"] += " " + line
                            continue
                    self.structures.append({"type": "other", "section": current["section"], "section_title": current["section_title"], "text": line, "page": page_num})
        return self.structures

    def save_to_json(self, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.structures, f, ensure_ascii=False, indent=2)

    def get_statistics(self):
        from collections import Counter
        return dict(Counter(x["type"] for x in self.structures))