from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from rank_bm25 import BM25Okapi
from langdetect import detect
from sentence_transformers import SentenceTransformer, util
from pymongo import MongoClient
import re
import json
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

# Download NLTK resources
nltk.download('stopwords')

app = Flask(__name__)
CORS(app)

# --- Configuration ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "multilingual_ir"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

collections = {
    "en": db["docs_en"],
    "es": db["docs_es"],
    "hi": db["docs_hi"]
}

# --- NLP Preprocessing Setup ---
stemmers = {
    "en": SnowballStemmer("english"),
    "es": SnowballStemmer("spanish"),
    "hi": None
}

stop_words = {
    "en": set(stopwords.words("english")),
    "es": set(stopwords.words("spanish")),
    "hi": set()
}

def preprocess_text(text, lang):
    text = re.sub(r'[^\w\s]', '', text.lower())
    tokens = text.split()
    if lang in stop_words:
        tokens = [t for t in tokens if t not in stop_words[lang]]
    if stemmers.get(lang):
        tokens = [stemmers[lang].stem(t) for t in tokens]
    return tokens

# --- Load Data & Build Indices ---
print("Loading documents from MongoDB...")
documents = {} 
flat_docs = {} 

for lang, col in collections.items():
    docs = list(col.find({}, {"text": 1, "title": 1, "url": 1}))
    documents[lang] = docs
    flat_docs[lang] = [d['text'] for d in docs]

print(f"Loading Semantic Model: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

print("Creating Embeddings...")
doc_embeddings = {
    lang: model.encode(docs, convert_to_tensor=True)
    for lang, docs in flat_docs.items()
}

print("Building Advanced BM25 Indices...")
bm25_indices = {}
for lang, texts in flat_docs.items():
    tokenized_corpus = [preprocess_text(doc, lang) for doc in texts]
    bm25_indices[lang] = BM25Okapi(tokenized_corpus)

# --- Helper Functions ---
def normalize_scores(scores):
    scores = np.array(scores)
    if len(scores) == 0:
        return scores
    min_val = np.min(scores)
    max_val = np.max(scores)
    if max_val - min_val == 0:
        return np.zeros(len(scores))
    return (scores - min_val) / (max_val - min_val)

def hybrid_search(query, lang, alpha=0.6):
    if not flat_docs[lang]:
        return []

    # 1. Semantic Search
    query_embedding = model.encode(query, convert_to_tensor=True)
    semantic_scores = util.cos_sim(query_embedding, doc_embeddings[lang])[0].cpu().numpy()
    
    # 2. BM25 Search
    tokenized_query = preprocess_text(query, lang)
    bm25_scores = bm25_indices[lang].get_scores(tokenized_query)
    
    # 3. Normalization
    norm_semantic = normalize_scores(semantic_scores)
    norm_bm25 = normalize_scores(bm25_scores)
    
    # 4. Weighted Fusion
    final_scores = (alpha * norm_semantic) + ((1 - alpha) * norm_bm25)
    
    # 5. Ranking
    results = []
    for idx, score in enumerate(final_scores):
        if score < 0.2: # Threshold
            continue

        doc_data = documents[lang][idx]
        
        # --- MODIFIED: Return Full Text instead of Summary ---
        full_text = doc_data.get('text', '')

        results.append({
            "lang": lang,
            "title": doc_data.get('title', 'No Title'),
            "summary": full_text, # Sending full text as requested
            "url": doc_data.get('url', '#'),
            "score": float(score),
            "semantic_score": float(norm_semantic[idx]),
            "bm25_score": float(norm_bm25[idx])
        })
        
    return results

# --- Routes ---
@app.route("/search")
def search():
    q = request.args.get("q", "")
    
    if not q:
        return jsonify({"error": "Empty query"}), 400

    try:
        detected_lang = detect(q)
        primary_lang = {"en": "en", "es": "es", "hi": "hi"}.get(detected_lang, "en")
    except:
        primary_lang = "en"

    target_langs = ["en", "es", "hi"]
    all_results = []

    for target in target_langs:
        current_alpha = 0.6 if target == primary_lang else 1.0   
        hits = hybrid_search(q, target, alpha=current_alpha)
        all_results.extend(hits)

    # Global Sort
    all_results.sort(key=lambda x: x['score'], reverse=True)

    # LIMIT TO 12 RESULTS
    limited_results = all_results[:12]

    response_data = {
        "query_detected_lang": primary_lang,
        "results": limited_results 
    }

    return Response(
        json.dumps(response_data, ensure_ascii=False),
        mimetype="application/json"
    )

if __name__ == "__main__":
    print("Server running (Full Text Mode)...")
    app.run(debug=True, port=5000)