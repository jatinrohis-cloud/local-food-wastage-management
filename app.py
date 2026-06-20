import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# --- STEP 1: PAGE CONFIGURATION & THEME ---
st.set_page_config(
    page_title="Local Food Wastage Management System",
    page_icon="🍲",
    layout="wide"
)

st.title("🍲 Local Food Wastage Management System Dashboard")
st.markdown("### Production Analytical Workspace | Real-Time Supply & Demand Matrix Optimization")
st.write("---")

# --- STEP 2: IN-MEMORY DATABASE HANDSHAKE EMULATION ---
@st.cache_resource
def load_and_initialize_database():
    """Reads processed storage vectors and establishes an analytical runtime layer."""
    # Using local cleaned data streams
    providers_df = pd.read_csv("providers_clean.csv")
    receivers_df = pd.read_csv("receivers_clean.csv")
    listings_df = pd.read_csv("food_listings_clean.csv")
    claims_df = pd.read_csv("claims_clean.csv")
    
    # Establish local transactional environment
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    providers_df.to_sql("providers", conn, index=False, if_exists="replace")
    receivers_df.to_sql("receivers", conn, index=False, if_exists="replace")
    listings_df.to_sql("food_listings", conn, index=False, if_exists="replace")
    claims_df.to_sql("claims", conn, index=False, if_exists="replace")
    return conn

try:
    db_connection = load_and_initialize_database()
except Exception as e:
    st.error(f"⚠️ Infrastructure Initialization Aborted: {e}")
    st.info("Ensure providers_clean.csv, receivers_clean.csv, food_listings_clean.csv, and claims_clean.csv exist in your running path.")
    st.stop()

# --- STEP 3: SIDEBAR CONTROL ENGINE & SYSTEM FILTERS ---
st.sidebar.header("🛠️ Dashboard Control Panel")

# Pull filter criteria parameters directly from the DB schema
available_cities = pd.read_sql("SELECT DISTINCT Location FROM food_listings ORDER BY Location", db_connection)["Location"].tolist()
available_provider_types = pd.read_sql("SELECT DISTINCT Provider_Type FROM food_listings ORDER BY Provider_Type", db_connection)["Provider_Type"].tolist()
available_meal_types = pd.read_sql("SELECT DISTINCT Meal_Type FROM food_listings ORDER BY Meal_Type", db_connection)["Meal_Type"].tolist()
available_food_types = pd.read_sql("SELECT DISTINCT Food_Type FROM food_listings ORDER BY Food_Type", db_connection)["Food_Type"].tolist()

# Render Multi-Select Widgets with comprehensive default coverage
selected_cities = st.sidebar.multiselect("📍 Filter by City Location", available_cities, default=available_cities[:3])
selected_provider_types = st.sidebar.multiselect("🏢 Filter by Provider Type", available_provider_types, default=available_provider_types)
selected_meal_types = st.sidebar.multiselect("⏰ Filter by Meal Time Windows", available_meal_types, default=available_meal_types)
selected_food_types = st.sidebar.multiselect("🥦 Filter by Dietary Food Type", available_food_types, default=available_food_types)

# If an operator clears a field selection, default to full structural scope to prevent runtime crash
filter_cities = selected_cities if selected_cities else available_cities
filter_providers = selected_provider_types if selected_provider_types else available_provider_types
filter_meals = selected_meal_types if selected_meal_types else available_meal_types
filter_foods = selected_food_types if selected_food_types else available_food_types

