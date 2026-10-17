"""AQI categories, colours, health effects and safety measures.

Two scales are supported:
  * India CPCB (National AQI)  - 6 categories, 0-500
  * US AQI (EPA)               - 6 categories, 0-500

Both scales have six severity tiers, so the same advice text is reused
tier-by-tier (tier 1 = best air, tier 6 = worst air).
"""

CPCB = "India CPCB"
US = "US AQI"
SCALES = [CPCB, US]

# Advice per severity tier (index 0 = cleanest air, 5 = worst)
ADVICE = [
    {
        "emoji": "😊",
        "summary": "Air quality is excellent. Pollution poses little or no risk.",
        "effects": ["No noticeable health effects for anyone."],
        "at_risk": ["Nobody is at special risk."],
        "measures": [
            "Enjoy outdoor activities freely.",
            "Open windows to ventilate your home.",
            "Good day for exercise, walking and cycling outdoors.",
        ],
    },
    {
        "emoji": "🙂",
        "summary": "Air quality is acceptable. Very sensitive people may feel slight discomfort.",
        "effects": [
            "Minor breathing discomfort for people with lung or heart disease.",
            "Slight irritation in eyes or throat for very sensitive individuals.",
        ],
        "at_risk": ["People with asthma or allergies (minor)."],
        "measures": [
            "Normal outdoor activity is fine for most people.",
            "Sensitive people should watch for symptoms such as coughing.",
            "Keep inhalers / medication handy if you have asthma.",
        ],
    },
    {
        "emoji": "😐",
        "summary": "Breathing discomfort is likely for sensitive groups on prolonged exposure.",
        "effects": [
            "Breathing discomfort for people with lung disease, asthma and heart disease.",
            "Cough and throat irritation on longer outdoor exposure.",
            "Reduced stamina during heavy exercise.",
        ],
        "at_risk": ["Children", "Older adults", "Pregnant women", "People with asthma, COPD or heart disease"],
        "measures": [
            "Reduce long or intense outdoor exertion if you are sensitive.",
            "Prefer parks / low-traffic routes; avoid busy roads at rush hour.",
            "Use an N95 mask if you must spend long hours outside.",
            "Keep indoor air clean - avoid smoking, incense and burning waste.",
        ],
    },
    {
        "emoji": "😷",
        "summary": "Unhealthy. Most people may begin to feel effects; sensitive groups are seriously affected.",
        "effects": [
            "Breathing discomfort for most people on prolonged exposure.",
            "Eye, nose and throat irritation, persistent cough.",
            "Aggravated asthma, bronchitis and heart conditions.",
            "Headache, fatigue and reduced lung function.",
        ],
        "at_risk": ["Everyone on prolonged exposure", "Children and elderly (high risk)", "People with heart / lung disease (high risk)"],
        "measures": [
            "Avoid outdoor exercise; shift workouts indoors.",
            "Wear a well-fitted N95/FFP2 mask outdoors.",
            "Keep windows closed during peak pollution hours; use an air purifier (HEPA).",
            "Limit time outside for children and elders.",
            "Stay hydrated; rinse eyes/face after coming home.",
        ],
    },
    {
        "emoji": "🤢",
        "summary": "Very unhealthy. Serious respiratory effects on prolonged exposure.",
        "effects": [
            "Respiratory illness on prolonged exposure.",
            "Serious aggravation of heart and lung disease.",
            "Frequent coughing, wheezing, chest tightness.",
            "Higher risk of infections; early symptoms of lung disease in healthy people.",
        ],
        "at_risk": ["Entire population", "Children, elderly, pregnant women (severe risk)", "Outdoor workers"],
        "measures": [
            "Stay indoors as much as possible with doors and windows shut.",
            "Run HEPA air purifiers; create a 'clean room' at home.",
            "Wear N95/FFP2 mask for any outdoor trip; avoid all outdoor exertion.",
            "Postpone outdoor events; consider remote work / school closure.",
            "Seek medical help for chest pain, severe cough or breathlessness.",
        ],
    },
    {
        "emoji": "☠️",
        "summary": "Severe / hazardous. Emergency conditions - serious effects even on healthy people.",
        "effects": [
            "Serious respiratory effects even during light activity.",
            "Severe aggravation of heart and lung disease; risk of heart attack and stroke.",
            "Chronic exposure can cause long-term lung damage.",
            "Premature mortality risk among people with existing illness.",
        ],
        "at_risk": ["Everyone", "Children, elderly, pregnant women and sick people (critical risk)"],
        "measures": [
            "Do NOT go outdoors unless essential; avoid all physical exertion.",
            "Seal gaps, run HEPA purifiers, avoid anything that burns indoors.",
            "Wear a properly fitted N95/FFP2 (or better) mask if you must go out.",
            "Follow local government health advisories.",
            "Consider temporarily relocating vulnerable people to a cleaner area.",
            "Seek emergency care for severe breathing trouble or chest pain.",
        ],
    },
]

_CPCB_BASE = [
    (0, 50, "Good", "#00B050"),
    (51, 100, "Satisfactory", "#92D050"),
    (101, 200, "Moderately Polluted", "#FFD400"),
    (201, 300, "Poor", "#FF9900"),
    (301, 400, "Very Poor", "#E8242B"),
    (401, 500, "Severe", "#9B1C1C"),
]

_US_BASE = [
    (0, 50, "Good", "#00C853"),
    (51, 100, "Moderate", "#FFEB3B"),
    (101, 150, "Unhealthy for Sensitive Groups", "#FF9800"),
    (151, 200, "Unhealthy", "#E53935"),
    (201, 300, "Very Unhealthy", "#8E24AA"),
    (301, 500, "Hazardous", "#7B1020"),
]


def _build(base):
    return [
        {"low": lo, "high": hi, "name": name, "color": color, "tier": i, **ADVICE[i]}
        for i, (lo, hi, name, color) in enumerate(base)
    ]


LEVELS = {CPCB: _build(_CPCB_BASE), US: _build(_US_BASE)}


def get_level(aqi, scale=CPCB):
    """Return the level dict for an AQI value on the given scale."""
    v = int(round(min(max(float(aqi), 0), 500)))
    for lv in LEVELS[scale]:
        if lv["low"] <= v <= lv["high"]:
            return lv
    return LEVELS[scale][-1]


def text_color_for(hex_color):
    """Black or white text, whichever is readable on the given background."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#111111" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#FFFFFF"
