"""
GeoSmart AI -- 3D Pile Foundation Load Behaviour Simulator
Geotechnical Engineering Explanation Assistant
Course: Foundation Engineering and Design (21CEE301T)

Generates rule-based engineering diagnostics, load-transfer insights,
parametric design recommendations, and educational assumptions & cautions.
Completely functional offline without external API keys.
"""

from typing import Optional, Dict, Any, List
from core.calculations import SinglePileResult, PileGroupResult


def generate_rule_based_explanation(
    single_res: SinglePileResult,
    group_res: Optional[PileGroupResult] = None
) -> Dict[str, Any]:
    """
    Generates rule-based geotechnical commentary on safety,
    load-transfer mechanics, sensitivity, and engineering caveats.
    """
    pile = single_res.pile
    soil = single_res.soil
    is_group = group_res is not None and group_res.total_piles > 1

    if is_group:
        applied = group_res.total_applied_load
        capacity = group_res.q_group_all
        ur = group_res.group_utilization
        entity_name = f"the {group_res.total_piles}-pile foundation group"
    else:
        applied = single_res.applied_load
        capacity = single_res.q_all
        ur = single_res.utilization_ratio
        entity_name = "the single vertical pile"

    # 1. Capacity & Safety Status
    if ur <= 0.70:
        safety_status = "STABLE / CONSERVATIVE DESIGN"
        safety_tone = "success"
        safety_summary = (
            f"The applied load of **{applied:.1f} kN** utilizes only **{ur*100:.1f}%** "
            f"of the calculated allowable capacity ({capacity:.1f} kN). "
            f"The foundation has an ample safety margin (~{(1 - ur)*100:.1f}% surplus reserve) "
            f"under the applied factor of safety (FS = {single_res.factor_of_safety:.2f})."
        )
    elif ur <= 1.00:
        safety_status = "ADEQUATE / HIGH UTILIZATION"
        safety_tone = "warning"
        safety_summary = (
            f"The applied load of **{applied:.1f} kN** is within allowable capacity "
            f"({capacity:.1f} kN) at **{ur*100:.1f}% utilization**. While technically compliant, "
            f"the remaining safety margin is limited. Any transient surge loads or unanticipated site "
            f"variability could cause the demand to breach the allowable threshold."
        )
    else:
        safety_status = "OVERLOAD RISK / CAPACITY EXCEEDED"
        safety_tone = "danger"
        safety_summary = (
            f"**WARNING: Demand exceeds allowable working limit!** The applied load of **{applied:.1f} kN** "
            f"exceeds the calculated allowable capacity ({capacity:.1f} kN) by **{(ur - 1.0)*100:.1f}%** "
            f"(Utilization Ratio = {ur:.2f}). Foundation redesign (increasing embedment depth, enlarging pile diameter, "
            f"or adding additional piles) is required to restore an acceptable factor of safety."
        )

    # 2. Resistance Mechanism & Load Transfer Breakdown
    qs_pct = single_res.qs_percent
    qb_pct = single_res.qb_percent

    if qs_pct >= 75.0:
        mechanism_type = "Friction-Dominated Pile (Floating Pile)"
        mechanism_text = (
            f"**Shaft friction governs load transfer**, accounting for **{qs_pct:.1f}%** "
            f"({single_res.qs:.1f} kN) of ultimate capacity, whereas base resistance provides only "
            f"**{qb_pct:.1f}%** ({single_res.qb:.1f} kN). In cohesive clays or deep embedments, "
            f"the extensive circumferential area ({pile.shaft_area:.2f} m²) mobilizes substantial adhesion "
            f"(f_s = {single_res.unit_qs_avg:.1f} kPa) before significant toe displacement occurs."
        )
    elif qb_pct >= 60.0:
        mechanism_type = "End-Bearing Dominated Pile"
        mechanism_text = (
            f"**Base resistance governs load transfer**, supplying **{qb_pct:.1f}%** "
            f"({single_res.qb:.1f} kN) of total ultimate capacity, while shaft friction contributes "
            f"**{qs_pct:.1f}%** ({single_res.qs:.1f} kN). This typical behavior occurs in dense sands or when the toe "
            f"rests in high-strength bearing strata where high bearing capacity factors (N_q = {calculate_meyerhof_nq_safe(soil.friction_angle_phi):.1f}) "
            f"generate intense unit toe resistance (q_b = {single_res.unit_qb:.1f} kPa)."
        )
    else:
        mechanism_type = "Combined Friction and End-Bearing Pile"
        mechanism_text = (
            f"**Balanced load sharing** is observed: shaft friction provides **{qs_pct:.1f}%** "
            f"({single_res.qs:.1f} kN) and end bearing delivers **{qb_pct:.1f}%** ({single_res.qb:.1f} kN). "
            f"Notice that full shaft friction is mobilized at minimal settlement (typically 5 to 10 mm), "
            f"whereas full base resistance requires larger settlements (10% to 25% of pile diameter) to fully mobilize."
        )

    # 3. Parametric Sensitivity & Engineering Recommendations
    recommendations = []
    if soil.soil_type == "Cohesive (Clay)":
        recommendations.append(
            "**Lengthening Embedment Depth (L):** In cohesive soils, increasing pile length L directly increases shaft area A_s "
            "and engages deeper soil adhesion. Because end-bearing Nc = 9 is constant for deep piles, increasing depth is generally "
            "more economical for clay strata than expanding pile diameter."
        )
        recommendations.append(
            "**Adhesion Degradation Check:** For stiff to hard clays, adhesion factor alpha drops significantly (Tomlinson correlation). "
            "Ensure remoulding during driven installation or borehole softening during bored pile drilling is accounted for."
        )
    elif soil.soil_type == "Cohesionless (Sand)":
        recommendations.append(
            "**Enlarging Pile Diameter (D):** In granular soils with high friction angle phi, base capacity scales with D² while unit base "
            "resistance q_b is high. Enlarging the diameter provides a strong quadratic increase in end-bearing capacity."
        )
        recommendations.append(
            "**Critical Depth Awareness:** Notice that both shaft and base resistance taper once depth exceeds z_c (~15D to 20D) "
            "due to soil arching and particle crushing. Purely deepening a pile beyond z_c yields diminishing returns."
        )
    else:
        recommendations.append(
            "**Dual Optimization:** In mixed c-phi strata, both lengthening (to tap deeper confining stress) and widening (to tap base area) "
            "yield substantial capacity gains."
        )

    # 4. Group Efficiency Analysis (if Group)
    group_insights = []
    if is_group:
        eta_pct = group_res.group_efficiency * 100.0
        spacing_ratio = group_res.spacing_ratio
        group_insights.append(
            f"**Group Efficiency Factor (η = {eta_pct:.1f}%):** Computed via the Converse-Labarre formulation for "
            f"{group_res.rows}×{group_res.cols} layout at spacing s = {group_res.spacing:.2f} m ({spacing_ratio:.1f}D). "
            f"Due to stress overlap between adjacent piles, individual pile capacities cannot simply be summed without an efficiency reduction."
        )
        if group_res.block_capacity is not None:
            group_insights.append(
                f"**Block Failure Check:** The equivalent block capacity of the group perimeter was calculated at "
                f"**{group_res.block_capacity:.1f} kN**. If spacing is too tight (< 2.5D), block shear failure can govern over individual pile failure."
            )
        if spacing_ratio < 2.5:
            group_insights.append(
                f"**WARNING: Tight Spacing (s = {spacing_ratio:.1f}D < 2.5D):** Standard geotechnical codes (IS 2911, ACI, Eurocode 7) "
                f"recommend a minimum spacing of 2.5D to 3.0D for friction piles to prevent severe capacity loss and ground heave."
            )
        else:
            group_insights.append(
                f"**Standard Spacing (s = {spacing_ratio:.1f}D ≥ 2.5D):** Meets recommended practice for reducing mutual stress interaction."
            )

    # 5. Core Assumptions and Academic Limitations
    assumptions_list = [
        "**Educational Demonstration Scope:** This simulator is developed for Course 21CEE301T (Foundation Engineering and Design) as an interactive pedagogical tool. It is NOT certified engineering design software.",
        "**Homogeneous Stratum Assumption:** Calculations assume homogeneous or simplified two-layer soil properties along the embedded pile shaft.",
        "**Static Axial Loading Only:** Calculations evaluate vertical compressive axial resistance. Lateral loading, moment-induced pile head rotations, seismic shear, and cyclic degradation are not modelled in this MVP.",
        "**Equal Load Distribution:** Rigid pile cap action is assumed where all piles share applied vertical load equally. In reality, corner piles attract higher stiffness loads than interior piles.",
        "**Settlement Estimate Disclaimer:** The load-settlement curve is generated from an empirical Chin-Kondner hyperbolic model. True site settlement requires subsoil consolidation and elastic finite-element modeling.",
        "**Subsurface Investigation Mandate:** Real-world pile foundation design requires site-specific geotechnical investigations (SPT, CPT, lab triaxial tests) and field static load tests (ASTM D1143 / IS 2911)."
    ]

    return {
        "safety_status": safety_status,
        "safety_tone": safety_tone,
        "safety_summary": safety_summary,
        "mechanism_type": mechanism_type,
        "mechanism_text": mechanism_text,
        "recommendations": recommendations,
        "group_insights": group_insights,
        "assumptions": assumptions_list
    }


def calculate_meyerhof_nq_safe(phi: float) -> float:
    """Helper to return approximate N_q for commentary display."""
    from core.calculations import calculate_meyerhof_nq
    return calculate_meyerhof_nq(phi)