# --- STEP 4: FILTERED DATAFRAME COMPILATION ---
base_query = """
    SELECT 
        f.Food_ID, f.Food_Name, f.Quantity, f.Expiry_Date, f.Location as City, 
        f.Food_Type, f.Meal_Type, f.Provider_Type, p.Name as Provider_Name, p.Contact as Provider_Contact,
        c.Claim_ID, c.Status as Claim_Status, c.Timestamp as Claim_Time, r.Name as Receiver_Name
    FROM food_listings f
    LEFT JOIN providers p ON f.Provider_ID = p.Provider_ID
    LEFT JOIN claims c ON f.Food_ID = c.Food_ID
    LEFT JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
    WHERE f.Location IN ({})
      AND f.Provider_Type IN ({})
      AND f.Meal_Type IN ({})
      AND f.Food_Type IN ({})
"""

# Dynamic parameter injection strings to protect runtime syntax compilation
city_placeholders = ",".join([f"'{c}'" for c in filter_cities])
provider_placeholders = ",".join([f"'{p}'" for p in filter_providers])
meal_placeholders = ",".join([f"'{m}'" for m in filter_meals])
food_placeholders = ",".join([f"'{f}'" for f in filter_foods])

formatted_query = base_query.format(city_placeholders, provider_placeholders, meal_placeholders, food_placeholders)
master_df = pd.read_sql(formatted_query, db_connection)

