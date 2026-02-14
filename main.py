import streamlit as st
import pandas as pd
import re
import os
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="ClimateScope", layout="wide")

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "users" not in st.session_state:
    st.session_state.users = {
        "subhadip": {
            "email": "subhadip@gmail.com",
            "password": "subhadip123"
        }
    }

if "image_counter" not in st.session_state:
    st.session_state.image_counter = 0

# --------------------------------------------------
# LOAD DATA (LOCAL + STREAMLIT CLOUD SAFE)
# --------------------------------------------------
@st.cache_data
def load_data():
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "GlobalWeatherRepository.csv"
    )

    if not os.path.exists(csv_path):
        csv_path = "GlobalWeatherRepository.csv"

    if not os.path.exists(csv_path):
        st.error("❌ GlobalWeatherRepository.csv not found. Upload it to GitHub repo.")
        st.stop()

    return pd.read_csv(csv_path)

# --------------------------------------------------
# AUTH PAGE
# --------------------------------------------------
def auth_page():
    st.image(
        "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b",
        use_container_width=True
    )

    st.title("🔐 ClimateScope Authentication")
    st.caption("Login or Register to access the ClimateScope Dashboard")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in st.session_state.users and \
               st.session_state.users[username]["password"] == password:
                st.success("✅ Login Successful")
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    with tab2:
        reg_user = st.text_input("Username", key="reg_user")
        reg_email = st.text_input("Email")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        reg_conf = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if not reg_user or not reg_email or not reg_pass:
                st.error("❌ All fields required")
            elif reg_user in st.session_state.users:
                st.error("❌ Username already exists")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", reg_email):
                st.error("❌ Invalid email format")
            elif reg_pass != reg_conf:
                st.error("❌ Passwords do not match")
            else:
                st.session_state.users[reg_user] = {
                    "email": reg_email,
                    "password": reg_pass
                }
                st.success("✅ Registration successful. Please login.")

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
def dashboard():

    # --------------------------------------------------
    # LIVE IMAGE
    # --------------------------------------------------
    st.header("⏱ Live Weather Image Control")

    enable_timer = st.checkbox("Enable Auto Image Change")

    timer_options = {
        "15 seconds": 15000,
        "30 seconds": 30000,
        "1 minute": 60000
    }

    selected_timer = st.selectbox(
        "Select Timer",
        list(timer_options.keys()),
        disabled=not enable_timer
    )

    weather_images = [
        "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b",
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
        "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31",
        "https://images.unsplash.com/photo-1500674425229-f692875b0ab7"
    ]

    if enable_timer:
        st_autorefresh(interval=timer_options[selected_timer], key="auto")
        st.session_state.image_counter += 1
    else:
        st.session_state.image_counter = 0

    index = st.session_state.image_counter % len(weather_images)

    st.image(
        weather_images[index],
        use_container_width=True,
        caption=f"Live Weather Image (Update #{st.session_state.image_counter})"
    )

    st.divider()

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------
    st.title("🌍 ClimateScope Dashboard")
    st.subheader("Visualizing Global Weather Trends")
    st.success(f"Welcome {st.session_state.username} 👋")

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------
    df = load_data()

    # --------------------------------------------------
    # USER CONTROLS
    # --------------------------------------------------
    st.header("🔘 User Controls")

    countries = sorted(df["country"].dropna().unique())
    selected_country = st.selectbox("🌍 Select Country", countries)

    unit = st.radio("🌡 Temperature Unit", ["Celsius", "Fahrenheit"])
    temp_col = "temperature_celsius" if unit == "Celsius" else "temperature_fahrenheit"

    country_df = df[df["country"] == selected_country]

    st.subheader(f"📄 Data Preview – {selected_country}")
    st.dataframe(country_df.head(), use_container_width=True)

    # --------------------------------------------------
    # SMART WEATHER SUMMARY
    # --------------------------------------------------
    st.header("🧠 Smart Weather Summary")

    avg_temp = country_df[temp_col].mean()
    max_temp = country_df[temp_col].max()
    avg_wind = country_df["wind_kph"].mean()
    common_condition = country_df["condition_text"].mode()[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡 Avg Temp", f"{avg_temp:.1f}")
    c2.metric("🔥 Max Temp", f"{max_temp:.1f}")
    c3.metric("💨 Avg Wind (km/h)", f"{avg_wind:.1f}")
    c4.metric("☁ Common Weather", common_condition)

    if unit == "Celsius" and max_temp > 35:
        st.error("🚨 Heat Alert: Extremely high temperature detected!")

    # --------------------------------------------------
    # ⭐ FEATURE 1: CLIMATE RISK SCORE
    # --------------------------------------------------
    st.header("⚠️ Climate Risk Index")

    risk_score = 0

    if max_temp > 35:
        risk_score += 40
    elif max_temp > 30:
        risk_score += 25

    if avg_wind > 30:
        risk_score += 30
    elif avg_wind > 20:
        risk_score += 15

    extreme_conditions = country_df["condition_text"].str.contains(
        "storm|thunder|snow|rain", case=False, na=False
    ).sum()

    risk_score += min(extreme_conditions / len(country_df) * 30, 30)
    risk_score = min(int(risk_score), 100)

    st.progress(risk_score / 100)

    if risk_score >= 70:
        st.error(f"🚨 High Climate Risk: {risk_score}/100")
    elif risk_score >= 40:
        st.warning(f"⚠️ Moderate Climate Risk: {risk_score}/100")
    else:
        st.success(f"✅ Low Climate Risk: {risk_score}/100")

    # --------------------------------------------------
    # ⭐ FEATURE 2: AI WEATHER INSIGHT
    # --------------------------------------------------
    st.header("🧠 AI Weather Insight")

    insight = (
        f"{selected_country} shows an average temperature of {avg_temp:.1f}°{unit[0]}. "
        f"The maximum recorded temperature is {max_temp:.1f}°{unit[0]}, "
        f"with predominant weather conditions being {common_condition.lower()}. "
    )

    if max_temp > 35:
        insight += "This indicates a potential heatwave risk. "

    if avg_wind > 30:
        insight += "Strong wind patterns suggest unstable atmospheric conditions. "

    st.info(insight)

    # --------------------------------------------------
    # ⭐ FEATURE 3: MONTHLY ANALYSIS
    # --------------------------------------------------
    if "last_updated" in country_df.columns:
        st.header("📅 Monthly Temperature Analysis")

        country_df["last_updated"] = pd.to_datetime(country_df["last_updated"])
        country_df["Month"] = country_df["last_updated"].dt.month_name()

        monthly_avg = country_df.groupby("Month")[temp_col].mean()
        st.bar_chart(monthly_avg)

    # --------------------------------------------------
    # ⭐ FEATURE 4: EXTREME DAYS AND TIME
    # --------------------------------------------------
    st.header("🏆 Extreme Days")
    country_df["last_updated"] = pd.to_datetime(country_df["last_updated"], errors="coerce")

    hot_day = country_df.loc[country_df[temp_col].idxmax()]
    cold_day = country_df.loc[country_df[temp_col].idxmin()]

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "🔥 Hottest Day",
            f"{hot_day[temp_col]:.1f}°{unit[0]}"
        )
        st.caption(f"📅 Date: {hot_day['last_updated'].date()}")

    with c2:
        st.metric(
            "❄️ Coldest Day",
            f"{cold_day[temp_col]:.1f}°{unit[0]}"
        )
        st.caption(f"📅 Date: {cold_day['last_updated'].date()}")

    # --------------------------------------------------
    # ⭐ FEATURE 5: DOWNLOAD DATA
    # --------------------------------------------------
    st.header("📥 Download Data")

    csv = country_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Selected Country Data",
        csv,
        file_name=f"{selected_country}_weather.csv",
        mime="text/csv"
    )

    st.divider()

    # --------------------------------------------------
    # LOGOUT
    # --------------------------------------------------
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.image_counter = 0
        st.rerun()

# --------------------------------------------------
# PAGE CONTROLLER
# --------------------------------------------------
if st.session_state.logged_in:
    dashboard()
else:
    auth_page()
