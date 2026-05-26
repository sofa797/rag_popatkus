import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from utils.config import Config

class Embedder:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(Config.EMBEDDING_MODEL, local_files_only=True)
            self.model = AutoModel.from_pretrained(Config.EMBEDDING_MODEL, local_files_only=True).to(self.device)
        except Exception:
            self.tokenizer = AutoTokenizer.from_pretrained(Config.EMBEDDING_MODEL)
            self.model = AutoModel.from_pretrained(Config.EMBEDDING_MODEL).to(self.device)
        self.model.eval()

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def encode(self, texts, is_query=False, batch_size=4, max_length=512):
        prefix = "query: " if is_query else "passage: "
        prefixed_texts = [prefix + text for text in texts]
        all_embeddings = []
        for i in range(0, len(prefixed_texts), batch_size):
            batch_texts = prefixed_texts[i : i + batch_size]
            
            inputs = self.tokenizer(
                batch_texts, 
                padding=True, 
                truncation=True, 
                max_length=max_length, 
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = self._mean_pooling(outputs, inputs['attention_mask'])
                embeddings = F.normalize(embeddings, p=2, dim=-1)
                all_embeddings.append(embeddings.cpu())
        return torch.cat(all_embeddings, dim=0).numpy().tolist()
