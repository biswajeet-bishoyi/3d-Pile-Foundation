"""
GeoSmart AI -- 3D Pile Foundation Load Behaviour Simulator
Core Geotechnical Calculation Engine

Implements documented classical and modern geotechnical engineering methods:
- Cohesive Soils (Clay): Total Stress Method (Alpha Method / Tomlinson / API RP2A)
- Cohesionless Soils (Sand): Effective Stress Method (Beta Method / Meyerhof 1976)
- Mixed Soils (c-phi): General Static Superposition Formulation
- Pile Groups: Converse-Labarre Efficiency, Feld's Rule, Block Failure Analysis (Skempton / Terzaghi)
- Settlement: Hyperbolic Load-Settlement Response (Chin-Kondner / Poulos Elastic-Plastic formulation)

Educational demonstration software for Course 21CEE301T: Foundation Engineering and Design.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


@dataclass
class PileGeometry:
    """Represents pile dimensions and geometric properties."""
    diameter: float          # m (circular pile)
    length: float            # m (embedded depth)
    pile_type: str = "Bored Cast-in-situ"  # "Driven Concrete", "Bored Cast-in-situ", "Driven Steel"

    @property
    def base_area(self) -> float:
        """Base cross-sectional area A_b in m^2."""
        return math.pi * (self.diameter ** 2) / 4.0

    @property
    def perimeter(self) -> float:
        """Pile perimeter in m."""
        return math.pi * self.diameter

    @property
    def shaft_area(self) -> float:
        """Total shaft circumferential surface area A_s in m^2."""
        return self.perimeter * self.length

    @property
    def slenderness_ratio(self) -> float:
        """L / D ratio."""
        return self.length / max(self.diameter, 1e-4)


@dataclass
class SoilParameters:
    """Represents geotechnical soil profile parameters."""
    soil_type: str           # "Cohesive (Clay)", "Cohesionless (Sand)", "Mixed (c-phi)"
    unit_weight: float       # kN/m^3 (total or effective)
    cohesion_cu: float = 0.0 # kPa (undrained shear strength for clay / cohesion c' for c-phi)
    friction_angle_phi: float = 0.0  # degrees
    adhesion_factor_alpha: Optional[float] = None  # user override or computed
    earth_pressure_coeff_ks: Optional[float] = None # K_s (lateral earth pressure coefficient)
    delta_ratio: float = 0.75 # delta / phi (pile-soil friction angle ratio)
    critical_depth_ratio: float = 15.0 # z_c / D for limiting effective stress in sand
    water_table_depth: float = 999.0   # m from ground surface
    unit_weight_sat: float = 20.0      # kN/m^3 saturated unit weight if WT above toe
    elastic_modulus_es: float = 25000.0 # kPa (soil Young's modulus for settlement)
    poissons_ratio: float = 0.30       # soil Poisson's ratio


@dataclass
class SinglePileResult:
    """Detailed calculation outputs for a single pile."""
    pile: PileGeometry
    soil: SoilParameters
    applied_load: float      # kN
    factor_of_safety: float  # FS
    qs: float                # kN (shaft resistance)
    qb: float                # kN (base resistance)
    q_ult: float             # kN (ultimate capacity)
    q_all: float             # kN (allowable capacity)
    unit_qs_avg: float       # kPa (average unit skin friction)
    unit_qb: float           # kPa (unit base resistance)
    qs_percent: float        # % contribution of shaft
    qb_percent: float        # % contribution of base
    utilization_ratio: float # P / Q_all
    is_safe: bool
    status_text: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)


@dataclass
class PileGroupResult:
    """Group calculations including interaction and efficiency."""
    single_result: SinglePileResult
    rows: int                # m
    cols: int                # n
    spacing: float           # s in meters
    spacing_ratio: float     # s / D
    efficiency_method: str   # "Converse-Labarre", "Feld's Rule", "Block Failure", "Combined Minimum"
    group_efficiency: float  # eta
    q_group_sum: float       # n_total * Q_single_ult
    q_group_ult: float       # kN
    q_group_all: float       # kN
    total_applied_load: float# kN
    load_per_pile: float     # kN
    group_utilization: float # P_group / Q_group_all
    is_group_safe: bool
    block_capacity: Optional[float] = None # kN (if cohesive)
    group_cap_width: float = 0.0   # B_g (m)
    group_cap_length: float = 0.0  # L_g (m)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def total_piles(self) -> int:
        return self.rows * self.cols


# ============================================================================
# HELPER FORMULAS & CORRELATIONS
# ============================================================================

def estimate_alpha_tomlinson(cu: float, pa: float = 100.0) -> float:
    """
    Tomlinson / API RP2A empirical adhesion factor alpha for cohesive soils.
    alpha = 0.5 * (cu / pa)^(-0.5) for cu/pa > 1.0, and 1.0 for cu/pa <= 1.0, capped between 0.35 and 1.0.
    """
    if cu <= 0:
        return 0.0
    ratio = cu / pa
    if ratio <= 1.0:
        alpha = 1.0 - 0.5 * ratio
        return max(0.40, min(1.0, alpha))
    else:
        alpha = 0.5 * (ratio ** -0.5)
        return max(0.35, min(0.90, alpha))


def calculate_meyerhof_nq(phi_deg: float) -> float:
    """
    Meyerhof (1976) deep foundation bearing capacity factor N_q.
    Approximate closed-form formulation for deep circular piles.
    """
    phi_rad = math.radians(phi_deg)
    if phi_deg <= 0:
        return 1.0
    if phi_deg >= 45:
        phi_rad = math.radians(45.0)

    # Meyerhof deep pile N_q empirical fit
    # For shallow: Nq = tan^2(45 + phi/2) * exp(pi * tan(phi))
    # For deep driven/bored piles, Meyerhof values exceed shallow Terzaghi:
    shallow_nq = (math.tan(math.radians(45.0 + phi_deg / 2.0)) ** 2) * math.exp(math.pi * math.tan(phi_rad))
    # Depth enhancement factor for L/D >= 10 tends to deep Meyerhof table
    # Interpolated values from Meyerhof (1976) Table for deep foundations:
    phi_table = [20, 25, 28, 30, 32, 34, 36, 38, 40, 42, 45]
    nq_table = [8.0, 15.0, 21.0, 29.0, 40.0, 58.0, 86.0, 130.0, 200.0, 310.0, 550.0]
    return float(np.interp(phi_deg, phi_table, nq_table))


def get_default_ks(pile_type: str) -> float:
    """Default lateral earth pressure coefficient K_s based on installation method."""
    if "Driven" in pile_type or "Displacement" in pile_type:
        return 1.0  # Driven displacement pile (0.9 - 1.4)
    elif "Steel" in pile_type:
        return 0.8  # Low displacement steel pipe
    else:
        return 0.7  # Bored / cast-in-situ pile (0.5 - 0.7)


# ============================================================================
# SINGLE PILE CAPACITY ENGINE
# ============================================================================

def calculate_single_pile(
    pile: PileGeometry,
    soil: SoilParameters,
    applied_load: float,
    factor_of_safety: float = 2.5
) -> SinglePileResult:
    """
    Calculate axial capacity of a single vertical circular pile.
    Returns SinglePileResult with detailed intermediate steps and verification traces.
    """
    steps = []
    assumptions = []

    # Step 1: Geometry calculations
    A_b = pile.base_area
    A_s = pile.shaft_area
    perimeter = pile.perimeter
    L = pile.length
    D = pile.diameter

    steps.append({
        "name": "Pile Cross-Sectional Geometry",
        "formula": "A_b = \\frac{\\pi D^2}{4}, \\quad A_s = \\pi D L, \\quad P = \\pi D",
        "substituted": f"A_b = \\frac{{\\pi \\times {D:.3f}^2}}{{4}} = {A_b:.4f}\\text{{ m}}^2, \\quad A_s = \\pi \\times {D:.3f} \\times {L:.2f} = {A_s:.3f}\\text{{ m}}^2",
        "result": f"A_b = {A_b:.4f} m², A_s = {A_s:.3f} m², L/D = {pile.slenderness_ratio:.1f}",
        "units": "m²"
    })

    gamma = soil.unit_weight
    cu = soil.cohesion_cu
    phi = soil.friction_angle_phi

    if soil.soil_type == "Cohesive (Clay)":
        # Total stress approach (Alpha method)
        assumptions.append("Undrained total stress analysis (short-term condition) governed by undrained shear strength c_u.")
        assumptions.append("Skempton bearing capacity factor N_c = 9.0 applied at pile base for deep embedment (L/D >= 4).")
        assumptions.append("Equal adhesion factor alpha assumed along full embedment unless layered.")

        if soil.adhesion_factor_alpha is not None and soil.adhesion_factor_alpha > 0:
            alpha = soil.adhesion_factor_alpha
            alpha_origin = "User-specified adhesion factor"
        else:
            alpha = estimate_alpha_tomlinson(cu)
            alpha_origin = "Calculated via Tomlinson / API RP2A correlation"

        # Unit skin friction f_s = alpha * c_u
        f_s = alpha * cu
        Q_s = f_s * A_s

        steps.append({
            "name": "Shaft Resistance (Alpha Method)",
            "formula": "Q_s = \\alpha \\cdot c_u \\cdot A_s",
            "substituted": f"Q_s = {alpha:.3f} \\times {cu:.2f}\\text{{ kPa}} \\times {A_s:.3f}\\text{{ m}}^2",
            "result": f"Q_s = {Q_s:.2f} kN (Unit f_s = {f_s:.2f} kPa, \\alpha = {alpha:.3f} [{alpha_origin}])",
            "units": "kN"
        })

        # Base resistance Q_b = c_u * N_c * A_b
        # N_c = 9.0 for L/D >= 4
        N_c = 9.0 if pile.slenderness_ratio >= 4.0 else (6.0 * (1.0 + 0.2 * pile.slenderness_ratio))
        q_b = cu * N_c
        Q_b = q_b * A_b

        steps.append({
            "name": "Base Resistance (End Bearing)",
            "formula": "Q_b = c_u \\cdot N_c \\cdot A_b",
            "substituted": f"Q_b = {cu:.2f}\\text{{ kPa}} \\times {N_c:.1f} \\times {A_b:.4f}\\text{{ m}}^2",
            "result": f"Q_b = {Q_b:.2f} kN (Unit q_b = {q_b:.2f} kPa, N_c = {N_c:.1f})",
            "units": "kN"
        })

    elif soil.soil_type == "Cohesionless (Sand)":
        # Effective stress approach (Beta method & Meyerhof base resistance)
        assumptions.append("Drained effective stress analysis based on internal friction angle phi and effective overburden stress.")
        assumptions.append("Critical depth z_c cap applied (Meyerhof 1976) to prevent unrealistic linearly infinite stresses.")
        assumptions.append(f"Interface friction angle delta taken as {soil.delta_ratio:.2f} * phi.")

        K_s = soil.earth_pressure_coeff_ks if soil.earth_pressure_coeff_ks is not None else get_default_ks(pile.pile_type)
        delta_deg = soil.delta_ratio * phi
        delta_rad = math.radians(delta_deg)

        # Critical depth z_c = critical_depth_ratio * D
        z_c = soil.critical_depth_ratio * D
        z_eff_toe = min(L, z_c)

        # Effective vertical stress at mid-depth for shaft resistance
        # If L <= z_c, sigma'_v increases linearly from 0 to gamma * L, avg = 0.5 * gamma * L
        # If L > z_c, shaft is in two zones: 0 to z_c (triangular) and z_c to L (constant = gamma * z_c)
        if L <= z_c:
            sigma_v_avg = 0.5 * gamma * L
        else:
            area_stress = (0.5 * gamma * z_c * z_c) + (gamma * z_c * (L - z_c))
            sigma_v_avg = area_stress / L

        beta = K_s * math.tan(delta_rad)
        f_s = beta * sigma_v_avg
        # Limiting unit skin friction (Meyerhof: ~100 kPa for medium sand, 120 kPa for dense)
        f_s_limit = 100.0 if phi < 35 else 120.0
        f_s_applied = min(f_s, f_s_limit)
        Q_s = f_s_applied * A_s

        steps.append({
            "name": "Shaft Resistance (Beta Method with Limiting Stress)",
            "formula": "Q_s = K_s \\cdot \\bar{\\sigma}'_v \\cdot \\tan(\\delta) \\cdot A_s = \\beta \\cdot \\bar{\\sigma}'_v \\cdot A_s",
            "substituted": f"Q_s = {K_s:.2f} \\times {sigma_v_avg:.2f}\\text{{ kPa}} \\times \\tan({delta_deg:.1f}^\\circ) \\times {A_s:.3f}\\text{{ m}}^2",
            "result": f"Q_s = {Q_s:.2f} kN (\\beta = {beta:.3f}, \\bar{{\\sigma}}'_v = {sigma_v_avg:.1f} kPa, z_c = {z_c:.1f} m, f_s = {f_s_applied:.1f} kPa)",
            "units": "kN"
        })

        # Base resistance: Meyerhof 1976
        # sigma'_v at toe capped at z_c
        sigma_v_toe = gamma * min(L, z_c)
        N_q = calculate_meyerhof_nq(phi)
        q_b_raw = sigma_v_toe * N_q
        # Limiting base resistance q_b_limit = 50 * N_q * tan(phi) kPa (Meyerhof)
        q_b_limit = 50.0 * N_q * math.tan(math.radians(phi))
        q_b = min(q_b_raw, q_b_limit)
        Q_b = q_b * A_b

        steps.append({
            "name": "Base Resistance (Meyerhof Deep Foundation Formulation)",
            "formula": "Q_b = \\sigma'_{v,toe} \\cdot N_q \\cdot A_b \\le q_{b,limit} \\cdot A_b",
            "substituted": f"Q_b = \\min({sigma_v_toe:.1f} \\times {N_q:.1f}, {q_b_limit:.1f})\\text{{ kPa}} \\times {A_b:.4f}\\text{{ m}}^2",
            "result": f"Q_b = {Q_b:.2f} kN (Unit q_b = {q_b:.1f} kPa, N_q = {N_q:.1f}, q_b(limit) = {q_b_limit:.1f} kPa)",
            "units": "kN"
        })

    else:
        # Mixed (c - phi) Soil
        assumptions.append("Superposition static formula for general c-phi soil stratum.")
        assumptions.append("Both cohesion adhesion and frictional interface shearing mobilized.")

        alpha = soil.adhesion_factor_alpha if soil.adhesion_factor_alpha is not None else 0.50
        K_s = soil.earth_pressure_coeff_ks if soil.earth_pressure_coeff_ks is not None else get_default_ks(pile.pile_type)
        delta_deg = soil.delta_ratio * phi
        delta_rad = math.radians(delta_deg)

        z_c = soil.critical_depth_ratio * D
        sigma_v_avg = 0.5 * gamma * min(L, z_c)
        sigma_v_toe = gamma * min(L, z_c)

        f_s = (alpha * cu) + (K_s * sigma_v_avg * math.tan(delta_rad))
        Q_s = f_s * A_s

        N_c = 9.0
        N_q = calculate_meyerhof_nq(phi)
        q_b = (cu * N_c) + (sigma_v_toe * N_q)
        Q_b = q_b * A_b

        steps.append({
            "name": "Shaft Resistance (c-phi Superposition)",
            "formula": "Q_s = (\\alpha c_u + K_s \\bar{\\sigma}'_v \\tan\\delta) A_s",
            "substituted": f"Q_s = ({alpha:.2f} \\times {cu:.1f} + {K_s:.2f} \\times {sigma_v_avg:.1f} \\times \\tan({delta_deg:.1f}^\\circ)) \\times {A_s:.3f}",
            "result": f"Q_s = {Q_s:.2f} kN (Unit f_s = {f_s:.2f} kPa)",
            "units": "kN"
        })

        steps.append({
            "name": "Base Resistance (c-phi Superposition)",
            "formula": "Q_b = (c_u N_c + \\sigma'_{v,toe} N_q) A_b",
            "substituted": f"Q_b = ({cu:.1f} \\times 9.0 + {sigma_v_toe:.1f} \\times {N_q:.1f}) \\times {A_b:.4f}",
            "result": f"Q_b = {Q_b:.2f} kN (Unit q_b = {q_b:.2f} kPa)",
            "units": "kN"
        })

    # Total Ultimate and Allowable Capacity
    Q_ult = Q_s + Q_b
    Q_all = Q_ult / max(factor_of_safety, 1.0)
    qs_pct = (Q_s / Q_ult) * 100.0 if Q_ult > 0 else 0.0
    qb_pct = (Q_b / Q_ult) * 100.0 if Q_ult > 0 else 0.0
    utilization = applied_load / max(Q_all, 1e-4)
    is_safe = applied_load <= Q_all

    if utilization <= 0.85:
        status_text = "SAFE / Within Calculated Allowable Capacity (Optimal Margin)"
    elif utilization <= 1.0:
        status_text = "ACCEPTABLE / High Utilization (Near Allowable Limit)"
    else:
        status_text = f"OVERLOAD RISK / Exceeds Calculated Allowable Capacity (UR = {utilization:.2f})"

    steps.append({
        "name": "Total Ultimate Axial Capacity",
        "formula": "Q_{ult} = Q_s + Q_b",
        "substituted": f"Q_{{ult}} = {Q_s:.2f}\\text{{ kN}} + {Q_b:.2f}\\text{{ kN}}",
        "result": f"Q_{{ult}} = {Q_ult:.2f} kN (Shaft: {qs_pct:.1f}%, Base: {qb_pct:.1f}%)",
        "units": "kN"
    })

    steps.append({
        "name": "Calculated Allowable Working Capacity",
        "formula": "Q_{all} = \\frac{Q_{ult}}{FS}",
        "substituted": f"Q_{{all}} = \\frac{{{Q_ult:.2f}\\text{{ kN}}}}{{{factor_of_safety:.2f}}}",
        "result": f"Q_{{all}} = {Q_all:.2f} kN (Applied Load P = {applied_load:.1f} kN, UR = {utilization:.2f})",
        "units": "kN"
    })

    return SinglePileResult(
        pile=pile,
        soil=soil,
        applied_load=applied_load,
        factor_of_safety=factor_of_safety,
        qs=Q_s,
        qb=Q_b,
        q_ult=Q_ult,
        q_all=Q_all,
        unit_qs_avg=Q_s / A_s if A_s > 0 else 0.0,
        unit_qb=Q_b / A_b if A_b > 0 else 0.0,
        qs_percent=qs_pct,
        qb_percent=qb_pct,
        utilization_ratio=utilization,
        is_safe=is_safe,
        status_text=status_text,
        steps=steps,
        assumptions=assumptions
    )


# ============================================================================
# PILE GROUP CAPACITY ENGINE
# ============================================================================

def calculate_converse_labarre_efficiency(rows: int, cols: int, diameter: float, spacing: float) -> float:
    """
    Converse-Labarre equation for pile group efficiency eta:
    eta = 1 - [ theta / 90 * { (n-1)*m + (m-1)*n } / (m * n) ]
    where theta = arctan(D / s) in degrees.
    """
    m, n = rows, cols
    if m == 1 and n == 1:
        return 1.0
    if spacing <= diameter:
        return 0.50

    theta_deg = math.degrees(math.atan(diameter / spacing))
    numerator = ((n - 1) * m) + ((m - 1) * n)
    denominator = m * n
    eta = 1.0 - (theta_deg / 90.0) * (numerator / denominator)
    return max(0.40, min(1.0, eta))


def calculate_pile_group(
    single_res: SinglePileResult,
    rows: int,
    cols: int,
    spacing: float,
    total_applied_load: float,
    efficiency_method: str = "Converse-Labarre"
) -> PileGroupResult:
    """
    Calculate pile group behavior, individual sum, block capacity, and group efficiency.
    Discloses educational simplifications and checks block failure for cohesive soils.
    """
    m, n = rows, cols
    N = m * n
    D = single_res.pile.diameter
    L = single_res.pile.length
    FS = single_res.factor_of_safety
    spacing_ratio = spacing / max(D, 1e-4)

    steps = []
    notes = [
        "Rigid pile cap assumed with equal axial load distribution among all piles in group.",
        "Group interaction and block failure simplified for educational demonstration (Course 21CEE301T).",
        "Unequal corner/center pile load distributions require advanced finite element/boundary element solvers."
    ]

    # Group footprint dimensions (outer pile centers + pile diameter)
    B_g = ((m - 1) * spacing) + D
    L_g = ((n - 1) * spacing) + D

    # 1. Sum of individual piles
    Q_sum_ult = N * single_res.q_ult

    # 2. Efficiency calculation
    eta_cl = calculate_converse_labarre_efficiency(m, n, D, spacing)

    # 3. Block failure check (for cohesive soils)
    block_cap = None
    if single_res.soil.soil_type in ["Cohesive (Clay)", "Mixed (c-phi)"]:
        cu = single_res.soil.cohesion_cu
        # Perimeter of block P_g = 2 * (B_g + L_g)
        P_g = 2.0 * (B_g + L_g)
        # Base area of block A_gb = B_g * L_g
        A_gb = B_g * L_g
        # Skempton Nc for rectangular foundation
        Nc_group = 9.0 * min(1.0, (1.0 + 0.2 * (B_g / max(L_g, 1e-4))))
        block_cap = (P_g * L * cu) + (cu * Nc_group * A_gb)
        notes.append(f"Block failure capacity analyzed: Q_block = {block_cap:.1f} kN (Perimeter = {P_g:.2f} m, Base = {A_gb:.2f} m²).")

    # Determine ultimate group capacity based on selected method
    if efficiency_method == "Converse-Labarre":
        eta = eta_cl
        Q_group_ult = Q_sum_ult * eta
    elif efficiency_method == "Sum of Individual (No Loss)":
        eta = 1.0
        Q_group_ult = Q_sum_ult
    elif efficiency_method == "Block Failure" and block_cap is not None:
        Q_group_ult = block_cap
        eta = block_cap / Q_sum_ult if Q_sum_ult > 0 else 1.0
    else:  # Combined Minimum (governing engineering check)
        if block_cap is not None:
            Q_group_ult = min(Q_sum_ult * eta_cl, block_cap)
            eta = Q_group_ult / Q_sum_ult if Q_sum_ult > 0 else eta_cl
        else:
            eta = eta_cl
            Q_group_ult = Q_sum_ult * eta

    Q_group_all = Q_group_ult / max(FS, 1.0)
    load_per_pile = total_applied_load / max(N, 1)
    group_ur = total_applied_load / max(Q_group_all, 1e-4)
    is_safe = total_applied_load <= Q_group_all

    steps.append({
        "name": "Pile Group Configuration",
        "formula": "N = m \\times n, \\quad B_g = (m-1)s + D, \\quad L_g = (n-1)s + D",
        "substituted": f"N = {m} \\times {n} = {N}, \\quad B_g = {B_g:.2f}\\text{{ m}}, \\quad L_g = {L_g:.2f}\\text{{ m}}, \\quad s = {spacing:.2f}\\text{{ m}} ({spacing_ratio:.1f}D)",
        "result": f"N = {N} piles, Spacing = {spacing:.2f} m ({spacing_ratio:.1f}D)",
        "units": "count / m"
    })

    steps.append({
        "name": "Converse-Labarre Group Efficiency",
        "formula": "\\eta = 1 - \\frac{\\theta}{90^\\circ} \\left[ \\frac{(n-1)m + (m-1)n}{mn} \\right], \\quad \\theta = \\arctan(D/s)",
        "substituted": f"\\theta = \\arctan({D:.2f}/{spacing:.2f}) = {math.degrees(math.atan(D/spacing)):.2f}^\\circ \\implies \\eta = {eta_cl:.3f}",
        "result": f"Group Efficiency \\eta = {eta_cl:.3f} ({eta_cl * 100:.1f}%)",
        "units": "fraction"
    })

    steps.append({
        "name": "Governing Ultimate & Allowable Group Capacity",
        "formula": "Q_{g,ult} = \\eta \\cdot \\sum Q_{ult}, \\quad Q_{g,all} = \\frac{Q_{g,ult}}{FS}",
        "substituted": f"Q_{{g,ult}} = {eta:.3f} \\times ({N} \\times {single_res.q_ult:.1f}\\text{{ kN}}) = {Q_group_ult:.1f}\\text{{ kN}}",
        "result": f"Q_{{g,ult}} = {Q_group_ult:.1f} kN, Q_{{g,all}} = {Q_group_all:.1f} kN (Applied: {total_applied_load:.1f} kN, UR = {group_ur:.2f})",
        "units": "kN"
    })

    return PileGroupResult(
        single_result=single_res,
        rows=rows,
        cols=cols,
        spacing=spacing,
        spacing_ratio=spacing_ratio,
        efficiency_method=efficiency_method,
        group_efficiency=eta,
        q_group_sum=Q_sum_ult,
        q_group_ult=Q_group_ult,
        q_group_all=Q_group_all,
        total_applied_load=total_applied_load,
        load_per_pile=load_per_pile,
        group_utilization=group_ur,
        is_group_safe=is_safe,
        block_capacity=block_cap,
        group_cap_width=B_g,
        group_cap_length=L_g,
        steps=steps,
        notes=notes
    )


# ============================================================================
# LOAD-SETTLEMENT HYPERBOLIC MODEL
# ============================================================================

def generate_load_settlement_curve(
    q_ult: float,
    pile: PileGeometry,
    soil: SoilParameters,
    max_settlement_mm: float = 40.0,
    num_points: int = 50
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Generates an illustrative non-linear load-settlement response curve
    using the established Chin-Kondner hyperbolic relationship:
    P = S / [ (1/K_i) + (S / Q_ult) ]
    where K_i is initial elastic stiffness (kN/mm).
    """
    # Estimate initial stiffness K_i:
    # Ep for concrete ~ 25 to 30 GPa = 25e6 to 30e6 kPa
    E_p = 28e6  # kPa (concrete)
    E_s = soil.elastic_modulus_es  # kPa
    D = pile.diameter
    L = pile.length

    # Poulos & Davis elastic interaction approximation
    # K_i (kN/mm) = Q / S
    # Initial settlement ~ P / (E_s * D * I_p)
    I_p = 0.50  # influence factor for semi-infinite elastic mass
    k_soil_kN_per_m = (E_s * D) / I_p  # kN/m
    k_pile_kN_per_m = (pile.base_area * E_p) / max(L, 1.0)
    # Combined series/parallel stiffness
    k_initial_kN_per_m = 0.75 * k_soil_kN_per_m + 0.25 * k_pile_kN_per_m
    k_i = max(k_initial_kN_per_m / 1000.0, 10.0)  # in kN/mm

    settlements_mm = np.linspace(0.0, max_settlement_mm, num_points)
    loads_kN = np.zeros_like(settlements_mm)

    for i, s in enumerate(settlements_mm):
        if s == 0:
            loads_kN[i] = 0.0
        else:
            # Hyperbolic formula: P = s / ( (1/K_i) + (s / Q_ult) )
            # As s -> infinity, P -> Q_ult
            denom = (1.0 / k_i) + (s / max(q_ult, 1.0))
            loads_kN[i] = min(s / denom, q_ult)

    return settlements_mm, loads_kN, k_i

