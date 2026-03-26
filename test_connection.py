import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Load the variables from your .env file
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

def test_supabase():
    try:
        # 2. Initialize the client
        supabase: Client = create_client(url, key)
        
        # 3. Try to fetch one row (even if the table is empty, this checks connection)
        response = supabase.table("regulations").select("*").limit(1).execute()
        
        print("✅ Success! Connected to Supabase.")
        print(f"Connection URL: {url}")
        
    except Exception as e:
        print("❌ Connection Failed.")
        print(f"Error: {e}")
        print("\nChecklist:")
        print("- Is your .env file named exactly '.env'?")
        print("- Are the URL and KEY copied correctly from Supabase Settings -> API?")
        print("- Did you run 'pip install supabase python-dotenv'?")

if __name__ == "__main__":
    test_supabase()