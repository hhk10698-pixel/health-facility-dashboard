import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Health Facilities Dashboard", layout="wide")

@st.cache_data
def load_data():
    if os.path.exists("master_health_facilities.csv"):
        return pd.read_csv("master_health_facilities.csv")
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("⚠️ Master dataset not found! Please run 'python data_prep.py' first.")
else:
    st.sidebar.header("Filters")
    state_list = ["All India"] + sorted(df['Name of State/UTs'].dropna().unique().tolist())
    selected_state = st.sidebar.selectbox("Select State/UT", state_list)
    
    filtered_df = df if selected_state == "All India" else df[df['Name of State/UTs'] == selected_state]

    st.title(f"🏥 Health Facilities Dashboard: {selected_state}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Facilities", f"{len(filtered_df):,}")
    c2.metric("Districts", filtered_df['District'].nunique() if 'District' in filtered_df.columns else 0)
    c3.metric("Data Status", "Live")

    st.markdown("---")

    if 'District' in filtered_df.columns and 'Type of Facility (Category)' in filtered_df.columns:
        st.subheader("📋 Facility Pivot Table")
        pivot_df = pd.pivot_table(
            filtered_df,
            values='Name of Facility',
            index='District',
            columns='Type of Facility (Category)',
            aggfunc='count',
            fill_value=0,
            margins=True,
            margins_name='Grand Total'
        )
        # Fixed: use width="stretch" instead of use_container_width
        st.dataframe(pivot_df, width="stretch")
        
        st.markdown("---")
        st.subheader("📊 Visual Breakdown")
        chart_df = pivot_df.drop('Grand Total', axis=0, errors='ignore').drop('Grand Total', axis=1, errors='ignore')
        
        fig = px.bar(
            chart_df, 
            barmode='stack',
            height=600,
            labels={'value': 'Count', 'District': 'District'}
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.warning("Data found, but columns like 'District' or 'Type' couldn't be identified for this state.")