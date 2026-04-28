# src/api.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.gift_finder import run_gift_finder
from src.moms_verdict import run_moms_verdict
from src.data_loader import get_collection
import json
from pathlib import Path

app = FastAPI(title="Mumz Gift Finder", description="AI gift finder + Moms Verdict for Mumzworld")

class GiftRequest(BaseModel):
    query: str

@app.get("/")
def root():
    return {"status": "ok", "features": ["gift-finder", "moms-verdict"]}

@app.post("/gift-finder")
def gift_finder(req: GiftRequest):
    """Find gift recommendations from natural language query."""
    if not req.query or len(req.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query too short")
    result = run_gift_finder(req.query)
    return result

@app.get("/moms-verdict/{product_id}")
def moms_verdict(product_id: str):
    """Get synthesized Moms Verdict for a product."""
    result = run_moms_verdict(product_id)
    if "error" in result and "not found" in result.get("error", ""):
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/products")
def list_products():
    """List all products (for demo/testing)."""
    products_path = Path("data/products.json")
    if not products_path.exists():
        return []
    products = json.loads(products_path.read_text(encoding="utf-8"))
    return [{"id": p["id"], "name_en": p["name_en"], "price_aed": p["price_aed"], "category": p["category"]} for p in products]