# --- STEP 5: SQL ANALYTICAL QUERIES DEFINITION ---
SQL_QUERIES = {
    "1. Total Providers by City": {
        "query": """SELECT City, COUNT(*) as Total_Providers 
FROM providers 
GROUP BY City 
ORDER BY Total_Providers DESC;""",
        "description": "Displays the geographical distribution of food providers, indicating which cities have the most active donation networks."
    },
    "2. Total Receivers by City": {
        "query": """SELECT City, COUNT(*) as Total_Receivers 
FROM receivers 
GROUP BY City 
ORDER BY Total_Receivers DESC;""",
        "description": "Displays the geographical distribution of organizations or receivers registered to rescue surplus food."
    },
    "3. Top 5 Providers by Donated Quantity": {
        "query": """SELECT p.Name, p.Type, SUM(f.Quantity) as Total_Quantity_Donated
FROM providers p
JOIN food_listings f ON p.Provider_ID = f.Provider_ID
GROUP BY p.Provider_ID, p.Name, p.Type
ORDER BY Total_Quantity_Donated DESC
LIMIT 5;""",
        "description": "Lists the top 5 most generous providers based on the total quantity of food items they have listed."
    },
    "4. Most Claimed Food Items": {
        "query": """SELECT f.Food_Name, COUNT(c.Claim_ID) as Total_Claims
FROM food_listings f
JOIN claims c ON f.Food_ID = c.Food_ID
WHERE c.Status = 'Completed'
GROUP BY f.Food_Name
ORDER BY Total_Claims DESC;""",
        "description": "Identifies the food items that are successfully claimed and rescued most frequently, showing high-demand categories."
    },
    "5. Cumulative Food Volume Units": {
        "query": """SELECT SUM(Quantity) as Cumulative_Food_Volume_Units 
FROM food_listings;""",
        "description": "Calculates the total aggregate volume of all food items listed in the system."
    },
    "6. Top 5 Cities by Listings Logged": {
        "query": """SELECT Location AS City, COUNT(*) as Total_Listings_Logged
FROM food_listings
GROUP BY Location
ORDER BY Total_Listings_Logged DESC
LIMIT 5;""",
        "description": "Lists the top 5 locations (cities) where the highest number of food listings have been published."
    },
    "7. Food Listings by Food Type": {
        "query": """SELECT Food_Type, COUNT(*) as Total_Listings, SUM(Quantity) as Total_Quantity
FROM food_listings
GROUP BY Food_Type
ORDER BY Total_Quantity DESC;""",
        "description": "Analyzes dietary food types (e.g., Veg, Non-Veg) by number of listings and cumulative quantities."
    },
    "8. Claim Attempts by Listing": {
        "query": """SELECT f.Food_ID, f.Food_Name, COUNT(c.Claim_ID) as Claim_Attempts
FROM food_listings f
LEFT JOIN claims c ON f.Food_ID = c.Food_ID
GROUP BY f.Food_ID, f.Food_Name
ORDER BY Claim_Attempts DESC;""",
        "description": "Examines the level of interest/claims generated per food listing, helping to track popularity or activity."
    },
    "9. Top 5 Providers by Successful Claims": {
        "query": """SELECT p.Name as Provider_Name, COUNT(c.Claim_ID) as Successful_Claims_Count
FROM providers p
JOIN food_listings f ON p.Provider_ID = f.Provider_ID
JOIN claims c ON f.Food_ID = c.Food_ID
WHERE c.Status = 'Completed'
GROUP BY p.Provider_ID, p.Name
ORDER BY Successful_Claims_Count DESC
LIMIT 5;""",
        "description": "Highlights the top 5 providers whose listings successfully resulted in completed claims."
    },
    "10. Claim Status Distribution": {
        "query": """SELECT Status, 
       COUNT(*) as Status_Count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims), 2) as Percentage_Share
FROM claims
GROUP BY Status;""",
        "description": "Breaks down all claims by status (e.g., Completed, Pending, Cancelled) and calculates their percentage share."
    },
    "11. Average Quantity per Completed Claim": {
        "query": """SELECT ROUND(AVG(f.Quantity), 2) as Average_Quantity_Per_Claim
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
WHERE c.Status = 'Completed';""",
        "description": "Calculates the average quantity of food items rescued in a single completed transaction."
    },
    "12. Claims Count by Meal Type": {
        "query": """SELECT f.Meal_Type, COUNT(c.Claim_ID) as Claims_Count
FROM food_listings f
JOIN claims c ON f.Food_ID = c.Food_ID
GROUP BY f.Meal_Type
ORDER BY Claims_Count DESC;""",
        "description": "Measures claims activity across different meal timing windows (e.g., Lunch, Dinner, Breakfast)."
    },
    "13. Total Units Provided by Provider Type": {
        "query": """SELECT Provider_Type, SUM(Quantity) as Total_Units_Provided
FROM food_listings
GROUP BY Provider_Type
ORDER BY Total_Units_Provided DESC;""",
        "description": "Compares food volume contribution based on the provider type (e.g., Restaurant, Hotel, NGO)."
    },
    "14. Top 5 Receivers by Quantity Rescued": {
        "query": """SELECT r.Name as Receiver_Name, r.Type as Receiver_Type, SUM(f.Quantity) as Total_Quantity_Rescued
FROM receivers r
JOIN claims c ON r.Receiver_ID = c.Receiver_ID
JOIN food_listings f ON c.Food_ID = f.Food_ID
WHERE c.Status = 'Completed'
GROUP BY r.Receiver_ID, r.Name, r.Type
ORDER BY Total_Quantity_Rescued DESC
LIMIT 5;""",
        "description": "Lists the top 5 receiving organizations that successfully rescued the largest volume of food."
    },
    "15. Top 10 Upcoming Expiry Date Food Items": {
        "query": """SELECT Food_Name, Quantity, Expiry_Date, Provider_Type, Location
FROM food_listings
WHERE Expiry_Date >= '2025-01-01'
ORDER BY Expiry_Date ASC
LIMIT 10;""",
        "description": "Displays the top 10 soonest-to-expire food items that are still available, prioritizing urgent rescue needs."
    }
}

# --- STEP 6: DEFINE TABS ---
tab1, tab2 = st.tabs(["📊 Executive Dashboard", "💻 SQL Query Terminal & Analytics"])

