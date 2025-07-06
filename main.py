# app.py

import streamlit as st
import pandas as pd
import pydeck as pdk
from openaq import OpenAQ

# --- Streamlit setup ---
st.set_page_config(layout="wide")
st.title("🌇 Jakarta Air Quality - Spatial View (OpenAQ v3 SDK)")

# --- Constants ---
API_KEY = st.secrets["openaq_api_key"]
JAKARTA_COORDS = [106.84513, -6.21462]  # [lon, lat]
RADIUS_METERS = 15000
LIMIT = 100

# --- Safely fetch data using context manager ---
@st.cache_data(ttl=600)
def get_cached_location_data():
    with OpenAQ(api_key=API_KEY) as client:
        response = client.locations.list(
            coordinates=JAKARTA_COORDS,
            radius=RADIUS_METERS,
            limit=LIMIT
        )
        return response["results"]

# --- Main logic ---
try:
    results = get_cached_location_data()

    # Flatten location and parameter info
    records = []
    for loc in results:
        coords = loc.get("coordinates", {})
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        for param in loc.get("parameters", []):
            records.append({
                "location": loc.get("name"),
                "parameter": param.get("parameter"),
                "value": param.get("lastValue"),
                "unit": param.get("unit"),
                "latitude": lat,
                "longitude": lon
            })

    df = pd.DataFrame(records)

    if df.empty:
        st.warning("No air quality data found for Jakarta.")
    else:
        # --- Sidebar filter ---
        st.sidebar.title("⚙️ Filters")
        pollutant = st.sidebar.selectbox("Select pollutant", df["parameter"].unique())

        df_filtered = df[df["parameter"] == pollutant]

        # --- Spatial map ---
        st.subheader(f"🗺️ {pollutant.upper()} Levels in Jakarta")

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_filtered,
            get_position='[longitude, latitude]',
            get_color='[255, 140 - value, 100]',
            get_radius=800,
            pickable=True,
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
