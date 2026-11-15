"""
GeoSmart AI -- 3D Pile Foundation Load Behaviour Simulator
Automated Validation & Unit Test Suite
Course: Foundation Engineering and Design (21CEE301T)
"""

import math
import pytest
from core.calculations import (
    PileGeometry,
    SoilParameters,
    calculate_single_pile,
    calculate_pile_group,
    calculate_converse_labarre_efficiency,
    generate_load_settlement_curve
)
from core.presets import BENCHMARK_PRESETS


def test_pile_geometry():
    """Verify circular pile geometric area and perimeter formulas."""
    pile = PileGeometry(diameter=0.50, length=10.0)
    expected_ab = math.pi * (0.50 ** 2) / 4.0
    expected_as = math.pi * 0.50 * 10.0
    expected_p = math.pi * 0.50

    assert pytest.approx(pile.base_area, rel=1e-4) == expected_ab
    assert pytest.approx(pile.shaft_area, rel=1e-4) == expected_as
    assert pytest.approx(pile.perimeter, rel=1e-4) == expected_p
    assert pytest.approx(pile.slenderness_ratio, rel=1e-4) == 20.0


def test_case_1_das_clay():
    """
    Hand-worked verification against Braja M. Das / Tomlinson Alpha Method:
    D = 0.45 m, L = 15.0 m, cu = 40.0 kPa, gamma = 18.0 kN/m3, alpha = 0.70, FS = 2.5.
    Hand-calculations:
    A_b = pi * 0.45^2 / 4 = 0.159043 m2
    A_s = pi * 0.45 * 15.0 = 21.20575 m2
    Q_s = 0.70 * 40 * 21.20575 = 593.761 kN
    Q_b = 9.0 * 40 * 0.159043 = 57.255 kN
    Q_ult = 593.761 + 57.255 = 651.016 kN
    Q_all = 651.016 / 2.5 = 260.406 kN
    """
    pile = PileGeometry(diameter=0.45, length=15.0, pile_type="Driven Concrete")
    soil = SoilParameters(
        soil_type="Cohesive (Clay)",
        unit_weight=18.0,
        cohesion_cu=40.0,
        adhesion_factor_alpha=0.70
    )
    res = calculate_single_pile(pile, soil, applied_load=200.0, factor_of_safety=2.5)

    assert pytest.approx(res.qs, rel=1e-3) == 593.76
    assert pytest.approx(res.qb, rel=1e-3) == 57.26
    assert pytest.approx(res.q_ult, rel=1e-3) == 651.02
    assert pytest.approx(res.q_all, rel=1e-3) == 260.41
    assert res.is_safe is True
    assert res.utilization_ratio < 1.0


def test_case_2_sand_meyerhof():
    """
    Verify sand calculation with critical depth capping and Meyerhof Nq.
    D = 0.60 m, L = 14.0 m, phi = 34 deg, gamma = 18.5 kN/m3, Ks = 0.70.
    """
    pile = PileGeometry(diameter=0.60, length=14.0, pile_type="Bored Cast-in-situ")
    soil = SoilParameters(
        soil_type="Cohesionless (Sand)",
        unit_weight=18.5,
        friction_angle_phi=34.0,
        earth_pressure_coeff_ks=0.70,
        delta_ratio=0.75,
        critical_depth_ratio=15.0
    )
    res = calculate_single_pile(pile, soil, applied_load=750.0, factor_of_safety=2.5)

    assert res.qs > 0.0
    assert res.qb > 0.0
    assert res.q_ult == pytest.approx(res.qs + res.qb, rel=1e-5)
    assert res.q_all == pytest.approx(res.q_ult / 2.5, rel=1e-5)


def test_converse_labarre_formula():
    """
    Verify Converse-Labarre group efficiency calculation:
    2x2 group, D = 0.50 m, s = 1.50 m.
    theta = arctan(0.5 / 1.5) = 18.4349 deg.
    eta = 1 - (18.4349 / 90) * [(1*2 + 1*2) / 4] = 1 - 0.20483 * 1.0 = 0.79517.
    """
    eta = calculate_converse_labarre_efficiency(rows=2, cols=2, diameter=0.50, spacing=1.50)
    assert pytest.approx(eta, abs=1e-3) == 0.7952

    # Single pile should have efficiency 1.0
    eta_single = calculate_converse_labarre_efficiency(rows=1, cols=1, diameter=0.50, spacing=1.50)
    assert eta_single == 1.0


def test_case_3_group_clay():
    """
    Verify 2x2 pile group in cohesive clay.
    """
    pile = PileGeometry(diameter=0.50, length=12.0, pile_type="Driven Concrete")
    soil = SoilParameters(
        soil_type="Cohesive (Clay)",
        unit_weight=19.0,
        cohesion_cu=65.0,
        adhesion_factor_alpha=0.55
    )
    single_res = calculate_single_pile(pile, soil, applied_load=450.0, factor_of_safety=2.5)
    group_res = calculate_pile_group(
        single_res=single_res,
        rows=2, cols=2, spacing=1.50,
        total_applied_load=1800.0,
        efficiency_method="Converse-Labarre"
    )

    assert group_res.total_piles == 4
    assert pytest.approx(group_res.group_efficiency, abs=1e-3) == 0.7952
    assert group_res.q_group_sum == pytest.approx(4 * single_res.q_ult, rel=1e-4)
    assert group_res.q_group_ult == pytest.approx(group_res.q_group_sum * group_res.group_efficiency, rel=1e-4)


def test_hyperbolic_load_settlement():
    """Verify hyperbolic load-settlement curve generation and asymptotic behavior."""
    pile = PileGeometry(diameter=0.50, length=10.0)
    soil = SoilParameters(soil_type="Cohesive (Clay)", unit_weight=18.0, cohesion_cu=50.0)
    res = calculate_single_pile(pile, soil, applied_load=200.0)

    s, p, ki = generate_load_settlement_curve(res.q_ult, pile, soil, max_settlement_mm=50.0)

    assert len(s) == len(p)
    assert s[0] == 0.0 and p[0] == 0.0
    # Strictly monotonically increasing
    assert all(p[i] <= p[i+1] for i in range(len(p)-1))
    # Never exceeds ultimate capacity
    assert all(load <= res.q_ult + 1e-3 for load in p)

