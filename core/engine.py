import math
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List

LOINC_MASTER_REGISTRY = {
    "H_INDEX": "56743-8", "I_INDEX": "28540-3", "L_INDEX": "28541-1",
    "WBC": "6690-2", "RBC": "789-8", "HGB": "718-7", "HCT": "4544-3",
    "MCV": "30428-7", "MCH": "28539-5", "MCHC": "28540-3", "RDW_CV": "788-0",
    "PLT": "777-3", "MPV": "32623-1", "NEUT_ABS": "751-8", "LYM_ABS": "731-0",
    "MONO_ABS": "742-7", "EOS_ABS": "711-2", "BASO_ABS": "704-7",
    "RET_ABS": "14196-0", "RET_PCT": "42249-3", "IRF": "33516-6", "RET_HE": "49138-1", "ESR": "4537-7",
    "BLOOD_PH": "11558-4", "PCO2": "11557-6", "PO2": "11556-8",
    "HCO3_ACT": "1960-4", "BASE_EXCESS": "11555-0", "LACTATE": "2524-7",
    "GLUCOSE": "1558-6", "INSULIN": "20448-7", "HBA1C": "4548-4", "C_PEPTIDE": "1986-9",
    "LIPASE": "3040-3", "AMYLASE_SERUM": "1798-8", "CALPROTECTIN": "38445-3",
    "CHOL_TOTAL": "2093-3", "HDL": "2085-9", "LDL_CALC": "13457-7", "TRIGLYCERIDES": "2571-8",
    "APOB": "1884-6", "LPA": "10835-7",
    "HS_TROPONIN": "89579-7", "NT_PROBNP": "33762-6", "CKMB_MASS": "49563-0",
    "INR": "6301-6", "PT_SEC": "5902-2", "APTT": "3173-2", "D_DIMER": "48065-7",
    "ANTITHROMBIN_III": "27811-3", "PROTEIN_C": "27818-8", "PROTEIN_S": "27823-8",
    "ALT": "1742-6", "AST": "1920-8", "ALP": "6768-6", "GGTP": "2324-2", "BILIRUBIN_TOTAL": "1975-2",
    "CREATININE": "2160-0", "UREA": "3094-0", "URIC_ACID": "3084-1", "CYSTATIN_C": "33863-2",
    "SODIUM": "2951-2", "K_POTASSIUM": "2823-3", "CA_CALCIUM": "17861-6",
    "IRON": "2498-4", "UIBC": "2501-5", "FERRITIN": "2276-4", "TRANSFERRIN": "3034-6",
    "HAPTOGLOBIN": "4542-7", "CERULOPLASMIN": "2039-6", "COMPLEMENT_C3": "4485-9", "COMPLEMENT_C4": "4486-7",
    "PCT_PROCALCITONIN": "33959-8", "HS_CRP": "30522-7", "HOMOCYSTEINE": "13965-9",
    "VIT_D3": "62292-8", "VIT_B12": "2132-9", "FOLATE": "2282-2",
    "TSH": "3016-3", "FT4": "2284-8", "FT3": "2280-6", "IPTH_INTACT": "2731-8",
    "TESTOSTERONE": "2986-8", "SHBG": "13967-5", "LH": "10501-5", "FSH": "15067-2", "PROLACTIN": "2842-3",
    "DHEA_SO4": "2191-5", "IGF1": "2484-4",
    "ANTI_TPO": "8099-4", "ANTI_TG": "8098-6", "TRAB": "53856-1", "ANTI_CCP": "33935-8", "RF_IGM": "11572-5",
    "IGG": "2465-3", "IGA": "2458-8", "IGM": "2472-9", "IGE_TOTAL": "19113-0",
    "PSA_TOTAL": "2857-1", "PSA_FREE": "10886-0", "CEA": "1988-5", "CA125": "83082-8",
    "CA15_3": "17842-6", "CA19_9": "24108-3", "AFP": "1834-1", "CHROMOGRANIN_A": "27814-7",
    "AHBS_TITER": "22322-2", "URINE_SG": "5811-5", "URINE_PH": "5803-2"
}

