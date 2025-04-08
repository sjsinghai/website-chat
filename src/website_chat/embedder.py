import json
import os
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "Snowflake/snowflake-arctic-embed-s"


class Embedder:
    def __init__(self, doc_dir=str):
        self.store = {}  # id: embedding, metadata
        self.new_id = 0
        self.doc_dir = doc_dir
        self.init_embedding_model()
        self.document_stats = {}
        self.chunk_size = 200
        self.sim_threshold = 0.60  # coupled with embedding model

    def init_embedding_model(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    def add(self, ids: list, texts: list, metadatas: list[dict]):
        for ii in range(len(ids)):
            embedding = self.embedding_model.encode(texts[ii])

            metadatas[ii]["text"] = texts[ii]

            self.store[ids[ii]] = {
                "embedding": embedding.tolist(),
                "metadata": metadatas[ii],
            }

    def _compute_sim(self, query_vector, vector):
        return np.dot(query_vector, vector) / (
            np.linalg.norm(query_vector) * np.linalg.norm(vector)
        )

    def semantic_search(self, query: str, limit=2) -> tuple[list[dict], list[float]]:
        """returns the metadata of the most similar documents to a query and the corresponding max similarity score"""
        query_vector = self.embedding_model.encode(query, prompt_name="query")

        sim_list = []
        index_list = []
        for k, row in self.store.items():
            vector = row["embedding"]
            index_list.append(k)
            sim_list.append(self._compute_sim(query_vector, vector))

        sim_list = np.array(sim_list)
        indices = np.argsort(sim_list)[::-1]
        indices = indices[:limit]

        return [self.store[index_list[i]]["metadata"] for i in indices], [
            sim_list[i] for i in indices
        ]

    def export(self):
        if not self.doc_dir:
            return
        file_path = f"{self.doc_dir}/embeddings.json"
        with open(file_path, "w") as json_file:
            json.dump(self.store, json_file, indent=4)

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks"""
        sentences = text.replace("\n", " ").split(". ")
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if not sentence.endswith("."):
                sentence += "."

            sentence_size = len(sentence)

            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def read_document(self, file_path) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def process_document(self, file_path: str) -> tuple[list, list, list[dict]]:
        """Process a single document and prepare it for vector store"""
        try:
            # Read the document
            content = self.read_document(file_path)

            # Split into chunks
            chunks = self.split_text(content)

            # Prepare metadata
            file_name = os.path.basename(file_path)
            metadatas = [{"source": file_name, "chunk": i} for i in range(len(chunks))]
            ids = [f"{file_name}_chunk_{i}" for i in range(len(chunks))]
            return ids, chunks, metadatas
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return [], [], []

    def embed_documents(self):
        """Process and add documents to the collection"""
        directory = Path(self.doc_dir)
        file_paths = [file for file in directory.rglob("*") if file.is_file()]
        self.document_stats = {
            "num_files": 0,
            "num_chunks": 0,
            "num_words": 0,
            "num_words_per_file": [],
        }
        for file_path in file_paths:
            ids, texts, meta_datas = self.process_document(str(file_path))
            self.add(ids, texts, meta_datas)
            self.document_stats["num_files"] += 1
            self.document_stats["num_chunks"] += len(texts)

            num_words_per_file = 0
            for text in texts:
                num_words_per_file += len(text.split())
            self.document_stats["num_words"] += num_words_per_file
            self.document_stats["num_words_per_file"].append(num_words_per_file)

        self.export()

    def get_context_for_query(self, query: str) -> tuple[str, float]:
        results, scores = self.semantic_search(query)
        # if max(scores) < self.sim_threshold:
        #     return "", max(scores)
        filtered_results = [
            r for r, s in zip(results, scores) if s > self.sim_threshold
        ]
        context, _ = self.get_context_with_sources(filtered_results)
        return context, max(scores)

    def get_doc_content(self, file_name: str, doc_dir: str) -> str:
        full_path = doc_dir + "/" + file_name
        return self.read_document(full_path)

    def landing_page_sources(self, doc_dir: str) -> list[str]:
        doc_dir = doc_dir + "/landing"
        file_paths = [file for file in Path(doc_dir).rglob("*") if file.is_file()]
        sources = []
        for file_path in file_paths:
            sources.append(os.path.basename(file_path))
        return sources

    def get_context_with_sources(self, results: list[dict]) -> tuple[str, list[str]]:
        """Get a combined context and formatted sources from search results."""
        # Combine the document chunks into a single context
        sources_from_search = list(set([r["source"] for r in results]))
        sources_from_landing = self.landing_page_sources(self.doc_dir)
        sources = list(set(sources_from_search + sources_from_landing))
        doc_content = []
        file_name_set = []
        for file_name in sources:
            if file_name not in file_name_set:
                file_name_set.append(file_name)
                doc_content.append(self.get_doc_content(file_name, self.doc_dir))
        context = "\n\n".join(doc_content)

        return context, sources
