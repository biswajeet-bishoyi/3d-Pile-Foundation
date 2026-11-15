"""
GeoSmart AI -- 3D Pile Foundation Load Behaviour Simulator
Textbook Verification Benchmark Cases and Presets
Course: Foundation Engineering and Design (21CEE301T)
"""

from typing import Dict, Any

BENCHMARK_PRESETS: Dict[str, Dict[str, Any]] = {
    "Case 1: Driven Pile in Cohesive Clay (Das/Tomlinson)": {
        "description": "Textbook benchmark (Braja M. Das): Driven circular concrete pile in soft-to-medium clay stratum using the Total Stress Alpha method.",
        "pile": {
            "diameter": 0.45,
            "length": 15.0,
            "pile_type": "Driven Concrete"
        },
        "soil": {
            "soil_type": "Cohesive (Clay)",
            "unit_weight": 18.0,
            "cohesion_cu": 40.0,
            "friction_angle_phi": 0.0,
            "adhesion_factor_alpha": 0.70,
            "earth_pressure_coeff_ks": 1.0,
            "delta_ratio": 0.75,
            "elastic_modulus_es": 20000.0
        },
        "group": {
            "rows": 1,
            "cols": 1,
            "spacing": 1.5,
            "efficiency_method": "Converse-Labarre"
        },
        "applied_load": 200.0,
        "factor_of_safety": 2.5,
        "hand_calc": {
            "A_s": 21.206,
            "A_b": 0.159,
            "Q_s": 593.76,
            "Q_b": 57.26,
            "Q_ult": 651.02,
            "Q_all": 260.41,
            "governing_note": "Shaft-dominated friction pile (Q_s accounts for ~91% of total capacity)."
        }
    },
    "Case 2: Bored Pile in Cohesionless Sand (Meyerhof Method)": {
        "description": "Standard geotechnical case: Bored cast-in-situ pile installed in medium dense sand. Uses effective stress Beta method with critical depth capping.",
        "pile": {
            "diameter": 0.60,
            "length": 14.0,
            "pile_type": "Bored Cast-in-situ"
        },
        "soil": {
            "soil_type": "Cohesionless (Sand)",
            "unit_weight": 18.5,
            "cohesion_cu": 0.0,
            "friction_angle_phi": 34.0,
            "adhesion_factor_alpha": None,
            "earth_pressure_coeff_ks": 0.70,
            "delta_ratio": 0.75,
            "elastic_modulus_es": 35000.0
        },
        "group": {
            "rows": 1,
            "cols": 1,
            "spacing": 1.8,
            "efficiency_method": "Converse-Labarre"
        },
        "applied_load": 750.0,
        "factor_of_safety": 2.5,
        "hand_calc": {
            "A_s": 26.389,
            "A_b": 0.2827,
            "critical_depth_zc": 9.0,
            "governing_note": "End-bearing provides significant resistance due to deep N_q Meyerhof multiplier."
        }
    },
    "Case 3: 2x2 Pile Group in Stiff Clay (Converse-Labarre & Block Failure)": {
        "description": "Group action benchmark: 4-pile group (2x2) spaced at 3D center-to-centre in stiff clay. Demonstrates Converse-Labarre group efficiency and block failure checks.",
        "pile": {
            "diameter": 0.50,
            "length": 12.0,
            "pile_type": "Driven Concrete"
        },
        "soil": {
            "soil_type": "Cohesive (Clay)",
            "unit_weight": 19.0,
            "cohesion_cu": 65.0,
            "friction_angle_phi": 0.0,
            "adhesion_factor_alpha": 0.55,
            "earth_pressure_coeff_ks": 1.0,
            "delta_ratio": 0.75,
            "elastic_modulus_es": 30000.0
        },
        "group": {
            "rows": 2,
            "cols": 2,
            "spacing": 1.50,
            "efficiency_method": "Combined Minimum"
        },
        "applied_load": 1800.0,
        "factor_of_safety": 2.5,
        "hand_calc": {
            "theta_deg": 18.435,
            "efficiency_eta": 0.795,
            "single_q_ult": 786.1,
            "governing_note": "Group efficiency eta = 79.5% reduces single pile sum from 3144 kN to ~2500 kN ultimate."
        }
    },
    "Case 4: Dense Sand High-Capacity End-Bearing Pile": {
        "description": "Heavily loaded industrial column pile terminating in very dense gravelly sand (phi = 38 deg). High base resistance.",
        "pile": {
            "diameter": 0.80,
            "length": 16.0,
            "pile_type": "Driven Concrete"
        },
        "soil": {
            "soil_type": "Cohesionless (Sand)",
            "unit_weight": 20.0,
            "cohesion_cu": 0.0,
            "friction_angle_phi": 38.0,
            "adhesion_factor_alpha": None,
            "earth_pressure_coeff_ks": 1.1,
            "delta_ratio": 0.85,
            "elastic_modulus_es": 60000.0
        },
        "group": {
            "rows": 1,
            "cols": 1,
            "spacing": 2.4,
            "efficiency_method": "Converse-Labarre"
        },
        "applied_load": 1800.0,
        "factor_of_safety": 2.5,
        "hand_calc": {
            "governing_note": "End-bearing dominant (>60% of total capacity due to high N_q value)."
        }
    },
    "Case 5: 3x3 High-Rise Core Pile Group (9 Piles)": {
        "description": "Multi-pile group layout supporting a multi-story building core in mixed c-phi weathered rock/stiff soil.",
        "pile": {
            "diameter": 0.60,
            "length": 15.0,
            "pile_type": "Bored Cast-in-situ"
        },
        "soil": {
            "soil_type": "Mixed (c-phi)",
            "unit_weight": 19.5,
            "cohesion_cu": 30.0,
            "friction_angle_phi": 28.0,
            "adhesion_factor_alpha": 0.60,
            "earth_pressure_coeff_ks": 0.8,
            "delta_ratio": 0.75,
            "elastic_modulus_es": 40000.0
        },
        "group": {
            "rows": 3,
            "cols": 3,
            "spacing": 1.80,
            "efficiency_method": "Converse-Labarre"
        },
        "applied_load": 7500.0,
        "factor_of_safety": 2.5,
        "hand_calc": {
            "governing_note": "Large group with 9 piles; group efficiency eta ~ 72% reflects mutual stress overlap."
        }
    }
}

