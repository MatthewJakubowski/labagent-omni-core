import streamlit as st
import hashlib
from datetime import datetime, timezone
from core.engine import UltimateClinicalAuditor, FullFHIRBundleExporter

st.set_page_config(
    page_title="LabAgent-Omni Core",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stylizacja bazowa
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
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid #334155;
        border-left: 4px solid #38bdf8;
        padding: 16px;
        border-radius: 6px;
        font-size: 11px;
        color: #94a3b8;
        line-height: 1.6;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Panel boczny - Kontrola Scenariuszy
st.sidebar.title("⚡ LabAgent-Omni")
st.sidebar.caption("Clinical Intelligence & Autovalidation Sidecar")

scenario = st.sidebar.selectbox(
    "Wybierz profil kliniczny:",
    [
        "Scenariusz A: Profilaktyka & Adaptacja Mięśniowa",
        "Scenariusz B: Krytyczna Blokada EDTA (Błąd Przedanalityczny)",
        "Scenariusz C: Przekroczony Indeks Hemolizy (Odrzucenie)"
    ]
)

view_mode = st.sidebar.radio(
    "Tryb prezentacji wyników:",
    ["Dynamiczny Paszport Narządowy", "Kliniczny Raport Lekarski (SBAR)", "Eksport HL7 FHIR R4 Bundle", "Certyfikat Zgodności & Nadzór Prawny"]
)

# Mocki pacjenta
pt_info = {
    "hash": hashlib.sha256(b"DEMO-SESSION-2026").hexdigest(),
    "age": 40,
    "sex": "M"
}

# Definicje danych wg scenariuszy
if "Scenariusz A" in scenario:
    cur_data = {
        "K_POTASSIUM": 4.4, "CA_CALCIUM": 2.38, "H_INDEX": 0.04,
        "WBC": 5.8, "RBC": 5.12, "HGB": 15.6, "HCT": 45.2, "MCV": 88.4, "RDW_CV": 12.1,
        "PLT": 242.0, "NEUT_ABS": 3.4, "LYM_ABS": 1.9, "RET_PCT": 1.21, "RET_HE": 33.5, "ESR": 6.0,
        "BLOOD_PH": 7.41, "PCO2": 39.5, "PO2": 94.0, "LACTATE": 1.1,
        "GLUCOSE": 92.0, "INSULIN": 10.4, "HBA1C": 5.2, "C_PEPTIDE": 1.82,
        "CHOL_TOTAL": 188.0, "HDL": 55.0, "TRIGLYCERIDES": 162.0, "APOB": 84.0, "LPA": 14.0,
        "HS_TROPONIN": 4.2, "NT_PROBNP": 48.0, "D_DIMER": 280.0, "INR": 1.02, "ANTITHROMBIN_III": 104.0,
        "ALT": 46.0, "AST": 27.0, "ALP": 56.0, "GGTP": 24.0,
        "CREATININE": 0.94, "CYSTATIN_C": 0.82, "UREA": 32.0, "URIC_ACID": 6.4,
        "IRON": 112.0, "UIBC": 212.0, "FERRITIN": 145.0, "HS_CRP": 0.48, "HOMOCYSTEINE": 8.4,
        "TSH": 2.05, "FT4": 1.22, "FT3": 3.25, "ANTI_TPO": 10.4, "TRAB": 0.45, "ANTI_CCP": 1.8,
        "TESTOSTERONE": 640.0, "SHBG": 35.0, "VIT_D3": 46.5, "PSA_TOTAL": 0.78, "CA125": 12.1
    }
elif "Scenariusz B" in scenario:
    cur_data = {
        "K_POTASSIUM": 8.4, "CA_CALCIUM": 0.78, "H_INDEX": 0.04,
        "WBC": 5.8, "HGB": 15.6, "MCV": 88.4, "RDW_CV": 12.1, "PLT": 242.0,
        "GLUCOSE": 92.0, "INSULIN": 10.4, "HBA1C": 5.2,
        "ALT": 46.0, "AST": 27.0, "CREATININE": 0.94
    }
else:
    cur_data = {
        "K_POTASSIUM": 4.4, "CA_CALCIUM": 2.38, "H_INDEX": 0.68,
        "WBC": 5.8, "HGB": 15.6, "MCV": 88.4, "RDW_CV": 12.1, "PLT": 242.0,
        "GLUCOSE": 92.0, "INSULIN": 10.4, "HBA1C": 5.2,
        "ALT": 46.0, "AST": 27.0, "CREATININE": 0.94
    }

# Uruchomienie deterministycznego audytu
audit = UltimateClinicalAuditor.execute_god_mode_audit(pt_info, cur_data, {})
pre = audit["preanalytical"]

# Nagłówek aplikacji
st.title("⚡ LabAgent-Omni Core Showcase")
st.caption("Certyfikowana warstwa inteligencji medycznej (ISO 15189:2023 / HL7 FHIR R4)")

# Pasek stanu przedanalitycznego
if pre["passed"]:
    st.success(f"🛡️ **Status Fazy Przedanalitycznej:** {pre['reason']}")
else:
    st.error(f"🚨 **KRYTYCZNA BLOKADA SYSTEMOWA:** {pre['reason']}")

st.divider()

if not pre["passed"]:
    st.warning("Dalsza interpretacja narządowa została zablokowana zgodnie z rygorem ISO 15189:2023. Wymagane ponowne pobranie próbki.")
else:
    if view_mode == "Dynamiczny Paszport Narządowy":
        st.subheader("Wielowymiarowy Paszport Narządowy (20 Osi)")
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

    elif view_mode == "Kliniczny Raport Lekarski (SBAR)":
        st.subheader("Strukturyzowany Raport Kliniczny SBAR")
        st.markdown(f"""
        **S (Situation):** Pacjent {pt_info['age']}L, płeć {pt_info['sex']}. Zgłoszenie na rutynowy audyt biomarkerowy.  
        **B (Background):** Wykluczono błędy fazy przedanalitycznej (indeksy HIL w normie, brak chelatacji EDTA).  
        **A (Assessment):**
        """)
        for ax in audit["axes"]:
            st.markdown(f"- **{ax['name']}:** {ax['summary']}")
        st.markdown("""
        **R (Recommendation):** Wyniki zweryfikowane deterministycznie. Wskazana dalsza obserwacja dynamiki metabolizmu węglowodanowego.
        """)

    elif view_mode == "Eksport HL7 FHIR R4 Bundle":
        st.subheader("HL7 FHIR R4 Transaction Bundle")
        fhir_res = FullFHIRBundleExporter.export(audit)
        st.json(fhir_res)

    elif view_mode == "Certyfikat Zgodności & Nadzór Prawny":
        st.subheader("Formalne Ramy Prawne, Certyfikacja & Nadzór Regulacyjny")
        st.markdown("""
        ### Status Badawczy & Klasyfikacja Systemu (Proof-of-Concept)
        Niniejsza platforma (`LabAgent-Omni Core`) stanowi eksperymentalne środowisko badawczo-rozwojowe (**Proof-of-Concept**) dedykowane deterministycznej autowalizacji regułowej oraz biostatystyce laboratoryjnej.

        #### Zgodność z Polskim i Europejskim Porządkiem Prawnym:
        1. **Ustawa z dnia 15 września 2022 r. o medycynie laboratoryjnej (Dz.U. 2022 poz. 2280):** 
           System nie zastępuje czynności diagnostyki laboratoryjnej ani autoryzacji wyniku. Zgodnie z art. 5 i art. 27 ustawy, prawo do autoryzacji wyniku badania laboratoryjnego oraz sprawowania merytorycznego nadzoru przysługuje wyłącznie uprawnionemu **diagnoście laboratoryjnemu**.
        2. **Ustawa z dnia 5 grudnia 1996 r. o zawodach lekarza i lekarza dentysty:**
           Wszelkie zestawienia, wskaźniki korelacyjne i raporty formatu SBAR generowane przez silnik mają charakter pomocniczy (Clinical Decision Support). Ostateczna decyzja terapeutyczna, rozpoznanie kliniczne i wdrożenie leczenia należą do **lekarza prowadzącego**.
        3. **Rozporządzenie Parlamentu Europejskiego i Rady (UE) 2024/1689 (EU AI Act):**
           System zaprojektowano zgodnie z zasadami **Human-in-the-loop (HITL)**, pełnej wyjaśnialności (Explainable AI - XAI), rygorystycznego zarządzania ryzykiem oraz bezwzględnego zakazu autonomicznego podejmowania decyzji klinicznych bez weryfikacji przez człowieka.
        4. **Standardy Badań Klinicznych ICH GCP (Good Clinical Practice) & ISO 15189:2023:**
           Architektura silnika zapewnia audytowalność każdej reguły logicznej, nienaruszalność danych (data integrity) oraz deterministyczną weryfikację błędów fazy przedanalitycznej.
        """)

# Żelazny Disclaimer na dole każdej strony
st.markdown("""
<div class="legal-box">
    <strong>⚖️ ŻELAZNA KLAUZULA PRAWNA & REGULATORY COMPLIANCE SHIELD:</strong><br>
    System <em>LabAgent-Omni</em> jest oprogramowaniem prototypowym typu <strong>Proof-of-Concept (PoC)</strong> o charakterze naukowo-badawczym. Narzędzie <strong>NIE JEST</strong> wyrobem medycznym w rozumieniu Rozporządzenia Parlamentu Europejskiego i Rady (UE) 2017/746 (IVDR) ani Rozporządzenia (UE) 2017/745 (MDR) i nie służy do samodzielnego stawiania diagnozy medycznej. Zgodnie z <em>Ustawą o medycynie laboratoryjnej</em> wyłączną odpowiedzialność za autoryzację wyników ponosi <strong>uprawniony diagnosta laboratoryjny</strong>, a ostateczne decyzje diagnostyczno-terapeutyczne podejmuje wyłącznie <strong>lekarz prowadzący</strong> na podstawie pełnego obrazu klinicznego pacjenta. System spełnia wymogi nadzoru ludzkiego (Human-in-the-loop) zgodnie z <em>EU AI Act</em> oraz standardami <em>ICH GCP</em>.
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.caption("Zero-Data Retention Architecture • ISO 15189:2023 • EU AI Act HITL")
