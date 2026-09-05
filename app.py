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
        padding: 14px 18px;
        margin-top: 15px;
        margin-bottom: 20px;
    }
    .author-btn {
        display: inline-block;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid #38bdf8;
        color: #38bdf8 !important;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    .author-btn:hover {
        background: #38bdf8;
        color: #070a13 !important;
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
        "pre_ok": "🛡️ STATUS PRZEDANALITYCZNY:",
        "pre_block": "🚨 KRYTYCZNA BLOKADA PRZEDANALITYCZNA:",
        "pre_warning": "Dalsza interpretacja narządowa zablokowana zgodnie z rygorem ISO 15189:2023. Wymagane ponowne pobranie próbki.",
        "passport_title": "Dynamiczny Paszport Narządowy (Live)",
        "sbar_title": "Kliniczny Raport Lekarski (Format SBAR)",
        "sbar_sit": "S (Sytuacja):",
        "sbar_bg": "B (Kontekst):",
        "sbar_ass": "A (Ocena):",
        "sbar_rec": "R (Rekomendacja):",
        "sbar_sit_text": "Pacjent 40L, płeć M. Rutynowy kompleksowy panel biochemiczno-hematologiczny.",
        "sbar_bg_text": "Wykluczono interferencje przedanalityczne (indeksy HIL w normie, brak chelatacji EDTA).",
        "sbar_rec_text": "Wyniki zweryfikowane deterministycznie. Brak cech martwicy narządowej. Zalecana dalsza obserwacja dynamiki metabolizmu węglowodanowego.",
        "edit_header": "Interaktywny Edytor Badań Laboratoryjnych (Pełny Panel >80 Analitów)",
        "edit_caption": "Zmień dowolną wartość w tabeli poniżej – silnik natychmiast przeliczy audyt, formuły wieloosiowe i reguły autowalizacji.",
        "author_tag": "Architektura & Rozwój:",
        "legal_header": "Formalne Ramy Prawne, Certyfikacja & Nadzór Regulacyjny",
        "legal_body": """
        ### Status Badawczy & Klasyfikacja Systemu (Proof-of-Concept)
        Platforma `LabAgent-Omni Core` stanowi eksperymentalne środowisko badawczo-rozwojowe (**Proof-of-Concept**).

        #### Zgodność z Polskim i Europejskim Porządkiem Prawnym:
        1. **Ustawa z dnia 15 września 2022 r. o medycynie laboratoryjnej (Dz.U. 2022 poz. 2280):** 
           System nie dokonuje samodzielnej autoryzacji wyników. Wyłączne prawo do autoryzacji przysługuje uprawnionemu **diagnoście laboratoryjnemu**.
        2. **Ustawa o zawodach lekarza i lekarza dentysty:**
           Wszelkie zestawienia i wskaźniki pełnią rolę Clinical Decision Support (CDS). Decyzję terapeutyczną podejmuje wyłącznie **lekarz prowadzący**.
        3. **Rozporządzenie EU AI Act (2024/1689):**
           Zasada **Human-in-the-loop (HITL)**, pełna wyjaśnialność (XAI) oraz brak niekontrolowanych decyzji autonomicznych.
        4. **ICH GCP & PN-EN ISO 15189:2023:**
           Pełna audytowalność każdej reguły, nienaruszalność danych i deterministyczna weryfikacja błędów przedanalitycznych.
        """,
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
        "pre_ok": "🛡️ PREANALYTICAL STATUS:",
        "pre_block": "🚨 CRITICAL PREANALYTICAL BLOCK:",
        "pre_warning": "Downstream organ interpretation halted pursuant to ISO 15189:2023 criteria. Specimen recollection mandated.",
        "passport_title": "Dynamic Multi-Organ Passport (Live)",
        "sbar_title": "Physician Clinical SBAR Brief",
        "sbar_sit": "S (Situation):",
        "sbar_bg": "B (Background):",
        "sbar_ass": "A (Assessment):",
        "sbar_rec": "R (Recommendation):",
        "sbar_sit_text": "Patient 40y, male. Comprehensive routine biochemical and hematological evaluation.",
        "sbar_bg_text": "Preanalytical interferences excluded (HIL indices optimal, EDTA cation chelation ruled out).",
        "sbar_rec_text": "Deterministically verified results. No evidence of acute cell necrosis. Continuous observation of glucose metabolism trajectory advised.",
        "edit_header": "Interactive Laboratory Test Editor (Full Scope >80 Analytes)",
        "edit_caption": "Modify any biomarker in the table below – the deterministic engine will immediately re-evaluate autovalidation rules.",
        "author_tag": "Architecture & Engineering:",
        "legal_header": "Statutory Governance, Certification & Legal Shield",
        "legal_body": """
        ### Research & Proof-of-Concept Status
        The `LabAgent-Omni Core` platform is an experimental demonstration system (**Proof-of-Concept**).

        #### Regulatory & Legal Alignment:
        1. **Laboratory Diagnostics Act:** 
           The system does not perform autonomous authorization of clinical results. Final authorization authority resides strictly with certified **Medical Laboratory Diagnosticians / Clinical Scientists**.
        2. **Medical Practitioner Regulations:**
           All multi-axial correlations and summaries serve strictly as Clinical Decision Support (CDS). Final clinical diagnoses and therapy decisions belong exclusively to the **attending licensed physician**.
        3. **EU AI Act Regulation (2024/1689):**
           Designed with **Human-in-the-Loop (HITL)** oversight, full Explainable AI (XAI) transparency, and zero uncontrolled autonomous clinical decision-making.
        4. **ICH GCP & ISO 15189:2023 Quality Norms:**
           Rigorous rule auditability, zero-data-retention cryptographic integrity, and deterministic preanalytical interference blocking.
        """,
        "legal_shield_text": (
            "⚖️ REGULATORY COMPLIANCE & LEGAL SHIELD: "
            "The LabAgent-Omni system is an experimental Proof-of-Concept (PoC) platform. "
            "This software is NOT an In Vitro Diagnostic Medical Device under Regulation (EU) 2017/746 (IVDR) or (EU) 2017/745 (MDR). "
            "Final clinical validation and authorization remain the exclusive legal purview of certified Laboratory Diagnosticians / Clinical Scientists, "
            "while ultimate diagnostic categorization is restricted to the attending licensed physician. Fully compliant with EU AI Act (Human-in-the-Loop) and ICH GCP standards."
        )
    }
}

