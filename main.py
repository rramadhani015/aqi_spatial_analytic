# app.py

import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("🌍 OpenAQ: Air Quality Monitoring by Coordinates")

# --- API Key ---
API_KEY = st.secrets["openaq_api_key"]

# --- Default Coordinates (from OpenAQ docs) ---
default_coords = [136.90610, 35.14942]  # [lon, lat]
default_radius = 12000  # meters
default_limit = 1000

# --- User input ---
lon = st.sidebar.number_input("Longitude", value=default_coords[0], format="%.5f")
lat = st.sidebar.number_input("Latitude", value=default_coords[1], format="%.5f")
radius = st.sidebar.slider("Radius (m)", 1000, 30000, default_radius)
limit = st.sidebar.slider("Limit", 10, 1000, default_limit)

# --- Fetch Data ---
@st.cache_data(ttl=600)
def fetch_locations_by_coords(lat, lon, radius, limit):
    url = "https://api.openaq.org/v3/locations"
    headers = {"X-API-Key": API_KEY}
    params = {
        "coordinates": f"{lat},{lon}",
        "radius": radius,
        "limit": limit
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["results"]

try:
    results = fetch_locations_by_coords(lat, lon, radius, limit)

    records = []
    for loc in results:
        coords = loc.get("coordinates", {})
        for param in loc.get("parameters", []):
            value = param.get("lastValue")
            if value is not None and coords.get("latitude") and coords.get("longitude"):
                records.append({
                    "location": loc.get("name"),
                    "parameter": param.get("parameter"),
                    "value": value,
                    "unit": param.get("unit"),
                    "latitude": coords.get("latitude"),
                    "longitude": coords.get("longitude")
                })

    df = pd.DataFrame(records)

    if df.empty:
        st.warning("No AQI data found for this location and radius.")
    else:
        st.sidebar.write("📌 Found pollutants:", df["parameter"].unique().tolist())
        selected = st.sidebar.selectbox("Filter by pollutant", df["parameter"].unique())
        df_filtered = df[df["parameter"] == selected]

        st.subheader(f"🗺️ {selected.upper()} levels near ({lat}, {lon})")

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_filtered,
            get_position='[longitude, latitude]',
            get_color='[255, 140 - value, 100]',
            get_radius=800,
            pickable=True,
        )

        view_state = pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=10.5
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"text": "{location}\n{parameter}: {value} {unit}"}
        ))

        st.dataframe(df_filtered)

except Exception as e:
    st.error(f"❌ Failed to fetch or parse data: {e}")
