"""
GeoSmart AI -- 3D Pile Foundation Load Behaviour Simulator
Core 3D Interactive Conceptual Visualization (Plotly 3D)
Course: Foundation Engineering and Design (21CEE301T)

Renders:
- Ground surface plane and soil stratigraphic volume
- Superstructure column and concrete pile cap
- Single or group circular pile cylinders
- Applied vertical load vector (downward red arrow)
- Mobilized shaft friction vectors (upward green arrows along shaft)
- Base end-bearing resistance vectors (upward blue cones at pile toe)
- Dimensional annotations (Length, Diameter, Spacing)
"""

import math
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import plotly.graph_objects as go

from core.calculations import SinglePileResult, PileGroupResult, PileGeometry


def generate_cylinder_coords(
    x_center: float,
    y_center: float,
    radius: float,
    z_top: float,
    z_bottom: float,
    n_theta: int = 32,
    n_z: int = 4
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generates 2D coordinate grids for Plotly go.Surface cylinder."""
    theta = np.linspace(0, 2 * np.pi, n_theta)
    z = np.linspace(z_bottom, z_top, n_z)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_grid = x_center + radius * np.cos(theta_grid)
    y_grid = y_center + radius * np.sin(theta_grid)
    return x_grid, y_grid, z_grid


def generate_box_mesh(
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    z_min: float, z_max: float
) -> Tuple[List[float], List[float], List[float], List[int], List[int], List[int]]:
    """Generates vertices and triangular face indices for a 3D box (Mesh3d)."""
    # 8 vertices
    x = [x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min]
    y = [y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max]
    z = [z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max]

    # 12 triangular faces (2 per side)
    i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
    j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
    k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
    return x, y, z, i, j, k


def create_3d_pile_model(
    single_res: SinglePileResult,
    group_res: Optional[PileGroupResult] = None,
    show_soil_layers: bool = True,
    show_friction_arrows: bool = True,
    show_base_arrow: bool = True,
    show_dimensions: bool = True
) -> go.Figure:
    """
    Builds the complete interactive 3D conceptual pile foundation model.
    """
    pile = single_res.pile
    D = pile.diameter
    L = pile.length
    radius = D / 2.0

    # Layout configuration
    if group_res is not None and (group_res.rows > 1 or group_res.cols > 1):
        m, n = group_res.rows, group_res.cols
        spacing = group_res.spacing
        total_piles = m * n
        applied_load = group_res.total_applied_load
        qs_val = single_res.qs * total_piles * group_res.group_efficiency
        qb_val = single_res.qb * total_piles * group_res.group_efficiency
    else:
        m, n = 1, 1
        spacing = 0.0
        total_piles = 1
        applied_load = single_res.applied_load
        qs_val = single_res.qs
        qb_val = single_res.qb

    # Compute pile center positions symmetrically centered around (0,0)
    x_offsets = [(c - (n - 1) / 2.0) * spacing for c in range(n)]
    y_offsets = [(r - (m - 1) / 2.0) * spacing for r in range(m)]

    pile_centers = []
    for r in range(m):
        for c in range(n):
            pile_centers.append((x_offsets[c], y_offsets[r]))

    # Cap geometry (sits at ground level Z=0 or slightly above)
    overhang = max(0.4 * D, 0.30)
    cap_h = max(0.6 * D, 0.60)
    if m == 1 and n == 1:
        cap_x_min, cap_x_max = -radius - overhang, radius + overhang
        cap_y_min, cap_y_max = -radius - overhang, radius + overhang
    else:
        cap_x_min = min(x_offsets) - radius - overhang
        cap_x_max = max(x_offsets) + radius + overhang
        cap_y_min = min(y_offsets) - radius - overhang
        cap_y_max = max(y_offsets) + radius + overhang

    cap_z_min = 0.0
    cap_z_max = cap_h

    # Column geometry resting atop pile cap
    col_w = max(0.6 * D, 0.40)
    col_h = max(1.5, 2.0 * D)
    col_x_min, col_x_max = -col_w / 2.0, col_w / 2.0
    col_y_min, col_y_max = -col_w / 2.0, col_w / 2.0
    col_z_min = cap_z_max
    col_z_max = cap_z_max + col_h

    # Domain boundary for soil volume
    extent_x = max(abs(cap_x_min), abs(cap_x_max), 2.0) + 2.5 * D
    extent_y = max(abs(cap_y_min), abs(cap_y_max), 2.0) + 2.5 * D
    z_soil_bottom = -(L + 2.0 * D)

    fig = go.Figure()

    # 1. GROUND SURFACE PLANE (Z = 0)
    ground_x = np.linspace(-extent_x, extent_x, 10)
    ground_y = np.linspace(-extent_y, extent_y, 10)
    gx, gy = np.meshgrid(ground_x, ground_y)
    gz = np.zeros_like(gx)

    fig.add_trace(go.Surface(
        x=gx, y=gy, z=gz,
        colorscale=[[0, "#8D6E63"], [1, "#A1887F"]],
        showscale=False,
        opacity=0.35,
        hoverinfo="text",
        text="Ground Surface (GL ±0.00 m)",
        name="Ground Surface"
    ))

    # 2. SOIL STRATA VOLUME (Conceptual Layers)
    if show_soil_layers:
        soil_type = single_res.soil.soil_type
        # Layer 1: Upper Soil Layer (0 to -0.6 * L)
        z1_bot = -0.55 * L
        bx, by, bz, bi, bj, bk = generate_box_mesh(-extent_x, extent_x, -extent_y, extent_y, z1_bot, 0.0)
        fig.add_trace(go.Mesh3d(
            x=bx, y=by, z=bz, i=bi, j=bj, k=bk,
            color="#D7CCC8",
            opacity=0.10,
            hoverinfo="text",
            text=f"Soil Stratum 1 (Upper Embedment): {soil_type}",
            name="Soil Layer 1"
        ))

        # Layer 2: Bearing Stratum (-0.55 * L to bottom)
        bx2, by2, bz2, bi2, bj2, bk2 = generate_box_mesh(-extent_x, extent_x, -extent_y, extent_y, z_soil_bottom, z1_bot)
        fig.add_trace(go.Mesh3d(
            x=bx2, y=by2, z=bz2, i=bi2, j=bj2, k=bk2,
            color="#BCAAA4",
            opacity=0.15,
            hoverinfo="text",
            text=f"Soil Stratum 2 (Deep Bearing Stratum): {soil_type}",
            name="Soil Layer 2 (Toe Zone)"
        ))

    # 3. CONCRETE PILE CAP
    cx, cy, cz, ci, cj, ck = generate_box_mesh(cap_x_min, cap_x_max, cap_y_min, cap_y_max, cap_z_min, cap_z_max)
    fig.add_trace(go.Mesh3d(
        x=cx, y=cy, z=cz, i=ci, j=cj, k=ck,
        color="#78909C",
        opacity=0.92,
        hoverinfo="text",
        text=f"Reinforced Concrete Pile Cap<br>Thickness: {cap_h:.2f} m<br>Dimensions: {cap_x_max-cap_x_min:.2f} m × {cap_y_max-cap_y_min:.2f} m",
        name="Pile Cap"
    ))

    # 4. SUPERSTRUCTURE COLUMN
    col_x, col_y, col_z, coli, colj, colk = generate_box_mesh(col_x_min, col_x_max, col_y_min, col_y_max, col_z_min, col_z_max)
    fig.add_trace(go.Mesh3d(
        x=col_x, y=col_y, z=col_z, i=coli, j=colj, k=colk,
        color="#546E7A",
        opacity=0.95,
        hoverinfo="text",
        text=f"Superstructure Column<br>Applied Axial Load: {applied_load:.1f} kN",
        name="Column"
    ))

    # 5. PILE CYLINDERS
    for idx, (px, py) in enumerate(pile_centers):
        cyl_x, cyl_y, cyl_z = generate_cylinder_coords(
            x_center=px,
            y_center=py,
            radius=radius,
            z_top=0.0,
            z_bottom=-L,
            n_theta=24,
            n_z=4
        )
        fig.add_trace(go.Surface(
            x=cyl_x, y=cyl_y, z=cyl_z,
            colorscale=[[0, "#455A64"], [1, "#607D8B"]],
            showscale=False,
            opacity=0.95,
            hoverinfo="text",
            text=f"Pile #{idx+1}<br>Diameter: {D:.2f} m<br>Length: {L:.2f} m<br>Type: {pile.pile_type}",
            name=f"Pile #{idx+1}"
        ))

        # Bottom toe disc
        theta_toe = np.linspace(0, 2 * np.pi, 20)
        disc_x = [px] + [px + radius * math.cos(t) for t in theta_toe]
        disc_y = [py] + [py + radius * math.sin(t) for t in theta_toe]
        disc_z = [-L] * len(disc_x)
        fig.add_trace(go.Scatter3d(
            x=disc_x, y=disc_y, z=disc_z,
            mode="lines",
            line=dict(color="#1A237E", width=4),
            hoverinfo="text",
            text=f"Pile #{idx+1} Toe (End-Bearing Base)",
            showlegend=False
        ))

    # 6. FORCE VECTORS
    # A) Applied Column Load Vector (Red Arrow pointing DOWN onto column)
    arrow_z_start = col_z_max + max(1.8, 1.5 * D)
    arrow_z_end = col_z_max

    # Arrow stem
    fig.add_trace(go.Scatter3d(
        x=[0.0, 0.0], y=[0.0, 0.0], z=[arrow_z_start, arrow_z_end + 0.3],
        mode="lines+text",
        line=dict(color="#D32F2F", width=8),
        text=["", f"<b>P = {applied_load:.1f} kN ↓</b>"],
        textposition="top center",
        textfont=dict(size=14, color="#D32F2F"),
        name="Applied Vertical Load P",
        hoverinfo="text"
    ))

    # Arrow Cone tip pointing DOWN (u=0, v=0, w=-1)
    fig.add_trace(go.Cone(
        x=[0.0], y=[0.0], z=[arrow_z_end + 0.3],
        u=[0.0], v=[0.0], w=[-0.8],
        sizemode="scaled",
        sizeref=0.6,
        colorscale=[[0, "#D32F2F"], [1, "#D32F2F"]],
        showscale=False,
        name="Load Direction (Down)",
        hoverinfo="text",
        text=f"Applied Column Axial Load: {applied_load:.1f} kN"
    ))

    # B) Shaft Resistance Friction Arrows (Green Arrows pointing UP along pile shafts)
    if show_friction_arrows:
        # Place 4 arrows per pile along embedment depth
        arrow_depths = [-0.25 * L, -0.50 * L, -0.75 * L]
        arrow_len = 0.08 * L

        for px, py in pile_centers:
            for d_z in arrow_depths:
                for angle in [0, math.pi / 2, math.pi, 3 * math.pi / 2]:
                    ax = px + (radius + 0.08 * D) * math.cos(angle)
                    ay = py + (radius + 0.08 * D) * math.sin(angle)
                    # Stem
                    fig.add_trace(go.Scatter3d(
                        x=[ax, ax], y=[ay, ay], z=[d_z - arrow_len, d_z],
                        mode="lines",
                        line=dict(color="#2E7D32", width=4),
                        showlegend=False,
                        hoverinfo="skip"
                    ))
                    # Cone pointing UP (w = +1)
                    fig.add_trace(go.Cone(
                        x=[ax], y=[ay], z=[d_z],
                        u=[0], v=[0], w=[0.35],
                        sizemode="scaled",
                        sizeref=0.25,
                        colorscale=[[0, "#2E7D32"], [1, "#2E7D32"]],
                        showscale=False,
                        showlegend=False,
                        hoverinfo="text",
                        text=f"Skin Friction Q_s = {qs_val:.1f} kN (Mobilized upward)"
                    ))

        # Legend dummy for Shaft Resistance
        fig.add_trace(go.Scatter3d(
            x=[None], y=[None], z=[None],
            mode="lines",
            line=dict(color="#2E7D32", width=6),
            name=f"Shaft Resistance Q_s ({single_res.qs_percent:.1f}%) ↑"
        ))

    # C) Base Resistance / End Bearing Vector (Blue Cone pointing UP at pile toe)
    if show_base_arrow:
        for px, py in pile_centers:
            toe_z = -L
            # Stem below toe
            fig.add_trace(go.Scatter3d(
                x=[px, px], y=[py, py], z=[toe_z - 0.15 * L, toe_z],
                mode="lines",
                line=dict(color="#1565C0", width=6),
                showlegend=False,
                hoverinfo="skip"
            ))
            # Cone pointing UP into base (w = +1)
            fig.add_trace(go.Cone(
                x=[px], y=[py], z=[toe_z],
                u=[0], v=[0], w=[0.5],
                sizemode="scaled",
                sizeref=0.45,
                colorscale=[[0, "#1565C0"], [1, "#1565C0"]],
                showscale=False,
                showlegend=False,
                hoverinfo="text",
                text=f"End Bearing Q_b = {qb_val:.1f} kN (Base resistance)"
            ))

        # Legend dummy for Base Resistance
        fig.add_trace(go.Scatter3d(
            x=[None], y=[None], z=[None],
            mode="lines",
            line=dict(color="#1565C0", width=6),
            name=f"Base Resistance Q_b ({single_res.qb_percent:.1f}%) ↑"
        ))

    # 7. DIMENSION ANNOTATIONS
    if show_dimensions:
        # Pile Length L dimension line on left
        dim_x = cap_x_min - 0.8 * D - 0.4
        dim_y = 0.0
        fig.add_trace(go.Scatter3d(
            x=[dim_x, dim_x], y=[dim_y, dim_y], z=[0.0, -L],
            mode="lines+text",
            line=dict(color="#37474F", width=3, dash="dash"),
            text=["", f"<b>L = {L:.2f} m</b>"],
            textposition="middle left",
            textfont=dict(size=12, color="#263238"),
            name="Length Dimension",
            hoverinfo="text"
        ))

        # Pile Diameter D annotation on first pile
        first_px, first_py = pile_centers[0]
        fig.add_trace(go.Scatter3d(
            x=[first_px - radius, first_px + radius],
            y=[first_py, first_py],
            z=[-0.15 * L, -0.15 * L],
            mode="lines+text",
            line=dict(color="#FF6F00", width=4),
            text=["", f"<b>D={D:.2f}m</b>"],
            textposition="top center",
            textfont=dict(size=11, color="#E65100"),
            name="Diameter Dimension",
            hoverinfo="text"
        ))

        # Spacing dimension if group
        if total_piles > 1 and spacing > 0:
            if n > 1:
                p1 = pile_centers[0]
                p2 = pile_centers[1]
                fig.add_trace(go.Scatter3d(
                    x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[cap_z_max + 0.15, cap_z_max + 0.15],
                    mode="lines+text",
                    line=dict(color="#4A148C", width=3, dash="dot"),
                    text=["", f"<b>s = {spacing:.2f} m</b>"],
                    textposition="top center",
                    textfont=dict(size=11, color="#4A148C"),
                    name="Pile Spacing",
                    hoverinfo="text"
                ))

    # Camera & Scene Layout
    fig.update_layout(
        title=dict(
            text=f"<b>Interactive 3D Conceptual Model</b> — {total_piles} {'Pile' if total_piles==1 else 'Piles Group'} ({single_res.soil.soil_type})<br><sup>*Educational Conceptual Visualization: illustrates load transfer & resistance mechanisms (Not an FEA stress contour)</sup>",
            x=0.05,
            y=0.96,
            font=dict(size=14, color="#1E293B")
        ),
        scene=dict(
            xaxis=dict(title="X (m)", backgroundcolor="#F8FAFC", gridcolor="#E2E8F0", showbackground=True),
            yaxis=dict(title="Y (m)", backgroundcolor="#F8FAFC", gridcolor="#E2E8F0", showbackground=True),
            zaxis=dict(title="Elevation Z (m)", backgroundcolor="#F1F5F9", gridcolor="#CBD5E1", showbackground=True),
            aspectmode="data",
            camera=dict(
                eye=dict(x=1.8, y=-1.8, z=1.2),
                center=dict(x=0, y=0, z=-L * 0.35)
            )
        ),
        margin=dict(l=10, r=10, b=10, t=60),
        legend=dict(
            x=0.02, y=0.95,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#CBD5E1",
            borderwidth=1
        ),
        height=620
    )

    return fig