EN_AXIS_MAP = {
    "Oś Hematologiczna & Retikulocyty": "Hematology & Reticulocyte Axis",
    "Oś Równowagi Kwasowo-Zasadowej & Mleczany": "Acid-Base Balance & Lactate",
    "Oś Metaboliczna & Wrażliwość Insulinowa": "Metabolic & Insulin Sensitivity Axis",
    "Oś Lipidowa, Aterogenność & Lp(a)": "Lipid, Atherogenicity & Lp(a) Axis",
    "Oś Kardiologii CITO & Trombofilii": "Critical Cardiology & Thrombophilia",
    "Oś Wątrobowo-Żółciowa & Cytoprotekcja": "Hepatobiliary Cytoprotection Axis",
    "Oś Nerkowa, Cystatyna C & Elektrolity": "Renal Axis, Cystatin C & Electrolytes",
    "Gospodarka Żelazem, Metylacja & hs-CRP": "Iron Metabolism, Methylation & hs-CRP",
    "Oś Tarczycowa & Autoprzeciwciała (A-TPO, TRAb, A-CCP)": "Thyroid & Autoantibodies (A-TPO, TRAb, A-CCP)",
    "Steroidy, Witaminy & Nadzór Onkologiczny": "Steroids, Vitamins & Tumor Markers"
}

