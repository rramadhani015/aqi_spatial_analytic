# app.py

import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

st.set_page_config(layout="wide")
st.title("🌇 Jakarta Air Quality Map (OpenAQ API v3)")

# --- Settings ---
LOCATION_ID = 8118  # You can change to another location ID
API_KEY = st.secrets["openaq_api_key"]  # Set in .streamlit/secrets.toml

# --- Fetch Location Data from OpenAQ v3 ---
@st.cache_data(ttl=600)
def fetch_location_data(location_id):
    url = f"https://api.openaq.org/v3/locations/{location_id}"
    headers = {"X-API-Key": API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# --- Fetch Latest Measurements from OpenAQ v3 ---
@st.cache_data(ttl=600)
def fetch_latest_measurements(location_id):
    url = "https://api.openaq.org/v3/latest"
    headers = {"X-API-Key": API_KEY}
    params = {
        "location_id": location_id,
        "limit": 100
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# --- Main ---
try:
    location_data = fetch_location_data(LOCATION_ID)
    latest_data = fetch_latest_measurements(LOCATION_ID)

    location = location_data["data"]
    measurements = latest_data["data"]

    st.subheader(f"📍 Location: {location['name']}")

    # Flatten pollutant readings
    rows = []
    for entry in measurements:
        for m in entry["measurements"]:
            rows.append({
                "parameter": m["parameter"],
                "value": m["value"],
                "unit": m["unit"],
                "latitude": entry["coordinates"]["latitude"],
                "longitude": entry["coordinates"]["longitude"]
            })

    df = pd.DataFrame(rows)

    st.sidebar.title("⚙️ Controls")
    selected_pollutant = st.sidebar.selectbox("Select pollutant", df["parameter"].unique())

    filtered_df = df[df["parameter"] == selected_pollutant]

    # --- Pydeck Map ---
    if filtered_df.empty:
        st.warning("No measurements available for the selected pollutant.")
    else:
        st.subheader(f"🗺️ Spatial View - {selected_pollutant.upper()} Concentrations")

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtered_df,
            get_position='[longitude, latitude]',
            get_radius=800,
            get_color='[255, 140 - value, 100]',
            pickable=True,
        )

        view_state = pdk.ViewState(
            latitude=filtered_df["latitude"].mean(),
            longitude=filtered_df["longitude"].mean(),
            zoom=11,
            pitch=0,
        )

        r = pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"text": "{parameter}: {value} {unit}"}
        )

        st.pydeck_chart(r)
        st.dataframe(filtered_df)

except Exception as e:
    st.error(f"❌ Failed to fetch data: {e}")
