# app.py

import streamlit as st
import pandas as pd
import pydeck as pdk
from openaq import OpenAQ

# --- Setup ---
st.set_page_config(layout="wide")
st.title("📍 Jakarta Air Quality (OpenAQ SDK)")

API_KEY = st.secrets["openaq_api_key"]

# Coordinates for Jakarta
JAKARTA_COORDS = [106.84513, -6.21462]  # [longitude, latitude]
RADIUS_METERS = 15000

# --- Fetch Location Data from OpenAQ SDK ---
@st.cache_data(ttl=600)
def fetch_locations(coordinates, radius=12000, limit=100):
    client = OpenAQ(api_key=API_KEY)
    try:
        response = client.locations.list(
            coordinates=coordinates,
            radius=radius,
            limit=limit
        )
        return response["results"]
    finally:
        client.close()

# --- Fetch and Process Data ---
try:
    results = fetch_locations(JAKARTA_COORDS, RADIUS_METERS, limit=100)
    data = []

    for item in results:
        if "coordinates" in item:
            lat = item["coordinates"]["latitude"]
            lon = item["coordinates"]["longitude"]
            for param in item.get("parameters", []):
                data.append({
                    "location": item.get("name"),
                    "parameter": param["parameter"],
                    "value": param["lastValue"],
                    "unit": param["unit"],
                    "latitude": lat,
                    "longitude": lon
                })

    df = pd.DataFrame(data)

    if df.empty:
        st.warning("No AQI data available.")
    else:
        st.sidebar.title("⚙️ Filter")
        selected_param = st.sidebar.selectbox("Select pollutant", df["parameter"].unique())
        df_filtered = df[df["parameter"] == selected_param]

        st.subheader(f"🗺️ {selected_param.upper()} Levels in Jakarta (via OpenAQ SDK)")

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_filtered,
            get_position='[longitude, latitude]',
            get_color='[255, 140 - value, 100]',
            get_radius=800,
            pickable=True
        )

        view_state = pdk.ViewState(
            latitude=JAKARTA_COORDS[1],
            longitude=JAKARTA_COORDS[0],
            zoom=10.5
        )

        deck = pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"text": "{location}\n{parameter}: {value} {unit}"}
        )

        st.pydeck_chart(deck)
        st.dataframe(df_filtered)

except Exception as e:
    st.error(f"❌ Error fetching data: {e}")
