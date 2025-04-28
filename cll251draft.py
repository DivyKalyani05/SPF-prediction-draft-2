import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

# --- Constants ---
BASE_UV_INDEX = 8
OZONE_BASE = 300
SKIN_TYPES = {
    "Type I (Very fair)": 5,
    "Type II (Fair)": 10,
    "Type III (Medium)": 15,
    "Type IV (Olive)": 20,
    "Type V (Brown)": 25,
    "Type VI (Dark brown)": 30,
}
ALTITUDE_BOOST = 0.1  # UV increases ~10% per 1000m

API_KEY = "a7ee76b52d850ee8f45f066d98acf4973a402bfd"

# --- Function to fetch ozone thickness ---
def get_ozone_thickness(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url)
    data = response.json()

    try:
        ozone_ugm3 = data['list'][0]['components']['o3']
        ozone_du = ozone_ugm3 / 2.1415
        return round(ozone_du, 2)
    except:
        return None

# --- UV Index Calculation ---
def get_uv_index(ozone_du, cloud_cover, altitude_km):
    base_uv = BASE_UV_INDEX * (OZONE_BASE / ozone_du)
    cloud_factor = 1 - (cloud_cover / 100) * 0.75  # Clouds block 75% UV
    altitude_factor = 1 + ALTITUDE_BOOST * altitude_km
    return base_uv * cloud_factor * altitude_factor

# --- Safe Exposure Time ---
def get_protection_time(spf, uv_index, skin_minutes):
    return (spf * skin_minutes) / uv_index

# --- Streamlit App ---
st.set_page_config("☀️ Sunburn Risk & Ozone Simulator", layout="centered")
st.title("☀️ Sunburn Risk & Ozone Depletion Simulator with Live Ozone Fetch and SPF prediction")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header(" Simulation Inputs")
    
    use_live_ozone = st.checkbox("Use Live Ozone by Location?", value=True)

    if use_live_ozone:
        lat = st.number_input("Enter Latitude:", value=28.6139, format="%.4f")
        lon = st.number_input("Enter Longitude:", value=77.2090, format="%.4f")
        ozone_live = get_ozone_thickness(lat, lon, API_KEY)

        if ozone_live:
            st.success(f"Live Ozone Thickness: {ozone_live} DU")
            ozone = ozone_live
        else:
            st.warning("⚠️ Failed to fetch live ozone. Please enter manually.")
            ozone = st.slider("Ozone Thickness (DU)", 100, 400, 300)
    else:
        ozone = st.slider("Ozone Thickness (DU)", 100, 400, 300)

    cloud = st.slider("Cloud Cover (%)", 0, 100, 20)
    altitude = st.slider("Altitude (km)", 0.0, 5.0, 0.0, step=0.1)
    spf = st.slider("Sunscreen SPF", 5, 100, 30)
    exposure = st.slider("Time in Sun (minutes)", 5, 180, 60)
    skin_type = st.selectbox("Select Skin Type", list(SKIN_TYPES.keys()))

# --- Simulation ---
uv_index = get_uv_index(ozone, cloud, altitude)
base_time = SKIN_TYPES[skin_type]
safe_time = get_protection_time(spf, uv_index, base_time)
risk_level = (
    "Low" if uv_index < 3 else
    "Moderate" if uv_index < 6 else
    "High" if uv_index < 8 else
    "Very High" if uv_index < 11 else
    "Extreme"
)

# --- Output Display ---
st.subheader("UV Risk Summary")
st.markdown(f"""
- **Estimated UV Index**: `{uv_index:.2f}` → **{risk_level} Risk**
- **Skin Type**: `{skin_type}` (burns in ~{base_time} min)
- **Sunscreen SPF**: `{spf}`
- **Estimated Safe Exposure Time**: `{safe_time:.1f} minutes`
""")

# --- Risk Alert ---
if exposure > safe_time:
    st.error("🚨 WARNING: Sun exposure exceeds protection time. HIGH sunburn risk!")
else:
    st.success("✅ You're within safe exposure time.")

# --- New Improved Graph ---
minutes = np.linspace(0, 180, 500)  # smoother points
# Smoothly increasing burn risk after safe_time
risk_array = 1 / (1 + np.exp(-(minutes - safe_time) / 10))

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(minutes, risk_array, label="Burn Risk Level", color="crimson", linewidth=2)
ax.axvline(safe_time, linestyle="--", color="orange", label=f"Safe Limit ({safe_time:.1f} min)")
ax.axvline(exposure, linestyle="--", color="blue", label=f"Your Exposure ({exposure} min)")

ax.set_ylim(0, 1.05)
ax.set_xlabel("Minutes in Sun", fontsize=12)
ax.set_ylabel("Burn Risk (0 = Safe, 1 = High Risk)", fontsize=12)
ax.set_title("UV Exposure vs Burn Risk Over Time", fontsize=14)
ax.legend()
ax.grid(True, linestyle='--', alpha=0.7)
st.pyplot(fig)

# --- CSV Export ---
df = pd.DataFrame({
    "Minute": minutes,
    "Burn Risk (0=Safe, 1=High)": risk_array
})
st.download_button("📥 Download Risk Timeline as CSV", df.to_csv(index=False), "uv_risk_data.csv")

# --- Footer ---
st.markdown("---")
st.markdown("<center><small> Submitted to Prof MKS Verma | Built by Divy, Ansh, Nishan, Apoorv, Rathod</small></center>", unsafe_allow_html=True)
