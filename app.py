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

# --- STEP 5: KEY PERFORMANCE INDICATOR (KPI) METRICS ---
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

# --- STEP 6: EXPLORATORY DATA ANALYSIS (EDA) CHARTS VISUALIZATION ---
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

# --- STEP 7: MASTER QUERY DATA SEARCH COMPONENT & CONTACT BOOK ---
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

# --- STEP 8: PRODUCTION-GRADE CONTEXTUAL EXPORTS ---
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