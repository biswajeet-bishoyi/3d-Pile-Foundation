"""
GeoSmart AI -- 3D Pile Foundation Load Behaviour Simulator
Automated Engineering Calculation Report Generator
Course: Foundation Engineering and Design (21CEE301T)

Generates:
1. Publication-quality printable HTML engineering calculation report
2. Native PDF report using ReportLab
3. CSV calculation summary
"""

import io
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

from core.calculations import SinglePileResult, PileGroupResult
from core.explainer import generate_rule_based_explanation


def generate_html_report(
    single_res: SinglePileResult,
    group_res: Optional[PileGroupResult] = None,
    project_title: str = "3D Pile Foundation Load Behaviour Simulation",
    student_name: str = "Civil Engineering Student",
    roll_number: str = "21CEE301T-DEMO"
) -> str:
    """
    Generates a print-ready academic engineering report in clean HTML/CSS format.
    """
    pile = single_res.pile
    soil = single_res.soil
    explanation = generate_rule_based_explanation(single_res, group_res)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    is_group = group_res is not None and group_res.total_piles > 1

    steps_html = ""
    for idx, s in enumerate(single_res.steps, 1):
        steps_html += f"""
        <div class="step-card">
            <div class="step-header">Step {idx}: {s['name']}</div>
            <div class="step-formula">Formula: <code>{s['formula']}</code></div>
            <div class="step-calc">Substituted: {s['substituted']}</div>
            <div class="step-res"><b>Output: {s['result']}</b></div>
        </div>
        """

    group_html = ""
    if is_group:
        group_html = f"""
        <h3>Pile Group Interaction & Efficiency</h3>
        <table class="report-table">
            <tr><th>Parameter</th><th>Value</th><th>Unit</th></tr>
            <tr><td>Arrangement (m × n)</td><td>{group_res.rows} × {group_res.cols}</td><td>count</td></tr>
            <tr><td>Total Piles in Group (N)</td><td>{group_res.total_piles}</td><td>piles</td></tr>
            <tr><td>Center-to-Center Spacing (s)</td><td>{group_res.spacing:.2f} m ({group_res.spacing_ratio:.1f}D)</td><td>m</td></tr>
            <tr><td>Cap Dimensions (B_g × L_g)</td><td>{group_res.group_cap_width:.2f} m × {group_res.group_cap_length:.2f} m</td><td>m</td></tr>
            <tr><td>Group Efficiency (η)</td><td>{group_res.group_efficiency * 100:.1f}% ({group_res.efficiency_method})</td><td>%</td></tr>
            <tr><td>Individual Sum (N × Q_ult)</td><td>{group_res.q_group_sum:.1f}</td><td>kN</td></tr>
            <tr><td>Governing Ultimate Group Capacity (Q_g,ult)</td><td><b>{group_res.q_group_ult:.1f}</b></td><td>kN</td></tr>
            <tr><td>Allowable Group Capacity (Q_g,all)</td><td><b>{group_res.q_group_all:.1f}</b></td><td>kN</td></tr>
            <tr><td>Total Applied Load (P_total)</td><td>{group_res.total_applied_load:.1f}</td><td>kN</td></tr>
            <tr><td>Load Per Individual Pile</td><td>{group_res.load_per_pile:.1f}</td><td>kN/pile</td></tr>
            <tr><td>Group Utilization Ratio</td><td><b>{group_res.group_utilization * 100:.1f}%</b> ({'SAFE' if group_res.is_group_safe else 'OVERLOAD'})</td><td>-</td></tr>
        </table>
        """

    recommendations_html = "".join([f"<li>{r}</li>" for r in explanation["recommendations"]])
    assumptions_html = "".join([f"<li>{a}</li>" for a in explanation["assumptions"]])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{project_title} - Engineering Report</title>