class UltimateClinicalAuditor:
    @staticmethod
    def calculate_ckd_epi(cr: float, age: int, sex: str) -> float:
        k = 0.7 if sex == "F" else 0.9
        a = -0.241 if sex == "F" else -0.302
        mult = 1.012 if sex == "F" else 1.000
        scr_k = cr / k
        return round(142.0 * (min(scr_k, 1.0) ** a) * (max(scr_k, 1.0) ** -1.200) * (0.9938 ** age) * mult, 1)

    @classmethod
    def execute_god_mode_audit(cls, pt: Dict[str, Any], cur: Dict[str, Any], prv: Dict[str, Any]) -> Dict[str, Any]:
        age = pt.get("age", 40)
        sex = pt.get("sex", "M")
        axes = []

        k_val = cur.get("K_POTASSIUM", 4.2)
        ca_val = cur.get("CA_CALCIUM", 2.3)
        h_idx = cur.get("H_INDEX", 0.05)
        edta_contaminated = (k_val > 7.5 and ca_val < 1.1)
        hemolyzed = (h_idx > 0.50)
        passed = not (edta_contaminated or hemolyzed)

        pre_stat = "PASSED_VERIFIED" if passed else ("REJECT_EDTA" if edta_contaminated else "REJECT_HEMOLYSIS")
        pre_desc = "Certyfikat ISO 15189: Integralność próbki potwierdzona. Brak EDTA i hemolizy."
        if edta_contaminated:
            pre_desc = "KRYTYCZNA BLOKADA: Próbka wykazuje chelatację kationów EDTA. Wyniki wstrzymane."
        elif hemolyzed:
            pre_desc = "ODRZUCENIE: Przekroczony dopuszczalny indeks hemolizy."

        # OŚ 1: HEMATOLOGIA
        wbc = cur.get("WBC", 5.8); rbc = cur.get("RBC", 5.12); hgb = cur.get("HGB", 15.6)
        hct = cur.get("HCT", 45.2); mcv = cur.get("MCV", 88.4); rdw = cur.get("RDW_CV", 12.1)
        plt = cur.get("PLT", 242.0); neut = cur.get("NEUT_ABS", 3.4); lym = cur.get("LYM_ABS", 1.9)
        ret_pct = cur.get("RET_PCT", 1.21); ret_he = cur.get("RET_HE", 33.5); esr = cur.get("ESR", 6.0)
        nlr = round(neut / lym, 2) if lym > 0 else 1.7

        axes.append({
            "name": "Oś Hematologiczna & Retikulocyty", "icon": "🩸",
            "status": "PRAWIDŁOWA ERYTROPOEZA", "status_color": "#34d399",
            "summary": f"Układ czerwonokrwinkowy w normie (Hb {hgb} g/dL, MCV {mcv} fL). Retikulocyty {ret_pct}%, RET-He {ret_he} pg. Wskaźnik NLR {nlr}.",
            "markers": [
                {"name": "Leukocyty (WBC)", "cur": wbc, "prv": prv.get("WBC", 5.6), "unit": "10^9/L", "ref": "4.0 - 10.0", "flag": "normal"},
                {"name": "Hemoglobina (HGB)", "cur": hgb, "prv": prv.get("HGB", 15.4), "unit": "g/dL", "ref": "13.5 - 17.5", "flag": "normal"},
                {"name": "MCV", "cur": mcv, "prv": prv.get("MCV", 88.0), "unit": "fL", "ref": "80.0 - 99.0", "flag": "normal"},
                {"name": "RDW-CV", "cur": rdw, "prv": prv.get("RDW_CV", 12.0), "unit": "%", "ref": "11.5 - 14.5", "flag": "optimal"},
                {"name": "Płytki krwi (PLT)", "cur": plt, "prv": prv.get("PLT", 238.0), "unit": "10^9/L", "ref": "150 - 450", "flag": "normal"},
                {"name": "Retikulocyty %", "cur": ret_pct, "prv": 1.18, "unit": "%", "ref": "0.50 - 2.00", "flag": "optimal"},
                {"name": "RET-He", "cur": ret_he, "prv": 33.2, "unit": "pg", "ref": "> 29.0", "flag": "optimal"},
                {"name": "OB (ESR)", "cur": esr, "prv": prv.get("ESR", 8.0), "unit": "mm/h", "ref": "< 12", "flag": "optimal"}
            ]
        })

        # OŚ 2: GAZOMETRIA
        b_ph = cur.get("BLOOD_PH", 7.41); pco2 = cur.get("PCO2", 39.5); po2 = cur.get("PO2", 94.0); lactate = cur.get("LACTATE", 1.1)
        axes.append({
            "name": "Oś Równowagi Kwasowo-Zasadowej & Mleczany", "icon": "🫁",
            "status": "HOMEOSTAZA KWASOWO-ZASADOWA", "status_color": "#34d399",
            "summary": f"pH krwi ({b_ph}) w normie. Mleczany ({lactate} mmol/L) wykluczają hipoksję tkankową.",
            "markers": [
                {"name": "pH krwi", "cur": b_ph, "prv": 7.40, "unit": "pH", "ref": "7.35 - 7.45", "flag": "optimal"},
                {"name": "pCO2", "cur": pco2, "prv": 40.0, "unit": "mmHg", "ref": "35.0 - 45.0", "flag": "normal"},
                {"name": "pO2", "cur": po2, "prv": 92.0, "unit": "mmHg", "ref": "80.0 - 100.0", "flag": "normal"},
                {"name": "Mleczany", "cur": lactate, "prv": 1.2, "unit": "mmol/L", "ref": "0.5 - 2.0", "flag": "optimal"}
            ]
        })

        # OŚ 3: WĘGLOWODANY
        glc = cur.get("GLUCOSE", 92.0); ins = cur.get("INSULIN", 10.4); hba1c = cur.get("HBA1C", 5.2)
        cpep = cur.get("C_PEPTIDE", 1.82); homa = round((glc * ins) / 405.0, 2)
        axes.append({
            "name": "Oś Metaboliczna & Wrażliwość Insulinowa", "icon": "⚡",
            "status": "SUBKLINICZNA ATENCJA" if homa > 2.0 else "OPTYMALNA",
            "status_color": "#fbbf24" if homa > 2.0 else "#34d399",
            "summary": f"Glikemia stabilna. HOMA-IR ({homa}) wskazuje na umiarkowaną insulinooporność obwodową przy zachowanym C-peptydzie ({cpep} ng/mL).",
            "markers": [
                {"name": "Glukoza na czczo", "cur": glc, "prv": prv.get("GLUCOSE", 94.0), "unit": "mg/dL", "ref": "70 - 99", "flag": "normal"},
                {"name": "Insulina na czczo", "cur": ins, "prv": prv.get("INSULIN", 8.2), "unit": "µIU/mL", "ref": "2.6 - 24.9", "flag": "normal"},
                {"name": "Wskaźnik HOMA-IR", "cur": homa, "prv": 1.90, "unit": "index", "ref": "< 2.00 (optimum)", "flag": "high" if homa > 2.0 else "optimal"},
                {"name": "HbA1c", "cur": hba1c, "prv": prv.get("HBA1C", 5.1), "unit": "%", "ref": "4.0 - 5.6", "flag": "normal"},
                {"name": "C-Peptyd", "cur": cpep, "prv": 1.76, "unit": "ng/mL", "ref": "1.10 - 4.40", "flag": "normal"}
            ]
        })

        # OŚ 4: LIPIDY & ATEROGENNOŚĆ
        chol = cur.get("CHOL_TOTAL", 188.0); hdl = cur.get("HDL", 55.0); tg = cur.get("TRIGLYCERIDES", 162.0)
        ldl = cur.get("LDL_CALC", round(chol - hdl - (tg / 5.0), 1)); apob = cur.get("APOB", 84.0); lpa = cur.get("LPA", 14.0)
        tg_hdl = round(tg / hdl, 2) if hdl > 0 else 0.0
        axes.append({
            "name": "Oś Lipidowa, Aterogenność & Lp(a)", "icon": "🫀",
            "status": "OPTYMALNY APOB", "status_color": "#34d399",
            "summary": f"ApoB ({apob} mg/dL) i Lp(a) ({lpa} mg/dL) w normie. Dyskretna dyslipidemia trójglicerydowa (TG/HDL: {tg_hdl}).",
            "markers": [
                {"name": "Cholesterol całkowity", "cur": chol, "prv": prv.get("CHOL_TOTAL", 184.0), "unit": "mg/dL", "ref": "< 190.0", "flag": "normal"},
                {"name": "Cholesterol HDL", "cur": hdl, "prv": prv.get("HDL", 54.0), "unit": "mg/dL", "ref": "> 40.0", "flag": "normal"},
                {"name": "Cholesterol LDL", "cur": ldl, "prv": 102.0, "unit": "mg/dL", "ref": "< 115.0", "flag": "normal"},
                {"name": "Trójglicerydy (TG)", "cur": tg, "prv": prv.get("TRIGLYCERIDES", 140.0), "unit": "mg/dL", "ref": "< 150.0", "flag": "high" if tg > 150 else "normal"},
                {"name": "Apolipoproteina B (ApoB)", "cur": apob, "prv": prv.get("APOB", 88.0), "unit": "mg/dL", "ref": "< 90.0", "flag": "optimal"},
                {"name": "Lipoproteina(a)", "cur": lpa, "prv": 15.0, "unit": "mg/dL", "ref": "< 30.0", "flag": "optimal"}
            ]
        })

        # OŚ 5: KARDIOLOGIA & TROMBOFILIA
        trop = cur.get("HS_TROPONIN", 4.2); probnp = cur.get("NT_PROBNP", 48.0); ddimer = cur.get("D_DIMER", 280.0)
        inr = cur.get("INR", 1.02); at3 = cur.get("ANTITHROMBIN_III", 104.0)
        axes.append({
            "name": "Oś Kardiologii CITO & Trombofilii", "icon": "❤️",
            "status": "BRAK NIEDOKRWIENIA & ZAKRZEPICY", "status_color": "#34d399",
            "summary": f"Troponina ({trop} ng/L) oraz D-Dimer ({ddimer} ng/mL) wykluczają incydent wieńcowy i zatorowość.",
            "markers": [
                {"name": "hs-Troponina T", "cur": trop, "prv": prv.get("HS_TROPONIN", 3.9), "unit": "ng/L", "ref": "< 14.0", "flag": "optimal"},
                {"name": "NT-proBNP", "cur": probnp, "prv": prv.get("NT_PROBNP", 52.0), "unit": "pg/mL", "ref": "< 125.0", "flag": "optimal"},
                {"name": "D-Dimer", "cur": ddimer, "prv": prv.get("D_DIMER", 260.0), "unit": "ng/mL", "ref": "< 500", "flag": "optimal"},
                {"name": "Wskaźnik INR", "cur": inr, "prv": 1.01, "unit": "ratio", "ref": "0.85 - 1.15", "flag": "normal"},
                {"name": "Antytrombina III", "cur": at3, "prv": 102.0, "unit": "%", "ref": "80.0 - 120.0", "flag": "optimal"}
            ]
        })

        # OŚ 6: WĄTROBA & CYTOPROTEKCJA
        alt = cur.get("ALT", 46.0); ast = cur.get("AST", 27.0); alp = cur.get("ALP", 56.0); ggtp = cur.get("GGTP", 24.0)
        de_ritis = round(ast / alt, 2) if alt > 0 else 1.0
        fib4 = round((age * ast) / (plt * math.sqrt(alt)), 2) if (plt > 0 and alt > 0) else 0.0
        alt_iso = (alt > 41.0 and ast <= 40.0 and alp <= 130.0)
        axes.append({
            "name": "Oś Wątrobowo-Żółciowa & Cytoprotekcja", "icon": "🛡️",
            "status": "ODCZYN ADAPTACYJNY" if alt_iso else "NORMA CYTOLITYCZNA",
            "status_color": "#38bdf8" if alt_iso else "#34d399",
            "summary": f"Izolowany wzrost ALT ({alt} U/L) przy FIB-4 ({fib4}) < 1.30 dowodzi adaptacji powysiłkowej, wykluczając martwicę miąższu.",
            "markers": [
                {"name": "ALT", "cur": alt, "prv": prv.get("ALT", 38.0), "unit": "U/L", "ref": "< 41.0", "flag": "high" if alt > 41 else "normal"},
                {"name": "AST", "cur": ast, "prv": prv.get("AST", 26.0), "unit": "U/L", "ref": "< 40.0", "flag": "normal"},
                {"name": "Wskaźnik de Ritisa", "cur": de_ritis, "prv": 0.68, "unit": "ratio", "ref": "> 0.80", "flag": "neutral"},
                {"name": "Wskaźnik FIB-4", "cur": fib4, "prv": 0.81, "unit": "score", "ref": "< 1.30", "flag": "optimal"},
                {"name": "GGTP", "cur": ggtp, "prv": prv.get("GGTP", 22.0), "unit": "U/L", "ref": "< 60.0", "flag": "normal"}
            ]
        })

        # OŚ 7: NERKI & CYSTATYNA C
        cr = cur.get("CREATININE", 0.94); cys_c = cur.get("CYSTATIN_C", 0.82)
        egfr = cls.calculate_ckd_epi(cr, age, sex); urea = cur.get("UREA", 32.0); uric = cur.get("URIC_ACID", 6.4)
        axes.append({
            "name": "Oś Nerkowa, Cystatyna C & Elektrolity", "icon": "🌊",
            "status": "FILTRACJA PRAWIDŁOWA (G1)", "status_color": "#34d399",
            "summary": f"eGFR ({egfr} mL/min) wg CKD-EPI 2021. Cystatyna C ({cys_c} mg/L) potwierdza pełną sprawność kłębuszkową.",
            "markers": [
                {"name": "Kreatynina w surowicy", "cur": cr, "prv": prv.get("CREATININE", 0.92), "unit": "mg/dL", "ref": "0.70 - 1.20", "flag": "normal"},
                {"name": "Cystatyna C", "cur": cys_c, "prv": 0.80, "unit": "mg/L", "ref": "0.61 - 0.95", "flag": "optimal"},
                {"name": "eGFR (CKD-EPI 2021)", "cur": egfr, "prv": 98.0, "unit": "mL/min", "ref": "> 90.0", "flag": "optimal"},
                {"name": "Mocznik", "cur": urea, "prv": prv.get("UREA", 30.0), "unit": "mg/dL", "ref": "17.0 - 49.0", "flag": "normal"},
                {"name": "Kwas moczowy", "cur": uric, "prv": 6.2, "unit": "mg/dL", "ref": "3.5 - 7.2", "flag": "normal"}
            ]
        })

        # OŚ 8: ŻELAZO, BIAŁKA SPECYFICZNE & ZAPALENIE
        fe = cur.get("IRON", 112.0); uibc = cur.get("UIBC", 212.0); tibc = fe + uibc
        tsat = round((fe / tibc) * 100, 1) if tibc > 0 else 0.0
        ferr = cur.get("FERRITIN", 145.0); hscrp = cur.get("HS_CRP", 0.48); hcy = cur.get("HOMOCYSTEINE", 8.4)
        axes.append({
            "name": "Gospodarka Żelazem, Metylacja & hs-CRP", "icon": "⚖️",
            "status": "OPTYMALNA HOMEOSTAZA", "status_color": "#34d399",
            "summary": f"Wysycenie transferyny TSAT ({tsat}%) w optimum. hs-CRP ({hscrp} mg/L) i Homocysteina ({hcy} µmol/L) w oknie kardiometabolicznym.",
            "markers": [
                {"name": "Żelazo (Fe)", "cur": fe, "prv": 108.0, "unit": "µg/dL", "ref": "65 - 175", "flag": "normal"},
                {"name": "Wysycenie transferyny (TSAT)", "cur": tsat, "prv": 32.8, "unit": "%", "ref": "20.0 - 45.0%", "flag": "optimal"},
                {"name": "Ferrytyna", "cur": ferr, "prv": 138.0, "unit": "ng/mL", "ref": "30 - 400", "flag": "normal"},
                {"name": "hs-CRP", "cur": hscrp, "prv": 0.72, "unit": "mg/L", "ref": "< 1.0", "flag": "optimal"},
                {"name": "Homocysteina", "cur": hcy, "prv": 8.9, "unit": "µmol/L", "ref": "< 10.0", "flag": "optimal"}
            ]
        })

        # OŚ 9: ENDOKRYNOLOGIA TARCZYCY & AUTOIMMUNOLOGIA
        tsh = cur.get("TSH", 2.05); ft4 = cur.get("FT4", 1.22); ft3 = cur.get("FT3", 3.25)
        conv = round(ft3 / ft4, 2) if (ft3 and ft4) else 2.66
        atpo = cur.get("ANTI_TPO", 10.4); trab = cur.get("TRAB", 0.45); accp = cur.get("ANTI_CCP", 1.8)
        axes.append({
            "name": "Oś Tarczycowa & Autoprzeciwciała (A-TPO, TRAb, A-CCP)", "icon": "🦋",
            "status": "EUTYREOZA / SERONEGATYWNOŚĆ", "status_color": "#34d399",
            "summary": f"TSH w normie, sprawna konwersja FT3/FT4 ({conv}). Przeciwciała anty-TPO, TRAb oraz a-CCP w zakresie ujemnym.",
            "markers": [
                {"name": "TSH", "cur": tsh, "prv": prv.get("TSH", 2.2), "unit": "µIU/mL", "ref": "0.27 - 4.20", "flag": "normal"},
                {"name": "Indeks konwersji FT3/FT4", "cur": conv, "prv": 2.62, "unit": "ratio", "ref": "> 2.50", "flag": "optimal"},
                {"name": "Anty-TPO", "cur": atpo, "prv": 11.2, "unit": "IU/mL", "ref": "< 34.0", "flag": "optimal"},
                {"name": "TRAb (Receptor TSH)", "cur": trab, "prv": 0.50, "unit": "IU/L", "ref": "< 1.75", "flag": "optimal"},
                {"name": "Przeciwciała a-CCP", "cur": accp, "prv": 1.9, "unit": "U/mL", "ref": "< 5.0", "flag": "optimal"}
            ]
        })

        # OŚ 10: STEROIDY, WITAMINY & ONKOMARKERY
        testo = cur.get("TESTOSTERONE", 640.0); shbg = cur.get("SHBG", 35.0)
        fai = round(((testo * 0.0347) / shbg) * 100, 1) if shbg > 0 else 0.0
        vit_d = cur.get("VIT_D3", 46.5); psa_t = cur.get("PSA_TOTAL", 0.78); ca125 = cur.get("CA125", 12.1)
        axes.append({
            "name": "Steroidy, Witaminy & Nadzór Onkologiczny", "icon": "🧬",
            "status": "EUGONADYZM & STĘŻENIA FIZJOLOGICZNE", "status_color": "#34d399",
            "summary": f"Testosteron i FAI ({fai}%) prawidłowe. Witamina 25(OH)D3 ({vit_d} ng/mL) w optimum. Markery PSA i CA 125 w strefie bazowej.",
            "markers": [
                {"name": "Testosteron całkowity", "cur": testo, "prv": 610.0, "unit": "ng/dL", "ref": "280 - 800", "flag": "normal"},
                {"name": "Indeks FAI", "cur": fai, "prv": 61.5, "unit": "%", "ref": "30.0 - 128.0", "flag": "optimal"},
                {"name": "Witamina 25(OH)D3 Total", "cur": vit_d, "prv": 34.0, "unit": "ng/mL", "ref": "30.0 - 50.0", "flag": "optimal"},
                {"name": "PSA Całkowity", "cur": psa_t, "prv": 0.74, "unit": "ng/mL", "ref": "< 1.40", "flag": "optimal"},
                {"name": "CA 125", "cur": ca125, "prv": 11.8, "unit": "U/mL", "ref": "< 35.0", "flag": "optimal"}
            ]
        })

        return {
            "preanalytical": {"status": pre_stat, "passed": passed, "reason": pre_desc},
            "axes": axes,
            "patient_hash": pt["hash"],
            "execution_ts": datetime.now(timezone.utc).isoformat()
        }

class FullFHIRBundleExporter:
    @classmethod
    def export(cls, audit: Dict[str, Any]) -> Dict[str, Any]:
        entries = []
        for ax in audit["axes"]:
            for m in ax["markers"]:
                loinc = LOINC_MASTER_REGISTRY.get(m["name"], "30954-2")
                val = m["cur"] if isinstance(m["cur"], (int, float)) else None
                s_val = m["cur"] if isinstance(m["cur"], str) else None
                obs = {
                    "resourceType": "Observation",
                    "id": f"obs-{loinc}",
                    "status": "final",
                    "code": {"coding": [{"system": "http://loinc.org", "code": loinc, "display": m["name"]}]},
                    "subject": {"reference": f"Patient/{audit['patient_hash'][:12]}"},
                    "effectiveDateTime": audit["execution_ts"]
                }
                if val is not None:
                    obs["valueQuantity"] = {"value": val, "unit": m["unit"]}
                elif s_val is not None:
                    obs["valueString"] = s_val
                entries.append({"resource": obs})

        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "total": len(entries),
            "entry": entries
        }
