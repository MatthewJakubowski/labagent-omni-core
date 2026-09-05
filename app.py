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

view_mode = st.sidebar.radio("Tryb prezentacji wyników:", ["Dynamiczny Paszport Narządowy", "Kliniczny Raport Lekarski (SBAR)", "Eksport HL7 FHIR R4 Bundle"])

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
    st.warning("Dalsza interpretacja narządowa została zablokowana zgodnie z rygorem ISO 15189. Wymagane ponowne pobranie próbki.")
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

st.sidebar.divider()
st.sidebar.caption("Zero-Data Retention Architecture • ISO 15189:2023")
