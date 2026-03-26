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
    # params = {
    #     "conditions[publication_date][is]": target_date,
    #     "conditions[agency_ids][]": AGENCY_IDS,
    #     "fields[]": ["document_number", "title", "publication_date", "agencies", "abstract", "html_url"]
    # }
    params = [("conditions[publication_date][is]", target_date)]
    params += [(f"conditions[agency_ids][]", agency) for agency in AGENCY_IDS]
    params += [(f"fields[]", field) for field in ["document_number", "title", "publication_date", "agencies", "abstract", "html_url"]]
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def upsert_to_supabase(docs):
    for doc in docs:
        data = {
            "document_number": doc["document_number"],
            "title": doc["title"],
            "publication_date": doc["publication_date"],
            "agency_names": [a["name"] for a in doc["agencies"]],
            "summary": doc.get("abstract"),
            "html_url": doc["html_url"],
            "raw_json": doc
        }
        
        # Upsert logic to prevent duplicates
        supabase.table("regulations").upsert(data, on_conflict="document_number").execute()

if __name__ == "__main__":
    records = fetch_daily_regulations()
    if records:
        print(f"Found {len(records)} records. Ingesting...")
        upsert_to_supabase(records)
    else:
        print("No new records found for the target date.")