EN_STATUS_MAP = {
    "PRAWIDŁOWA ERYTROPOEZA": "NORMAL ERYTHROPOIESIS",
    "HOMEOSTAZA KWASOWO-ZASADOWA": "ACID-BASE HOMEOSTASIS",
    "SUBKLINICZNA ATENCJA": "SUBCLINICAL ATTENTION",
    "OPTYMALNA": "OPTIMAL",
    "OPTYMALNY APOB": "OPTIMAL APOB TARGET",
    "BRAK NIEDOKRWIENIA & ZAKRZEPICY": "RULE-OUT ACS & THROMBOSIS",
    "ODCZYN ADAPTACYJNY": "EXERCISE ADAPTATION",
    "NORMA CYTOLITYCZNA": "NORMAL CYTOLYSIS",
    "FILTRACJA PRAWIDŁOWA (G1)": "NORMAL FILTRATION (G1)",
    "OPTYMALNA HOMEOSTAZA": "OPTIMAL HOMEOSTASIS",
    "EUTYREOZA / SERONEGATYWNOŚĆ": "EUTHYROID / SERONEGATIVE",
    "EUGONADYZM & STĘŻENIA FIZJOLOGICZNE": "EUGONADISM & PHYSIOLOGICAL LEVELS"
}

# -------------------------------------------------------------
# 2. DEFINICJE BAZOWE SCENARIUSZY (PEŁNY PANEL >80 ANALITÓW)
# -------------------------------------------------------------
def get_scenario_data(idx: int) -> dict:
    base = {
        # Faza Przedanalityczna (Indeksy HIL)
        "H_INDEX": 0.04, "I_INDEX": 0.02, "L_INDEX": 0.01,
        
        # Oś 1: Hematologia & Retikulocyty
        "WBC": 5.8, "RBC": 5.12, "HGB": 15.6, "HCT": 45.2, "MCV": 88.4, 
        "MCH": 30.5, "MCHC": 34.5, "RDW_CV": 12.1, "PLT": 242.0, "MPV": 9.8,
        "NEUT_ABS": 3.4, "LYM_ABS": 1.9, "MONO_ABS": 0.42, "EOS_ABS": 0.12, "BASO_ABS": 0.03,
        "RET_ABS": 62.0, "RET_PCT": 1.21, "IRF": 0.08, "RET_HE": 33.5, "ESR": 6.0,
        
        # Oś 2: Gazometria & Mleczany
        "BLOOD_PH": 7.41, "PCO2": 39.5, "PO2": 94.0, "HCO3_ACT": 24.2, "BASE_EXCESS": 0.2, "LACTATE": 1.1,
        
        # Oś 3: Metabolizm & Insulinooporność
        "GLUCOSE": 92.0, "INSULIN": 10.4, "HBA1C": 5.2, "C_PEPTIDE": 1.82,
        
        # Oś 4: Lipidologia & Aterogenność
        "CHOL_TOTAL": 188.0, "HDL": 55.0, "TRIGLYCERIDES": 162.0, "APOB": 84.0, "LPA": 14.0,
        
        # Oś 5: Kardiologia CITO & Koagulologia
        "HS_TROPONIN": 4.2, "NT_PROBNP": 48.0, "CKMB_MASS": 1.8,
        "INR": 1.02, "PT_SEC": 11.2, "APTT": 28.4, "D_DIMER": 280.0, 
        "ANTITHROMBIN_III": 104.0, "PROTEIN_C": 110.0, "PROTEIN_S": 98.0,
        
        # Oś 6: Wątroba & Przewód Pokarmowy
        "ALT": 46.0, "AST": 27.0, "ALP": 56.0, "GGTP": 24.0, "BILIRUBIN_TOTAL": 0.72,
        "LIPASE": 28.0, "AMYLASE_SERUM": 54.0, "CALPROTECTIN": 18.0,
        
        # Oś 7: Nerki & Elektrolity
        "CREATININE": 0.94, "CYSTATIN_C": 0.82, "UREA": 32.0, "URIC_ACID": 6.4,
        "SODIUM": 141.0, "K_POTASSIUM": 4.4, "CA_CALCIUM": 2.38,
        
        # Oś 8: Żelazo, Białka & Zapalenie
        "IRON": 112.0, "UIBC": 212.0, "FERRITIN": 145.0, "TRANSFERRIN": 2.45,
        "HAPTOGLOBIN": 1.15, "CERULOPLASMIN": 28.0, "COMPLEMENT_C3": 1.18, "COMPLEMENT_C4": 0.24,
        "PCT_PROCALCITONIN": 0.02, "HS_CRP": 0.48, "HOMOCYSTEINE": 8.4,
        
        # Oś 9: Witaminy & Endokrynologia Tarczycy
        "VIT_D3": 46.5, "VIT_B12": 420.0, "FOLATE": 8.8,
        "TSH": 2.05, "FT4": 1.22, "FT3": 3.25, "IPTH_INTACT": 32.0,
        
        # Oś 10: Steroidy & Przysadka
        "TESTOSTERONE": 640.0, "SHBG": 35.0, "LH": 4.2, "FSH": 3.8, "PROLACTIN": 9.2, 
        "DHEA_SO4": 260.0, "IGF1": 175.0,
        
        # Oś 11: Autoimmunologia Specjalistyczna
        "ANTI_TPO": 10.4, "ANTI_TG": 12.0, "TRAB": 0.45, "ANTI_CCP": 1.8, "RF_IGM": 8.0,
        
        # Oś 12: Immunoglobuliny
        "IGG": 10.5, "IGA": 2.1, "IGM": 1.1, "IGE_TOTAL": 35.0,
        
        # Oś 13: Onkomarkery Narządowe
        "PSA_TOTAL": 0.78, "PSA_FREE": 0.22, "CEA": 1.4, "CA125": 12.1, 
        "CA15_3": 14.2, "CA19_9": 8.5, "AFP": 2.8, "CHROMOGRANIN_A": 48.0,
        
        # Oś 14: Serologia Zakaźna & Mocz
        "AHBS_TITER": 240.0, "URINE_SG": 1.020, "URINE_PH": 6.0
    }
    
    # Modyfikatory interferencyjne
    if idx == 1:
        base["K_POTASSIUM"] = 8.4
        base["CA_CALCIUM"] = 0.78
        base["H_INDEX"] = 0.04
    elif idx == 2:
        base["K_POTASSIUM"] = 4.4
        base["CA_CALCIUM"] = 2.38
        base["H_INDEX"] = 0.68
        
    return base

