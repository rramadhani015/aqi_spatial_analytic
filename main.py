# app.py

import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

# --- Streamlit setup ---
st.set_page_config(layout="wide")
st.title("🌇 Jakarta Air Quality - Spatial View (OpenAQ v3 REST API)")

# --- Constants ---
API_KEY = st.secrets["openaq_api_key"]
JAKARTA_COORDS = [106.84513, -6.21462]
RADIUS_METERS = 15000
LIMIT = 100

# --- Fetch using requests ---
@st.cache_data(ttl=600)
def fetch_openaq_locations():
    url = "https://api.openaq.org/v3/locations"
    headers = {"X-API-Key": API_KEY}
    params = {
        "coordinates": f"{JAKARTA_COORDS[1]},{JAKARTA_COORDS[0]}",  # lat,lon
        "radius": RADIUS_METERS,
        "limit": LIMIT
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["results"]

# --- Main ---
try:
    results = fetch_openaq_locations()

    records = []
    for loc in results:
        coords = loc.get("coordinates", {})
        for param in loc.get("parameters", []):
            records.append({
                "location": loc.get("name"),
                "parameter": param.get("parameter"),
                "value": param.get("lastValue"),
                "unit": param.get("unit"),
                "latitude": coords.get("latitude"),
                "longitude": coords.get("longitude")
            })

    df = pd.DataFrame(records)

    if df.empty:
        st.warning("No AQI data found.")
    else:
        st.sidebar.title("⚙️ Filter")
        pollutant = st.sidebar.selectbox("Select pollutant", df["parameter"].unique())
        df_filtered = df[df["parameter"] == pollutant]

        st.subheader(f"🗺️ {pollutant.upper()} Levels in Jakarta")

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
    st.error(f"❌ Error fetching AQI data: {e}")