<style>
    @page {{ size: A4; margin: 15mm; }}
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #1e293b;
        line-height: 1.5;
        background: #f8fafc;
        margin: 0;
        padding: 20px;
    }}
    .container {{
        max-width: 900px;
        margin: 0 auto;
        background: #ffffff;
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }}
    .header {{
        border-bottom: 3px solid #1e40af;
        padding-bottom: 16px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }}
    .header h1 {{ margin: 0 0 6px 0; color: #1e3a8a; font-size: 24px; }}
    .header .subtitle {{ color: #64748b; font-size: 13px; font-weight: 500; }}
    .badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }}
    .badge-success {{ background: #dcfce7; color: #166534; }}
    .badge-danger {{ background: #fee2e2; color: #991b1b; }}
    .badge-warning {{ background: #fef3c7; color: #92400e; }}
    h2 {{ color: #1e3a8a; font-size: 18px; border-left: 4px solid #2563eb; padding-left: 10px; margin-top: 28px; }}
    h3 {{ color: #334155; font-size: 15px; margin-top: 20px; }}
    .report-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0 20px 0;
        font-size: 13px;
    }}
    .report-table th, .report-table td {{
        border: 1px solid #e2e8f0;
        padding: 8px 12px;
        text-align: left;
    }}
    .report-table th {{ background: #f1f5f9; color: #334155; font-weight: 600; }}
    .step-card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-size: 13px;
    }}
    .step-header {{ font-weight: 600; color: #1e40af; margin-bottom: 4px; }}
    .step-formula {{ color: #475569; margin-bottom: 4px; }}
    .step-calc {{ color: #334155; font-family: monospace; margin-bottom: 4px; }}
    .step-res {{ color: #0f172a; }}
    .disclaimer {{
        margin-top: 35px;
        padding: 16px;
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 6px;
        font-size: 11px;
        color: #92400e;
    }}
    @media print {{
        body {{ background: #ffffff; padding: 0; }}
        .container {{ box-shadow: none; padding: 0; }}
        .no-print {{ display: none; }}
    }}
</style>
</head>
<body>

<div class="container">
    <div class="header">
        <div>
            <h1>GeoSmart AI — 3D Pile Foundation Simulator</h1>
            <div class="subtitle">Course: Foundation Engineering and Design (21CEE301T) | Version 1.0</div>
            <div class="subtitle">Generated on: {timestamp}</div>
        </div>
        <div>
            <span class="badge {'badge-success' if single_res.is_safe else 'badge-danger'}">
                {'SAFE DESIGN' if single_res.is_safe else 'OVERLOAD WARNING'}
            </span>
        </div>
    </div>

    <h2>1. Executive Summary & Status</h2>
    <p><b>Assessment Verdict:</b> {explanation['safety_status']}</p>
    <p>{explanation['safety_summary']}</p>
    <p><b>Dominant Load Transfer Mechanism:</b> {explanation['mechanism_type']}</p>
    <p>{explanation['mechanism_text']}</p>

    <h2>2. Input Parameters & Geotechnical Profile</h2>
    <table class="report-table">
        <tr><th>Category</th><th>Parameter</th><th>Value</th><th>Unit</th></tr>
        <tr><td rowspan="4"><b>Pile Geometry</b></td><td>Pile Diameter (D)</td><td>{pile.diameter:.3f}</td><td>m</td></tr>
        <tr><td>Embedded Length (L)</td><td>{pile.length:.2f}</td><td>m</td></tr>
        <tr><td>Slenderness Ratio (L/D)</td><td>{pile.slenderness_ratio:.1f}</td><td>-</td></tr>
        <tr><td>Installation Type</td><td>{pile.pile_type}</td><td>-</td></tr>
        <tr><td rowspan="5"><b>Soil Strata</b></td><td>Soil Stratum Classification</td><td>{soil.soil_type}</td><td>-</td></tr>
        <tr><td>Effective Unit Weight (γ)</td><td>{soil.unit_weight:.2f}</td><td>kN/m³</td></tr>
        <tr><td>Undrained Cohesion (c_u)</td><td>{soil.cohesion_cu:.2f}</td><td>kPa</td></tr>
        <tr><td>Internal Friction Angle (φ)</td><td>{soil.friction_angle_phi:.1f}°</td><td>deg</td></tr>
        <tr><td>Adhesion Factor (α) / Earth Coeff (Ks)</td><td>α={soil.adhesion_factor_alpha or 'Auto'}, Ks={soil.earth_pressure_coeff_ks or 'Auto'}</td><td>-</td></tr>
        <tr><td rowspan="2"><b>Design Demands</b></td><td>Applied Axial Load (P)</td><td>{single_res.applied_load:.1f}</td><td>kN</td></tr>
        <tr><td>Factor of Safety (FS)</td><td>{single_res.factor_of_safety:.2f}</td><td>-</td></tr>
    </table>

    <h2>3. Capacity Breakdown & Calculation Results</h2>
    <table class="report-table">
        <tr><th>Quantity</th><th>Symbol</th><th>Calculated Value</th><th>Share (%)</th></tr>
        <tr><td>Pile Base Cross-Sectional Area</td><td>A_b</td><td>{pile.base_area:.4f} m²</td><td>-</td></tr>
        <tr><td>Pile Circumferential Shaft Area</td><td>A_s</td><td>{pile.shaft_area:.3f} m²</td><td>-</td></tr>
        <tr><td>Shaft Resistance (Skin Friction)</td><td>Q_s</td><td><b>{single_res.qs:.2f} kN</b></td><td>{single_res.qs_percent:.1f}%</td></tr>
        <tr><td>Base Resistance (End Bearing)</td><td>Q_b</td><td><b>{single_res.qb:.2f} kN</b></td><td>{single_res.qb_percent:.1f}%</td></tr>
        <tr><td>Total Ultimate Axial Capacity</td><td>Q_ult</td><td><b>{single_res.q_ult:.2f} kN</b></td><td>100.0%</td></tr>
        <tr><td>Allowable Working Capacity (FS={single_res.factor_of_safety:.2f})</td><td>Q_all</td><td><b>{single_res.q_all:.2f} kN</b></td><td>-</td></tr>
        <tr><td>Applied Column Load</td><td>P</td><td>{single_res.applied_load:.1f} kN</td><td>-</td></tr>
        <tr><td>Load Utilization Ratio</td><td>P / Q_all</td><td><b>{single_res.utilization_ratio * 100:.1f}%</b></td><td>-</td></tr>
    </table>

    {group_html}

    <h2>4. Step-by-Step Geotechnical Derivations</h2>
    {steps_html}

    <h2>5. Engineering Insights & Parametric Recommendations</h2>
    <ul>
        {recommendations_html}
    </ul>

    <h2>6. Assumptions, Academic Limitations & Disclaimers</h2>
    <ul>
        {assumptions_html}
    </ul>

    <div class="disclaimer">
        <b>SAFETY & ENGINEERING DISCLAIMER:</b> This report is generated strictly for educational demonstration
        in Course 21CEE301T (Foundation Engineering and Design). Outputs are computed using classical closed-form
        empirical formulations and MUST NOT be used for real-world construction, bidding, structural sizing,
        or site safety approval. Professional design mandates certified geotechnical site investigation,
        multi-layer boring logs, groundwater observation, structural pile-cap reinforcement design,
        and full-scale static load testing (ASTM D1143 / IS 2911).
    </div>
</div>

</body>
</html>
"""
    return html


def generate_pdf_report(
    single_res: SinglePileResult,
    group_res: Optional[PileGroupResult] = None,
    project_title: str = "3D Pile Foundation Simulator Report"
) -> bytes:
    """
    Generates a native PDF report using ReportLab.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E3A8A')
    )
    h2_style = ParagraphStyle(
        'RepH2',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E40AF'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'RepBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1E293B')
    )
    bold_style = ParagraphStyle(
        'RepBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # Title Banner
    story.append(Paragraph("GeoSmart AI — 3D Pile Foundation Load Behaviour Simulator", title_style))
    story.append(Paragraph(f"Course: Foundation Engineering and Design (21CEE301T) | Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Spacer(1, 12))

    # Summary Table
    verdict = "SAFE DESIGN" if single_res.is_safe else "OVERLOAD WARNING"
    verdict_color = colors.HexColor('#166534') if single_res.is_safe else colors.HexColor('#991B1B')

    summary_data = [
        [Paragraph("<b>Applied Load (P)</b>", body_style), f"{single_res.applied_load:.1f} kN",
         Paragraph("<b>Status Verdict</b>", body_style), Paragraph(f"<b>{verdict}</b>", ParagraphStyle('V', parent=body_style, textColor=verdict_color))],
        [Paragraph("<b>Allowable Capacity (Q_all)</b>", body_style), f"{single_res.q_all:.1f} kN",
         Paragraph("<b>Utilization Ratio</b>", body_style), f"{single_res.utilization_ratio * 100:.1f}%"],
        [Paragraph("<b>Shaft Resistance (Q_s)</b>", body_style), f"{single_res.qs:.1f} kN ({single_res.qs_percent:.1f}%)",
         Paragraph("<b>Base Resistance (Q_b)</b>", body_style), f"{single_res.qb:.1f} kN ({single_res.qb_percent:.1f}%)"],
        [Paragraph("<b>Ultimate Capacity (Q_ult)</b>", body_style), f"{single_res.q_ult:.1f} kN",
         Paragraph("<b>Factor of Safety (FS)</b>", body_style), f"{single_res.factor_of_safety:.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[140, 120, 140, 140])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # Pile & Soil Parameters
    story.append(Paragraph("1. Design Inputs & Geotechnical Properties", h2_style))
    pile = single_res.pile
    soil = single_res.soil
    params_data = [
        ["Parameter", "Symbol / Description", "Value", "Units"],
        ["Pile Diameter", "D (Circular section)", f"{pile.diameter:.3f}", "m"],
        ["Embedded Length", "L", f"{pile.length:.2f}", "m"],
        ["Base Area / Shaft Area", "A_b / A_s", f"{pile.base_area:.4f} / {pile.shaft_area:.3f}", "m²"],
        ["Soil Stratum Type", soil.soil_type, "-", "-"],
        ["Effective Unit Weight", "gamma", f"{soil.unit_weight:.2f}", "kN/m³"],
        ["Undrained Cohesion", "c_u", f"{soil.cohesion_cu:.2f}", "kPa"],
        ["Friction Angle", "phi", f"{soil.friction_angle_phi:.1f}", "degrees"],
        ["Applied Vertical Load", "P (Column axial)", f"{single_res.applied_load:.1f}", "kN"]
    ]
    params_table = Table(params_data, colWidths=[140, 180, 120, 100])
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(params_table)
    story.append(Spacer(1, 14))

    # Calculations Steps
    story.append(Paragraph("2. Mathematical Derivations & Substituted Calculations", h2_style))
    for idx, s in enumerate(single_res.steps, 1):
        step_text = f"<b>Step {idx}: {s['name']}</b><br/>" \
                    f"Formula: {s['formula']}<br/>" \
                    f"Substituted: {s['substituted']}<br/>" \
                    f"<b>Result: {s['result']}</b>"
        story.append(Paragraph(step_text, body_style))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Educational Disclaimer:</b> This report is generated strictly for academic coursework demonstration (21CEE301T). It is not certified structural or geotechnical engineering design.", ParagraphStyle('D', parent=body_style, fontSize=7, textColor=colors.HexColor('#64748B'))))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_summary_csv(
    single_res: SinglePileResult,
    group_res: Optional[PileGroupResult] = None
) -> str:
    """Generates a downloadable CSV summary table of calculations."""
    records = [
        {"Parameter": "Pile Diameter D", "Value": single_res.pile.diameter, "Unit": "m"},
        {"Parameter": "Pile Length L", "Value": single_res.pile.length, "Unit": "m"},
        {"Parameter": "Base Area A_b", "Value": round(single_res.pile.base_area, 4), "Unit": "m^2"},
        {"Parameter": "Shaft Area A_s", "Value": round(single_res.pile.shaft_area, 3), "Unit": "m^2"},
        {"Parameter": "Soil Classification", "Value": single_res.soil.soil_type, "Unit": "-"},
        {"Parameter": "Undrained Cohesion c_u", "Value": single_res.soil.cohesion_cu, "Unit": "kPa"},
        {"Parameter": "Friction Angle phi", "Value": single_res.soil.friction_angle_phi, "Unit": "deg"},
        {"Parameter": "Applied Axial Load P", "Value": single_res.applied_load, "Unit": "kN"},
        {"Parameter": "Factor of Safety FS", "Value": single_res.factor_of_safety, "Unit": "-"},
        {"Parameter": "Shaft Resistance Q_s", "Value": round(single_res.qs, 2), "Unit": "kN"},
        {"Parameter": "Base Resistance Q_b", "Value": round(single_res.qb, 2), "Unit": "kN"},
        {"Parameter": "Ultimate Capacity Q_ult", "Value": round(single_res.q_ult, 2), "Unit": "kN"},
        {"Parameter": "Allowable Capacity Q_all", "Value": round(single_res.q_all, 2), "Unit": "kN"},
        {"Parameter": "Utilization Ratio UR", "Value": round(single_res.utilization_ratio, 3), "Unit": "-"},
        {"Parameter": "Safety Status", "Value": "SAFE" if single_res.is_safe else "OVERLOAD", "Unit": "-"},
    ]

    if group_res is not None and group_res.total_piles > 1:
        records.extend([
            {"Parameter": "Pile Group Rows m", "Value": group_res.rows, "Unit": "count"},
            {"Parameter": "Pile Group Cols n", "Value": group_res.cols, "Unit": "count"},
            {"Parameter": "Total Group Piles N", "Value": group_res.total_piles, "Unit": "count"},
            {"Parameter": "Spacing s", "Value": group_res.spacing, "Unit": "m"},
            {"Parameter": "Group Efficiency eta", "Value": round(group_res.group_efficiency, 4), "Unit": "fraction"},
            {"Parameter": "Group Ultimate Capacity Q_g,ult", "Value": round(group_res.q_group_ult, 2), "Unit": "kN"},
            {"Parameter": "Group Allowable Capacity Q_g,all", "Value": round(group_res.q_group_all, 2), "Unit": "kN"},
            {"Parameter": "Group Applied Load P_total", "Value": round(group_res.total_applied_load, 2), "Unit": "kN"},
            {"Parameter": "Group Utilization Ratio", "Value": round(group_res.group_utilization, 3), "Unit": "-"}
        ])

    df = pd.DataFrame(records)
    return df.to_csv(index=False)

