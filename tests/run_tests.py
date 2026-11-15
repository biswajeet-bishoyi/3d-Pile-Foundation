"""
GeoSmart AI -- Test Runner using standard library unittest
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import math
from core.calculations import (
    PileGeometry,
    SoilParameters,
    calculate_single_pile,
    calculate_pile_group,
    calculate_converse_labarre_efficiency,
    generate_load_settlement_curve
)


class TestGeotechnicalCalculations(unittest.TestCase):

    def test_pile_geometry(self):
        pile = PileGeometry(diameter=0.50, length=10.0)
        expected_ab = math.pi * (0.50 ** 2) / 4.0
        expected_as = math.pi * 0.50 * 10.0
        expected_p = math.pi * 0.50

        self.assertAlmostEqual(pile.base_area, expected_ab, places=4)
        self.assertAlmostEqual(pile.shaft_area, expected_as, places=3)
        self.assertAlmostEqual(pile.perimeter, expected_p, places=3)
        self.assertAlmostEqual(pile.slenderness_ratio, 20.0, places=2)

    def test_case_1_das_clay(self):
        """
        Hand-worked verification against Braja M. Das / Tomlinson Alpha Method:
        D = 0.45 m, L = 15.0 m, cu = 40.0 kPa, gamma = 18.0 kN/m3, alpha = 0.70, FS = 2.5.
        """
        pile = PileGeometry(diameter=0.45, length=15.0, pile_type="Driven Concrete")
        soil = SoilParameters(
            soil_type="Cohesive (Clay)",
            unit_weight=18.0,
            cohesion_cu=40.0,
            adhesion_factor_alpha=0.70
        )
        res = calculate_single_pile(pile, soil, applied_load=200.0, factor_of_safety=2.5)

        self.assertAlmostEqual(res.qs, 593.76, places=1)
        self.assertAlmostEqual(res.qb, 57.26, places=1)
        self.assertAlmostEqual(res.q_ult, 651.02, places=1)
        self.assertAlmostEqual(res.q_all, 260.41, places=1)
        self.assertTrue(res.is_safe)
        self.assertLess(res.utilization_ratio, 1.0)

    def test_case_2_sand_meyerhof(self):
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

        self.assertGreater(res.qs, 0.0)
        self.assertGreater(res.qb, 0.0)
        self.assertAlmostEqual(res.q_ult, res.qs + res.qb, places=3)
        self.assertAlmostEqual(res.q_all, res.q_ult / 2.5, places=3)

    def test_converse_labarre_formula(self):
        eta = calculate_converse_labarre_efficiency(rows=2, cols=2, diameter=0.50, spacing=1.50)
        self.assertAlmostEqual(eta, 0.7952, places=3)

        eta_single = calculate_converse_labarre_efficiency(rows=1, cols=1, diameter=0.50, spacing=1.50)
        self.assertEqual(eta_single, 1.0)

    def test_case_3_group_clay(self):
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

        self.assertEqual(group_res.total_piles, 4)
        self.assertAlmostEqual(group_res.group_efficiency, 0.7952, places=3)
        self.assertAlmostEqual(group_res.q_group_sum, 4 * single_res.q_ult, places=1)
        self.assertAlmostEqual(group_res.q_group_ult, group_res.q_group_sum * group_res.group_efficiency, places=1)

    def test_hyperbolic_load_settlement(self):
        pile = PileGeometry(diameter=0.50, length=10.0)
        soil = SoilParameters(soil_type="Cohesive (Clay)", unit_weight=18.0, cohesion_cu=50.0)
        res = calculate_single_pile(pile, soil, applied_load=200.0)

        s, p, ki = generate_load_settlement_curve(res.q_ult, pile, soil, max_settlement_mm=50.0)

        self.assertEqual(len(s), len(p))
        self.assertEqual(s[0], 0.0)
        self.assertEqual(p[0], 0.0)
        for i in range(len(p) - 1):
            self.assertLessEqual(p[i], p[i+1])
        for load in p:
            self.assertLessEqual(load, res.q_ult + 1e-3)


if __name__ == '__main__':
    unittest.main(verbosity=2)

