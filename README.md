# 🌫️ Air Quality Management System (Streamlit)

## Directory structure
```
aqi_system/
├── app.py                  # Main Streamlit app (3 tabs)
├── requirements.txt        # Python dependencies
├── README.md
├── .streamlit/
│   └── config.toml         # Theme
└── modules/
    ├── __init__.py
    ├── api.py              # Live data: Open-Meteo geocoding + air-quality (no API key)
    ├── calculator.py       # CPCB AQI calculator (sub-index + dominant pollutant)
    ├── aqi_info.py         # Categories, colours, health effects, safety measures
    └── charts.py           # Plotly line chart, gauge, bar chart
```

## Run
```
cd aqi_system
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```
Opens at http://localhost:8501 — internet is required for live data.

## Features
1. **City AQI & 10-Day History** - search any city, live AQI, pollutant levels, 10-day line chart.
2. **AQI Calculator** - enter pollutant concentrations, get AQI (CPCB method), dominant pollutant.
3. **Pollution Level Explorer** - slide the AQI 0-500 for level, health effects, who is at risk, safety tips.
4. **Live data** - Open-Meteo Air Quality API (free, no key). Sidebar switches India CPCB / US AQI scale.
