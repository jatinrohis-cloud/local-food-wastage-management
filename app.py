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

# --- STEP 2: RAW DATASET LOADING ENGINE ---
@st.cache_data
def load_raw_data_sources():
    """Reads processing source storage files directly from the repository root."""
    try:
        providers_df = pd.read_csv("providers_data.csv")
        receivers_df = pd.read_csv("receivers_data.csv")
        listings_df = pd.read_csv("food_listings_data.csv")
        claims_df = pd.read_csv("claims_data.csv")
        return providers_df, receivers_df, listings_df, claims_df
    except Exception as e:
        st.error(f"⚠️ Data Sourcing Error: {e}")
        st.info("Ensure providers_data.csv, receivers_data.csv, food_listings_data.csv, and claims_data.csv exist in your root directory.")
        st.stop()

providers_raw, receivers_raw, listings_raw, claims_raw = load_raw_data_sources()

# --- STEP 3: SIDEBAR CONTROL PANEL & FILTERS ---
st.sidebar.header("🛠️ Dashboard Control Panel")

# Pull filter criteria parameters directly from the raw frames safely
available_cities = sorted(listings_raw["Location"].dropna().unique().tolist())
available_provider_types = sorted(listings_raw["Provider_Type"].dropna().unique().tolist())
available_meal_types = sorted(listings_raw["Meal_Type"].dropna().unique().tolist())
available_food_types = sorted(listings_raw["Food_Type"].dropna().unique().tolist())

# FIX: Set the default to show ALL cities, types, and meals on boot so charts load data instantly!
selected_cities = st.sidebar.multiselect("📍 Filter by City Location", available_cities, default=available_cities)
selected_provider_types = st.sidebar.multiselect("🏢 Filter by Provider Type", available_provider_types, default=available_provider_types)
selected_meal_types = st.sidebar.multiselect("⏰ Filter by Meal Time Windows", available_meal_types, default=available_meal_types)
selected_food_types = st.sidebar.multiselect("🥦 Filter by Dietary Food Type", available_food_types, default=available_food_types)

# Fallback: If an operator clears a field selection, default to full structural scope to prevent crash
filter_cities = selected_cities if selected_cities else available_cities
filter_providers = selected_provider_types if selected_provider_types else available_provider_types
filter_meals = selected_meal_types if selected_meal_types else available_meal_types
filter_foods = selected_food_types if selected_food_types else available_food_types

# --- STEP 4: PRE-FILTERING DATA AND IN-MEMORY DATABASE HANDSHAKE ---
filtered_listings = listings_raw[
    (listings_raw["Location"].isin(filter_cities)) &
    (listings_raw["Provider_Type"].isin(filter_providers)) &
    (listings_raw["Meal_Type"].isin(filter_meals)) &
    (listings_raw["Food_Type"].isin(filter_foods))
]

# Re-instantiate local transactional SQL environment based on active selections
conn = sqlite3.connect(":memory:", check_same_thread=False)
providers_raw.to_sql("providers", conn, index=False, if_exists="replace")
receivers_raw.to_sql("receivers", conn, index=False, if_exists="replace")
filtered_listings.to_sql("food_listings", conn, index=False, if_exists="replace")
claims_raw.to_sql("claims", conn, index=False, if_exists="replace")

# Compile full relational table matrix view using an explicit join
base_query = """
    SELECT 
        f.Food_ID, f.Food_Name, f.Quantity, f.Expiry_Date, f.Location as City, 
        f.Food_Type, f.Meal_Type, f.Provider_Type, p.Name as Provider_Name, p.Contact as Provider_Contact,
        c.Claim_ID, c.Status as Claim_Status, c.Timestamp as Claim_Time, r.Name as Receiver_Name
    FROM food_listings f
    LEFT JOIN providers p ON f.Provider_ID = p.Provider_ID
    LEFT JOIN claims c ON f.Food_ID = c.Food_ID
    LEFT JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
"""
master_df = pd.read_sql(base_query, conn)

# --- STEP 5: KEY PERFORMANCE INDICATOR (KPI) METRICS ---
col1, col2, col3, col4 = st.columns(4)

if len(master_df) > 0:
    total_items = len(master_df["Food_ID"].unique())
    # Group by Food_ID to calculate exact unique available food volume sum without duplicate join rows
    total_qty = int(master_df.groupby("Food_ID")["Quantity"].first().sum())
    completed_claims = len(master_df[master_df["Claim_Status"] == "Completed"])
    success_rate = round((completed_claims / len(master_df) * 100), 2)
else:
    total_items, total_qty, completed_claims, success_rate = 0, 0, 0, 0.0

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

if len(master_df) > 0:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### Total Food Quantity Available by Top 10 Cities")
        # Top 10 cities by volume to keep charts clean and easy to read
        city_volume = master_df.groupby("City")["Quantity"].sum().reset_index().sort_values(by="Quantity", ascending=False).head(10)
        fig_city = px.bar(city_volume, x="City", y="Quantity", color="City", text_auto=True,
                          labels={"Quantity": "Units Allocated"}, template="plotly_white")
        st.plotly_chart(fig_city, use_container_width=True)

    with chart_col2:
        st.markdown("#### Demand Velocity Breakdown (Total Claims Generated by Meal Type)")
        meal_distribution = master_df.groupby("Meal_Type")["Food_ID"].count().reset_index()
        meal_distribution.columns = ["Meal Type", "Transaction Claims Generated"]
        fig_meal = px.pie(meal_distribution, values="Transaction Claims Generated", names="Meal Type", 
                          hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_meal, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.markdown("#### Volume Stream Profile (Dietary Composition Matrix)")
        diet_df = master_df.groupby(["Food_Type", "Provider_Type"])["Quantity"].sum().reset_index()
        fig_diet = px.bar(diet_df, x="Food_Type", y="Quantity", color="Provider_Type", barmode="group",
                           labels={"Quantity": "Volume Sum", "Food_Type": "Diet Category Pattern"}, template="plotly_white")
        st.plotly_chart(fig_diet, use_container_width=True)

    with chart_col4:
        st.markdown("#### Active System Claims Operations Tracking Status")
        status_df = master_df["Claim_Status"].fillna("Unclaimed").value_counts().reset_index()
        status_df.columns = ["Status", "Record Count"]
        fig_status = px.funnel(status_df, x="Record Count", y="Status", color="Status")
        st.plotly_chart(fig_status, use_container_width=True)
else:
    st.warning("⚠️ No data records match the current combination of sidebar filters. Please adjust your filters to view analytics.")

st.write("---")

# --- STEP 7: MASTER QUERY DATA SEARCH COMPONENT & CONTACT BOOK ---
st.subheader("🔍 Master Operations Records Search & Logistics Engine")

search_term = st.text_input("💡 Query Vector Search (Enter Food Item Name, Provider Name, or Status to filter)...")

display_df = master_df[[
    "Food_ID", "Food_Name", "Quantity", "Expiry_Date", "City", 
    "Meal_Type", "Provider_Type", "Provider_Name", "Provider_Contact", "Claim_Status"
]].drop_duplicates()

if search_term and len(display_df) > 0:
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
if len(display_df) > 0:
    csv_data = display_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Export Current View Workspace to CSV",
        data=csv_data,
        file_name="filtered_food_logistics_manifest.csv",
        mime="text/csv"
)

st.sidebar.success("💡 Tip: Use filters to quickly generate clean data distributions for target cities or high-priority dietary profiles!")
