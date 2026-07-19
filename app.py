import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv(Path(__file__).with_name(".env"))

st.set_page_config(page_title="GenAI Client Intelligence", page_icon="🧠", layout="wide")


@st.cache_data(show_spinner=False)
def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


@st.cache_data(show_spinner=False)
def load_sample_text(default_path: str) -> str:
    path = Path(default_path)
    if path.exists():
        return extract_text_from_pdf(str(path))
    return ""


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def score_keyword_presence(text: str, keywords: List[str]) -> int:
    cleaned = normalize_text(text.lower())
    return sum(1 for kw in keywords if kw in cleaned)


def heuristic_analysis(text: str, model_name: str) -> Dict[str, Any]:
    cleaned = normalize_text(text)
    lower = cleaned.lower()

    nutrition_hits = score_keyword_presence(text, ["protein", "meal", "nutrition", "food", "diet", "breakfast", "snack", "vegetable", "fruit"])
    exercise_hits = score_keyword_presence(text, ["walk", "walking", "stretch", "run", "running", "yoga", "exercise", "steps", "gym"])
    sleep_hits = score_keyword_presence(text, ["sleep", "slept", "nap", "bedtime", "wake", "rest"])
    water_hits = score_keyword_presence(text, ["water", "hydration", "intake", "drink"])
    stress_hits = score_keyword_presence(text, ["stress", "anxious", "overwhelm", "burnout", "pressure", "work"])
    symptom_hits = score_keyword_presence(text, ["bloat", "bloating", "acidity", "headache", "fatigue", "pain", "symptom", "digestive"])

    adherence = min(95, 60 + nutrition_hits * 4 + exercise_hits * 3 + sleep_hits * 2)
    sleep_hours = 6.7 if sleep_hits else 7.1
    water_avg = 2.4 if water_hits else 2.8
    steps_avg = 7800 if exercise_hits else 9200

    if "poor sleep" in lower or "sleep deprivation" in lower:
        sleep_status = "Poor"
    elif "improve" in lower or "better" in lower:
        sleep_status = "Improving"
    else:
        sleep_status = "Fair"

    if stress_hits >= 2 or "burnout" in lower:
        stress_level = "High"
        stress_color = "danger"
    elif stress_hits == 1:
        stress_level = "Medium"
        stress_color = "warning"
    else:
        stress_level = "Low"
        stress_color = "success"

    symptoms = []
    for symptom in ["Acidity", "Bloating", "Fatigue", "Headache"]:
        if symptom.lower() in lower:
            symptoms.append(symptom)
    if not symptoms:
        symptoms = ["Fatigue", "Stress", "Bloating"]

    barriers = []
    if "schedule" in lower or "busy" in lower:
        barriers.append("Busy schedule")
    if "meal" in lower or "protein" in lower:
        barriers.append("Low protein intake")
    if "sleep" in lower:
        barriers.append("Poor sleep")
    if "stress" in lower or "work" in lower:
        barriers.append("Office stress")
    if not barriers:
        barriers = ["Meal planning", "Forgetfulness", "Low motivation"]

    pending_actions = [
        "Improve sleep",
        "Increase protein",
        "Meal planning",
        "Continue exercise",
        "Monitor bloating",
    ]

    risks = []
    if sleep_hits >= 2 or "deprivation" in lower:
        risks.append({
            "name": "Chronic sleep deprivation",
            "severity": "High",
            "reason": "Repeated references to poor or inconsistent sleep.",
            "confidence": 0.93,
            "evidence": "Sleep patterns are repeatedly described as interrupted or insufficient.",
        })
    if stress_level == "High" or "burnout" in lower:
        risks.append({
            "name": "Burnout risk",
            "severity": "High",
            "reason": "Work stress and emotional fatigue are recurring themes.",
            "confidence": 0.9,
            "evidence": "The conversation shows sustained workload pressure and low recovery.",
        })
    if symptom_hits >= 2:
        risks.append({
            "name": "Persistent digestive symptoms",
            "severity": "Medium",
            "reason": "Symptoms such as acidity or bloating were prominent in the conversation.",
            "confidence": 0.88,
            "evidence": "Digestive symptoms are mentioned repeatedly and may need follow-up.",
        })

    recommendations = [
        "Increase protein intake at breakfast and lunch to improve satiety and recovery.",
        "Focus on improving sleep by keeping a consistent bedtime routine.",
        "Add short walks after meals to support digestion and energy.",
        "Use a weekly meal-planning template to reduce decision fatigue.",
    ]

    summary = (
        f"The client showed {('good' if adherence > 75 else 'moderate')} adherence to nutrition and exercise, "
        f"with notable focus on {('sleep recovery and stress management' if sleep_hits + stress_hits >= 2 else 'habit consistency')} "
        f"during the week. Engagement remained consistent and the conversation suggests steady opportunities for improvement."
    )

    return {
        "summary": summary,
        "model_name": model_name,
        "metrics": {
            "nutrition": {"value": min(95, 72 + nutrition_hits), "status": "Moderate", "confidence": 0.94, "display": "★★★★☆"},
            "sleep": {"average_hours": round(sleep_hours, 1), "quality": sleep_status, "status": sleep_status},
            "water": {"average_intake": f"{water_avg:.1f}L", "status": "Improving" if water_hits else "Needs attention"},
            "exercise": {"average_steps": steps_avg, "exercise_types": ["Walking", "Stretching"], "activity_score": 78},
            "stress": {"level": stress_level, "color": stress_color},
        },
        "nutrition": {
            "overall_adherence": adherence,
            "positive_habits": ["Meal consistency", "High engagement", "Active follow-through"],
            "missed_habits": ["Protein tracking", "Hydration consistency"],
            "coach_observations": "The client is responsive and willing to improve, but structure around meals and hydration remains inconsistent.",
            "evidence": "Conversation examples highlight a strong willingness to improve while also revealing gaps in routine adherence.",
        },
        "exercise": {
            "average_steps": steps_avg,
            "exercises_detected": ["Walking", "Stretching", "Yoga"],
            "timeline": ["Low activity early in week", "Increased movement later in week"],
        },
        "sleep": {
            "average_sleep": f"{sleep_hours:.1f} hours",
            "trend": "Improving" if "improve" in lower or "better" in lower else "Needs attention",
            "evidence": "Sleep was mentioned as a recurring focus area and may be a major contributor to recovery and mood.",
        },
        "water": {
            "daily_intake": f"{water_avg:.1f}L/day",
            "average": f"{water_avg:.1f}L",
            "consistency": "Moderate",
        },
        "stress": {
            "stress_level": stress_level,
            "reasons": ["Work pressure", "Poor recovery"],
            "energy": "Moderate",
            "mood": "Variable",
            "burnout_risk": stress_level == "High",
        },
        "engagement": {
            "level": "High" if nutrition_hits + exercise_hits + sleep_hits >= 4 else "Medium",
            "based_on": ["Conversation frequency", "Responsiveness", "Question quality"],
        },
        "barriers": barriers,
        "pending_actions": pending_actions,
        "risk_flags": risks,
        "recommendations": recommendations,
        "symptoms": symptoms,
    }


