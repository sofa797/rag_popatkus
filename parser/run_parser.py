import os
import sys
from popatkus_parser import PopatkusParser

def main():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    pdf_path = os.path.join(BASE_DIR, "data/pdf/popatkus.pdf") 
    output_dir = os.path.join(BASE_DIR, "data", "parsed")
    output_file = os.path.join(output_dir, "parsed_pdf1.json")

    if not os.path.exists(pdf_path):
        print(f"error: initial file {pdf_path} is not found")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        parser = PopatkusParser(pdf_path)
        parser.parse()
        parser.save_to_json(output_file)
        
        stats = parser.get_statistics()
        print("parsing statistics:")
        for block_type, count in stats.items():
            print(f"  - {block_type}: {count}")
            
    except Exception as e:
        print(f"error: {e}")

if __name__ == "__main__":
    main()
