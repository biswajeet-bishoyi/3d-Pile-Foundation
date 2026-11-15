# 🏗️ GeoSmart AI — 3D Pile Foundation Load Behaviour Simulator

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50%2B-FF4B4B.svg)](https://streamlit.io/)
[![Plotly 3D](https://img.shields.io/badge/Plotly-3D%20Interactive-3F51B5.svg)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Project:** GeoSmart AI — 3D Pile Foundation Load Behaviour Simulator  
**Course:** Foundation Engineering and Design (21CEE301T)  
**Version:** 1.0 (MVP)  
**Purpose:** Educational demonstration software; not certified engineering design software.

---

## 🌟 Executive Overview

The **3D Pile Foundation Load Behaviour Simulator** is an interactive, browser-based geotechnical engineering application. It models and demonstrates how vertical compressive column loads transfer through reinforced concrete pile caps and deep foundation piles into surrounding soil strata via **shaft friction (skin resistance)** and **toe end-bearing**.

The application bridges theoretical textbook equations (Braja M. Das, Meyerhof, Tomlinson) with interactive 3D conceptual modeling, parametric sensitivity graphs, non-linear load-settlement response, automated rule-based diagnostics, and publication-ready calculation reports.

---

## 🚀 Key Features

### 1. 🧮 Comprehensive Calculation Engine
- **Cohesive Soils (Clay):** Total Stress Method ($\alpha$-method) with Skempton deep bearing capacity factor ($N_c = 9.0$). Supports Tomlinson / API RP2A empirical adhesion factor correlation ($\alpha = 0.5 \cdot (c_u/p_a)^{-0.5}$).
- **Cohesionless Soils (Sand):** Effective Stress Method ($\beta$-method) with Meyerhof (1976) deep foundation bearing capacity factor ($N_q$) and critical depth capping ($z_c = 15D$) to model stress arching and limiting skin friction.
- **Mixed ($c$-$\phi$) Stratum:** Superposition static analysis.
- **Factor of Safety ($FS$):** Transparent, customizable safety margin (default $2.5$).

### 2. 👥 Pile Group Interaction & Efficiency
- **Arrangements:** Single pile, $2 \times 1$, $2 \times 2$, $3 \times 2$, $3 \times 3$, up to $5 \times 5$ grids.
- **Converse-Labarre Formulation:** Calculates efficiency factor $\eta = 1 - \frac{\theta}{90^\circ} \left[ \frac{(n-1)m + (m-1)n}{mn} \right]$ based on spacing ratio $s/D$.
- **Block Failure Analysis:** Computes block shear failure perimeter $P_g$ and base area $A_{gb}$ in cohesive soils.
- **Load Distribution:** Equal load sharing across group with transparent educational disclosure of assumptions.

### 3. 🌐 Interactive 3D Conceptual Model (Plotly 3D)
- True 3D geometry of column, pile cap, pile shafts, toe disks, and soil strata.
- **Force Vectors:**
  - 🔴 **Applied Column Load ($P \downarrow$):** Downward red vector acting on the column.
  - 🟢 **Shaft Resistance ($Q_s \uparrow$):** Upward green vectors mobilized along the embedded pile shaft.
  - 🔵 **Base Resistance ($Q_b \uparrow$):** Upward blue cone vectors acting at the pile toe.
- **Dimensional Annotations:** Dynamic callouts for Length $L$, Diameter $D$, and Spacing $s$.
- Rotate, pan, zoom, and perspective reset controls.

### 4. 📊 Geotechnical Analytics & Parametric Sensitivity
1. **Applied Load vs. Allowable Capacity:** Visual threshold comparison with Safe/Overload status indicators.
2. **Resistance Mechanism Breakdown:** Donut chart classifying piles as friction-dominated or end-bearing.
3. **Embedment Length ($L$) Sensitivity:** Parametric curves showing $Q_s(L)$, $Q_b(L)$, and $Q_{all}(L)$ with current design point.
4. **Diameter ($D$) Sensitivity:** Highlights linear scaling of shaft area ($\propto D$) versus quadratic scaling of base area ($\propto D^2$).
5. **Illustrative Load-Settlement Response:** Chin-Kondner hyperbolic elastic-plastic formulation ($P = S / [ (1/K_i) + (S/Q_{ult}) ]$).
6. **Field Test Data Import:** Upload CSV from standard ASTM D1143 / IS 2911 static load tests to overlay real site measurements against theoretical curves.

### 5. 🧠 Geotechnical Engineering Assistant
- Rule-based engineering evaluation:
  - Safety and stress margin assessment.
  - Load-transfer classification (floating vs. end-bearing).
  - Practical parametric optimization recommendations.
  - Explicit list of design assumptions, groundwater impacts, and professional cautions.

### 6. 📄 Automated Report Export
- **Print-Ready HTML Report:** High-resolution CSS styled document with complete equation derivations and diagrams.
- **Native PDF Report:** One-click PDF generation via ReportLab.
- **CSV Data Summary:** Machine-readable tabular results for spreadsheet audits.

---

## 📚 Hand-Worked Verification Benchmarks

To ensure numerical accuracy and meet PRD Milestone M7, the calculation engine has been verified against documented textbook problems:

| Benchmark Case | Configuration | Soil Parameters | Calculated $Q_{ult}$ | Hand Verification |
|---|---|---|---|---|
| **Case 1: Das (2019) Clay Pile** | $D = 0.45\text{ m}$, $L = 15.0\text{ m}$ | $c_u = 40\text{ kPa}$, $\alpha = 0.70$ | **$651.02\text{ kN}$** | $Q_s = 593.76\text{ kN}$, $Q_b = 57.26\text{ kN}$ (Exact Match) |
| **Case 2: Meyerhof Sand Pile** | $D = 0.60\text{ m}$, $L = 14.0\text{ m}$ | $\phi = 34^\circ$, $K_s = 0.70$ | **$1963.2\text{ kN}$** | Verified with $z_c = 9.0\text{ m}$ cap |
| **Case 3: 2×2 Pile Group (Clay)** | 4 Piles, $s = 1.5\text{ m}$ ($3D$) | $c_u = 65\text{ kPa}$, $\alpha = 0.55$ | **$2500.3\text{ kN}$** | $\eta = 79.52\%$ via Converse-Labarre |

---

## 💻 Installation & Quickstart

### Prerequisites
- Python 3.10+
- pip

### 1. Clone or Navigate to Project Directory
```bash
cd "geosmart-pile-simulator"
```

### 2. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Unit Tests
```bash
python tests/run_tests.py
```
*Expected Output: `Ran 6 tests in 0.004s — OK`*

### 4. Launch the Streamlit Application
```bash
streamlit run streamlit_app.py
```
Open your browser at `http://localhost:8501`.

---

## 📁 Repository Structure

```
geosmart-pile-simulator/
│
├── app.py                     # Main interactive Streamlit application
├── requirements.txt           # Python dependency specifications
├── README.md                  # Comprehensive documentation and theory
│
├── core/                      # Modular computational backend
│   ├── __init__.py
│   ├── calculations.py        # Single pile, group efficiency, & settlement engines
│   ├── visualizer3d.py        # Interactive 3D Plotly scene & force vectors
│   ├── charts.py              # Parametric sensitivity & capacity graphs
│   ├── explainer.py           # Geotechnical rule-based explanation assistant
│   ├── presets.py             # Pre-configured textbook benchmark cases
│   └── report_gen.py          # HTML and PDF report generators
│
├── tests/                     # Validation test suite
│   ├── __init__.py
│   ├── run_tests.py           # Standalone unittest verification script
│   └── test_calculations.py   # Test cases
│
└── sample_data/               # Sample field datasets
    └── pile_load_test_sample.csv # ASTM D1143 load test template
```

---

## ⚠️ Safety & Engineering Disclaimer

> [!CAUTION]
> This application is strictly for **educational demonstration and academic study** within Course 21CEE301T (Foundation Engineering and Design).
> **Outputs must NOT be used for actual construction, commercial design, or safety certification.** Real-world pile foundation design requires site-specific geotechnical investigations (SPT, CPT, triaxial testing), groundwater monitoring, structural pile cap design, settlement and group downdrag analysis, and certified review by a licensed geotechnical and structural engineer.

