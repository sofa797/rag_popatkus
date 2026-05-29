import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.parser.popatkus_parser import PopatkusParser

def download_popatkus_pdf():
    page_url = "https://www.hse.ru/docs/1026832917.html"
    save_dir = "shared/data/pdf"
    save_path = os.path.join(save_dir, "popatkus.pdf")
    
    os.makedirs(save_dir, exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(page_url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    target_name = "Положение об организации промежуточной аттестации и текущего контроля успеваемости студентов Национального исследовательского университета «Высшая школа экономики»"
    
    pdf_link = None
    for link in soup.find_all('a', href=True):
        link_text = link.get_text().strip()
        href = link.get('href', '').lower()
        if target_name in link_text and href.endswith('.pdf'):
            pdf_link = link['href']
            break
    
    if not pdf_link:
        for link in soup.find_all('a', href=True):
            link_text = link.get_text().lower()
            href = link.get('href', '').lower()
            if 'положение об организации промежуточной аттестации' in link_text and href.endswith('.pdf'):
                pdf_link = link['href']
                break
    
    if not pdf_link:
        raise Exception("PDF document is not found")
    
    file_url = urljoin(page_url, pdf_link)
    file_response = requests.get(file_url, headers=headers)
    file_response.raise_for_status()
    
    with open(save_path, 'wb') as f:
        f.write(file_response.content)
    
    print(f"saved: {save_path}")
    return save_path

def parse_popatkus_pdf(pdf_path):
    parser = PopatkusParser(pdf_path)
    structures = parser.parse()
    
    output_dir = "shared/data/parsed"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "parsed_pdf.json")
    
    parser.save_to_json(output_path)
    
    print(f"parsed: {output_path}")
    stats = parser.get_statistics()
    print(f"statistics: {stats}")
    
    return structures

if __name__ == "__main__":
    pdf_file = download_popatkus_pdf()
    parse_popatkus_pdf(pdf_file)
