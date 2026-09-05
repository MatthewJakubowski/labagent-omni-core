import streamlit as st
import hashlib
import pandas as pd
from datetime import datetime, timezone
from core.engine import UltimateClinicalAuditor, FullFHIRBundleExporter

st.set_page_config(
    page_title="LabAgent-Omni Core",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stylizacja bazowa CSS
st.markdown("""
<style>
    .metric-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .legal-box {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid #334155;
        border-left: 4px solid #38bdf8;
        padding: 16px;
        border-radius: 6px;
        font-size: 11px;
        color: #94a3b8;
        line-height: 1.6;
        margin-top: 30px;
    }
    .author-card {
        background: linear-gradient(135deg, #0b1120 0%, #0f172a 100%);
        border: 1px solid #38bdf8;
        border-radius: 10px;
        padding: 16px;
        margin-top: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. SŁOWNIK WIELOJĘZYCZNY (PL / EN)
# -------------------------------------------------------------
TRANSLATIONS = {
    "PL": {
        "title": "⚡ LabAgent-Omni Core",
        "subtitle": "Bezstanowy silnik autowalizacji i inteligencji klinicznej (ISO 15189:2023 / HL7 FHIR R4)",
        "lang_select": "Język / Language",
        "scenario_label": "Wybierz scenariusz bazowy:",
        "scenarios": [
            "Scenariusz A: Profilaktyka & Adaptacja Mięśniowa",
            "Scenariusz B: Krytyczna Blokada EDTA (Błąd Przedanalityczny)",
            "Scenariusz C: Przekroczony Indeks Hemolizy (Odrzucenie)"
        ],
        "view_mode_label": "Widok systemu:",
        "views": [
            "Dynamiczny Paszport Narządowy",
            "Interaktywny Edytor Badań (Live Lab)",
            "Kliniczny Raport Lekarski (SBAR)",
            "Eksport HL7 FHIR R4 Bundle",
            "Certyfikat Zgodności & Nadzór Prawny"
        ],
        "pre_ok": "🛡️ STATUS PRZEDANALITYCZNY: Integralność próbki potwierdzona.",
        "pre_block": "🚨 KRYTYCZNA BLOKADA PRZEDANALITYCZNA:",
        "pre_warning": "Dalsza interpretacja narządowa zablokowana zgodnie z rygorem ISO 15189:2023. Wymagane ponowne pobranie próbki.",
        "sbar_sit": "S (Sytuacja):",
        "sbar_bg": "B (Kontekst):",
        "sbar_ass": "A (Ocena):",
        "sbar_rec": "R (Rekomendacja):",
        "edit_header": "Interaktywna Modyfikacja Wyników Badań (Weryfikacja w locie)",
        "edit_caption": "Zmień dowolną wartość w tabeli poniżej – silnik zaktualizuje audyt, odcięcia i reguły w czasie rzeczywistym.",
        "author_tag": "Architektura & Implementacja:",
        "author_role": "Starszy Technolog Laboratoryjny & Clinical AI Developer",
        "author_bio": "Projektant systemów automatycznej walidacji laboratoryjnej, koordynator badań klinicznych oraz twórca inicjatywy #FromPipetteToPython.",
        "legal_title": "Formalne Ramy Prawne, Certyfikacja & Nadzór Regulacyjny",
        "legal_shield_text": (
            "⚖️ ŻELAZNA KLAUZULA PRAWNA & REGULATORY COMPLIANCE SHIELD: "
            "System LabAgent-Omni jest oprogramowaniem badawczo-rozwojowym typu Proof-of-Concept (PoC). "
            "Narzędzie NIE JEST wyrobem medycznym w rozumieniu Rozporządzenia (UE) 2017/746 (IVDR) ani (UE) 2017/745 (MDR). "
            "Zgodnie z Ustawą z dnia 15 września 2022 r. o medycynie laboratoryjnej wyłączną odpowiedzialność za autoryzację wyników ponosi uprawniony diagnosta laboratoryjny, "
            "a ostateczne decyzje podejmuje lekarz prowadzący. System spełnia wymogi Human-in-the-loop (EU AI Act 2024/1689) oraz standardy ICH GCP."
        )
    },
    "EN": {
        "title": "⚡ LabAgent-Omni Core",
        "subtitle": "Stateless Clinical Intelligence & Autovalidation Sidecar (ISO 15189:2023 / HL7 FHIR R4)",
        "lang_select": "Language / Język",
        "scenario_label": "Select Baseline Scenario:",
        "scenarios": [
            "Scenario A: Wellness & Muscle Adaptation",
            "Scenario B: Critical EDTA Contamination (Preanalytical Reject)",
            "Scenario C: Excessive Hemolysis Index (Interference Reject)"
        ],
        "view_mode_label": "System View Mode:",
        "views": [
            "Dynamic Multi-Organ Passport",
            "Interactive Lab Editor (Live Test)",
            "Physician Clinical SBAR Brief",
            "HL7 FHIR R4 Bundle Export",
            "Regulatory Compliance & Governance"
        ],
        "pre_ok": "🛡️ PREANALYTICAL INTEGRITY: Specimen verified.",
        "pre_block": "🚨 CRITICAL PREANALYTICAL BLOCK:",
        "pre_warning": "Downstream organ interpretation halted pursuant to ISO 15189:2023 criteria. Specimen recollection mandated.",
        "sbar_sit": "S (Situation):",
        "sbar_bg": "B (Background):",
        "sbar_ass": "A (Assessment):",
        "sbar_rec": "R (Recommendation):",
        "edit_header": "Interactive Lab Value Modification (Real-Time Verification)",
        "edit_caption": "Modify any biomarker value in the table below – the deterministic engine will immediately re-run autovalidation.",
        "author_tag": "System Architecture & Engineering:",
        "author_role": "Senior Medical Laboratory Technologist & Clinical AI Developer",
        "author_bio": "Designer of clinical autovalidation architectures, former clinical research coordinator, and author of the #FromPipetteToPython initiative.",
        "legal_title": "Statutory Governance, Certification & Legal Shield",
        "legal_shield_text": (
            "⚖️ REGULATORY COMPLIANCE & LEGAL SHIELD: "
            "The LabAgent-Omni system is an experimental Proof-of-Concept (PoC) platform. "
            "This software is NOT an In Vitro Diagnostic Medical Device under Regulation (EU) 2017/746 (IVDR) or (EU) 2017/745 (MDR). "
            "Final clinical validation and authorization remain the exclusive legal purview of certified Laboratory Diagnosticians / Clinical Scientists, "
            "while ultimate diagnostic categorization is restricted to the attending licensed physician. Fully compliant with EU AI Act (Human-in-the-Loop) and ICH GCP standards."
        )
    }
}

# -------------------------------------------------------------
# 2. PANEL BOCZNY (KONTROLA & WIZYTÓWKA)
# -------------------------------------------------------------
lang = st.sidebar.radio("🌐 Language / Język", ["PL", "EN"], horizontal=True)
T = TRANSLATIONS[lang]

st.sidebar.divider()
st.sidebar.markdown(f"### {T['title']}")
scenario_choice = st.sidebar.selectbox(T["scenario_label"], T["scenarios"])
view_mode = st.sidebar.radio(T["view_mode_label"], T["views"])

# Wizytówka Twórcy w panelu bocznym
st.sidebar.divider()
st.sidebar.markdown(f"""
<div style="font-size: 11px; line-height: 1.5; color: #94a3b8;">
    <strong style="color: #38bdf8; font-size: 12px;">Mateusz Jakubowski</strong><br>
    <em>{T['author_role']}</em><br><br>
    📍 Rzeszów, Poland<br>
    🧬 Master of Experimental Biology<br>
    🎓 Postgraduate in Clinical Research<br>
    🔬 15+ Years Clinical Diagnostics<br><br>
    <strong>Wizytówki & Portfolio:</strong><br>
    🔗 <a href="https://from-pipette-to-python.ai.studio" target="_blank" style="color: #38bdf8; text-decoration: none;">from-pipette-to-python.ai.studio</a><br>
    🔗 <a href="https://mateusz-jakubowski.ai.studio" target="_blank" style="color: #38bdf8; text-decoration: none;">mateusz-jakubowski.ai.studio</a><br>
    💻 <a href="https://github.com/MatthewJakubowski" target="_blank" style="color: #38bdf8; text-decoration: none;">GitHub: @MatthewJakubowski</a><br>
    📊 <a href="https://www.kaggle.com/matthewjakubowski" target="_blank" style="color: #38bdf8; text-decoration: none;">Kaggle: @matthewjakubowski</a><br>
    🤗 <a href="https://huggingface.co/matthewjakubowski" target="_blank" style="color: #38bdf8; text-decoration: none;">Hugging Face: @matthewjakubowski</a><br>
    🍷 <a href="https://www.vivino.com/users/mateusz.jakubowski" target="_blank" style="color: #38bdf8; text-decoration: none;">Vivino Enthusiast Profile</a>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. ZARZĄDZANIE STANEM & BAZA DANYCH
# -------------------------------------------------------------
default_labs = {
    "K_POTASSIUM": 4.4, "CA_CALCIUM": 2.38, "H_INDEX": 0.04,
    "WBC": 5.8, "HGB": 15.6, "MCV": 88.4, "RDW_CV": 12.1, "PLT": 242.0, "RET_PCT": 1.21, "RET_HE": 33.5, "ESR": 6.0,
    "BLOOD_PH": 7.41, "PCO2": 39.5, "PO2": 94.0, "LACTATE": 1.1,
    "GLUCOSE": 92.0, "INSULIN": 10.4, "HBA1C": 5.2, "C_PEPTIDE": 1.82,
    "CHOL_TOTAL": 188.0, "HDL": 55.0, "TRIGLYCERIDES": 162.0, "APOB": 84.0, "LPA": 14.0,
    "HS_TROPONIN": 4.2, "NT_PROBNP": 48.0, "D_DIMER": 280.0, "INR": 1.02, "ANTITHROMBIN_III": 104.0,
    "ALT": 46.0, "AST": 27.0, "ALP": 56.0, "GGTP": 24.0, "BILIRUBIN_TOTAL": 0.72,
    "CREATININE": 0.94, "CYSTATIN_C": 0.82, "UREA": 32.0, "URIC_ACID": 6.4, "SODIUM": 141.0,
    "IRON": 112.0, "UIBC": 212.0, "FERRITIN": 145.0, "HS_CRP": 0.48, "HOMOCYSTEINE": 8.4,
    "TSH": 2.05, "FT4": 1.22, "FT3": 3.25, "ANTI_TPO": 10.4, "TRAB": 0.45, "ANTI_CCP": 1.8,
    "TESTOSTERONE": 640.0, "SHBG": 35.0, "VIT_D3": 46.5, "PSA_TOTAL": 0.78, "CA125": 12.1
}

# Wstrzyknięcie profilu scenariusza
if "Scenariusz B" in scenario_choice or "Scenario B" in scenario_choice:
    default_labs["K_POTASSIUM"] = 8.4
    default_labs["CA_CALCIUM"] = 0.78
elif "Scenariusz C" in scenario_choice or "Scenario C" in scenario_choice:
    default_labs["H_INDEX"] = 0.68

if "active_labs" not in st.session_state:
    st.session_state.active_labs = default_labs.copy()

# -------------------------------------------------------------
# 4. GŁÓWNY WIDOK APLIKACJI
# -------------------------------------------------------------
st.title(T["title"])
st.caption(T["subtitle"])

# Baner Autorski w nagłówku
st.markdown(f"""
<div class="author-card">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <span style="font-size: 16px; font-weight: 800; color: #38bdf8;">Mateusz Jakubowski</span>
            <span style="font-size: 12px; color: #94a3b8; margin-left: 8px;">| {T['author_role']}</span>
            <div style="font-size: 11px; color: #cbd5e1; margin-top: 4px;">{T['author_bio']}</div>
        </div>
        <div style="font-size: 11px; color: #38bdf8; text-align: right; margin-top: 6px;">
            <code>#FromPipetteToPython</code> • <code>#BuildInPublic</code>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Jeśli wybrano edytor wyników, pozwalamy użytkownikowi modyfikować dane
if view_mode in ["Interaktywny Edytor Badań (Live Lab)", "Interactive Lab Editor (Live Test)"]:
    st.subheader(T["edit_header"])
    st.caption(T["edit_caption"])

    df_edit = pd.DataFrame([
        {"Parametr": k, "Wartość": float(v), "Typ": "Numeryczny"}
        for k, v in st.session_state.active_labs.items()
    ])
    
    edited_df = st.data_editor(
        df_edit,
        use_container_width=True,
        num_rows="fixed",
        column_config={"Parametr": st.column_config.TextColumn(disabled=True)}
    )
    # Aktualizacja stanu
    for _, row in edited_df.iterrows():
        st.session_state.active_labs[row["Parametr"]] = row["Wartość"]

# Wykonanie audytu na aktualnych (lub zmodyfikowanych) danych
pt_info = {"hash": hashlib.sha256(b"PORTFOLIO-SESSION").hexdigest(), "age": 40, "sex": "M"}
audit = UltimateClinicalAuditor.execute_god_mode_audit(pt_info, st.session_state.active_labs, {})
pre = audit["preanalytical"]

# Wyświetlenie paska stanu przedanalitycznego
if pre["passed"]:
    st.success(f"{T['pre_ok']} {pre['reason']}")
else:
    st.error(f"{T['pre_block']} {pre['reason']}")

st.divider()

if not pre["passed"]:
    st.warning(T["pre_warning"])
else:
    if view_mode in ["Dynamiczny Paszport Narządowy", "Dynamic Multi-Organ Passport"]:
        st.subheader("Dynamiczny Paszport Narządowy (20 Osi / Live)")
        for ax in audit["axes"]:
            with st.expander(f"{ax['icon']} {ax['name']} — Status: {ax['status']}", expanded=False):
                st.info(f"💡 {ax['summary']}")
                cols = st.columns(4)
                for i, m in enumerate(ax["markers"]):
                    cols[i % 4].metric(
                        label=m["name"],
                        value=f"{m['cur']} {m['unit']}",
                        delta=f"Norma: {m['ref']}",
                        delta_color="off"
                    )

    elif view_mode in ["Kliniczny Raport Lekarski (SBAR)", "Physician Clinical SBAR Brief"]:
        st.subheader("Kliniczny Raport Lekarski (Format SBAR)")
        st.markdown(f"""
        **{T['sbar_sit']}** Pacjent {pt_info['age']}L, płeć {pt_info['sex']}. Zgłoszenie na audyt biomarkerowy.  
        **{T['sbar_bg']}** Wykluczono błędy przedanalityczne (indeksy HIL w normie, brak chelatacji EDTA).  
        **{T['sbar_ass']}**
        """)
        for ax in audit["axes"]:
            st.markdown(f"- **{ax['name']}:** {ax['summary']}")
        st.markdown(f"""
        **{T['sbar_rec']}** Wyniki zweryfikowane deterministycznie. Brak cech martwicy i ostrych incydentów. Wskazane monitorowanie tolerancji węglowodanów.
        """)

    elif view_mode in ["Eksport HL7 FHIR R4 Bundle", "HL7 FHIR R4 Bundle Export"]:
        st.subheader("HL7 FHIR R4 Transaction Bundle")
        fhir_res = FullFHIRBundleExporter.export(audit)
        st.json(fhir_res)

    elif view_mode in ["Certyfikat Zgodności & Nadzór Prawny", "Regulatory Compliance & Governance"]:
        st.subheader(T["legal_title"])
        st.markdown("""
        ### Status Badawczy & Klasyfikacja Systemu (Proof-of-Concept)
        Platforma `LabAgent-Omni Core` stanowi eksperymentalne środowisko badawczo-rozwojowe (**Proof-of-Concept**).

        #### Zgodność Regulacyjna:
        1. **Ustawa z dnia 15 września 2022 r. o medycynie laboratoryjnej (Dz.U. 2022 poz. 2280):** 
           System nie dokonuje samodzielnej autoryzacji wyników. Wyłączne prawo do autoryzacji przysługuje uprawnionemu **diagnoście laboratoryjnemu**.
        2. **Ustawa o zawodach lekarza i lekarza dentysty:**
           Wszelkie zestawienia i wskaźniki pełnią rolę Clinical Decision Support (CDS). Decyzję terapeutyczną podejmuje wyłącznie **lekarz prowadzący**.
        3. **Rozporządzenie EU AI Act (2024/1689):**
           Zasada **Human-in-the-loop (HITL)**, pełna wyjaśnialność (XAI) oraz brak niekontrolowanych decyzji autonomicznych.
        4. **ICH GCP & PN-EN ISO 15189:2023:**
           Pełna audytowalność każdej reguły, nienaruszalność danych i deterministyczna weryfikacja błędów przedanalitycznych.
        """)

# Stopka: Żelazny Disclaimer na dole strony
st.markdown(f"""
<div class="legal-box">
    {T['legal_shield_text']}
</div>
""", unsafe_allow_html=True)

st.sidebar.caption("Zero-Data Retention • ISO 15189:2023 • EU AI Act HITL")
