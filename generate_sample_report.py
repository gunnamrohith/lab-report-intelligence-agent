"""Generate a realistic sample lab report PDF for testing."""

from fpdf import FPDF


class LabReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(25, 60, 120)
        self.cell(0, 12, "HealthFirst Diagnostics", ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "123 Medical Plaza, Suite 400  |  Bangalore, KA 560001  |  Ph: (080) 4567-8901", ln=True, align="C")
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 5, "This report is generated for informational purposes. Consult your physician.", align="C", ln=True)
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="C")


def main():
    pdf = LabReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)

    # ── Patient Info ──
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "PATIENT INFORMATION", ln=True)
    pdf.set_font("Helvetica", "", 10)
    info = [
        ("Patient Name", "Rohith G"),
        ("Age / Gender", "29 / Male"),
        ("Sample ID", "HFD-2026-00451"),
        ("Date of Collection", "25-Feb-2026, 07:30 AM"),
        ("Date of Report", "26-Feb-2026"),
        ("Referred By", "Dr. Ananya Sharma"),
    ]
    for label, value in info:
        pdf.cell(50, 6, f"{label}:", ln=False)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, value, ln=True)
        pdf.set_font("Helvetica", "", 10)
    pdf.ln(4)

    # ── Helper to draw a section ──
    def section_header(title):
        pdf.set_fill_color(230, 240, 250)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(25, 60, 120)
        pdf.cell(0, 7, f"  {title}", ln=True, fill=True)
        pdf.set_text_color(30, 30, 30)
        # Column headers
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(65, 6, "Test Name", border="B")
        pdf.cell(30, 6, "Result", border="B", align="C")
        pdf.cell(25, 6, "Unit", border="B", align="C")
        pdf.cell(50, 6, "Reference Range", border="B", align="C")
        pdf.ln()

    def add_row(test, result, unit, ref_range, flag=""):
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(65, 5.5, test)
        # Bold + color for abnormal
        if flag == "H":
            pdf.set_text_color(200, 30, 30)
            pdf.set_font("Helvetica", "B", 9)
        elif flag == "L":
            pdf.set_text_color(200, 140, 0)
            pdf.set_font("Helvetica", "B", 9)
        pdf.cell(30, 5.5, result, align="C")
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(25, 5.5, unit, align="C")
        pdf.cell(50, 5.5, ref_range, align="C")
        if flag:
            pdf.set_font("Helvetica", "B", 9)
            color = (200, 30, 30) if flag == "H" else (200, 140, 0)
            pdf.set_text_color(*color)
            pdf.cell(10, 5.5, flag)
            pdf.set_text_color(30, 30, 30)
        pdf.ln()

    # ── CBC ──
    section_header("COMPLETE BLOOD COUNT (CBC)")
    add_row("Hemoglobin",           "11.2",   "g/dL",        "12.0 - 17.5",   "L")
    add_row("RBC Count",            "4.5",    "million/uL",  "4.0 - 6.0")
    add_row("WBC Count",            "12.8",   "thousand/uL", "4.0 - 11.0",    "H")
    add_row("Platelet Count",       "210",    "thousand/uL", "150 - 400")
    add_row("Hematocrit",           "34.1",   "%",           "36.0 - 50.0",   "L")
    add_row("MCV",                  "82.5",   "fL",          "80.0 - 100.0")
    add_row("MCH",                  "28.0",   "pg",          "27.0 - 33.0")
    add_row("MCHC",                 "33.1",   "g/dL",        "32.0 - 36.0")
    add_row("RDW",                  "15.8",   "%",           "11.5 - 14.5",   "H")
    pdf.ln(3)

    # ── Lipid Panel ──
    section_header("LIPID PROFILE")
    add_row("Total Cholesterol",    "242",    "mg/dL",       "< 200",         "H")
    add_row("LDL Cholesterol",      "158",    "mg/dL",       "< 100",         "H")
    add_row("HDL Cholesterol",      "38",     "mg/dL",       "40 - 60",       "L")
    add_row("Triglycerides",        "195",    "mg/dL",       "< 150",         "H")
    add_row("VLDL Cholesterol",     "39",     "mg/dL",       "2 - 30",        "H")
    pdf.ln(3)

    # ── Liver Function ──
    section_header("LIVER FUNCTION TESTS (LFT)")
    add_row("SGOT (AST)",          "52",     "U/L",         "5 - 40",        "H")
    add_row("SGPT (ALT)",          "68",     "U/L",         "7 - 56",        "H")
    add_row("Alkaline Phosphatase","88",     "U/L",         "44 - 147")
    add_row("Total Bilirubin",     "0.9",    "mg/dL",       "0.1 - 1.2")
    add_row("Direct Bilirubin",    "0.2",    "mg/dL",       "0.0 - 0.3")
    add_row("Total Protein",       "7.1",    "g/dL",        "6.0 - 8.3")
    add_row("Albumin",             "4.2",    "g/dL",        "3.5 - 5.5")
    add_row("Globulin",            "2.9",    "g/dL",        "2.0 - 3.5")
    add_row("A/G Ratio",           "1.45",   "",            "1.0 - 2.5")
    pdf.ln(3)

    # ── Kidney Function ──
    section_header("KIDNEY FUNCTION TESTS (KFT)")
    add_row("Creatinine",          "1.4",    "mg/dL",       "0.6 - 1.2",     "H")
    add_row("Blood Urea Nitrogen", "24",     "mg/dL",       "7 - 20",        "H")
    add_row("Uric Acid",           "8.2",    "mg/dL",       "3.0 - 7.0",     "H")
    add_row("eGFR",                "68",     "mL/min/1.73m2","90 - 120",     "L")
    pdf.ln(3)

    # ── Diabetes ──
    section_header("DIABETES PANEL")
    add_row("Fasting Glucose",     "118",    "mg/dL",       "70 - 100",      "H")
    add_row("HbA1c",               "6.4",    "%",           "4.0 - 5.6",     "H")
    pdf.ln(3)

    # ── Thyroid ──
    section_header("THYROID PROFILE")
    add_row("TSH",                 "5.8",    "mIU/L",       "0.4 - 4.0",     "H")
    add_row("Free T3",             "2.9",    "pg/mL",       "2.3 - 4.2")
    add_row("Free T4",             "1.1",    "ng/dL",       "0.8 - 1.8")
    pdf.ln(3)

    # ── Electrolytes ──
    section_header("ELECTROLYTES")
    add_row("Sodium",              "141",    "mEq/L",       "136 - 145")
    add_row("Potassium",           "4.2",    "mEq/L",       "3.5 - 5.0")
    add_row("Calcium",             "9.1",    "mg/dL",       "8.5 - 10.5")
    pdf.ln(3)

    # ── Vitamins & Iron ──
    section_header("VITAMINS & IRON STUDIES")
    add_row("Vitamin D",           "18.5",   "ng/mL",       "30 - 100",      "L")
    add_row("Vitamin B12",         "185",    "pg/mL",       "200 - 900",     "L")
    add_row("Iron",                "52",     "ug/dL",       "60 - 170",      "L")
    add_row("Ferritin",            "10",     "ng/mL",       "12 - 300",      "L")
    pdf.ln(3)

    # ── Inflammation ──
    section_header("INFLAMMATORY MARKERS")
    add_row("ESR",                 "28",     "mm/hr",       "0 - 20",        "H")
    add_row("CRP",                 "5.4",    "mg/L",        "0 - 3",         "H")

    # ── Pathologist sign-off ──
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "*** End of Report ***", align="C", ln=True)
    pdf.ln(6)
    pdf.cell(95, 5, "")
    pdf.cell(95, 5, "Dr. Vikram Patel, MD (Pathology)", align="R", ln=True)
    pdf.cell(95, 5, "")
    pdf.cell(95, 5, "Chief Laboratory Director", align="R", ln=True)

    out_path = "sample_lab_report.pdf"
    pdf.output(out_path)
    print(f"Sample report saved to: {out_path}")


if __name__ == "__main__":
    main()
