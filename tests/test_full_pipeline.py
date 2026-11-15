"""
End-to-End Pipeline Verification Script
Tests that calculations, 3D visualization, all 5 charts, explanation engine,
and PDF/HTML/CSV report generation run completely without errors.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.calculations import (
    PileGeometry,
    SoilParameters,
    calculate_single_pile,
    calculate_pile_group
)
from core.visualizer3d import create_3d_pile_model
from core.charts import (
    plot_load_vs_capacity,
    plot_resistance_breakdown,
    plot_length_sensitivity,
    plot_diameter_sensitivity,
    plot_load_settlement_curve
)
from core.explainer import generate_rule_based_explanation
from core.report_gen import generate_html_report, generate_pdf_report, generate_summary_csv
from core.presets import BENCHMARK_PRESETS


def test_full_pipeline():
    print("Testing End-to-End Pipeline across all Benchmark Cases...")

    for name, data in BENCHMARK_PRESETS.items():
        print(f"\n--- Testing: {name} ---")
        pile = PileGeometry(**data["pile"])
        soil = SoilParameters(**data["soil"])
        applied_load = data["applied_load"]
        fs = data["factor_of_safety"]

        # Single pile
        single_res = calculate_single_pile(pile, soil, applied_load=applied_load, factor_of_safety=fs)
        assert single_res.q_ult > 0
        assert single_res.q_all > 0

        # Group pile
        g_data = data["group"]
        group_res = calculate_pile_group(
            single_res=single_res,
            rows=g_data["rows"],
            cols=g_data["cols"],
            spacing=g_data["spacing"],
            total_applied_load=applied_load,
            efficiency_method=g_data["efficiency_method"]
        )
        assert group_res.q_group_ult > 0

        # 3D Model
        fig_3d = create_3d_pile_model(single_res, group_res)
        assert len(fig_3d.data) > 0
        print("  ✓ 3D Model generated")

        # Charts
        c1 = plot_load_vs_capacity(single_res, group_res)
        c2 = plot_resistance_breakdown(single_res)
        c3 = plot_length_sensitivity(pile, soil, applied_load=applied_load, factor_of_safety=fs)
        c4 = plot_diameter_sensitivity(pile, soil, applied_load=applied_load, factor_of_safety=fs)

        # Sample test data
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'pile_load_test_sample.csv')
        df_test = pd.read_csv(csv_path) if os.path.exists(csv_path) else None
        c5 = plot_load_settlement_curve(single_res, test_data_df=df_test)
        print("  ✓ All 5 Plotly Charts generated")

        # Explanation
        exp = generate_rule_based_explanation(single_res, group_res)
        assert len(exp["recommendations"]) > 0
        print("  ✓ Explanation Assistant diagnostic generated")

        # Reports
        html = generate_html_report(single_res, group_res)
        assert len(html) > 500
        pdf = generate_pdf_report(single_res, group_res)
        assert len(pdf) > 1000
        csv = generate_summary_csv(single_res, group_res)
        assert len(csv) > 100
        print(f"  ✓ HTML Report ({len(html)} bytes), PDF ({len(pdf)} bytes), CSV ({len(csv)} bytes)")

    print("\n✅ All benchmark pipelines, visualizations, and report exports PASSED successfully!")


if __name__ == '__main__':
    test_full_pipeline()

