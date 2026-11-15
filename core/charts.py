"""
GeoSmart AI -- 3D Pile Foundation Load Behaviour Simulator
Interactive Geotechnical Engineering Charts (Plotly)
Course: Foundation Engineering and Design (21CEE301T)

Charts implemented:
1. Applied Load vs. Allowable & Ultimate Capacity (with safety threshold zones)
2. Shaft vs. Base Resistance Breakdown (Donut & Breakdown)
3. Pile Embedment Length Sensitivity (L vs Q_s, Q_b, Q_all)
4. Pile Diameter Sensitivity (D vs Q_s, Q_b, Q_all)
5. Illustrative Load-Settlement Response (Hyperbolic model + Test Data Overlay)
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.calculations import (
    SinglePileResult,
    PileGroupResult,
    PileGeometry,
    SoilParameters,
    calculate_single_pile,
    generate_load_settlement_curve
)


def plot_load_vs_capacity(
    single_res: SinglePileResult,
    group_res: Optional[PileGroupResult] = None
) -> go.Figure:
    """
    Chart 1: Applied Load vs Allowable & Ultimate Capacity
    Shows utilization ratio, safety margin, and overload indicator.
    """
    is_group = group_res is not None and group_res.total_piles > 1
    if is_group:
        p_load = group_res.total_applied_load
        q_all = group_res.q_group_all
        q_ult = group_res.q_group_ult
        title_suffix = f"Pile Group ({group_res.total_piles} Piles)"
    else:
        p_load = single_res.applied_load
        q_all = single_res.q_all
        q_ult = single_res.q_ult
        title_suffix = "Single Pile"

    ur = p_load / max(q_all, 1e-4)

    # Bar colors
    color_load = "#D32F2F" if ur > 1.0 else ("#F57C00" if ur > 0.85 else "#388E3C")

    fig = go.Figure()

    categories = ["Applied Load (P)", "Allowable Capacity (Q_all)", "Ultimate Capacity (Q_ult)"]
    values = [p_load, q_all, q_ult]
    colors = [color_load, "#1976D2", "#455A64"]

    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker=dict(color=colors, line=dict(color="#263238", width=1.5)),
        text=[f"<b>{v:.1f} kN</b>" for v in values],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Value: %{y:.1f} kN<extra></extra>",
        width=0.45
    ))

    # Reference line for Allowable Limit
    fig.add_hline(
        y=q_all,
        line_dash="dot",
        line_color="#1976D2",
        annotation_text=f"Allowable Limit (FS={single_res.factor_of_safety:.1f})",
        annotation_position="bottom right"
    )

    status_badge = "SAFE (UR ≤ 1.0)" if ur <= 1.0 else f"OVERLOADED (UR = {ur:.2f})"
    badge_color = "#2E7D32" if ur <= 1.0 else "#C62828"

    fig.update_layout(
        title=dict(
            text=f"<b>Applied Load vs. Capacity Comparison — {title_suffix}</b><br><sup>Status: <span style='color:{badge_color};font-weight:bold;'>{status_badge}</span> | Utilization: {ur * 100:.1f}%</sup>",
            x=0.04, y=0.95
        ),
        yaxis=dict(title="Axial Force (kN)", gridcolor="#E2E8F0"),
        xaxis=dict(gridcolor="#E2E8F0"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        height=400,
        margin=dict(l=40, r=40, t=75, b=40)
    )

    return fig


def plot_resistance_breakdown(single_res: SinglePileResult) -> go.Figure:
    """
    Chart 2: Shaft vs Base Resistance Contribution (Donut Chart)
    """
    labels = ["Shaft Resistance (Q_s)", "Base Resistance (Q_b)"]
    values = [single_res.qs, single_res.qb]
    colors = ["#2E7D32", "#1565C0"]

    dominant = "Shaft-Bearing (Friction Pile)" if single_res.qs > single_res.qb else "End-Bearing Dominant"

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textinfo="label+percent",
        texttemplate="<b>%{label}</b><br>%{value:.1f} kN<br>(%{percent})",
        hovertemplate="<b>%{label}</b><br>Capacity: %{value:.1f} kN<br>Share: %{percent}<extra></extra>"
    )])

    fig.update_layout(
        title=dict(
            text=f"<b>Resistance Mechanism Breakdown</b><br><sup>Classification: <b>{dominant}</b> (Total Q_ult = {single_res.q_ult:.1f} kN)</sup>",
            x=0.04, y=0.95
        ),
        annotations=[dict(
            text=f"<b>Q_ult</b><br>{single_res.q_ult:.0f} kN",
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False
        )],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        height=380,
        margin=dict(l=30, r=30, t=70, b=40)
    )

    return fig


def plot_length_sensitivity(
    pile: PileGeometry,
    soil: SoilParameters,
    applied_load: float,
    factor_of_safety: float = 2.5,
    min_length: float = 4.0,
    max_length: float = 30.0,
    points: int = 35
) -> go.Figure:
    """
    Chart 3: Pile Embedment Length Sensitivity Curve (L vs Q_s, Q_b, Q_all)
    """
    lengths = np.linspace(min_length, max_length, points)
    qs_list, qb_list, qult_list, qall_list = [], [], [], []

    for l_val in lengths:
        temp_pile = PileGeometry(diameter=pile.diameter, length=l_val, pile_type=pile.pile_type)
        res = calculate_single_pile(temp_pile, soil, applied_load=applied_load, factor_of_safety=factor_of_safety)
        qs_list.append(res.qs)
        qb_list.append(res.qb)
        qult_list.append(res.q_ult)
        qall_list.append(res.q_all)

    fig = go.Figure()

    # Shaft resistance curve
    fig.add_trace(go.Scatter(
        x=lengths, y=qs_list,
        mode="lines", name="Shaft Resistance Q_s",
        line=dict(color="#2E7D32", width=2.5)
    ))

    # Base resistance curve
    fig.add_trace(go.Scatter(
        x=lengths, y=qb_list,
        mode="lines", name="Base Resistance Q_b",
        line=dict(color="#1565C0", width=2.5, dash="dash")
    ))

    # Allowable capacity curve
    fig.add_trace(go.Scatter(
        x=lengths, y=qall_list,
        mode="lines", name=f"Allowable Capacity Q_all (FS={factor_of_safety:.1f})",
        line=dict(color="#E65100", width=3)
    ))

    # Total ultimate capacity curve
    fig.add_trace(go.Scatter(
        x=lengths, y=qult_list,
        mode="lines", name="Ultimate Capacity Q_ult",
        line=dict(color="#37474F", width=2, dash="dot")
    ))

    # Current design length marker
    curr_res = calculate_single_pile(pile, soil, applied_load=applied_load, factor_of_safety=factor_of_safety)
    fig.add_trace(go.Scatter(
        x=[pile.length], y=[curr_res.q_all],
        mode="markers+text",
        marker=dict(color="#D32F2F", size=12, symbol="diamond"),
        text=[f"Current L={pile.length:.1f}m (Q_all={curr_res.q_all:.1f} kN)"],
        textposition="top left",
        name="Current Design Point"
    ))

    # Applied load reference line
    fig.add_hline(
        y=applied_load,
        line_dash="dash",
        line_color="#D32F2F",
        annotation_text=f"Applied Load P = {applied_load:.1f} kN",
        annotation_position="bottom right"
    )

    fig.update_layout(
        title=dict(
            text="<b>Parametric Sensitivity: Pile Embedment Length vs. Capacity</b><br><sup>Shows how shaft and base resistance scale with increasing pile depth</sup>",
            x=0.04, y=0.95
        ),
        xaxis=dict(title="Pile Embedded Length L (m)", gridcolor="#E2E8F0"),
        yaxis=dict(title="Axial Resistance (kN)", gridcolor="#E2E8F0"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=450,
        margin=dict(l=40, r=40, t=75, b=60)
    )

    return fig


def plot_diameter_sensitivity(
    pile: PileGeometry,
    soil: SoilParameters,
    applied_load: float,
    factor_of_safety: float = 2.5,
    min_dia: float = 0.30,
    max_dia: float = 1.50,
    points: int = 30
) -> go.Figure:
    """
    Chart 4: Pile Diameter Sensitivity Curve (D vs Q_s, Q_b, Q_all)
    Highlights linear scaling of shaft area vs quadratic scaling of base area.
    """
    diameters = np.linspace(min_dia, max_dia, points)
    qs_list, qb_list, qult_list, qall_list = [], [], [], []

    for d_val in diameters:
        temp_pile = PileGeometry(diameter=d_val, length=pile.length, pile_type=pile.pile_type)
        res = calculate_single_pile(temp_pile, soil, applied_load=applied_load, factor_of_safety=factor_of_safety)
        qs_list.append(res.qs)
        qb_list.append(res.qb)
        qult_list.append(res.q_ult)
        qall_list.append(res.q_all)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=diameters, y=qs_list,
        mode="lines", name="Shaft Resistance Q_s (linear in D)",
        line=dict(color="#2E7D32", width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=diameters, y=qb_list,
        mode="lines", name="Base Resistance Q_b (quadratic in D²)",
        line=dict(color="#1565C0", width=2.5, dash="dash")
    ))

    fig.add_trace(go.Scatter(
        x=diameters, y=qall_list,
        mode="lines", name=f"Allowable Capacity Q_all (FS={factor_of_safety:.1f})",
        line=dict(color="#E65100", width=3)
    ))

    curr_res = calculate_single_pile(pile, soil, applied_load=applied_load, factor_of_safety=factor_of_safety)
    fig.add_trace(go.Scatter(
        x=[pile.diameter], y=[curr_res.q_all],
        mode="markers+text",
        marker=dict(color="#D32F2F", size=12, symbol="circle"),
        text=[f"Current D={pile.diameter:.2f}m"],
        textposition="top left",
        name="Current Design Diameter"
    ))

    fig.add_hline(
        y=applied_load,
        line_dash="dash",
        line_color="#D32F2F",
        annotation_text=f"Applied Load P = {applied_load:.1f} kN",
        annotation_position="bottom right"
    )

    fig.update_layout(
        title=dict(
            text="<b>Parametric Sensitivity: Pile Diameter vs. Capacity</b><br><sup>Base resistance grows with D² while shaft resistance scales linearly with D</sup>",
            x=0.04, y=0.95
        ),
        xaxis=dict(title="Pile Diameter D (m)", gridcolor="#E2E8F0"),
        yaxis=dict(title="Axial Resistance (kN)", gridcolor="#E2E8F0"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=450,
        margin=dict(l=40, r=40, t=75, b=60)
    )

    return fig


def plot_load_settlement_curve(
    single_res: SinglePileResult,
    test_data_df: Optional[pd.DataFrame] = None,
    max_settlement_mm: float = 40.0
) -> go.Figure:
    """
    Chart 5: Illustrative Load-Settlement Response (Chin-Kondner Hyperbolic Formulation)
    Clearly labeled as illustrative. Allows optional overlay of uploaded test data.
    """
    settlements_mm, loads_kN, k_i = generate_load_settlement_curve(
        q_ult=single_res.q_ult,
        pile=single_res.pile,
        soil=single_res.soil,
        max_settlement_mm=max_settlement_mm
    )

    fig = go.Figure()

    # Theoretical Hyperbolic curve (Settlement on X, Load on Y)
    fig.add_trace(go.Scatter(
        x=settlements_mm, y=loads_kN,
        mode="lines",
        line=dict(color="#1E88E5", width=3),
        name="Conceptual Hyperbolic Model (Chin-Kondner)",
        hovertemplate="Settlement: %{x:.2f} mm<br>Load: %{y:.1f} kN<extra></extra>"
    ))

    # Applied working load marker on curve
    # Find settlement at applied load
    applied_load = single_res.applied_load
    if applied_load < single_res.q_ult:
        # S = P / (K_i * (1 - P/Q_ult))
        s_working = applied_load / (k_i * (1.0 - applied_load / single_res.q_ult))
        if 0 <= s_working <= max_settlement_mm:
            fig.add_trace(go.Scatter(
                x=[s_working], y=[applied_load],
                mode="markers+text",
                marker=dict(color="#D32F2F", size=11, symbol="star"),
                text=[f"Working Pt: S≈{s_working:.1f} mm"],
                textposition="bottom right",
                name=f"Working Load (P = {applied_load:.1f} kN)"
            ))

    # Allowable and Ultimate capacity reference lines
    fig.add_hline(
        y=single_res.q_all,
        line_dash="dot",
        line_color="#F57C00",
        annotation_text=f"Q_all = {single_res.q_all:.1f} kN",
        annotation_position="bottom right"
    )

    fig.add_hline(
        y=single_res.q_ult,
        line_dash="dash",
        line_color="#455A64",
        annotation_text=f"Q_ult = {single_res.q_ult:.1f} kN (Asymptote)",
        annotation_position="top right"
    )

    # Optional Overlay of Imported Test Data
    has_test_data = False
    if test_data_df is not None and not test_data_df.empty:
        # Identify columns
        cols = [c.lower() for c in test_data_df.columns]
        load_col = None
        settle_col = None
        for orig, c in zip(test_data_df.columns, cols):
            if "load" in c or "p" in c or "kn" in c:
                load_col = orig
            elif "settle" in c or "s" in c or "mm" in c or "disp" in c:
                settle_col = orig

        if load_col and settle_col:
            test_s = test_data_df[settle_col].values
            test_p = test_data_df[load_col].values
            fig.add_trace(go.Scatter(
                x=test_s, y=test_p,
                mode="markers+lines",
                marker=dict(color="#8E24AA", size=8, symbol="circle"),
                line=dict(color="#8E24AA", width=2, dash="dash"),
                name="Imported Field Test Data",
                hovertemplate="Measured Test:<br>Settlement: %{x:.2f} mm<br>Load: %{y:.1f} kN<extra></extra>"
            ))
            has_test_data = True

    subtitle_text = "Calibrated with Imported Load Test Data" if has_test_data else "<b>Illustrative Conceptual Response</b> (Chin-Kondner Elastic-Plastic Model — Non-FEA)"

    fig.update_layout(
        title=dict(
            text=f"<b>Axial Load vs. Pile-Head Settlement Curve</b><br><sup>*{subtitle_text}</sup>",
            x=0.04, y=0.95
        ),
        xaxis=dict(title="Settlement S (mm)", gridcolor="#E2E8F0"),
        yaxis=dict(title="Applied Axial Load P (kN)", gridcolor="#E2E8F0"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=450,
        margin=dict(l=40, r=40, t=75, b=60)
    )

    return fig

