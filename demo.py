import requests
import json
import sys

# Fix encoding issue on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def run_demo():
    print("="*50)
    print("MUMZ GIFT FINDER DEMO")
    print("="*50)
    
    # 1. Test Gift Finder
    query = "Looking for a gift for a newborn baby"
    print(f"\n[1] Testing Gift Finder")
    print(f"Query: '{query}'\n")
    
    response = requests.post(f"{BASE_URL}/gift-finder", json={"query": query})
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Intent Extracted & Products Retrieved!")
        print(f"Summary (EN): {data.get('search_summary_en')}")
        print(f"Summary (AR): {data.get('search_summary_ar')}\n")
        
        print("Recommended Products:")
        for i, item in enumerate(data.get("suggestions", []), 1):
            print(f"  {i}. {item['name_en']}")
            print(f"     Price: {item['price_aed']} AED")
            print(f"     Reason: {item['reason_en']}")
            print(f"     Score: {item['confidence_score']}\n")
            
            # Use the first product for the Moms Verdict test
            if i == 1:
                first_product_id = item['product_id']
                
        if not data.get("suggestions"):
            print("\n[!] No products returned (possibly due to API rate limits). Exiting demo.")
            return

    else:
        print(f"[ERROR]: {response.status_code} - {response.text}")
        return

    # 2. Test Moms Verdict
    print("="*50)
    print(f"\n[2] Testing Moms Verdict for Product ID: {first_product_id}")
    print("Analyzing 30 reviews...\n")
    
    response = requests.get(f"{BASE_URL}/moms-verdict/{first_product_id}")
    if response.status_code == 200:
        data = response.json()
        if "error" in data:
            print(f"[ERROR]: {data['error']}")
            if "raw_response" in data and data["raw_response"]:
                print(f"Raw: {data['raw_response']}")
            return

        verdict = data.get("verdict", {})
        print(f"[OK] Verdict Generated!")
        print(f"Score: {verdict.get('verdict_score')} / 5.0 (Based on {verdict.get('total_reviews_analyzed')} reviews)")
        print(f"Confidence: {verdict.get('confidence')}")
        
        print("\nPros:")
        for pro in verdict.get('pros_en', []):
            print(f"  + {pro}")
            
        print("\nCons:")
        for con in verdict.get('cons_en', []):
            print(f"  - {con}")
            
        print(f"\nAge Suitability: {verdict.get('age_suitability_note_en')}")
        if verdict.get('safety_notes_en'):
            print(f"Safety Notes: {verdict.get('safety_notes_en')}")
    else:
        print(f"[ERROR]: {response.status_code} - {response.text}")

if __name__ == "__main__":
    run_demo()
