from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "multilingual_ir"
COLLECTIONS = {
    'en': 'docs_en',
    'es': 'docs_es',
    'hi': 'docs_hi'
}

def main():
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    for lang, col_name in COLLECTIONS.items():
        col = db[col_name]
        docs = list(col.find())

        texts = [doc["text"] for doc in docs]
        embeddings = model.encode(texts)

        k = 3
        kmeans = KMeans(n_clusters=k, random_state=42)
        clusters = kmeans.fit_predict(embeddings)

        for doc, cluster_id in zip(docs, clusters):
            col.update_one({"_id": doc["_id"]},
                           {"$set": {"cluster": int(cluster_id)}})

        print(f"{lang}: clustering done ({k} clusters).")

if __name__ == "__main__":
    main()
