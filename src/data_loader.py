# src/data_loader.py
import json
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

PRODUCTS_PATH = Path("data/products.json")
CHROMA_PATH = Path(".chromadb")

def get_collection():
    """Load or create the ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_or_create_collection(
        name="mumz_products",
        embedding_function=ef
    )

    # Only populate if empty
    if collection.count() == 0:
        print("Embedding products into ChromaDB...")
        products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

        documents = []
        metadatas = []
        ids = []

        for p in products:
            # Combine English + Arabic for richer embedding
            doc_text = (
                f"{p['name_en']} {p['description_en']} "
                f"Category: {p['category']}. "
                f"Age: {p['age_min_months']}-{p['age_max_months']} months. "
                f"Price: {p['price_aed']} AED. "
                f"Tags: {' '.join(p['tags'])}"
            )
            documents.append(doc_text)
            metadatas.append({
                "product_id": p["id"],
                "name_en": p["name_en"],
                "name_ar": p["name_ar"],
                "category": p["category"],
                "price_aed": float(p["price_aed"]),
                "age_min_months": int(p["age_min_months"]),
                "age_max_months": int(p["age_max_months"]),
            })
            ids.append(p["id"])

        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"Embedded {len(products)} products.")

    return collection

def retrieve_products(query: str, n: int = 10,
                      age_months: int = None,
                      budget_aed: float = None,
                      categories: list[str] = None) -> list[dict]:
    """Semantic search with optional metadata filtering."""
    collection = get_collection()

    conditions = []
    if budget_aed:
        conditions.append({"price_aed": {"$lte": budget_aed}})
    if categories:
        conditions.append({"category": {"$in": categories}})

    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}
    else:
        where = None

    results = collection.query(
        query_texts=[query],
        n_results=n,
        where=where if where else None,
        include=["documents", "metadatas", "distances"]
    )

    products = []
    if not results["metadatas"] or not results["metadatas"][0]:
        return products

    for i, meta in enumerate(results["metadatas"][0]):
        # Age filter (ChromaDB doesn't support range queries on two fields simultaneously)
        if age_months is not None:
            if not (meta["age_min_months"] <= age_months <= meta["age_max_months"]):
                continue
        products.append({
            **meta,
            "relevance_score": 1 - results["distances"][0][i]
        })

    return products[:5]  # Return top 5 after filtering
