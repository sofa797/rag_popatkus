import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

    PDF_PATH = os.path.join(
        BASE_DIR,
        "data",
        "pdf",
        "popatkus.pdf"
    )

    PARSED_PATH = os.path.join(
        BASE_DIR,
        "data",
        "parsed",
        "parsed_pdf.json"
    )

    QDRANT_PATH = os.path.join(
        BASE_DIR,
        "data",
        "qdrant"
    )
    
    COLLECTION_NAME = "popatkus_documents"

    EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
    EMBEDDING_DIM = 1024

    MISTRAL_MODEL = "mistral-small-latest"
    TEMPERATURE = 0.2
    MAX_TOKENS = 700

    FINAL_TOP_K = 5

    SERVER_NAME = "0.0.0.0"
    SERVER_PORT = 7860
    SHARE = False
