import os
import requests
from datetime import datetime, timedelta
from supabase import create_client, Client

# Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Agency IDs for SEC (466), OCC (80), CFPB (573), FDIC (164), Treasury (497), FRB (188)

AGENCY_IDS = [466, 80, 573, 164, 497, 188]
KEYWORDS = ["investment advisor", "fiduciary", "wealth management", "compliance", "AML"]

def fetch_daily_regulations():
    # Set date to yesterday to ensure full day availability
    target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    url = "https://www.federalregister.gov/api/v1/documents.json"
    params = [("conditions[publication_date][is]", target_date)]
    params += [(f"conditions[agency_ids][]", agency) for agency in AGENCY_IDS]
    params += [(f"fields[]", field) for field in ["document_number", "title", "publication_date", "agency_names", "abstract", "html_url"]]
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        # We return the formatted list ready for Supabase
        cleaned_docs = []
        for doc in results:
            # Grab the list of names directly from the API response.
            # It's already a list of strings like ["Securities and Exchange Commission"]
            agency_names = doc.get("agency_names")

            # Fallback if the list is empty or None
            if not agency_names:
                agency_names = ["Unknown Agency"]

            cleaned_docs.append({
                "document_number": doc.get("document_number"),
                "title": doc.get("title"),
                "publication_date": doc.get("publication_date"),
                "agency_names": agency_names,
                "summary": doc.get("abstract"),
                "html_url": doc.get("html_url"),
                "raw_json": doc
            })
        return cleaned_docs
        
    except Exception as e:
        print(f"❌ Error fetching daily regs: {e}")
        return []

def upsert_to_supabase(records):     
    # THE MOVER JUST MOVES DATA
    for doc in records:
        try:
            # Upsert logic to prevent duplicates
            supabase.table("regulations").upsert(doc).execute()
        except Exception as e:
            print(f"⚠️ Skipping doc {doc.get('document_number')} due to DB error: {e}")

if __name__ == "__main__":
    records = fetch_daily_regulations()
    if records:
        print(f"Found {len(records)} records. Ingesting...")
        upsert_to_supabase(records)
    else:
        print("No new records found for the target date.")