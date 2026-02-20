from popatkus_parser import PopatkusParser


if __name__ == "__main__":
    pdf_file = "../data/popatkus.pdf"
    parser = PopatkusParser(pdf_file)
    structures = parser.parse()

    print(len(structures))
    for k, v in parser.get_statistics().items():
        print(f"{k}: {v}")

    for i, item in enumerate(structures[:300], 1):
        print(f"{i}. [{item['type']}] (p.{item['page']}) {item['text'][:80]}")

    parser.save_to_json("../data/parsed_popatkus.json")