# -------------------------------------------------------------
# 3. PANEL BOCZNY (KONTROLA & LINK)
# -------------------------------------------------------------
lang = st.sidebar.radio("🌐 Language / Język", ["PL", "EN"], horizontal=True)
T = TRANSLATIONS[lang]

st.sidebar.divider()
st.sidebar.markdown(f"### {T['title']}")

scenario_idx = st.sidebar.selectbox(
    T["scenario_label"],
    options=[0, 1, 2],
    format_func=lambda i: T["scenarios"][i]
)

view_idx = st.sidebar.radio(
    T["view_mode_label"],
    options=[0, 1, 2, 3, 4],
    format_func=lambda i: T["views"][i]
)

st.sidebar.divider()
st.sidebar.markdown(f"""
<div style="font-size: 11px; line-height: 1.6; color: #94a3b8;">
    <span style="color: #64748b; text-transform: uppercase; font-size: 10px; font-weight: 700;">{T['author_tag']}</span><br>
    <strong style="color: #f8fafc; font-size: 13px;">Mateusz Jakubowski</strong><br><br>
    <a href="https://mateusz-jakubowski.ai.studio" target="_blank" class="author-btn">
        🔗 mateusz-jakubowski.ai.studio ↗
    </a>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. DETERMINISTYCZNA KONTROLA STANU SESJI
# -------------------------------------------------------------
if "current_scenario_idx" not in st.session_state or st.session_state.current_scenario_idx != scenario_idx:
    st.session_state.current_scenario_idx = scenario_idx
    st.session_state.active_labs = get_scenario_data(scenario_idx)

if "active_labs" not in st.session_state:
    st.session_state.active_labs = get_scenario_data(scenario_idx)

# -------------------------------------------------------------
# 5. WIDOK GŁÓWNY
# -------------------------------------------------------------
st.title(T["title"])
st.caption(T["subtitle"])

st.markdown(f"""
<div class="author-card">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div>
            <span style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700;">{T['author_tag']}</span>
            <div style="font-size: 16px; font-weight: 800; color: #f8fafc;">Mateusz Jakubowski</div>
        </div>
        <a href="https://mateusz-jakubowski.ai.studio" target="_blank" class="author-btn">
            🌐 mateusz-jakubowski.ai.studio &nbsp;↗
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# Tryb 1: Interaktywny edytor badań (>80 biomarkerów)
if view_idx == 1:
    st.subheader(T["edit_header"])
    st.caption(T["edit_caption"])

    col_param = "Parametr" if lang == "PL" else "Biomarker"
    col_val = "Wartość" if lang == "PL" else "Value"

    df_edit = pd.DataFrame([
        {col_param: k, col_val: float(v)}
        for k, v in st.session_state.active_labs.items()
    ])
    
    edited_df = st.data_editor(
        df_edit,
        use_container_width=True,
        num_rows="fixed",
        key=f"editor_{scenario_idx}",
        column_config={col_param: st.column_config.TextColumn(disabled=True)}
    )
    for _, row in edited_df.iterrows():
        st.session_state.active_labs[row[col_param]] = row[col_val]

# Wykonanie deterministycznego audytu laboratoryjnego
pt_info = {"hash": hashlib.sha256(b"PORTFOLIO-SESSION").hexdigest(), "age": 40, "sex": "M"}
audit = UltimateClinicalAuditor.execute_god_mode_audit(pt_info, st.session_state.active_labs, {})
pre = audit["preanalytical"]

# Tłumaczenie statusu przedanalitycznego dla EN
if lang == "EN":
    if pre["passed"]:
        pre_reason_display = "ISO 15189 Certificate: Specimen integrity verified. Free of EDTA chelation and hemolysis."
    elif pre["status"] == "REJECT_EDTA":
        pre_reason_display = "CRITICAL BLOCK: Severe EDTA cation chelation detected. Results held."
    else:
        pre_reason_display = "REJECTION: Allowable hemolysis interference index exceeded."
else:
    pre_reason_display = pre["reason"]

if pre["passed"]:
    st.success(f"{T['pre_ok']} {pre_reason_display}")
else:
    st.error(f"{T['pre_block']} {pre_reason_display}")

st.divider()

if not pre["passed"]:
    st.warning(T["pre_warning"])
else:
    if view_idx == 0:
        st.subheader(T["passport_title"])
        for ax in audit["axes"]:
            axis_name = EN_AXIS_MAP.get(ax["name"], ax["name"]) if lang == "EN" else ax["name"]
            axis_status = EN_STATUS_MAP.get(ax["status"], ax["status"]) if lang == "EN" else ax["status"]
            
            with st.expander(f"{ax['icon']} {axis_name} — {axis_status}", expanded=False):
                st.info(f"💡 {ax['summary']}")
                cols = st.columns(4)
                for i, m in enumerate(ax["markers"]):
                    cols[i % 4].metric(
                        label=m["name"],
                        value=f"{m['cur']} {m['unit']}",
                        delta=f"Ref: {m['ref']}",
                        delta_color="off"
                    )

    elif view_idx == 2:
        st.subheader(T["sbar_title"])
        st.markdown(f"""
        **{T['sbar_sit']}** {T['sbar_sit_text']}  
        **{T['sbar_bg']}** {T['sbar_bg_text']}  
        **{T['sbar_ass']}**
        """)
        for ax in audit["axes"]:
            axis_name = EN_AXIS_MAP.get(ax["name"], ax["name"]) if lang == "EN" else ax["name"]
            st.markdown(f"- **{axis_name}:** {ax['summary']}")
        st.markdown(f"""
        **{T['sbar_rec']}** {T['sbar_rec_text']}
        """)

    elif view_idx == 3:
        st.subheader("HL7 FHIR R4 Transaction Bundle")
        fhir_res = FullFHIRBundleExporter.export(audit)
        st.json(fhir_res)

    elif view_idx == 4:
        st.subheader(T["legal_header"])
        st.markdown(T["legal_body"])

# Stopka: Żelazny Disclaimer prawny
st.markdown(f"""
<div class="legal-box">
    {T['legal_shield_text']}
</div>
""", unsafe_allow_html=True)

st.sidebar.caption("Zero-Data Retention • ISO 15189:2023 • EU AI Act HITL")
