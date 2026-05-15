import json
import time
import torch
import pandas as pd
import numpy as np
import os
import sys
from sentence_transformers import SentenceTransformer, util

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from chunking.chunker import Chunker
    print("module Chunker is imported")
except ImportError as e:
    print(f"import error: {e}")
    sys.exit(1)

def load_data(json_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, json_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"file is not found: {full_path}")
    with open(full_path, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    chunker_inst = Chunker()
    chunks = chunker_inst.chunk(parsed_data)
    return [c for c in chunks if str(c.get("text", "")).strip()]

test_dataset = [
    {"query": "Что такое элемент контроля?", "target": "Элемент контроля – элемент текущего контроля по Дисциплине, который оценивается по правилам, определенным в ПУД."},
    {"query": "В чем заключается принцип накопительной оценки?", "target": "7. Основополагающим принципом оценивания результатов обучения студентов является накопительный характер промежуточной аттестации: оценка по Дисциплине зависит от постоянных усилий студента, которые выявляются посредством каждого из Элементов контроля."},
    {"query": "Можно ли менять оценку после объявления?", "target": "8. Оценка за Элемент контроля, объявленная преподавателем студенту в установленном Положением порядке, не может быть изменена, кроме случаев, предусмотренных Положением."},
    {"query": "Можно ли исправить оценку 5 на более высокую?", "target": "157. Запрещается пересдача результатов промежуточной аттестации по Дисциплине с целью повышения удовлетворительной оценки (от 4 баллов по 10-балльной шкале), за исключением ситуаций, предусмотренных в пунктах 72, 102, 112 Положения."},
    {"query": "В какой срок нужно подать на апелляцию?", "target": "121. Заявление на апелляцию подается студентом на имя академического руководителя в течение 3 (трех) рабочих дней с момента объявления оценки за блокирующий Элемент контроля и (или) экзамен (включая пересдачи), на результаты которого подается апелляция."},
    {"query": "Суббота - учбеный день?", "target": "Учебные дни – для целей применения Положения срок, исчисляемый в учебных днях, определяется согласно графику учебного процесса. В сроки, исчисляемые учебными днями, включается суббота."},
    {"query": "Сколько задолженностей может иметь студент «отдельной категории» без фиксации недобросовестного освоения программы?", "target": "82. Если студент относится к отдельной категории, установленной Положением, то при первом получении академических задолженностей в количестве не более 5 (пяти), причины их набора студентом считаются уважительными, в связи с чем менеджер образовательной программы не фиксирует в порядке, предусмотренном Положением, недобросовестного освоения образовательной программы."},
    {"query": "Можно ли получить консультацию у преподавателя во время сессии?", "target": "66. Консультации преподавателей в период сессии не проводятся."},
    {"query": "За какой минимальный срок студенты должны узнать расписание сессии?", "target": "64. Расписание сессии не менее чем за неделю до ее начала доводится до сведения преподавателей и студентов менеджером образовательной программы через электронное расписание."},
]

MODELS = {
    "MiniLM-L12": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "MPNet-Base": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "E5-Large": "intfloat/multilingual-e5-large",
    "BGE-M3": "BAAI/bge-m3",
    "Distiluse": "sentence-transformers/distiluse-base-multilingual-cased-v2"
}

PREFIXES = {
    "E5-Large": {"query": "query: ", "doc": "passage: "},
    "GTE-Multi": {"query": "query: ", "doc": "passage: "}
}

def run_advanced_benchmark():
    all_chunks = load_data("data/parsed/parsed_pdf.json")
    corpus_texts = [c["text"] for c in all_chunks if "text" in c]
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"the number of downloaded chunks: {len(corpus_texts)} | device: {device.upper()}")
    results = []
    for name, path in MODELS.items():
        print(f"\ntesting model: {name}")
        try:
            model = SentenceTransformer(path, device=device, trust_remote_code=True)
            doc_prefix = PREFIXES.get(name, {}).get("doc", "")
            prepared_corpus = [doc_prefix + t for t in corpus_texts]
            
            t0 = time.time()
            corpus_embeddings = model.encode(prepared_corpus, convert_to_tensor=True, normalize_embeddings=True)
            idx_time = time.time() - t0

            hits_at_1 = 0
            hits_at_3 = 0
            mrr_sum = 0
            latencies = []
            
            for item in test_dataset:
                query_prefix = PREFIXES.get(name, {}).get("query", "")
                query = query_prefix + item["query"]
                
                t_start = time.time()
                query_emb = model.encode(query, convert_to_tensor=True, normalize_embeddings=True)
                cos_scores = util.cos_sim(query_emb, corpus_embeddings)[0]
                latencies.append(time.time() - t_start)
                
                top_k = torch.topk(cos_scores, k=min(3, len(corpus_texts)))
                top_indices = top_k.indices.tolist()
                found_texts = [corpus_texts[idx] for idx in top_indices]

                if found_texts[0] == item["target"]:
                    hits_at_1 += 1
                
                if item["target"] in found_texts:
                    hits_at_3 += 1
                    rank = found_texts.index(item["target"]) + 1
                    mrr_sum += 1.0 / rank

            results.append({
                "Model": name,
                "Acc@1 (%)": round((hits_at_1 / len(test_dataset)) * 100, 2),
                "Acc@3 (%)": round((hits_at_3 / len(test_dataset)) * 100, 2),
                "MRR": round(mrr_sum / len(test_dataset), 3),
                "Avg Lat (ms)": round(np.mean(latencies) * 1000, 2),
                "Idx Time (s)": round(idx_time, 3),
                "Dim": corpus_embeddings.shape[1]
            })
            del model
            if device == "cuda":
                torch.cuda.empty_cache()

        except Exception as e:
            print(f"the error of testing {name}: {e}")
            continue
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = run_advanced_benchmark()
    print("\nresults:")
    if not df.empty:
        print(df.to_string(index=False))
