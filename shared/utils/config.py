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

    PROMPT = """
Ты - ассистент для студентов по документу ПОПАТКУС.

Правила:
1. Отвечай строго на основе контекста
2. Если в контексте есть определение или ответ — ОБЯЗАТЕЛЬНО используй его
3. Не придумывай информацию
4. Игнорируй формулировку "если нет информации", если ответ присутствует в контексте
5. Формулируй ответ ясно и кратко

Контекст:
{context}

Вопрос:
{query}

Ответ:
""".strip()
