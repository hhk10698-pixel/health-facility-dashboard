import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Page Configuration
st.set_page_config(page_title="National Health Facility Map", layout="wide", page_icon="🗺️")

# 2. Load GeoJSON for India (State Boundaries)
@st.cache_data
def load_geojson():
    # Reliable public GeoJSON for India states
    repo_url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    return repo_url

# 3. Load Data
@st.cache_data
def load_data():
    if os.path.exists("master_health_facilities.csv"):
        df = pd.read_csv("master_health_facilities.csv")
        df['Name of State/UTs'] = df['Name of State/UTs'].str.strip()
        return df
    return pd.DataFrame()

df = load_data()
india_geojson = load_geojson()

# Dictionary to map your Excel filenames to standard GeoJSON state names
STATE_MAP = {
    "Arunachal": "Arunachal Pradesh",
    "DNH &DD": "Dadra and Nagar Haveli and Daman and Diu",
    "Jammu and Kashmir": "Jammu & Kashmir",
    "UP Health Facility Data": "Uttar Pradesh",
}

# The exact list of state names inside the GeoJSON boundary file
ALL_STATES = [
    "Andaman & Nicobar Island", "Andhra Pradesh", "Arunachal Pradesh", "Assam",
    "Bihar", "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu & Kashmir",
    "Jharkhand", "Karnataka", "Kerala", "Lakshadweep", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
    "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
]

if df.empty:
    st.error("⚠️ Master dataset not found! Please run your data preparation script first.")
else:
    # Standardize State Names in the dataframe for the map
    df['Name of State/UTs'] = df['Name of State/UTs'].replace(STATE_MAP)

    st.title("🏥 National Health Facility Explorer")
    
    # --- SECTION 1: INTERACTIVE INDIA HEATMAP ---
    st.subheader("🗺️ India Facility Density Map")
    st.markdown("*Hover over states to see facility breakdowns. **Red** = Data Not Received.*")
    
    # Process data to include ALL states (even missing ones)
    state_groups = df.groupby('Name of State/UTs')
    map_rows = []
    
    for state in ALL_STATES:
        if state in state_groups.groups:
            state_data = state_groups.get_group(state)
            total = len(state_data)
            
            # Format the breakdown for the hover tooltip
            if 'Type of Facility (Category)' in state_data.columns:
                breakdown = state_data['Type of Facility (Category)'].value_counts().to_dict()
                breakdown_str = "<br>".join([f"• {k}: {v:,}" for k, v in breakdown.items()])
            else:
                breakdown_str = "Breakdown unavailable"
                
            hover_text = f"<b>Total Facilities: {total:,}</b><br><br><b>Facility Breakdown:</b><br>{breakdown_str}"
            map_rows.append({'State': state, 'Total Facilities': total, 'Hover Text': hover_text})
        else:
            # State is missing from your data
            map_rows.append({'State': state, 'Total Facilities': 0, 'Hover Text': "<b>Status:</b><br>❌ Data Not Received"})
            
    map_data = pd.DataFrame(map_rows)
    max_facilities = map_data['Total Facilities'].max()

    # Custom Color Scale: Exactly 0 is Red, >0 jumps to light green and scales to dark green
    # 0.0001 represents a tiny fraction above 0 to create the strict cutoff
    custom_color_scale = [
        [0.0, "#ff4b4b"],         # 0 = Red
        [0.0001, "#ff4b4b"],      # Cutoff for Red
        [0.0001, "#e5f5e0"],      # Start of Green (Light)
        [1.0, "#00441b"]          # Max value = Dark Green
    ]

    # Create the choropleth map
    fig = px.choropleth(
        map_data,
        geojson=india_geojson,
        featureidkey="properties.ST_NM",
        locations="State",
        color="Total Facilities",
        color_continuous_scale=custom_color_scale,
        range_color=(0, max_facilities),
        custom_data=["Hover Text"]
    )

    # Apply the custom hover template
    fig.update_traces(hovertemplate="<b style='font-size:16px;'>%{location}</b><br><br>%{customdata[0]}<extra></extra>")
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        height=700, 
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_colorbar=dict(title="Facility Density")
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- SECTION 2: FILTERS & PIVOT TABLE ---
    st.sidebar.header("Filter Details")
    selected_state = st.sidebar.selectbox("Select State", ["All India"] + sorted(df['Name of State/UTs'].unique()))

    filtered_df = df if selected_state == "All India" else df[df['Name of State/UTs'] == selected_state]

    st.subheader(f"📊 Facility Distribution: {selected_state}")
    
    if 'District' in filtered_df.columns:
        pivot_df = pd.pivot_table(
            filtered_df,
            values='Name of Facility',
            index=['Name of State/UTs', 'District'], 
            columns='Type of Facility (Category)',
            aggfunc='count',
            fill_value=0,
            margins=True,
            margins_name='Grand Total'
        )
        st.dataframe(pivot_df, use_container_width=True)
    
    # --- SECTION 3: VISUAL BREAKDOWN ---
    st.subheader("📈 Type-wise Breakdown")
    chart_data = filtered_df['Type of Facility (Category)'].value_counts().reset_index()
    chart_data.columns = ['Facility Type', 'Count']
    
    fig_bar = px.bar(chart_data, x='Facility Type', y='Count', color='Facility Type', text_auto=True)
    st.plotly_chart(fig_bar, use_container_width=True)
