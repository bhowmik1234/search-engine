import pymongo
import wikipediaapi
import wikipedia
import sys



MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "multilingual_ir"
COLLECTIONS = {
    'en': 'docs_en',
    'es': 'docs_es',
    'hi': 'docs_hi'
}

TOPICS = {
    'en': [
        "India economy",
        "Spain festivals",
        "Machine learning",
        "Deep learning",
        "Renewable energy",
        "Stock market volatility",
        "Space exploration",
        "Artificial intelligence healthcare",
        "Quantum computing cryptography",
        "Global warming",
        "Economic reforms India",
        "Natural language processing",
        "Tourism in Spain",
        "Software development India",
        "Digital education",
        "Electric vehicles",
        "Cloud computing",
        "Agriculture India",
        "Sports analytics",
        "Blockchain technology"
    ],

    'es': [
        "Economía de España",
        "Cultura de España",
        "Aprendizaje automático",
        "Inteligencia artificial en salud",
        "Energía renovable",
        "Turismo en España",
        "Desarrollo de software India",
        "Cambio climático",
        "Vehículos eléctricos",
        "Computación cuántica",
        "Turismo España",
        "Agricultura",
        "Computación en la nube",
        "Análisis deportivo",
        "Economía digital",
        "Comercio global",
        "Blockchain",
        "Educación tecnológica",
        "Exploración espacial",
        "Inflación"
    ],

    'hi': [
        "भारत की अर्थव्यवस्था",
        "भारत में कृषि",
        "मशीन लर्निंग",
        "स्पेन की संस्कृति",
        "कृत्रिम बुद्धिमत्ता",
        "नवीकरणीय ऊर्जा",
        "जलवायु परिवर्तन",
        "भारत का पर्यटन",
        "डिजिटल शिक्षा",
        "भारत में सॉफ्टवेयर विकास",
        "ब्लॉकचेन",
        "भारत की जनसंख्या",
        "स्पेन पर्यटन",
        "क्वांटम कंप्यूटिंग",
        "विद्युत वाहन",
        "खेल विश्लेषण",
        "कृषि तकनीक",
        "भारत का विनिर्माण",
        "वैश्विक ऊष्मीकरण",
        "भारत की डिजिटल अर्थव्यवस्था"
    ]
}

wiki_handlers = {
    'en': wikipediaapi.Wikipedia("IRProjectBot/1.0", "en"),
    'es': wikipediaapi.Wikipedia("IRProjectBot/1.0", "es"),
    'hi': wikipediaapi.Wikipedia("IRProjectBot/1.0", "hi")
}


def fetch_docs(lang):
    wiki = wiki_handlers[lang]
    docs = []

    wikipedia.set_lang(lang)

    for i, query in enumerate(TOPICS[lang]):
        try:
            search_results = wikipedia.search(query)
        except Exception as e:
            print(f"[{lang}] Search failed for '{query}': {e}")
            continue

        if not search_results:
            print(f"[{lang}] No results for: {query}")
            continue

        page_title = search_results[0]
        page = wiki.page(page_title)

        if not page.exists():
            print(f"[{lang}] Page not found: {page_title}")
            continue

        summary = page.summary.strip()

        docs.append({
            "id": f"{lang}_{i+1}",
            "title": page.title,
            "text": summary,
            "url": page.fullurl
        })

    return docs


def main():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]

    for lang, col_name in COLLECTIONS.items():
        col = db[col_name]
        col.delete_many({})

        docs = fetch_docs(lang)

        if docs:
            col.insert_many(docs)
            print(f"{lang}: Inserted {len(docs)} documents")
        else:
            print(f"{lang}: No documents inserted (empty docs list)")


if __name__ == "__main__":
    main()
