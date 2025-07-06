# app.py
import streamlit as st
import pandas as pd
import requests
import pydeck as pdk


st.set_page_config(layout="wide")
st.title("🌍 Jakarta Air Quality - Spatial View")

# --- Fetch Data from OpenAQ ---
@st.cache_data(ttl=600)
def fetch_openaq_data(city="Jakarta", parameter="pm25", limit=100):
    url = "https://api.openaq.org/v2/measurements"
    params = {
        "city": city,
        "country": "ID",
        "parameter": parameter,
        "limit": limit,
        "sort": "desc",
        "order_by": "datetime"
    }
    r = requests.get(url, params=params)
    results = r.json()["results"]
    df = pd.DataFrame(results)
    df = df.dropna(subset=["coordinates"])
    df["lat"] = df["coordinates"].apply(lambda x: x["latitude"])
    df["lon"] = df["coordinates"].apply(lambda x: x["longitude"])
    return df

# --- Sidebar Controls ---
parameter = st.sidebar.selectbox("Select Pollutant", ["pm25", "pm10", "co", "no2", "o3"])
limit = st.sidebar.slider("Number of Data Points", 10, 100, 50)

df = fetch_openaq_data(parameter=parameter, limit=limit)

# --- Map View ---
st.subheader(f"Live {parameter.upper()} Data in Jakarta")

if df.empty:
    st.warning("No data available.")
else:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_color='[255, 140 - value, 100]',
        get_radius=800,
        pickable=True,
        auto_highlight=True
    )

    view_state = pdk.ViewState(
        latitude=-6.2,
        longitude=106.8,
        zoom=10,
        pitch=0,
    )

    r = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{location}\n{value} µg/m³"}
    )

    st.pydeck_chart(r)

    st.dataframe(df[["location", "value", "unit", "lat", "lon", "date"]])

