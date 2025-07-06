# app.py

import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

st.set_page_config(layout="wide")
st.title("📍 Jakarta Air Quality - Latest Readings (OpenAQ v3)")

# --- Settings ---
API_KEY = st.secrets["openaq_api_key"]
LOCATION_ID = 8118
LIMIT = 100

# --- Fetch from OpenAQ v3 `/latest` ---
@st.cache_data(ttl=600)
def fetch_latest_data(location_id, limit):
    url = "https://api.openaq.org/v3/latest"
    headers = {"X-API-Key": API_KEY}
    params = {
        "location_id": location_id,
        "limit": limit
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# --- Load & Flatten ---
try:
    data = fetch_latest_data(LOCATION_ID, LIMIT)
    measurements = data["data"]

    rows = []
    for item in measurements:
        coords = item.get("coordinates", {})
        for m in item.get("measurements", []):
            rows.append({
                "location": item.get("location"),
                "parameter": m.get("parameter"),
                "value": m.get("value"),
                "unit": m.get("unit"),
                "latitude": coords.get("latitude"),
                "longitude": coords.get("longitude"),
            })

    df = pd.DataFrame(rows)

    if df.empty:
        st.warning("No data found for the selected location.")
    else:
        st.sidebar.title("⚙️ Filter")
        pollutant = st.sidebar.selectbox("Select pollutant", df["parameter"].unique())
        df_filtered = df[df["parameter"] == pollutant]

        st.subheader(f"🗺️ {pollutant.upper()} Concentration - Location ID {LOCATION_ID}")

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_filtered,
            get_position='[longitude, latitude]',
            get_color='[255, 140 - value, 100]',
            get_radius=800,
            pickable=True,
        )

        view_state = pdk.ViewState(
            latitude=df_filtered["latitude"].mean(),
            longitude=df_filtered["longitude"].mean(),
            zoom=11,
            pitch=0,
        )

        deck = pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"text": "{parameter}: {value} {unit}"}
        )

        st.pydeck_chart(deck)
        st.dataframe(df_filtered)

except Exception as e:
    st.error(f"❌ Failed to fetch or process data: {e}")
