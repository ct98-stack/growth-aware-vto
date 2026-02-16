# vto_growth_app.py
# Growth-aware Dental VTO (McLaughlin/Dolphin-inspired) — Upper + Lower arches with separate calculations
# Adds (LOWER ONLY): dental midline + skeletal midline (numbers track with LOWER DENTAL midline)
# ENHANCED: CVMS-based growth prediction with toggle

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components


# -----------------------------
# Page + styling
# -----------------------------
st.set_page_config(page_title="Growth-aware Dental VTO (McLaughlin-inspired)", layout="wide")

CSS = """
<style>
/* Layout */
.main .block-container {max-width: 1280px; padding-top: 1.8rem; padding-bottom: 3rem;}
h1 {letter-spacing: -0.03em; margin-bottom: 0.2rem;}
.small-muted {color: rgba(49,51,63,0.65); font-size: 0.95rem;}

/* Panels */
.panel {
  border: 1px solid rgba(49,51,63,.15);
  border-radius: 16px;
  padding: 16px 16px 12px 16px;
  background: white;
  margin-bottom: 14px;
}
.panel-title {
  font-size: 1.15rem;
  font-weight: 800;
  margin-bottom: 10px;
}

/* Bands */
.band-gray {
  background: rgba(49,51,63,.05);
  border: 1px solid rgba(49,51,63,.10);
  border-radius: 12px;
  padding: 12px;
}
.band-blue {
  background: rgba(30, 111, 255, .08);
  border: 1px solid rgba(30, 111, 255, .18);
  border-radius: 12px;
  padding: 10px 12px;
  margin: 10px 0 10px 0;
  font-weight: 750;
}
.band-green {
  background: rgba(30, 180, 90, .08);
  border: 1px solid rgba(30, 180, 90, .18);
  border-radius: 12px;
  padding: 10px 12px;
  margin: 10px 0 10px 0;
  font-weight: 750;
}
.band-purple {
  background: rgba(138, 43, 226, .08);
  border: 1px solid rgba(138, 43, 226, .18);
  border-radius: 12px;
  padding: 10px 12px;
  margin: 10px 0 10px 0;
  font-weight: 750;
}
.hint {color: rgba(49,51,63,0.65); font-size: 0.92rem;}
hr {border: none; border-top: 1px solid rgba(49,51,63,.12); margin: 18px 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# -----------------------------
# Growth prediction data
# -----------------------------
GROWTH_DATA = {
    "No growth remaining": {"sagittal": 0.0, "vertical": 0.0, "transverse": 0.0, "description": "Adult patient, no further growth expected"},
    "CVMS 1": {"sagittal": 1.75, "vertical": 2.25, "transverse": 1.25, "description": "Pre-pubertal, early maturation"},
    "CVMS 2": {"sagittal": 2.5, "vertical": 2.25, "transverse": 1.25, "description": "Pre-pubertal, late maturation"},
    "CVMS 3": {"sagittal": 3.75, "vertical": 3.5, "transverse": 1.75, "description": "Pubertal peak growth"},
    "CVMS 4": {"sagittal": 2.5, "vertical": 2.25, "transverse": 1.25, "description": "Post-pubertal, declining growth"},
    "CVMS 5": {"sagittal": 1.0, "vertical": 1.25, "transverse": 0.75, "description": "Late adolescent, minimal growth"},
    "CVMS 6": {"sagittal": 0.25, "vertical": 0.25, "transverse": 0.25, "description": "Growth completion"},
    "Custom": {"sagittal": 0.0, "vertical": 0.0, "transverse": 0.0, "description": "Enter your own growth predictions"},
}


def calculate_growth_space_equivalent(
    cvms_stage: str, 
    treatment_duration_months: float, 
    include_growth: bool,
    custom_sagittal: float = 0.0,
    custom_vertical: float = 0.0,
    custom_transverse: float = 0.0
) -> dict:
    """
    Calculate space equivalent from growth based on CVMS stage or custom values.
    
    Mathematical approach:
    - Sagittal growth (A-P): Creates space as mandible advances
      * Upper receives 30% (maxillary contribution)
      * Lower receives 70% (mandibular advancement)
    - Vertical growth: Affects curve of Spee but NOT directly added to space
    - Transverse growth: Direct bilateral expansion
      * Multiplied by 2.0 (both sides)
      * Split equally between arches
    
    Returns dict with upper_total, lower_total, and breakdown
    """
    if not include_growth:
        return {
            "upper_total": 0.0,
            "lower_total": 0.0,
            "sagittal": 0.0,
            "vertical": 0.0,
            "transverse": 0.0,
            "upper_from_sagittal": 0.0,
            "lower_from_sagittal": 0.0,
            "upper_from_transverse": 0.0,
            "lower_from_transverse": 0.0,
        }
    
    # Use custom values if Custom is selected, otherwise use CVMS preset
    if cvms_stage == "Custom":
        data = {
            "sagittal": custom_sagittal,
            "vertical": custom_vertical,
            "transverse": custom_transverse
        }
    else:
        data = GROWTH_DATA[cvms_stage]
    
    # Convert months to years for calculation
    treatment_duration_years = treatment_duration_months / 12.0
    
    # Growth over treatment duration (mm)
    sagittal_growth = data["sagittal"] * treatment_duration_years
    vertical_growth = data["vertical"] * treatment_duration_years
    transverse_growth = data["transverse"] * treatment_duration_years
    
    # Space equivalent calculations
    # Sagittal: 30% upper, 70% lower (reflects differential contribution)
    upper_from_sagittal = sagittal_growth * 0.3
    lower_from_sagittal = sagittal_growth * 0.7
    
    # Transverse: bilateral (×2), split equally
    upper_from_transverse = transverse_growth * 2.0
    lower_from_transverse = transverse_growth * 2.0
    
    # Total space gained per arch
    upper_total = upper_from_sagittal + upper_from_transverse
    lower_total = lower_from_sagittal + lower_from_transverse
    
    return {
        "upper_total": upper_total,
        "lower_total": lower_total,
        "sagittal": sagittal_growth,
        "vertical": vertical_growth,
        "transverse": transverse_growth,
        "upper_from_sagittal": upper_from_sagittal,
        "lower_from_sagittal": lower_from_sagittal,
        "upper_from_transverse": upper_from_transverse,
        "lower_from_transverse": lower_from_transverse,
    }


# -----------------------------
# Helpers: session state
# -----------------------------
def ss_init(key: str, value):
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------
# Dolphin sign convention helpers
# -----------------------------
def remaining_status(x: float) -> str:
    # crowding negative -> remaining negative means still crowded
    if abs(x) < 0.05:
        return "≈ balanced (near 0)"
    if x < 0:
        return "Still short on space (crowding remains)"
    return "Excess space (spacing remains)"


def compute_initial_discrepancy(ant_cs: float, cos: float, midline_component: float, incisor_pos: float) -> float:
    """
    Dolphin-style: Initial discrepancy is sum of contributing rows.
    Sign convention: Crowding negative, spacing positive.
    """
    return float(ant_cs + cos + midline_component + incisor_pos)


def compute_remaining_dolphin(initial: float, strip: float, expansion: float, distal: float, extraction: float, growth_space: float) -> tuple[float, float]:
    """
    Space gained rows are positive.
    Remaining = initial + total_gained
    """
    gained = float(strip + expansion + distal + extraction + growth_space)
    remaining = float(initial + gained)
    return gained, remaining


# -----------------------------
# Step 1 SVG (Upper + Lower midlines; LOWER has dental + skeletal midline)
# -----------------------------
def initial_position_svg(
    r6: float,
    l6: float,
    upper_midline_mm: float,
    lower_dental_midline_mm: float,
    lower_skeletal_midline_mm: float,
) -> str:
    W, H = 920, 640
    cx = W // 2

    # two baselines
    y_upper = 205
    y_lower = 385

    scale = 18  # px/mm

    # molar positions (simple schematic)
    x_r6 = 150 + r6 * scale
    x_l6 = W - 150 - l6 * scale

    x_um = cx + upper_midline_mm * scale
    x_ld = cx + lower_dental_midline_mm * scale
    x_ls = cx + lower_skeletal_midline_mm * scale

    def box(x, y, text):
        return f"""
        <rect x="{x-30}" y="{y-18}" width="60" height="36" rx="4"
              fill="white" stroke="#999" stroke-width="2"/>
        <text x="{x}" y="{y+6}" text-anchor="middle"
              font-family="Arial" font-size="18" fill="#111">{text}</text>
        """

    def tooth(x, y, label, stroke="#333", stroke_w=2):
        return f"""
        <path d="M {x-18} {y-55}
                 C {x-36} {y-40}, {x-36} {y-8}, {x-18} {y+10}
                 C {x-10} {y+28}, {x+10} {y+28}, {x+18} {y+10}
                 C {x+36} {y-8}, {x+36} {y-40}, {x+18} {y-55}
                 Z"
              fill="white" stroke="{stroke}" stroke-width="{stroke_w}"/>
        <circle cx="{x}" cy="{y-18}" r="14" fill="white" stroke="{stroke}" stroke-width="{stroke_w}"/>
        <text x="{x}" y="{y-13}" text-anchor="middle" font-family="Arial" font-size="14">{label}</text>
        """

    def midline_marker(x, y, color="#111", label=None):
        lab = ""
        if label:
            lab = f"""<text x="{x}" y="{y-40}" text-anchor="middle" font-family="Arial" font-size="12" font-weight="700" fill="{color}">{label}</text>"""
        return f"""
        {lab}
        <line x1="{x}" y1="{y-28}" x2="{x}" y2="{y+28}" stroke="{color}" stroke-width="3"/>
        <circle cx="{x}" cy="{y}" r="6" fill="{color}"/>
        """
    
    def molar_arrow(val: float, side: str, y: int) -> str:
        """Show arrow indicating molar displacement from Class I (0 position)"""
        if abs(val) < 0.2:
            return ""  # No arrow if essentially at Class I

        # Position arrow ABOVE the tooth
        if side == "R":
            x = 150 + val * scale
        else:
            x = W - 150 - val * scale

        arrow_y = y - 115  # Positioned between R6/L6 boxes and arch line
        arrow_length = min(80, abs(val) * 24)  # Longer arrows (was 40, 12)

        # Arrow direction logic:
        # Positive value = molar shifted MESIALLY (toward midline)
        # Negative value = molar shifted DISTALLY (away from midline)

        if val > 0:  # Molar shifted mesially (forward/toward midline)
            color = "#e74c3c"  # Red for mesial
            if side == "R":
                # Right side: mesial = toward RIGHT (toward center)
                x1, x2 = x - 12, x - 12 + arrow_length  # Arrow points RIGHT
            else:  # side == "L"
                # Left side: mesial = toward LEFT (toward center)
                x1, x2 = x + 12, x + 12 - arrow_length  # Arrow points LEFT
        else:  # val < 0, Molar shifted distally (back/away from midline)
            color = "#3498db"  # Blue for distal
            if side == "R":
                # Right side: distal = toward LEFT (away from center)
                x1, x2 = x + 12, x + 12 - arrow_length  # Arrow points LEFT
            else:  # side == "L"
                # Left side: distal = toward RIGHT (away from center)
                x1, x2 = x - 12, x - 12 + arrow_length  # Arrow points RIGHT

        return f"""
        <defs>
          <marker id="arrow_{side}" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
            <path d="M0,0 L0,10 L10,5 z" fill="{color}"/>
          </marker>
        </defs>
        <line x1="{x1}" y1="{arrow_y}" x2="{x2}" y2="{arrow_y}"
              stroke="{color}" stroke-width="5" marker-end="url(#arrow_{side})"/>
        <text x="{x}" y="{arrow_y + 20}" text-anchor="middle"
              font-family="Arial" font-size="16" font-weight="800" fill="{color}">
          {abs(val):.1f}mm
        </text>
        """

    def midline_correction_arrow(midline_val: float, y: int, arch: str) -> str:
        """Show arrow indicating midline correction direction
        Positive midline = correct to patient's RIGHT (arrow →)
        Negative midline = correct to patient's LEFT (arrow ←)
        """
        if abs(midline_val) < 0.2:
            return ""  # No arrow if midline essentially centered

        x_midline = cx + midline_val * scale
        arrow_y = y + 90  # Below the tooth
        arrow_length = min(60, abs(midline_val) * 20)
        color = "#ff6f00"  # Orange for midline correction

        # Positive midline = arrow points RIGHT (→)
        # Negative midline = arrow points LEFT (←)
        if midline_val > 0:
            # Correct to patient's right →
            x1, x2 = x_midline - 10, x_midline - 10 + arrow_length
        else:
            # Correct to patient's left ←
            x1, x2 = x_midline + 10, x_midline + 10 - arrow_length

        return f"""
        <defs>
          <marker id="arrow_midline_{arch}" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
            <path d="M0,0 L0,10 L10,5 z" fill="{color}"/>
          </marker>
        </defs>
        <line x1="{x1}" y1="{arrow_y}" x2="{x2}" y2="{arrow_y}"
              stroke="{color}" stroke-width="5" marker-end="url(#arrow_midline_{arch})"/>
        <text x="{x_midline}" y="{arrow_y + 20}" text-anchor="middle"
              font-family="Arial" font-size="14" font-weight="800" fill="{color}">
          Correct {abs(midline_val):.1f}mm
        </text>
        """

    html = f"""
    <div style="border:1px solid rgba(49,51,63,.15); border-radius:14px; padding:12px; background:white;">
      <svg width="100%" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">

        <text x="{cx}" y="34" text-anchor="middle" font-family="Arial" font-size="24" font-weight="800">
          Initial Position (Upper + Lower; Lower Dental + Skeletal Midline)
        </text>

        <!-- UPPER -->
        <text x="70" y="{y_upper-20}" font-family="Arial" font-size="16" font-weight="700">Upper</text>
        <line x1="90" y1="{y_upper}" x2="{W-90}" y2="{y_upper}" stroke="#333" stroke-width="4"/>
        {tooth(x_r6, y_upper+55, "6")}
        {tooth(x_um, y_upper+55, "1")}
        {tooth(x_l6, y_upper+55, "6")}
        {midline_marker(x_um, y_upper, color="#111", label="Upper dental")}

        <!-- Molar arrows showing displacement from Class I -->
        {molar_arrow(r6, "R", y_upper+55)}
        {molar_arrow(l6, "L", y_upper+55)}

        <!-- Upper midline correction arrow -->
        {midline_correction_arrow(upper_midline_mm, y_upper+55, "upper")}

        <!-- LOWER -->
        <text x="70" y="{y_lower-20}" font-family="Arial" font-size="16" font-weight="700">Lower</text>
        <line x1="90" y1="{y_lower}" x2="{W-90}" y2="{y_lower}" stroke="#333" stroke-width="4"/>
        {tooth(x_r6, y_lower+55, "6")}
        {tooth(x_ld, y_lower+55, "1")}
        {tooth(x_l6, y_lower+55, "6")}
        {midline_marker(x_ls, y_lower, color="#7a7a7a", label="Skeletal")}
        {midline_marker(x_ld, y_lower, color="#111", label="Dental")}

        <!-- Lower midline correction arrow -->
        {midline_correction_arrow(lower_dental_midline_mm, y_lower+55, "lower")}

        <!-- Value boxes -->
        <text x="160" y="78" font-family="Arial" font-size="16" font-weight="700">R6</text>
        {box(160, 105, f"{r6:.1f}")}

        <text x="{W-160}" y="78" font-family="Arial" font-size="16" font-weight="700" text-anchor="end">L6</text>
        {box(W-160, 105, f"{l6:.1f}")}

      </svg>
    </div>
    """
    return html


# -----------------------------
# Step 3 SVG
# -----------------------------
def proposed_movement_svg_two_arch(
    u_r6: float, u_r3: float, u_inc: float, u_l3: float, u_l6: float,
    l_r6: float, l_r3: float, l_inc: float, l_l3: float, l_l6: float,
) -> str:
    W, H = 1000, 720
    cx = W // 2

    # X positions: R6, R3, Inc, L3, L6
    xs = [140, 350, cx, 650, 860]
    tooth_labels = ["6", "3", "1", "3", "6"]

    # Vertical layout - FIXED spacing
    title_y = 50

    # Upper arch
    yU_label = 120
    yU_line  = 180
    yU_tooth = 245
    yU_arrow = 330
    yU_num   = 375

    # Lower arch - more separation
    yL_label = 450
    yL_line  = 510
    yL_tooth = 575
    yL_arrow = 660
    yL_num   = 705

    def clean(v: float) -> float:
        return 0.0 if abs(v) < 0.05 else float(v)

    def fmt(v: float) -> str:
        return f"{clean(v):.1f}"

    def tooth(x: int, y: int, lab: str) -> str:
        return f"""
        <path d="M {x-24} {y-52}
                 C {x-42} {y-30}, {x-40} {y-2}, {x-20} {y+14}
                 C {x-10} {y+38}, {x+10} {y+38}, {x+20} {y+14}
                 C {x+40} {y-2}, {x+42} {y-30}, {x+24} {y-52}
                 Z"
              fill="white" stroke="#222" stroke-width="2.2"/>
        <circle cx="{x}" cy="{y-14}" r="16" fill="white" stroke="#222" stroke-width="2.2"/>
        <text x="{x}" y="{y-8}" text-anchor="middle"
              font-family="Arial" font-size="16" font-weight="900" fill="#111">{lab}</text>
        """

    def arrow(x: int, y: int, v: float, tooth_idx: int) -> str:
        """
        tooth_idx: 0=R6, 1=R3, 2=Inc, 3=L3, 4=L6

        Arrow direction follows value sign:
        - Positive value = MESIAL movement (toward front)
        - Negative value = DISTAL movement (toward back)

        The calculation (e.g., u_r3 = -u_r6 for extraction) already handles
        the direction, so arrows simply visualize the value's sign.
        """
        v = clean(v)
        # Don't show arrow if movement is essentially zero
        if abs(v) < 0.05:
            return ""

        L = max(22, min(70, abs(v) * 18))

        # All teeth follow same logic: arrow direction matches value sign
        # Positive = mesial, Negative = distal

        if tooth_idx == 0:  # R6 (right molar)
            # Positive = mesial (RIGHT →), Negative = distal (LEFT ←)
            if v > 0:
                x1, x2 = x - 10, x - 10 + L  # Points RIGHT →
            else:
                x1, x2 = x + 10, x + 10 - L  # Points LEFT ←

        elif tooth_idx == 1:  # R3 (right canine)
            # Positive = mesial (RIGHT →), Negative = distal (LEFT ←)
            if v > 0:
                x1, x2 = x - 10, x - 10 + L  # Points RIGHT →
            else:
                x1, x2 = x + 10, x + 10 - L  # Points LEFT ←

        elif tooth_idx == 3:  # L3 (left canine)
            # Positive = mesial (LEFT ←), Negative = distal (RIGHT →)
            if v > 0:
                x1, x2 = x + 10, x + 10 - L  # Points LEFT ←
            else:
                x1, x2 = x - 10, x - 10 + L  # Points RIGHT →

        elif tooth_idx == 4:  # L6 (left molar)
            # Positive = mesial (LEFT ←), Negative = distal (RIGHT →)
            if v > 0:
                x1, x2 = x + 10, x + 10 - L  # Points LEFT ←
            else:
                x1, x2 = x - 10, x - 10 + L  # Points RIGHT →

        else:  # Incisors (idx 2)
            if v > 0:
                x1, x2 = x + 10, x + 10 - L  # Points LEFT ←
            else:
                x1, x2 = x - 10, x - 10 + L  # Points RIGHT →

        return f"""
        <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"
              stroke="#1f77b4" stroke-width="5" marker-end="url(#arrowhead)"/>
        """

    def num(x: int, y: int, v: float) -> str:
        return f"""
        <text x="{x}" y="{y}" text-anchor="middle"
              font-family="Arial" font-size="28" font-weight="900" fill="#111">{fmt(v)}</text>
        """

    def row(label: str, y_label: int, y_line: int, y_tooth: int, y_arrow: int, y_num: int, vals) -> str:
        r6, r3, inc, l3, l6 = vals
        vs = [r6, r3, inc, l3, l6]

        # Arch label (left side)
        label_elem = f"""
        <text x="50" y="{y_label}" text-anchor="start"
              font-family="Arial" font-size="20" font-weight="700" fill="#333">{label}</text>
        """

        line = f"""<line x1="85" y1="{y_line}" x2="{W-85}" y2="{y_line}" stroke="#222" stroke-width="4"/>"""
        teeth = "\n".join(tooth(x, y_tooth, lab) for x, lab in zip(xs, tooth_labels))
        arrows = "\n".join(arrow(x, y_arrow, v, i) for i, (x, v) in enumerate(zip(xs, vs)))
        nums = "\n".join(num(x, y_num, v) for x, v in zip(xs, vs))

        return f"""
        {label_elem}
        {line}
        {teeth}
        {arrows}
        {nums}
        """

    svg = f"""
    <svg width="100%" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M0,0 L0,8 L8,4 z" fill="#1f77b4"/>
        </marker>
      </defs>

      <text x="{cx}" y="{title_y}" text-anchor="middle"
            font-family="Arial" font-size="28" font-weight="900" fill="#111">
        Dental VTO (Proposed Dental Movement)
      </text>

      {row("Upper Arch", yU_label, yU_line, yU_tooth, yU_arrow, yU_num, (u_r6, u_r3, u_inc, u_l3, u_l6))}
      {row("Lower Arch", yL_label, yL_line, yL_tooth, yL_arrow, yL_num, (l_r6, l_r3, l_inc, l_l3, l_l6))}
    </svg>
    """
    return svg


# -----------------------------
# Movement allocator (MVP — replace later with McLaughlin rules)
# -----------------------------
def expected_movement_allocation(remaining: float, treat_to: str) -> dict[str, float]:
    """
    Dolphin VTO logic: In crowding (remaining < 0), ALL teeth move by the FULL amount.
    In extraction/spacing (remaining > 0), movements are differentiated.
    
    remaining < 0 = crowded (need expansion) - all teeth move same amount
    remaining > 0 = spacing/extraction - distribute differently
    """
    mag = abs(remaining)
    
    if remaining < 0:
        # CROWDING: All teeth expand by the full amount
        # This matches Dolphin behavior
        return {"6": mag, "3": mag, "inc": mag}
    else:
        # EXTRACTION/SPACING: Use allocation weights
        if treat_to == "Class II":
            ant_w, post_w = 0.65, 0.35
        elif treat_to == "Class III":
            ant_w, post_w = 0.45, 0.55
        else:
            ant_w, post_w = 0.55, 0.45
        
        anterior = mag * ant_w
        posterior = mag * post_w
        inc = anterior * 0.55
        canine = anterior * 0.45
        molar = posterior
        return {"6": molar, "3": canine, "inc": inc}


def movement_sign(rem: float, side: str, tooth_type: str) -> float:
    """
    Convention: Positive = toward patient's LEFT, Negative = toward patient's RIGHT
    
    In the diagram (looking AT the patient):
    - Positive values → arrows point RIGHT (toward patient's left)
    - Negative values → arrows point LEFT (toward patient's right)
    
    Extraction mechanics (rem > 0, excess space):
    - MOLARS (6): Move MESIALLY/ANTERIORLY (forward) into extraction space
      - Both R6 and L6 move in POSITIVE direction (anteriorly/mesially on their arch)
    - CANINES (3) & INCISORS: Retract/move in NEGATIVE direction
    
    Crowding mechanics (rem < 0, need space):
    - ALL teeth: Sign MATCHES the remaining discrepancy sign
      - Negative remaining → negative movement (left)
      - This represents the direction of the crowding/shift
    """
    if rem == 0:
        return 0.0
    
    # CROWDING: Movement sign MATCHES remaining discrepancy sign
    if rem < 0:
        # Negative remaining = crowding shifted in negative direction
        return -1.0  # All teeth move in negative direction (left)
    
    # EXTRACTION/SPACING: Molars drift mesially, anteriors retract
    else:  # rem > 0
        if tooth_type == "6":  # MOLARS
            # Both molars drift MESIALLY/ANTERIORLY (forward on their arch)
            # This is POSITIVE direction for both sides
            return 1.0  # Both R6 and L6 move positive (anteriorly)
        else:  # CANINES and INCISORS
            # Anterior teeth retract
            return -1.0  # All anterior teeth move negative (posteriorly)


# -----------------------------
# Defaults
# -----------------------------
ss_init("include_growth", True)

# Step 1: initial positions
ss_init("r6_init", 0.0)
ss_init("l6_init", 0.0)

# Step 1 midlines
ss_init("upper_midline_mm", 0.0)

# LOWER ONLY: dental + skeletal midline
ss_init("lower_dental_midline_mm", 0.0)
ss_init("lower_skeletal_midline_mm", 0.0)

# Growth parameters
ss_init("cvms_stage", "CVMS 3")
ss_init("treatment_duration", 24.0)  # months
ss_init("custom_sagittal", 2.5)
ss_init("custom_vertical", 2.0)
ss_init("custom_transverse", 1.0)

# Store remaining discrepancies
ss_init("remaining_U_R", 0.0)
ss_init("remaining_U_L", 0.0)
ss_init("remaining_L_R", 0.0)
ss_init("remaining_L_L", 0.0)


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("## Global Settings")
include_growth = st.sidebar.checkbox("✨ Include growth prediction", value=st.session_state["include_growth"], key="include_growth")
st.sidebar.markdown("---")
st.sidebar.markdown("<div class='hint'>Sign convention: <b>Crowding = negative</b>, spacing = positive. Space gained rows are positive. Goal: Remaining ≈ 0.</div>", unsafe_allow_html=True)


# -----------------------------
# Header
# -----------------------------
st.markdown("# Growth-aware Dental VTO (McLaughlin-inspired)")
st.markdown("<div class='small-muted'>Upper and lower arches calculated separately. Lower arch includes dental + skeletal midline; midline discrepancy numbers track with the lower dental midline. <b>Growth prediction integrated via CVMS staging.</b></div>", unsafe_allow_html=True)

tabs = st.tabs(["Step 1: Initial Tooth Positions", "Step 1B: Growth Assessment", "Step 2: Upper + Lower Arch Discrepancy", "Step 3: Determining Movement"])


# =========================================================
# STEP 1
# =========================================================
with tabs[0]:
    left, right = st.columns([1.0, 1.35], gap="large")

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Step 1 — Initial Tooth Positions</div>', unsafe_allow_html=True)
        st.markdown(
            "<div class='band-gray'>"
            "<b>Purpose:</b> set initial molar positions and vertical factors (D and S). "
            "<br><span class='hint'>Upper midline is dental. Lower has <b>both</b> dental and skeletal midline markers.</span>"
            "</div>",
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)
        with c1:
            st.number_input("R6 (mm)", step=0.1, key="r6_init")
        with c2:
            st.number_input("L6 (mm)", step=0.1, key="l6_init")

        st.markdown('<div class="band-blue">Midlines</div>', unsafe_allow_html=True)

        st.number_input("Upper dental midline (mm)", step=0.1, key="upper_midline_mm")

        m1, m2 = st.columns(2)
        with m1:
            st.number_input(
                "Lower dental midline (mm)",
                step=0.1,
                key="lower_dental_midline_mm",
                help="Positive = correction to patient's RIGHT. Negative = correction to patient's LEFT."
            )
        with m2:
            st.number_input("Lower skeletal midline (mm)", step=0.1, key="lower_skeletal_midline_mm")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Visual Preview</div>', unsafe_allow_html=True)

        svg = initial_position_svg(
            r6=float(st.session_state["r6_init"]),
            l6=float(st.session_state["l6_init"]),
            upper_midline_mm=float(st.session_state["upper_midline_mm"]),
            lower_dental_midline_mm=float(st.session_state["lower_dental_midline_mm"]),
            lower_skeletal_midline_mm=float(st.session_state["lower_skeletal_midline_mm"]),
        )
        components.html(svg, height=680, scrolling=False)

        delta_ml = float(st.session_state["lower_dental_midline_mm"]) - float(st.session_state["lower_skeletal_midline_mm"])
        st.markdown(
            f"<div class='band-gray'><b>Lower midline delta (Dental − Skeletal):</b> {delta_ml:+.2f} mm</div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# STEP 1B: GROWTH ASSESSMENT
# =========================================================
with tabs[1]:
    st.markdown('<div class="panel"><div class="panel-title">Step 1B — Growth Assessment (CVMS-Based)</div>', unsafe_allow_html=True)
    
    st.markdown(
        "<div class='band-purple'>"
        "<b>Growth Prediction:</b> Based on Cervical Vertebral Maturation Stage (CVMS) and estimated treatment duration. "
        "Growth is converted to space equivalent and integrated into arch discrepancy calculations."
        "</div>",
        unsafe_allow_html=True
    )
    
    if not include_growth:
        st.warning("⚠️ Growth prediction is currently **disabled**. Enable it in the sidebar to use this feature.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Patient Growth Stage")
        cvms_stage = st.selectbox(
            "CVMS Stage",
            options=list(GROWTH_DATA.keys()),
            index=3,  # Default to CVMS 3
            key="cvms_stage",
            help="Cervical Vertebral Maturation Stage from lateral cephalogram, or select Custom to enter your own values"
        )
        
        stage_info = GROWTH_DATA[cvms_stage]
        st.markdown(
            f"<div class='band-gray'>"
            f"<b>{cvms_stage}:</b> {stage_info['description']}"
            f"</div>",
            unsafe_allow_html=True
        )
        
        treatment_duration = st.number_input(
            "Expected treatment duration (months)",
            min_value=6.0,
            max_value=60.0,
            value=24.0,
            step=1.0,
            key="treatment_duration",
            help="Typical orthodontic treatment: 18-36 months"
        )
        
        # Custom growth inputs (only show if Custom is selected)
        if cvms_stage == "Custom":
            st.markdown('<div class="band-blue"><b>Custom Growth Rates (mm/year)</b></div>', unsafe_allow_html=True)
            st.number_input(
                "Sagittal growth (A-P) mm/year",
                min_value=0.0,
                max_value=10.0,
                value=2.5,
                step=0.25,
                key="custom_sagittal",
                help="Anterior-posterior mandibular growth rate"
            )
            st.number_input(
                "Vertical growth mm/year",
                min_value=0.0,
                max_value=10.0,
                value=2.0,
                step=0.25,
                key="custom_vertical",
                help="Vertical facial growth rate"
            )
            st.number_input(
                "Transverse growth mm/year",
                min_value=0.0,
                max_value=5.0,
                value=1.0,
                step=0.25,
                key="custom_transverse",
                help="Lateral arch width growth rate"
            )
    
    with col2:
        st.markdown("### Growth Prediction")
        
        # Calculate growth with custom values if applicable
        growth_calc = calculate_growth_space_equivalent(
            cvms_stage, 
            treatment_duration, 
            include_growth,
            custom_sagittal=float(st.session_state.get("custom_sagittal", 0.0)),
            custom_vertical=float(st.session_state.get("custom_vertical", 0.0)),
            custom_transverse=float(st.session_state.get("custom_transverse", 0.0))
        )
        
        if include_growth:
            # Get the rates being used
            if cvms_stage == "Custom":
                sag_rate = float(st.session_state.get("custom_sagittal", 0.0))
                vert_rate = float(st.session_state.get("custom_vertical", 0.0))
                trans_rate = float(st.session_state.get("custom_transverse", 0.0))
                rate_source = "Custom"
            else:
                sag_rate = stage_info['sagittal']
                vert_rate = stage_info['vertical']
                trans_rate = stage_info['transverse']
                rate_source = cvms_stage
            
            st.markdown(
                f"<div class='band-blue'>"
                f"<b>Annual Growth Rates ({rate_source}):</b><br>"
                f"• Sagittal (A-P): {sag_rate:.2f} mm/year<br>"
                f"• Vertical: {vert_rate:.2f} mm/year<br>"
                f"• Transverse: {trans_rate:.2f} mm/year"
                f"</div>",
                unsafe_allow_html=True
            )
            
            st.markdown(
                f"<div class='band-green'>"
                f"<b>Total Growth Over {treatment_duration:.0f} Months ({treatment_duration/12:.1f} Years):</b><br>"
                f"• Sagittal: {growth_calc['sagittal']:.2f} mm<br>"
                f"• Vertical: {growth_calc['vertical']:.2f} mm<br>"
                f"• Transverse: {growth_calc['transverse']:.2f} mm"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.info("Enable growth prediction in sidebar to see calculations")
    
    # Mathematical explanation
    st.markdown("---")
    st.markdown("### 📊 Mathematical Integration")
    
    st.markdown(
        "<div class='band-gray'>"
        "<b>How growth converts to space equivalent:</b><br><br>"
        "<b>1. Sagittal Growth (A-P mandibular advancement):</b><br>"
        "   • Upper arch: receives 30% of sagittal growth<br>"
        "   • Lower arch: receives 70% of sagittal growth<br>"
        "   <span class='hint'>Rationale: Mandibular advancement creates more anterior space in lower arch</span><br><br>"
        "<b>2. Transverse Growth (lateral expansion):</b><br>"
        "   • Each arch: transverse growth × 2.0 (bilateral)<br>"
        "   <span class='hint'>Rationale: Growth occurs on both left and right sides</span><br><br>"
        "<b>3. Vertical Growth:</b><br>"
        "   • Not directly converted to space equivalent<br>"
        "   <span class='hint'>Affects curve of Spee and overbite, but not arch length</span>"
        "</div>",
        unsafe_allow_html=True
    )
    
    if include_growth:
        breakdown_data = pd.DataFrame([
            ["Sagittal contribution", f"{growth_calc['upper_from_sagittal']:.2f}", f"{growth_calc['lower_from_sagittal']:.2f}"],
            ["Transverse contribution", f"{growth_calc['upper_from_transverse']:.2f}", f"{growth_calc['lower_from_transverse']:.2f}"],
            ["<b>Total Space Equivalent</b>", f"<b>{growth_calc['upper_total']:.2f}</b>", f"<b>{growth_calc['lower_total']:.2f}</b>"],
        ], columns=["Component", "Upper (mm)", "Lower (mm)"])
        
        st.markdown("### Space Equivalent Breakdown")
        st.markdown(breakdown_data.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# STEP 2
# =========================================================
with tabs[2]:
    st.markdown('<div class="panel"><div class="panel-title">Step 2 — Lower Arch Discrepancy Analysis</div>', unsafe_allow_html=True)
    
    # Calculate growth space
    cvms_stage = st.session_state["cvms_stage"]
    treatment_duration = st.session_state["treatment_duration"]
    growth_calc = calculate_growth_space_equivalent(
        cvms_stage, 
        treatment_duration, 
        include_growth,
        custom_sagittal=float(st.session_state.get("custom_sagittal", 0.0)),
        custom_vertical=float(st.session_state.get("custom_vertical", 0.0)),
        custom_transverse=float(st.session_state.get("custom_transverse", 0.0))
    )
    
    growth_L_total = growth_calc["lower_total"]
    growth_L_33 = growth_L_total / 2.0  # Split between 3-3 sections
    growth_L_77 = 0.0  # No growth contribution to 7-7 posterior
    
    if include_growth:
        st.markdown(
            f"<div class='band-purple'>"
            f"<b>Growth Space:</b> {growth_L_total:.2f} mm total (applied to anterior 3-3)"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # Lower midline FROM STEP 1
    lower_dental_midline = float(st.session_state["lower_dental_midline_mm"])
    
    st.markdown(
        f"<div class='band-gray'>"
        f"<b>Midline from Step 1:</b> Lower dental = {lower_dental_midline:+.2f} mm"
        f"</div>",
        unsafe_allow_html=True
    )
    
    st.markdown("---")

    # Compact table CSS
    st.markdown("""
    <style>
    /* Make inputs more compact */
    div[data-testid="stNumberInput"] > div > div > input {
        font-size: 13px !important;
        padding: 4px 8px !important;
        height: 32px !important;
        text-align: center !important;
    }
    /* Reduce spacing between rows */
    div[data-testid="column"] {
        padding: 2px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create compact table-style layout
    st.markdown("<div style='font-size: 15px; font-weight: 600; margin-bottom: 8px;'>Lower Arch Discrepancy</div>", unsafe_allow_html=True)

    # Main section headers - more compact
    col_label, col_33_span, col_sep_main, col_77_span = st.columns([1.8, 1, 0.15, 1])
    with col_33_span:
        st.markdown("<div style='text-align: center; font-weight: 600; font-size: 14px; margin-bottom: 4px; color: #1e6fff;'>3 to 3</div>", unsafe_allow_html=True)
    with col_sep_main:
        st.markdown("<div style='border-left: 2px solid #999; height: 20px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col_77_span:
        st.markdown("<div style='text-align: center; font-weight: 600; font-size: 14px; margin-bottom: 4px; color: #1e6fff;'>7 to 7</div>", unsafe_allow_html=True)

    # Sub-headers (R and L) - more compact
    col_sh1, col_r_33, col_l_33, col_sep, col_r_77, col_l_77 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col_r_33:
        st.markdown("<div style='text-align: center; font-weight: 600; font-size: 12px; color: #666;'>R</div>", unsafe_allow_html=True)
    with col_l_33:
        st.markdown("<div style='text-align: center; font-weight: 600; font-size: 12px; color: #666;'>L</div>", unsafe_allow_html=True)
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #999; height: 18px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col_r_77:
        st.markdown("<div style='text-align: center; font-weight: 600; font-size: 12px; color: #666;'>R</div>", unsafe_allow_html=True)
    with col_l_77:
        st.markdown("<div style='text-align: center; font-weight: 600; font-size: 12px; color: #666;'>L</div>", unsafe_allow_html=True)
    
    # Initialize session state for all inputs
    ss_init("ant_cs_33_R", 0.0)
    ss_init("ant_cs_33_L", 0.0)
    ss_init("cos_bicusp_77_R", 0.0)
    ss_init("cos_bicusp_77_L", 0.0)
    ss_init("cos_molar_77_R", 0.0)
    ss_init("cos_molar_77_L", 0.0)
    ss_init("cos_33_R", 0.0)
    ss_init("cos_33_L", 0.0)
    ss_init("inc_pos_33_R", 0.0)
    ss_init("inc_pos_33_L", 0.0)
    ss_init("strip_33_R", 0.0)
    ss_init("strip_33_L", 0.0)
    ss_init("strip_77_R", 0.0)
    ss_init("strip_77_L", 0.0)
    ss_init("exp_33_R", 0.0)
    ss_init("exp_33_L", 0.0)
    ss_init("exp_77_R", 0.0)
    ss_init("exp_77_L", 0.0)
    ss_init("dist_33_R", 0.0)
    ss_init("dist_33_L", 0.0)
    ss_init("dist_77_R", 0.0)
    ss_init("dist_77_L", 0.0)
    ss_init("ext_33_R", 0.0)
    ss_init("ext_33_L", 0.0)
    ss_init("ext_77_R", 0.0)
    ss_init("ext_77_L", 0.0)
    
    # INITIAL DISCREPANCY SECTION (Blue) - Compact
    st.markdown("<div style='background: rgba(30, 111, 255, .06); padding: 4px; border-radius: 4px; margin: 6px 0 2px 0;'>", unsafe_allow_html=True)

    # Ant. Crowding/Spacing
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 500; padding: 6px 0;'>Ant. Crowding/Spacing</div>", unsafe_allow_html=True)
    with col2:
        st.number_input("", step=0.1, key="ant_cs_33_R", label_visibility="collapsed")
    with col3:
        st.number_input("", step=0.1, key="ant_cs_33_L", label_visibility="collapsed")
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #999; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)

    # Read values after inputs are created
    ant_cs_R = float(st.session_state.get('ant_cs_33_R', 0.0))
    ant_cs_L = float(st.session_state.get('ant_cs_33_L', 0.0))

    with col4:
        # Mirror from 3-3
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #e8f4f9; border-radius: 3px; font-size: 13px;'>{ant_cs_R:.1f}</div>", unsafe_allow_html=True)
    with col5:
        # Mirror from 3-3
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #e8f4f9; border-radius: 3px; font-size: 13px;'>{ant_cs_L:.1f}</div>", unsafe_allow_html=True)

    # C/S Bicusp/E
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 500; padding: 6px 0;'>C/S Bicusp/E</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: center; font-size: 13px; color: #999; padding: 6px 0;'>—</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='text-align: center; font-size: 13px; color: #999; padding: 6px 0;'>—</div>", unsafe_allow_html=True)
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #999; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col4:
        st.number_input("", step=0.1, key="cos_bicusp_77_R", label_visibility="collapsed")
    with col5:
        st.number_input("", step=0.1, key="cos_bicusp_77_L", label_visibility="collapsed")

    # C/S Molars
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 500; padding: 6px 0;'>C/S Molars</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: center; font-size: 13px; color: #999; padding: 6px 0;'>—</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='text-align: center; font-size: 13px; color: #999; padding: 6px 0;'>—</div>", unsafe_allow_html=True)
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #999; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col4:
        st.number_input("", step=0.1, key="cos_molar_77_R", label_visibility="collapsed")
    with col5:
        st.number_input("", step=0.1, key="cos_molar_77_L", label_visibility="collapsed")

    # Curve of Spee - Compact
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 500; padding: 6px 0;'>Curve of Spee</div>", unsafe_allow_html=True)
    with col2:
        st.number_input("", step=0.1, key="cos_33_R", label_visibility="collapsed")
    with col3:
        st.number_input("", step=0.1, key="cos_33_L", label_visibility="collapsed")
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #999; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col4:
        # Auto-populated from 3-3
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #e8f4f9; border-radius: 3px; font-size: 13px;'>{float(st.session_state.get('cos_33_R', 0.0)):.1f}</div>", unsafe_allow_html=True)
    with col5:
        # Auto-populated from 3-3
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #e8f4f9; border-radius: 3px; font-size: 13px;'>{float(st.session_state.get('cos_33_L', 0.0)):.1f}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # MIDLINE (Orange) - Auto-calculated from Step 1 - Compact
    st.markdown("<div style='background: rgba(255, 165, 0, .12); padding: 6px; border-radius: 4px; margin: 8px 0;'>", unsafe_allow_html=True)
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 600; padding: 6px 0;'>Midline</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #fff3e0; border-radius: 3px; font-size: 13px;'>{lower_dental_midline:+.1f}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #fff3e0; border-radius: 3px; font-size: 13px;'>{-lower_dental_midline:+.1f}</div>", unsafe_allow_html=True)
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #666; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col4:
        # Mirror from 3-3
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #fff3e0; border-radius: 3px; font-size: 13px;'>{lower_dental_midline:+.1f}</div>", unsafe_allow_html=True)
    with col5:
        # Mirror from 3-3
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #fff3e0; border-radius: 3px; font-size: 13px;'>{-lower_dental_midline:+.1f}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Incisor Position - Compact
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 500; padding: 6px 0;'>Incisor Position</div>", unsafe_allow_html=True)
    with col2:
        st.number_input("", step=0.1, key="inc_pos_33_R", label_visibility="collapsed")
    with col3:
        st.number_input("", step=0.1, key="inc_pos_33_L", label_visibility="collapsed")
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #999; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)

    # Read values after inputs are created
    inc_pos_R = float(st.session_state.get('inc_pos_33_R', 0.0))
    inc_pos_L = float(st.session_state.get('inc_pos_33_L', 0.0))

    with col4:
        # Auto-populated from 3-3
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #e8f4f9; border-radius: 3px; font-size: 13px;'>{inc_pos_R:.1f}</div>", unsafe_allow_html=True)
    with col5:
        # Auto-populated from 3-3
        st.markdown(f"<div style='text-align: center; padding: 4px; background: #e8f4f9; border-radius: 3px; font-size: 13px;'>{inc_pos_L:.1f}</div>", unsafe_allow_html=True)

    # Visual separator before calculations - Compact
    st.markdown("<hr style='border: none; border-top: 1px dashed #ccc; margin: 12px 0;'>", unsafe_allow_html=True)

    # Calculate Initial Discrepancy
    initial_33_R = (float(st.session_state["ant_cs_33_R"]) +
                    float(st.session_state["cos_33_R"]) +
                    lower_dental_midline +  # R uses +midline
                    float(st.session_state["inc_pos_33_R"]))
    initial_33_L = (float(st.session_state["ant_cs_33_L"]) +
                    float(st.session_state["cos_33_L"]) +
                    (-lower_dental_midline) +  # L uses -midline
                    float(st.session_state["inc_pos_33_L"]))
    
    # 7-7 includes: Ant C/S + C/S Bicusp + C/S Molars + COS + Midline + Inc Pos (from 3-3)
    initial_77_R = (float(st.session_state["ant_cs_33_R"]) +  # Ant C/S from 3-3
                    float(st.session_state["cos_bicusp_77_R"]) +
                    float(st.session_state["cos_molar_77_R"]) +  # C/S Molars (7-7 only)
                    float(st.session_state["cos_33_R"]) +  # COS from 3-3
                    lower_dental_midline +  # Midline from 3-3 (R uses +midline)
                    float(st.session_state["inc_pos_33_R"]))  # Inc Pos from 3-3
    initial_77_L = (float(st.session_state["ant_cs_33_L"]) +  # Ant C/S from 3-3
                    float(st.session_state["cos_bicusp_77_L"]) +
                    float(st.session_state["cos_molar_77_L"]) +  # C/S Molars (7-7 only)
                    float(st.session_state["cos_33_L"]) +  # COS from 3-3
                    (-lower_dental_midline) +  # Midline from 3-3 (L uses -midline)
                    float(st.session_state["inc_pos_33_L"]))  # Inc Pos from 3-3
    
    # INITIAL DISCREPANCY (Enhanced highlighting) - Compact
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='background: linear-gradient(135deg, rgba(255, 193, 7, .35) 0%, rgba(255, 152, 0, .35) 100%); padding: 8px 12px; border-radius: 6px; border: 2px solid rgba(255, 152, 0, .6); font-size: 14px; font-weight: 800; color: #e65100;'>⚠️ Initial Discrepancy</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(255, 193, 7, .35) 0%, rgba(255, 152, 0, .35) 100%); padding: 8px; border-radius: 6px; border: 2px solid rgba(255, 152, 0, .6); text-align: center; font-weight: 800; font-size: 16px; color: #e65100;'>{initial_33_R:.1f}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(255, 193, 7, .35) 0%, rgba(255, 152, 0, .35) 100%); padding: 8px; border-radius: 6px; border: 2px solid rgba(255, 152, 0, .6); text-align: center; font-weight: 800; font-size: 16px; color: #e65100;'>{initial_33_L:.1f}</div>", unsafe_allow_html=True)
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #e65100; height: 36px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(255, 193, 7, .35) 0%, rgba(255, 152, 0, .35) 100%); padding: 8px; border-radius: 6px; border: 2px solid rgba(255, 152, 0, .6); text-align: center; font-weight: 800; font-size: 16px; color: #e65100;'>{initial_77_R:.1f}</div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(255, 193, 7, .35) 0%, rgba(255, 152, 0, .35) 100%); padding: 8px; border-radius: 6px; border: 2px solid rgba(255, 152, 0, .6); text-align: center; font-weight: 800; font-size: 16px; color: #e65100;'>{initial_77_L:.1f}</div>", unsafe_allow_html=True)
    
    # SPACE GAINED SECTION (Green) - Compact
    st.markdown("<div style='background: rgba(30, 180, 90, .08); padding: 6px; border-radius: 4px; margin: 8px 0;'>", unsafe_allow_html=True)

    # Stripping - Compact
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 600; padding: 6px 0;'>Stripping</div>", unsafe_allow_html=True)
    with col2:
        st.number_input("", step=0.1, key="strip_33_R", label_visibility="collapsed")
    with col3:
        st.number_input("", step=0.1, key="strip_33_L", label_visibility="collapsed")
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #666; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)

    # Read 3-3 values
    strip_33_R = float(st.session_state.get('strip_33_R', 0.0))
    strip_33_L = float(st.session_state.get('strip_33_L', 0.0))

    # Auto-populate 7-7 to at least match 3-3 (but allow user to add more for posterior IPR)
    # Only update if 7-7 is less than 3-3 (preserves manual increases)
    strip_77_R_current = float(st.session_state.get('strip_77_R', 0.0))
    strip_77_L_current = float(st.session_state.get('strip_77_L', 0.0))

    if strip_77_R_current < strip_33_R:
        st.session_state["strip_77_R"] = strip_33_R
    if strip_77_L_current < strip_33_L:
        st.session_state["strip_77_L"] = strip_33_L

    with col4:
        st.number_input("", step=0.1, key="strip_77_R", label_visibility="collapsed")
    with col5:
        st.number_input("", step=0.1, key="strip_77_L", label_visibility="collapsed")

    # Expansion - Compact
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 600; padding: 6px 0;'>Expansion</div>", unsafe_allow_html=True)
    with col2:
        st.number_input("", step=0.1, key="exp_33_R", label_visibility="collapsed")
    with col3:
        st.number_input("", step=0.1, key="exp_33_L", label_visibility="collapsed")
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #666; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col4:
        st.number_input("", step=0.1, key="exp_77_R", label_visibility="collapsed")
    with col5:
        st.number_input("", step=0.1, key="exp_77_L", label_visibility="collapsed")

    # Distalizing 6-6 - Compact (7-7 only, doesn't affect canines)
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 600; padding: 6px 0;'>Distalizing 6-6</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: center; padding: 4px; font-size: 13px; color: #999;'>—</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='text-align: center; padding: 4px; font-size: 13px; color: #999;'>—</div>", unsafe_allow_html=True)
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #666; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col4:
        st.number_input("", step=0.1, key="dist_77_R", label_visibility="collapsed")
    with col5:
        st.number_input("", step=0.1, key="dist_77_L", label_visibility="collapsed")

    # Extraction - Compact
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='font-size: 13px; font-weight: 600; padding: 6px 0;'>Extraction</div>", unsafe_allow_html=True)
    with col2:
        st.number_input("", step=0.1, key="ext_33_R", label_visibility="collapsed")
    with col3:
        st.number_input("", step=0.1, key="ext_33_L", label_visibility="collapsed")
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #666; height: 32px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col4:
        st.number_input("", step=0.1, key="ext_77_R", label_visibility="collapsed")
    with col5:
        st.number_input("", step=0.1, key="ext_77_L", label_visibility="collapsed")

    st.markdown("</div>", unsafe_allow_html=True)
    
    # Calculate Total Gained and Remaining
    # Note: Distalizing 6-6 does NOT affect 3-3 (canines), only 7-7 (molars)
    gained_33_R = (float(st.session_state["strip_33_R"]) +
                   float(st.session_state["exp_33_R"]) +
                   float(st.session_state["ext_33_R"]) +
                   growth_L_33)
    gained_33_L = (float(st.session_state["strip_33_L"]) +
                   float(st.session_state["exp_33_L"]) +
                   float(st.session_state["ext_33_L"]) +
                   growth_L_33)
    gained_77_R = (float(st.session_state["strip_77_R"]) + 
                   float(st.session_state["exp_77_R"]) + 
                   float(st.session_state["dist_77_R"]) + 
                   float(st.session_state["ext_77_R"]) + 
                   growth_L_77)
    gained_77_L = (float(st.session_state["strip_77_L"]) + 
                   float(st.session_state["exp_77_L"]) + 
                   float(st.session_state["dist_77_L"]) + 
                   float(st.session_state["ext_77_L"]) + 
                   growth_L_77)
    
    remaining_33_R = initial_33_R + gained_33_R
    remaining_33_L = initial_33_L + gained_33_L
    remaining_77_R = initial_77_R + gained_77_R
    remaining_77_L = initial_77_L + gained_77_L
    
    # Store in session state for Step 3
    st.session_state["remaining_L_R"] = remaining_33_R  # 3-3 anterior
    st.session_state["remaining_L_L"] = remaining_33_L  # 3-3 anterior
    # For 7-7: exclude C/S Molars from movement (C/S Molars affects discrepancy but not tooth movement)
    st.session_state["remaining_77_R"] = remaining_77_R - float(st.session_state["cos_molar_77_R"])
    st.session_state["remaining_77_L"] = remaining_77_L - float(st.session_state["cos_molar_77_L"])

    # Visual separator before Remaining Discrepancy - Compact
    st.markdown("<hr style='border: none; border-top: 1px dashed #ccc; margin: 12px 0;'>", unsafe_allow_html=True)

    # REMAINING DISCREPANCY (Enhanced highlighting) - Compact
    col1, col2, col3, col_sep, col4, col5 = st.columns([1.8, 0.5, 0.5, 0.15, 0.5, 0.5])
    with col1:
        st.markdown("<div style='background: linear-gradient(135deg, rgba(76, 175, 80, .35) 0%, rgba(56, 142, 60, .35) 100%); padding: 8px 12px; border-radius: 6px; border: 2px solid rgba(56, 142, 60, .7); font-size: 14px; font-weight: 800; color: #1b5e20;'>✓ Remaining Discrepancy</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(76, 175, 80, .35) 0%, rgba(56, 142, 60, .35) 100%); padding: 8px; border-radius: 6px; border: 2px solid rgba(56, 142, 60, .7); text-align: center; font-weight: 800; font-size: 16px; color: #1b5e20;'>{remaining_33_R:.1f}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(76, 175, 80, .35) 0%, rgba(56, 142, 60, .35) 100%); padding: 8px; border-radius: 6px; border: 2px solid rgba(56, 142, 60, .7); text-align: center; font-weight: 800; font-size: 16px; color: #1b5e20;'>{remaining_33_L:.1f}</div>", unsafe_allow_html=True)
    with col_sep:
        st.markdown("<div style='border-left: 2px solid #1b5e20; height: 36px; margin: 0 auto;'></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(76, 175, 80, .35) 0%, rgba(56, 142, 60, .35) 100%); padding: 8px; border-radius: 6px; border: 2px solid rgba(56, 142, 60, .7); text-align: center; font-weight: 800; font-size: 16px; color: #1b5e20;'>{remaining_77_R:.1f}</div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(76, 175, 80, .35) 0%, rgba(56, 142, 60, .35) 100%); padding: 8px; border-radius: 6px; border: 2px solid rgba(56, 142, 60, .7); text-align: center; font-weight: 800; font-size: 16px; color: #1b5e20;'>{remaining_77_L:.1f}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# STEP 3
# =========================================================
with tabs[3]:
    st.markdown('<div class="panel"><div class="panel-title">Step 3 — Proposed Dental Movement</div>', unsafe_allow_html=True)
    st.markdown(
        "<div class='band-gray'>"
        "<b>Allocates remaining discrepancy</b> across tooth segments using expected movement patterns. "
        "Arrows show direction/magnitude of movement needed."
        "</div>",
        unsafe_allow_html=True
    )

    # Treatment goal selector
    st.markdown('<div class="band-blue">Treatment Goal</div>', unsafe_allow_html=True)
    treat_to = st.selectbox(
        "Treat to occlusion:",
        ["Class I", "Class II", "Class III"],
        index=0,
        key="treat_to"
    )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Upper Extraction inputs
    st.markdown('<div class="band-purple">Upper Arch Extraction Space</div>', unsafe_allow_html=True)
    st.markdown(
        "<div class='band-gray'>"
        "Enter extraction space for upper arch (e.g., 7.0 mm for first premolar extraction)"
        "</div>",
        unsafe_allow_html=True
    )

    # Initialize session state
    ss_init("upper_extraction_R", 0.0)
    ss_init("upper_extraction_L", 0.0)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.number_input("Right Upper Extraction (mm)", step=0.1, key="upper_extraction_R", min_value=0.0)
    with col2:
        st.number_input("Left Upper Extraction (mm)", step=0.1, key="upper_extraction_L", min_value=0.0)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ======================================
    # CALCULATE MOVEMENTS FROM REMAINING
    # ======================================
    
    # Get remaining from session state (calculated in Step 2)
    # McLAUGHLIN VTO: Movement = Remaining Discrepancy (1:1 relationship)
    
    L_remaining_33_R = float(st.session_state.get("remaining_L_R", 0.0))  # 3-3 R
    L_remaining_33_L = float(st.session_state.get("remaining_L_L", 0.0))  # 3-3 L
    L_remaining_77_R = float(st.session_state.get("remaining_77_R", 0.0))  # 7-7 R
    L_remaining_77_L = float(st.session_state.get("remaining_77_L", 0.0))  # 7-7 L

    # Get midline for incisor correction
    lower_dental_midline = float(st.session_state.get("lower_dental_midline_mm", 0.0))
    
    # ======================================
    # McLAUGHLIN VTO CALCULATION
    # ======================================
    # Following McLaughlin/Bennett/Trevisi exact methodology

    # STEP 1: Lower midline correction
    # Based on original lower dental midline from Chart 1
    l_inc = -lower_dental_midline

    # STEP 2: Lower canine movement
    # Based on "Remaining Discrepancy" in 3-3 column (Chart 2)
    # Canines move by the FULL remaining discrepancy amount
    # Midline is corrected separately by incisors only
    # Negative = distal movement, Positive = mesial movement
    l_r3 = L_remaining_33_R
    l_l3 = L_remaining_33_L

    # STEP 3: Lower premolar/molar space
    # Space behind canine = Total 7-7 space minus 3-3 space
    # This represents space available in premolar/molar region
    lower_premolar_space_R = L_remaining_77_R - L_remaining_33_R
    lower_premolar_space_L = L_remaining_77_L - L_remaining_33_L

    # STEP 4: Lower first molar movement
    # Based on canine movement + available space in premolar region
    # Formula: Molar movement = Canine movement + Premolar/molar space
    l_r6 = l_r3 + lower_premolar_space_R
    l_l6 = l_l3 + lower_premolar_space_L

    # STEP 5: Upper first molar movement
    # Based on original molar relationship (Chart 1) + lower molar movement
    # Get initial Class relationship from Step 1
    initial_r6_class = float(st.session_state.get("r6_init", 0.0))
    initial_l6_class = float(st.session_state.get("l6_init", 0.0))

    # Class correction needed to achieve Class I
    # Original molar position + Lower molar movement gives upper molar movement
    u_r6 = l_r6 - initial_r6_class
    u_l6 = l_l6 - initial_l6_class

    # STEP 6: Upper premolar/molar space
    # Get upper extraction values from user input in Step 3
    upper_extraction_R = float(st.session_state.get("upper_extraction_R", 0.0))
    upper_extraction_L = float(st.session_state.get("upper_extraction_L", 0.0))

    # Upper premolar space = extraction space (space between canine and molar)
    upper_premolar_space_R = upper_extraction_R
    upper_premolar_space_L = upper_extraction_L

    # STEP 7: Upper canine movement
    # Formula: Canine movement = Molar movement - Extraction space
    # This ensures the space between molar and canine closes by the extraction amount
    #
    # Example with 7mm extraction:
    # - Molar moves +2.5mm mesial
    # - Canine = 2.5 - 7 = -4.5mm distal
    # - Space closed = 2.5 - (-4.5) = 7mm ✓
    #
    # With no extraction (0mm):
    # - Canine = Molar - 0 = Molar (they move together)
    u_r3 = u_r6 - upper_premolar_space_R
    u_l3 = u_l6 - upper_premolar_space_L

    # STEP 7B: Class Relationship Adjustment
    # Apply treatment goal adjustment to upper molars AND canines
    # Class II: Move upper arch +7mm mesial (forward)
    # Class III: Move upper arch -6mm distal (backward)
    class_adjustment = 0.0
    if treat_to == "Class II":
        class_adjustment = 7.0  # Mesial movement
    elif treat_to == "Class III":
        class_adjustment = -6.0  # Distal movement

    # Apply adjustment to both molars and canines
    u_r6 += class_adjustment
    u_l6 += class_adjustment
    u_r3 += class_adjustment
    u_l3 += class_adjustment

    # STEP 8: Upper midline correction
    # Based on original upper dental midline from Chart 1
    upper_midline = float(st.session_state.get("upper_midline_mm", 0.0))
    u_inc = -upper_midline

    # ======================================
    # RENDER THE VISUALIZATION
    # ======================================
    st.markdown("### Visual Treatment Objective")

    svg = proposed_movement_svg_two_arch(
        u_r6, u_r3, u_inc, u_l3, u_l6,
        l_r6, l_r3, l_inc, l_l3, l_l6,
    )
    components.html(svg, height=760, scrolling=False)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ======================================
    # SHOW DETAILED BREAKDOWN (McLaughlin Steps)
    # ======================================
    st.markdown("### McLaughlin VTO Step-by-Step Calculation")

    st.markdown('<div class="band-blue">Lower Arch Calculations (Steps 1-4)</div>', unsafe_allow_html=True)

    lower_calc = pd.DataFrame([
        ["Step 1: Midline Correction", f"{lower_dental_midline:+.1f}", "→", f"{l_inc:+.1f}", "Incisors"],
        ["Step 2: Canine Movement", f"Remaining Disc.", "→", f"{l_r3:+.1f} / {l_l3:+.1f}", "R3 / L3"],
        ["", f"{L_remaining_33_R:+.1f} / {L_remaining_33_L:+.1f}", "", "", "Full amount"],
        ["Step 3: Premolar/Molar Space", f"{lower_premolar_space_R:+.1f} / {lower_premolar_space_L:+.1f}", "", "", "Behind canines"],
        ["Step 4: Molar Movement", f"Canine + PM space", "→", f"{l_r6:+.1f} / {l_l6:+.1f}", "R6 / L6"],
    ], columns=["McLaughlin Step", "Input", "", "Result", "Applies to"])
    st.dataframe(lower_calc, use_container_width=True, hide_index=True)

    st.markdown('<div class="band-green">Upper Arch Calculations (Steps 5-8)</div>', unsafe_allow_html=True)

    # Build step-by-step display
    steps = [
        ["Step 5: Molar Movement", f"Lower M6 - Class offset", "→", f"{u_r6:+.1f} / {u_l6:+.1f}", "R6 / L6"],
        ["Step 6: Premolar/Molar Space", f"{upper_premolar_space_R:+.1f} / {upper_premolar_space_L:+.1f}", "", "", "Extraction space"],
        ["Step 7: Canine Movement", f"M6 - Extraction space", "→", f"{u_r3:+.1f} / {u_l3:+.1f}", "R3 / L3"],
    ]

    # Add Class adjustment if not treating to Class I
    if treat_to != "Class I":
        class_desc = f"Treat to {treat_to}"
        steps.append(["Step 7B: Class Adjustment", class_desc, "→", f"{class_adjustment:+.1f}", "Both M6 & C3"])

    steps.append(["Step 8: Midline Correction", f"{upper_midline:+.1f}", "→", f"{u_inc:+.1f}", "Incisors"])

    upper_calc = pd.DataFrame(steps, columns=["McLaughlin Step", "Input", "", "Result", "Applies to"])
    st.dataframe(upper_calc, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Final Movement Summary (mm)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Upper Arch**")
        upper_movements = pd.DataFrame([
            ["R6", f"{u_r6:+.1f}"],
            ["R3", f"{u_r3:+.1f}"],
            ["Inc", f"{u_inc:+.1f}"],
            ["L3", f"{u_l3:+.1f}"],
            ["L6", f"{u_l6:+.1f}"],
        ], columns=["Tooth", "Movement"])
        st.dataframe(upper_movements, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Lower Arch**")
        lower_movements = pd.DataFrame([
            ["R6", f"{l_r6:+.1f}"],
            ["R3", f"{l_r3:+.1f}"],
            ["Inc", f"{l_inc:+.1f}"],
            ["L3", f"{l_l3:+.1f}"],
            ["L6", f"{l_l6:+.1f}"],
        ], columns=["Tooth", "Movement"])
        st.dataframe(lower_movements, use_container_width=True, hide_index=True)

    st.markdown(
        "<div class='hint'>"
        "Positive = toward patient's left; Negative = toward patient's right<br>"
        "<b>Calculation follows McLaughlin/Bennett/Trevisi methodology exactly</b>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)