with tab1:
    # --- STEP 7: KEY PERFORMANCE INDICATOR (KPI) METRICS ---
    col1, col2, col3, col4 = st.columns(4)

    total_items = len(master_df["Food_ID"].unique())
    total_qty = int(master_df["Quantity"].sum()) if len(master_df) > 0 else 0
    completed_claims = len(master_df[master_df["Claim_Status"] == "Completed"])
    success_rate = round((completed_claims / len(master_df) * 100), 2) if len(master_df) > 0 else 0.0

    with col1:
        st.metric(label="📦 Total Unique Food Items Listed", value=f"{total_items:,}")
    with col2:
        st.metric(label="📊 Aggregate Food Volume (Units)", value=f"{total_qty:,}")
    with col3:
        st.metric(label="✅ Successfully Secured Claims", value=f"{completed_claims:,}")
    with col4:
        st.metric(label="📈 Operational Claim Success Rate", value=f"{success_rate}%")

    st.write("---")

    # --- STEP 8: EXPLORATORY DATA ANALYSIS (EDA) CHARTS VISUALIZATION ---
    st.subheader("📊 Visual Distribution Metrics & Performance Trends")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### Total Food Quantity Available by City Location")
        if len(master_df) > 0:
            city_volume = master_df.groupby("City")["Quantity"].sum().reset_index()
            fig_city = px.bar(city_volume, x="City", y="Quantity", color="City", text_auto=True,
                              labels={"Quantity": "Units Allocated"}, template="plotly_white")
            st.plotly_chart(fig_city, use_container_width=True)
        else:
            st.info("No records match configuration parameters.")

    with chart_col2:
        st.markdown("#### Demand Velocity Breakdown (Total Claims Generated by Meal Type)")
        if len(master_df) > 0:
            meal_distribution = master_df.groupby("Meal_Type")["Food_ID"].count().reset_index()
            meal_distribution.columns = ["Meal Type", "Transaction Claims Generated"]
            fig_meal = px.pie(meal_distribution, values="Transaction Claims Generated", names="Meal Type", 
                              hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_meal, use_container_width=True)
        else:
            st.info("No records match configuration parameters.")

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.markdown("#### Volume Stream Profile (Dietary Composition Matrix)")
        if len(master_df) > 0:
            diet_df = master_df.groupby(["Food_Type", "Provider_Type"])["Quantity"].sum().reset_index()
            fig_diet = px.bar(diet_df, x="Food_Type", y="Quantity", color="Provider_Type", barmode="group",
                               labels={"Quantity": "Volume Sum", "Food_Type": "Diet Category Pattern"}, template="plotly_white")
            st.plotly_chart(fig_diet, use_container_width=True)
        else:
            st.info("No records match configuration parameters.")

    with chart_col4:
        st.markdown("#### Active System Claims Operations Tracking Status")
        if len(master_df) > 0:
            status_df = master_df["Claim_Status"].fillna("Unclaimed").value_counts().reset_index()
            status_df.columns = ["Status", "Record Count"]
            fig_status = px.funnel(status_df, x="Record Count", y="Status", color="Status")
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("No records match configuration parameters.")

    st.write("---")

    # --- STEP 9: MASTER QUERY DATA SEARCH COMPONENT & CONTACT BOOK ---
    st.subheader("🔍 Master Operations Records Search & Logistics Engine")

    search_term = st.text_input("💡 Query Vector Search (Enter Food Item Name, Provider Name, or Status to filter)...")

    display_df = master_df[[
        "Food_ID", "Food_Name", "Quantity", "Expiry_Date", "City", 
        "Meal_Type", "Provider_Type", "Provider_Name", "Provider_Contact", "Claim_Status"
    ]].drop_duplicates()

    if search_term:
        query_mask = (
            display_df["Food_Name"].str.contains(search_term, case=False, na=False) |
            display_df["Provider_Name"].str.contains(search_term, case=False, na=False) |
            display_df["Claim_Status"].str.contains(search_term, case=False, na=False)
        )
        display_df = display_df[query_mask]

    st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("📂 Analytical SQL Queries Library")
    st.markdown("💡 *These analytical SQL queries are run directly against the relational database schema representing the complete historical dataset.*")

    selected_query_name = st.selectbox("Select a query to execute:", list(SQL_QUERIES.keys()))
    query_info = SQL_QUERIES[selected_query_name]
    
    st.markdown(f"**Query Objective:** {query_info['description']}")
    st.code(query_info['query'], language="sql")
    
    try:
        query_result = pd.read_sql(query_info['query'], db_connection)
        
        # Display numerical table
        st.markdown("##### Query Results Table:")
        st.dataframe(query_result, use_container_width=True, hide_index=True)
        
        # Download button for results
        csv_res = query_result.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Query Result to CSV",
            data=csv_res,
            file_name=f"{selected_query_name.lower().replace(' ', '_').replace('.', '')}_results.csv",
            mime="text/csv",
            key=f"dl_{selected_query_name.replace(' ', '').replace('.', '')}"
        )
        
        # Dynamic Visual Representation of the SQL Query Results
        if len(query_result) > 0:
            st.markdown("##### Visual Representation:")
            cols = list(query_result.columns)
            
            # 1. Total Providers by City
            if selected_query_name == "1. Total Providers by City":
                fig = px.bar(query_result, x="City", y="Total_Providers", color="City", text_auto=True, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            
            # 2. Total Receivers by City
            elif selected_query_name == "2. Total Receivers by City":
                fig = px.bar(query_result, x="City", y="Total_Receivers", color="City", text_auto=True, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                
            # 3. Top 5 Providers by Donated Quantity
            elif selected_query_name == "3. Top 5 Providers by Donated Quantity":
                fig = px.bar(query_result, x="Name", y="Total_Quantity_Donated", color="Name", text_auto=True, template="plotly_white",
                             labels={"Name": "Provider Name", "Total_Quantity_Donated": "Total Quantity"})
                st.plotly_chart(fig, use_container_width=True)
                
            # 4. Most Claimed Food Items
            elif selected_query_name == "4. Most Claimed Food Items":
                fig = px.bar(query_result, x="Food_Name", y="Total_Claims", color="Food_Name", text_auto=True, template="plotly_white",
                             labels={"Food_Name": "Food Item Name", "Total_Claims": "Claims Completed"})
                st.plotly_chart(fig, use_container_width=True)
                
            # 6. Top 5 Cities by Listings Logged
            elif selected_query_name == "6. Top 5 Cities by Listings Logged":
                fig = px.pie(query_result, values="Total_Listings_Logged", names="City", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.Agsunset)
                st.plotly_chart(fig, use_container_width=True)
                
            # 7. Food Listings by Food Type
            elif selected_query_name == "7. Food Listings by Food Type":
                fig = px.bar(query_result, x="Food_Type", y="Total_Quantity", color="Food_Type", text_auto=True, template="plotly_white",
                             labels={"Food_Type": "Dietary Category", "Total_Quantity": "Total Quantity Units"})
                st.plotly_chart(fig, use_container_width=True)
                
            # 8. Claim Attempts by Listing
            elif selected_query_name == "8. Claim Attempts by Listing":
                # Let's show top 10 of claim attempts
                top_attempts = query_result.head(10)
                fig = px.bar(top_attempts, x="Food_Name", y="Claim_Attempts", color="Food_Name", text_auto=True, template="plotly_white",
                             labels={"Food_Name": "Food Item", "Claim_Attempts": "Attempt Count"})
                st.plotly_chart(fig, use_container_width=True)
                
            # 9. Top 5 Providers by Successful Claims
            elif selected_query_name == "9. Top 5 Providers by Successful Claims":
                fig = px.bar(query_result, x="Provider_Name", y="Successful_Claims_Count", color="Provider_Name", text_auto=True, template="plotly_white",
                             labels={"Provider_Name": "Provider Name", "Successful_Claims_Count": "Completed Claims"})
                st.plotly_chart(fig, use_container_width=True)
                
            # 10. Claim Status Distribution
            elif selected_query_name == "10. Claim Status Distribution":
                fig = px.pie(query_result, values="Status_Count", names="Status", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig, use_container_width=True)
                
            # 12. Claims Count by Meal Type
            elif selected_query_name == "12. Claims Count by Meal Type":
                fig = px.pie(query_result, values="Claims_Count", names="Meal_Type", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.Tealrose)
                st.plotly_chart(fig, use_container_width=True)
                
            # 13. Total Units Provided by Provider Type
            elif selected_query_name == "13. Total Units Provided by Provider Type":
                fig = px.bar(query_result, x="Provider_Type", y="Total_Units_Provided", color="Provider_Type", text_auto=True, template="plotly_white",
                             labels={"Provider_Type": "Provider Type", "Total_Units_Provided": "Units Donated"})
                st.plotly_chart(fig, use_container_width=True)
                
            # 14. Top 5 Receivers by Quantity Rescued
            elif selected_query_name == "14. Top 5 Receivers by Quantity Rescued":
                fig = px.bar(query_result, x="Receiver_Name", y="Total_Quantity_Rescued", color="Receiver_Name", text_auto=True, template="plotly_white",
                             labels={"Receiver_Name": "Receiver Name", "Total_Quantity_Rescued": "Quantity Rescued"})
                st.plotly_chart(fig, use_container_width=True)
                
    except Exception as err:
        st.error(f"❌ Execution Failure: {err}")

    st.write("---")
    st.subheader("💻 Custom SQL Terminal Interface")
    st.markdown("✍️ *Write and execute arbitrary SQL queries against the local in-memory SQLite tables.*")
    
    with st.expander("📖 Show Schema & References"):
        st.markdown("""
        **Database Tables & Columns:**
        1. **`providers`**: `Provider_ID` (INT), `Name` (VARCHAR), `Type` (VARCHAR), `Address` (VARCHAR), `City` (VARCHAR), `Contact` (VARCHAR)
        2. **`receivers`**: `Receiver_ID` (INT), `Name` (VARCHAR), `Type` (VARCHAR), `City` (VARCHAR), `Contact` (VARCHAR)
        3. **`food_listings`**: `Food_ID` (INT), `Food_Name` (VARCHAR), `Quantity` (INT), `Expiry_Date` (DATE), `Provider_ID` (INT), `Provider_Type` (VARCHAR), `Location` (VARCHAR), `Food_Type` (VARCHAR), `Meal_Type` (VARCHAR)
        4. **`claims`**: `Claim_ID` (INT), `Food_ID` (INT), `Receiver_ID` (INT), `Status` (VARCHAR), `Timestamp` (DATETIME)
        """)
        
    custom_sql = st.text_area("SQL Statement Console:", value="SELECT * FROM food_listings LIMIT 5;", height=150)
    
    if st.button("🚀 Run Console Query", key="execute_console"):
        if custom_sql.strip():
            try:
                custom_df = pd.read_sql(custom_sql, db_connection)
                st.success(f"Execution complete. Found {len(custom_df)} rows.")
                st.dataframe(custom_df, use_container_width=True, hide_index=True)
                
                custom_csv_bytes = custom_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Query Result to CSV",
                    data=custom_csv_bytes,
                    file_name="custom_terminal_results.csv",
                    mime="text/csv",
                    key="dl_custom_console"
                )
            except Exception as custom_err:
                st.error(f"⚠️ SQL compilation or runtime execution error: {custom_err}")
        else:
            st.warning("Please input a valid SQL command.")

# --- STEP 10: PRODUCTION-GRADE CONTEXTUAL EXPORTS ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Operational Vector Extractors")
csv_data = display_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="📥 Export Current View Workspace to CSV",
    data=csv_data,
    file_name="filtered_food_logistics_manifest.csv",
    mime="text/csv"
)

st.sidebar.success("💡 Tip: Use filters to quickly generate clean data distributions for target cities or high-priority dietary profiles!")
