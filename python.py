import pandas as pd

def clean_food_wastage_data():
    print("🚀 Initializing Step 1: Data Cleaning & Preprocessing for SQL Workbench Import...\n")
    
    # 1. Load Raw Datasets
    providers = pd.read_csv('providers_data.csv')
    receivers = pd.read_csv('receivers_data.csv')
    food_listings = pd.read_csv('food_listings_data.csv')
    claims = pd.read_csv('claims_data.csv')
    
    # 2. Schema Optimization & Datetime Handling
    # Converting date strings into standard ISO YYYY-MM-DD HH:MM:SS format for seamless SQL compilation
    print("📅 Formatting date strings to SQL-compliant datetime formats...")
    food_listings['Expiry_Date'] = pd.to_datetime(food_listings['Expiry_Date']).dt.strftime('%Y-%m-%d')
    claims['Timestamp'] = pd.to_datetime(claims['Timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    print("   ✅ 'Expiry_Date' and 'Timestamp' formatted successfully.\n")
    
    # 3. Text and Character Standardizations 
    # Address values often contain newlines which can break SQL file bulk loads. Let's fix that.
    print("🔤 Standardizing text fields (removing breaks)...")
    providers['Address'] = providers['Address'].str.replace(r'[\r\n]+', ' ', regex=True)
    print("   ✅ Street addresses standardized.\n")
    
    # 4. Integrity Check & Primary Key Constraints Validation
    print("🔍 Validating unique constraints on primary keys...")
    datasets_to_check = {
        "Providers": ('Provider_ID', providers),
        "Receivers": ('Receiver_ID', receivers),
        "Food Listings": ('Food_ID', food_listings),
        "Claims": ('Claim_ID', claims)
    }
    
    for name, (pk, df) in datasets_to_check.items():
        if df[pk].is_unique:
            print(f"   ✅ {name}: '{pk}' successfully validated as unique.")
        else:
            duplicate_count = df.duplicated(subset=[pk]).sum()
            print(f"   ⚠️ {name}: Found {duplicate_count} duplicated rows for '{pk}'. Dropping duplicates...")
            df.drop_duplicates(subset=[pk], keep='first', inplace=True)

    # 5. Exporting Clean Data for SQL Workbench
    print("\n💾 Saving clean datasets as ready-to-import CSVs...")
    providers.to_csv('providers_clean.csv', index=False)
    receivers.to_csv('receivers_clean.csv', index=False)
    food_listings.to_csv('food_listings_clean.csv', index=False)
    claims.to_csv('claims_clean.csv', index=False)
    
    print("\n🏁 Data cleaning step is complete! File outputs created:")
    print("   - providers_clean.csv\n   - receivers_clean.csv\n   - food_listings_clean.csv\n   - claims_clean.csv")

# Execute the script
clean_food_wastage_data()

# Load the cleaned datasets
providers = pd.read_csv('providers_clean.csv')
receivers = pd.read_csv('receivers_clean.csv')
food_listings = pd.read_csv('food_listings_clean.csv')
claims = pd.read_csv('claims_clean.csv')

# Re-export with strict utf-8 encoding
providers.to_csv('providers_clean.csv', index=False, encoding='utf-8')
receivers.to_csv('receivers_clean.csv', index=False, encoding='utf-8')
food_listings.to_csv('food_listings_clean.csv', index=False, encoding='utf-8')
claims.to_csv('claims_clean.csv', index=False, encoding='utf-8')

print("✅ Files converted to strict UTF-8! Try importing them into Workbench now.")