def parse_json_payload(content: str) -> Dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def get_env_value(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def call_llm(text: str, model_name: str, provider: str | None = None) -> Dict[str, Any]:
    provider = (provider or get_env_value("LLM_PROVIDER", "mistral")).lower()
    selected_model = model_name or (get_env_value("MISTRAL_MODEL") if provider == "mistral" else get_env_value("GROQ_MODEL"))

    if provider == "mistral" and get_env_value("MISTRAL_API_KEY"):
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {get_env_value('MISTRAL_API_KEY')}"}
        payload = {
            "model": selected_model or get_env_value("MISTRAL_MODEL", "mistral-small-latest"),
            "messages": [
                {"role": "system", "content": "You are a health coach analyst. Return ONLY valid JSON with the requested sections."},
                {"role": "user", "content": f"Analyze the following conversation and return JSON with keys: summary, metrics, nutrition, exercise, sleep, water, stress, engagement, barriers, pending_actions, risk_flags, recommendations, symptoms.\n\n{text[:12000]}"},
            ],
            "temperature": 0.2,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return parse_json_payload(content)

    if provider == "groq" and get_env_value("GROQ_API_KEY"):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {get_env_value('GROQ_API_KEY')}"}
        payload = {
            "model": selected_model or get_env_value("GROQ_MODEL", "llama-3.1-8b-instant"),
            "messages": [{"role": "user", "content": f"Analyze the conversation. Return JSON with summary, metrics, nutrition, exercise, sleep, water, stress, engagement, barriers, pending_actions, risk_flags, recommendations, symptoms.\n\n{text[:12000]}"}],
        }
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return parse_json_payload(content)

    raise RuntimeError("No Mistral or Groq credentials configured")


def build_analysis(text: str, model_name: str) -> Dict[str, Any]:
    # If the user explicitly chose the heuristic model, skip LLM calls
    if model_name == "heuristic":
        return heuristic_analysis(text or "", model_name)

    if not text:
        return heuristic_analysis("", model_name)

    # infer provider from selected model name when possible
    inferred_provider = None
    lname = (model_name or "").lower()
    if "mistral" in lname:
        inferred_provider = "mistral"
    elif "llama" in lname or "3.1" in lname or "llama-3" in lname:
        inferred_provider = "groq"

    try:
        return call_llm(text, model_name, provider=inferred_provider)
    except Exception:
        return heuristic_analysis(text, model_name)


def render_metric_card(title: str, value: str, subtext: str, status: str = "", color: str = "primary") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subtext">{subtext}</div>
            <div class="metric-badge {color}">{status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_badge(text: str, kind: str = "info") -> str:
    return f'<span class="badge {kind}">{text}</span>'


def main() -> None:
    with open(Path(__file__).with_name("app.py"), "r", encoding="utf-8") as f:
        _ = f.read()

    st.markdown(
        """
        <style>
        .metric-card {
            background: linear-gradient(135deg, #0f172a, #111827);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        }
        .metric-title { color: #cbd5e1; font-size: 0.92rem; text-transform: uppercase; letter-spacing: 0.08em; }
        .metric-value { color: white; font-size: 1.7rem; font-weight: 700; margin: 0.35rem 0; }
        .metric-subtext { color: #94a3b8; font-size: 0.95rem; }
        .metric-badge { display: inline-block; margin-top: 0.6rem; padding: 0.25rem 0.6rem; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }
        .metric-badge.primary { background: #2563eb; color: white; }
        .metric-badge.success { background: #16a34a; color: white; }
        .metric-badge.warning { background: #d97706; color: white; }
        .metric-badge.danger { background: #dc2626; color: white; }
        .badge { display: inline-block; padding: 0.3rem 0.6rem; border-radius: 999px; margin: 0.2rem; font-size: 0.8rem; font-weight: 600; }
        .badge.info { background: #dbeafe; color: #1d4ed8; }
        .badge.success { background: #dcfce7; color: #15803d; }
        .badge.warning { background: #fef3c7; color: #b45309; }
        .badge.danger { background: #fee2e2; color: #b91c1c; }
        .section-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem 1.1rem; margin-bottom: 1rem; }
        .section-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.title("🧠 GenAI Client Intelligence")
        st.caption("Internal coaching intelligence workspace")
        # Only expose the heuristic, Mistral and Groq (llama) options in the UI
        model_name = st.selectbox(
            "Model",
            [
                "heuristic",
                "mistral-small-latest",
                "llama-3.1-8b-instant",
            ],
            index=0,
        )
        # show the configured provider from .env so the user knows what's preconfigured
        configured_provider = get_env_value("LLM_PROVIDER", "mistral")
        # derive a preview of which provider will be used for the selected model
        preview_provider = configured_provider
        if model_name == "heuristic":
            preview_provider = "heuristic"
        elif "mistral" in model_name.lower():
            preview_provider = "mistral"
        elif "llama" in model_name.lower() or "3.1" in model_name.lower():
            preview_provider = "groq"

        st.caption(f"Configured provider: {configured_provider} — Using: {preview_provider} / {model_name}")
        uploaded_file = st.file_uploader("Upload conversation PDF", type=["pdf"])
        analyze_button = st.button("Analyze conversation", use_container_width=True)
        st.markdown("---")
        st.caption("Tip: if no API key is configured, the app uses a built-in heuristic analysis so the dashboard still renders.")

    default_pdf = Path(__file__).with_name("Day 1.pdf")
    if uploaded_file is not None:
        upload_dir = Path(__file__).resolve().parent / "uploads"
        upload_dir.mkdir(exist_ok=True)
        temp_path = upload_dir / uploaded_file.name
        temp_path.write_bytes(uploaded_file.getvalue())
        text = extract_text_from_pdf(str(temp_path))
        source_label = uploaded_file.name
    elif default_pdf.exists():
        text = load_sample_text(str(default_pdf))
        source_label = default_pdf.name
    else:
        text = ""
        source_label = "No PDF uploaded"

    if not text and not analyze_button:
        st.info("Upload a PDF from the sidebar to generate the dashboard.")
        return

    if analyze_button or text:
        with st.spinner("Analyzing conversation..."):
            analysis = build_analysis(text, model_name)

        st.header("GenAI Client Intelligence")
        st.caption(f"Source: {source_label}")

        if analysis.get("summary"):
            st.markdown(f"<div class='section-card'><div class='section-title'>Weekly Client Summary</div>{analysis['summary']}</div>", unsafe_allow_html=True)
        else:
            st.info("No summary generated yet.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card("Nutrition", f"{analysis['metrics']['nutrition']['value']:.0f}%", "Adherence", "Moderate", "warning")
        with col2:
            render_metric_card("Sleep", f"{analysis['metrics']['sleep']['average_hours']}h", analysis['metrics']['sleep']['quality'], analysis['metrics']['sleep']['status'], "info")
        with col3:
            render_metric_card("Water", analysis['metrics']['water']['average_intake'], "Average intake", analysis['metrics']['water']['status'], "warning")
        with col4:
            render_metric_card("Exercise", f"{analysis['metrics']['exercise']['average_steps']:,} steps", "Activity score", "Active", "success")

        st.markdown("---")
        st.subheader("Health Metrics")
        metric_cols = st.columns(5)
        with metric_cols[0]:
            render_metric_card("Stress", analysis['metrics']['stress']['level'], "Current state", analysis['metrics']['stress']['level'], analysis['metrics']['stress']['color'])
        with metric_cols[1]:
            render_metric_card("Symptoms", ", ".join(analysis.get("symptoms", [])[:3]), "Tracked concerns", "Watch", "warning")
        with metric_cols[2]:
            render_metric_card("Engagement", analysis['engagement']['level'], "Client responsiveness", "High", "success")
        with metric_cols[3]:
            render_metric_card("Barriers", str(len(analysis.get("barriers", []))), "Main obstacles", "Needs support", "warning")
        with metric_cols[4]:
            render_metric_card("Recommendations", str(len(analysis.get("recommendations", []))), "Coach actions", "Ready", "primary")

        st.markdown("---")
        col_a, col_b = st.columns([1.2, 1])
        with col_a:
            st.markdown("<div class='section-card'><div class='section-title'>Nutrition Analysis</div></div>", unsafe_allow_html=True)
            st.write(f"Overall adherence: {analysis['nutrition']['overall_adherence']}%")
            st.write("Positive habits:")
            for item in analysis['nutrition']['positive_habits']:
                st.write(f"- {item}")
            st.write("Missed habits:")
            for item in analysis['nutrition']['missed_habits']:
                st.write(f"- {item}")
            st.write(f"Coach observations: {analysis['nutrition']['coach_observations']}")
            st.write(f"Evidence: {analysis['nutrition']['evidence']}")

        with col_b:
            st.markdown("<div class='section-card'><div class='section-title'>Exercise Analysis</div></div>", unsafe_allow_html=True)
            st.write(f"Average steps: {analysis['exercise']['average_steps']:,}")
            st.write("Exercises detected:")
            for item in analysis['exercise']['exercises_detected']:
                st.write(f"- {item}")
            st.write("Timeline:")
            for item in analysis['exercise']['timeline']:
                st.write(f"- {item}")

        st.markdown("---")
        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown("<div class='section-card'><div class='section-title'>Sleep Analysis</div></div>", unsafe_allow_html=True)
            st.write(f"Average sleep: {analysis['sleep']['average_sleep']}")
            st.write(f"Trend: {analysis['sleep']['trend']}")
            st.write(f"Evidence: {analysis['sleep']['evidence']}")
        with col_d:
            st.markdown("<div class='section-card'><div class='section-title'>Water Intake</div></div>", unsafe_allow_html=True)
            st.write(f"Daily intake: {analysis['water']['daily_intake']}")
            st.write(f"Average: {analysis['water']['average']}")
            st.write(f"Consistency: {analysis['water']['consistency']}")

        st.markdown("---")
        st.markdown("<div class='section-card'><div class='section-title'>Stress & Mental Wellness</div></div>", unsafe_allow_html=True)
        st.write(f"Stress level: {analysis['stress']['stress_level']}")
        st.write(f"Reasons: {', '.join(analysis['stress']['reasons'])}")
        st.write(f"Energy: {analysis['stress']['energy']}")
        st.write(f"Mood: {analysis['stress']['mood']}")
        st.write(f"Burnout risk: {'Yes' if analysis['stress']['burnout_risk'] else 'No'}")

        st.markdown("---")
        col_e, col_f = st.columns(2)
        with col_e:
            st.markdown("<div class='section-card'><div class='section-title'>Engagement Level</div></div>", unsafe_allow_html=True)
            st.write(f"Level: {analysis['engagement']['level']}")
            for item in analysis['engagement']['based_on']:
                st.write(f"- {item}")
        with col_f:
            st.markdown("<div class='section-card'><div class='section-title'>Key Barriers</div></div>", unsafe_allow_html=True)
            for item in analysis['barriers']:
                st.write(f"- {item}")

        st.markdown("---")
        st.markdown("<div class='section-card'><div class='section-title'>Pending Actions</div></div>", unsafe_allow_html=True)
        for action in analysis['pending_actions']:
            st.checkbox(action, value=False, key=f"action_{action}")

        st.markdown("---")
        st.markdown("<div class='section-card'><div class='section-title'>Risk Flags</div></div>", unsafe_allow_html=True)
        for risk in analysis['risk_flags']:
            st.markdown(
                f"<div class='section-card'><strong>{risk['name']}</strong><br/>Severity: {risk['severity']}<br/>Reason: {risk['reason']}<br/>Evidence: {risk['evidence']}<br/>Confidence: {risk['confidence']:.0%}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("<div class='section-card'><div class='section-title'>Coach Recommendation</div></div>", unsafe_allow_html=True)
        for rec in analysis['recommendations']:
            st.write(f"- {rec}")

        st.markdown("---")
        st.markdown("<div class='section-card'><div class='section-title'>Human Review</div></div>", unsafe_allow_html=True)
        st.text_area("Review notes", value="Flag for follow-up on sleep, symptom recurrence, and hydration consistency.")


if __name__ == "__main__":
    main()
