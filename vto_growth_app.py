# vto_growth_app.py
# Growth-aware Dental VTO (McLaughlin/Dolphin-inspired) — Upper + Lower arches with separate calculations
# Adds (LOWER ONLY): dental midline + skeletal midline (numbers track with LOWER DENTAL midline)

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
.hint {color: rgba(49,51,63,0.65); font-size: 0.92rem;}
hr {border: none; border-top: 1px solid rgba(49,51,63,.12); margin: 18px 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


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
    d: float,
    s: float,
    upper_midline_mm: float,
    lower_dental_midline_mm: float,
    lower_skeletal_midline_mm: float,
) -> str:
    W, H = 920, 560
    cx = W // 2

    # two baselines
    y_upper = 205
    y_lower = 355

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

        <!-- LOWER -->
        <text x="70" y="{y_lower-20}" font-family="Arial" font-size="16" font-weight="700">Lower</text>
        <line x1="90" y1="{y_lower}" x2="{W-90}" y2="{y_lower}" stroke="#333" stroke-width="4"/>
        {tooth(x_r6, y_lower+55, "6")}
        {tooth(x_ld, y_lower+55, "1")}
        {tooth(x_l6, y_lower+55, "6")}
        {midline_marker(x_ls, y_lower, color="#7a7a7a", label="Skeletal")}
        {midline_marker(x_ld, y_lower, color="#111", label="Dental")}

        <!-- Value boxes -->
        <text x="160" y="78" font-family="Arial" font-size="16" font-weight="700">R6</text>
        {box(160, 105, f"{r6:.1f}")}

        <text x="{W-160}" y="78" font-family="Arial" font-size="16" font-weight="700" text-anchor="end">L6</text>
        {box(W-160, 105, f"{l6:.1f}")}

        <text x="{cx-26}" y="{H-110}" font-family="Arial" font-size="16" font-weight="700">D=</text>
        {box(cx+30, H-115, f"{d:.1f}")}

        <text x="{cx-26}" y="{H-62}" font-family="Arial" font-size="16" font-weight="700">S=</text>
        {box(cx+30, H-67, f"{s:.1f}")}

      </svg>
    </div>
    """
    return html


# -----------------------------
# Step 3 SVG (TRUE Upper vs Lower rows)
# -----------------------------
def proposed_movement_svg_two_arch(
    # Upper
    u_r6: float, u_r3: float, u_inc: float, u_l3: float, u_l6: float,
    # Lower
    l_r6: float, l_r3: float, l_inc: float, l_l3: float, l_l6: float,
) -> str:
    W, H = 980, 720
    cx = W // 2

    # Baselines
    yU = 260   # upper baseline y
    yL = 540   # lower baseline y

    # X positions
    x_r6 = 120
    x_r3 = 330
    x_inc = cx
    x_l3 = 650
    x_l6 = 860

    def fmt(v: float) -> str:
        # Dolphin-ish: show one decimal, keep -0.0 from appearing
        v = 0.0 if abs(v) < 0.05 else v
        return f"{v:.1f}"

    def value_box(x, y, label, val, w=84, h=46, fs=22):
        return f"""
        <text x="{x}" y="{y-10}" text-anchor="middle"
              font-family="Arial" font-size="18" font-weight="800" fill="#111">{label}</text>
        <rect x="{x-w/2}" y="{y}" width="{w}" height="{h}" rx="6"
              fill="white" stroke="#9a9a9a" stroke-width="2.2"/>
        <text x="{x}" y="{y+h/2+8}" text-anchor="middle"
              font-family="Arial" font-size="{fs}" font-weight="800" fill="#111">{fmt(val)}</text>
        """

    def tooth(x, y, label):
        # slightly larger tooth
        return f"""
        <path d="M {x-22} {y-78}
                 C {x-46} {y-55}, {x-46} {y-10}, {x-22} {y+12}
                 C {x-12} {y+42}, {x+12} {y+42}, {x+22} {y+12}
                 C {x+46} {y-10}, {x+46} {y-55}, {x+22} {y-78}
                 Z"
              fill="white" stroke="#333" stroke-width="2.4"/>
        <circle cx="{x}" cy="{y-28}" r="18" fill="white" stroke="#333" stroke-width="2.4"/>
        <text x="{x}" y="{y-22}" text-anchor="middle" font-family="Arial" font-size="16" font-weight="800">{label}</text>
        """

    def arrow(x, y, val, color="#1f77b4"):
        # Draw a horizontal arrow under tooth with big number next to it
        # Rightward arrow for positive, leftward for negative, small stub for zero
        v = 0.0 if abs(val) < 0.05 else val
        L = max(45, min(140, abs(v) * 40))  # more dramatic scale
        if v > 0:
            x1, x2 = x - 10, x - 10 + L
            tx = x2 + 24
            anchor = "start"
        elif v < 0:
            x1, x2 = x + 10, x + 10 - L
            tx = x2 - 24
            anchor = "end"
        else:
            x1, x2 = x - 40, x + 40
            tx = x + 0
            anchor = "middle"

        return f"""
        <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"
              stroke="{color}" stroke-width="7" marker-end="url(#arrowhead)"/>
        <text x="{tx}" y="{y+10}" text-anchor="{anchor}"
              font-family="Arial" font-size="22" font-weight="900" fill="#111">{fmt(val)}</text>
        """

    def row(title, y_base, r6, r3, inc, l3, l6):
        # top numeric boxes (like Dolphin)
        top_y = y_base - 190
        # baseline
        line = f"""<line x1="80" y1="{y_base}" x2="{W-80}" y2="{y_base}" stroke="#333" stroke-width="4.2"/>"""

        return f"""
        <text x="{cx}" y="{y_base-240}" text-anchor="middle"
              font-family="Arial" font-size="26" font-weight="900">{title}</text>

        {value_box(x_r6, top_y, "R6", r6)}
        {value_box(x_r3, top_y, "R3", r3)}
        {value_box(x_inc, top_y, "Inc", inc)}
        {value_box(x_l3, top_y, "L3", l3)}
        {value_box(x_l6, top_y, "L6", l6)}

        {line}

        {tooth(x_r6, y_base+78, "6")}
        {tooth(x_r3, y_base+78, "3")}
        {tooth(x_inc, y_base+78, "1")}
        {tooth(x_l3, y_base+78, "3")}
        {tooth(x_l6, y_base+78, "6")}

        {arrow(x_r6, y_base+185, r6)}
        {arrow(x_r3, y_base+185, r3)}
        {arrow(x_inc, y_base+185, inc)}
        {arrow(x_l3, y_base+185, l3)}
        {arrow(x_l6, y_base+185, l6)}
        """

    html = f"""
    <div style="border:1px solid rgba(49,51,63,.15); border-radius:16px; padding:12px; background:white;">
      <svg width="100%" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <marker id="arrowhead" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
            <path d="M0,0 L0,12 L12,6 z" fill="#1f77b4"/>
          </marker>
        </defs>

        <text x="{cx}" y="42" text-anchor="middle"
              font-family="Arial" font-size="28" font-weight="900">
          Dental VTO (Proposed Dental Movement)
        </text>

        {row("Upper", yU, u_r6, u_r3, u_inc, u_l3, u_l6)}
        {row("Lower", yL, l_r6, l_r3, l_inc, l_l3, l_l6)}
      </svg>
    </div>
    """
    return html


# -----------------------------
# Movement allocator (MVP — replace later with McLaughlin rules)
# -----------------------------
def expected_movement_allocation(remaining: float, treat_to: str) -> dict[str, float]:
    """
    remaining < 0 means still crowded (need space).
    Allocates magnitude across segments (6, 3, inc).
    """
    if treat_to == "Class II":
        ant_w, post_w = 0.65, 0.35
    elif treat_to == "Class III":
        ant_w, post_w = 0.45, 0.55
    else:
        ant_w, post_w = 0.55, 0.45

    mag = abs(remaining)
    anterior = mag * ant_w
    posterior = mag * post_w
    inc = anterior * 0.55
    canine = anterior * 0.45
    molar = posterior
    return {"6": molar, "3": canine, "inc": inc}


def outward_sign(rem: float, side: str) -> float:
    """
    Defines outward direction in the diagram:
      - Left side outward -> positive
      - Right side outward -> negative
    If rem < 0 (crowding remains): go outward.
    If rem > 0 (excess space): go inward (reverse).
    """
    if rem == 0:
        return 0.0
    outward = 1.0 if side == "L" else -1.0
    return outward if rem < 0 else -outward


# -----------------------------
# Defaults
# -----------------------------
ss_init("include_growth", True)

# Step 1: initial positions
ss_init("r6_init", 0.0)
ss_init("l6_init", 0.0)
ss_init("d_init", 0.0)
ss_init("s_init", 0.0)

# Step 1 midlines
ss_init("upper_midline_mm", 0.0)

# LOWER ONLY: dental + skeletal midline
ss_init("lower_dental_midline_mm", 0.0)
ss_init("lower_skeletal_midline_mm", 0.0)

# Growth inputs (space equivalent per arch total)
ss_init("growth_upper_total", 0.0)
ss_init("growth_lower_total", 0.0)

# Store remaining discrepancies
ss_init("remaining_U_R", 0.0)
ss_init("remaining_U_L", 0.0)
ss_init("remaining_L_R", 0.0)
ss_init("remaining_L_L", 0.0)


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("## Global")
include_growth = st.sidebar.checkbox("Include growth (space equiv)", value=st.session_state["include_growth"], key="include_growth")
st.sidebar.markdown("---")
st.sidebar.markdown("<div class='hint'>Sign convention: <b>Crowding = negative</b>, spacing = positive. Space gained rows are positive. Goal: Remaining ≈ 0.</div>", unsafe_allow_html=True)


# -----------------------------
# Header
# -----------------------------
st.markdown("# Growth-aware Dental VTO (McLaughlin-inspired)")
st.markdown("<div class='small-muted'>Upper and lower arches calculated separately. Lower arch includes dental + skeletal midline; midline discrepancy numbers track with the lower dental midline.</div>", unsafe_allow_html=True)

tabs = st.tabs(["Step 1: Initial Tooth Positions", "Step 2: Upper + Lower Arch Discrepancy", "Step 3: Determining Movement"])


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

        c3, c4 = st.columns(2)
        with c3:
            st.number_input("D (mm)", step=0.1, key="d_init")
        with c4:
            st.number_input("S (mm)", step=0.1, key="s_init")

        st.markdown('<div class="band-blue">Midlines</div>', unsafe_allow_html=True)

        st.number_input("Upper dental midline (mm)", step=0.1, key="upper_midline_mm")

        m1, m2 = st.columns(2)
        with m1:
            st.number_input("Lower dental midline (mm)", step=0.1, key="lower_dental_midline_mm")
        with m2:
            st.number_input("Lower skeletal midline (mm)", step=0.1, key="lower_skeletal_midline_mm")

        st.markdown(
            "<div class='band-gray'>"
            "<b>Note:</b> In Step 2 (Lower arch), the Midline discrepancy row is automatically computed from "
            "<b>Lower dental midline</b> so the numbers always track it."
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Visual Preview</div>', unsafe_allow_html=True)

        svg = initial_position_svg(
            r6=float(st.session_state["r6_init"]),
            l6=float(st.session_state["l6_init"]),
            d=float(st.session_state["d_init"]),
            s=float(st.session_state["s_init"]),
            upper_midline_mm=float(st.session_state["upper_midline_mm"]),
            lower_dental_midline_mm=float(st.session_state["lower_dental_midline_mm"]),
            lower_skeletal_midline_mm=float(st.session_state["lower_skeletal_midline_mm"]),
        )
        components.html(svg, height=620, scrolling=False)

        delta_ml = float(st.session_state["lower_dental_midline_mm"]) - float(st.session_state["lower_skeletal_midline_mm"])
        st.markdown(
            f"<div class='band-gray'><b>Lower midline delta (Dental − Skeletal):</b> {delta_ml:+.2f} mm</div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# STEP 2
# =========================================================
with tabs[1]:
    st.markdown('<div class="panel"><div class="panel-title">Step 2 — Discrepancy Calculations (Upper + Lower)</div>', unsafe_allow_html=True)
    st.markdown(
        "<div class='band-gray'>"
        "<b>Separate calculations:</b> Upper and Lower arches are computed independently (Right + Left). "
        "<br><span class='hint'>Lower Midline component is auto-derived from Step 1 lower dental midline.</span>"
        "</div>",
        unsafe_allow_html=True
    )

    # Growth totals
    st.markdown('<div class="band-green">Growth (space equivalent)</div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        st.number_input("Upper growth space equiv total (mm)", step=0.1, key="growth_upper_total")
    with g2:
        st.number_input("Lower growth space equiv total (mm)", step=0.1, key="growth_lower_total")

    growth_label = "Growth (space equiv) [ON]" if include_growth else "Growth (space equiv) [OFF]"
    growth_U_total = float(st.session_state["growth_upper_total"]) if include_growth else 0.0
    growth_L_total = float(st.session_state["growth_lower_total"]) if include_growth else 0.0

    growth_U_R = growth_U_total / 2.0
    growth_U_L = growth_U_total / 2.0
    growth_L_R = growth_L_total / 2.0
    growth_L_L = growth_L_total / 2.0

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ---------- LOWER ARCH ----------
    st.markdown("## Lower Arch Discrepancy")

    # Lower midline component tracks lower dental midline
    # Convention: Right midline component = +dental_midline, Left = -dental_midline (as in Dolphin screenshot style)
    lower_dental_midline = float(st.session_state["lower_dental_midline_mm"])
    midline_L_R = +lower_dental_midline
    midline_L_L = -lower_dental_midline

    st.markdown('<div class="band-blue">Initial Discrepancy Inputs (Lower 3–3)</div>', unsafe_allow_html=True)
    lA, lB = st.columns(2)
    with lA:
        st.markdown("**Lower Right (3–3)**")
        L_ant_R = st.number_input("Ant. Crowding/Spacing (R)", value=0.0, step=0.1, key="L_ant_R")
        L_cos_R = st.number_input("Curve of Spee (R)", value=0.0, step=0.1, key="L_cos_R")
        st.number_input("Midline (R) — auto", value=midline_L_R, step=0.1, disabled=True, key="L_mid_R_auto")
        L_inc_R = st.number_input("Incisor position (R)", value=0.0, step=0.1, key="L_inc_R")

    with lB:
        st.markdown("**Lower Left (3–3)**")
        L_ant_L = st.number_input("Ant. Crowding/Spacing (L)", value=0.0, step=0.1, key="L_ant_L")
        L_cos_L = st.number_input("Curve of Spee (L)", value=0.0, step=0.1, key="L_cos_L")
        st.number_input("Midline (L) — auto", value=midline_L_L, step=0.1, disabled=True, key="L_mid_L_auto")
        L_inc_L = st.number_input("Incisor position (L)", value=0.0, step=0.1, key="L_inc_L")

    st.markdown('<div class="band-green">Space Gained (Lower)</div>', unsafe_allow_html=True)
    lC, lD = st.columns(2)
    with lC:
        st.markdown("**Lower Right**")
        L_strip_R = st.number_input("Stripping/IPR (R)", value=0.0, step=0.1, key="L_strip_R")
        L_exp_R = st.number_input("Expansion (treatment) (R)", value=0.0, step=0.1, key="L_exp_R")
        L_dist_R = st.number_input("Distalizing 6–6 (R)", value=0.0, step=0.1, key="L_dist_R")
        L_ext_R = st.number_input("Extraction space (R)", value=0.0, step=0.1, key="L_ext_R")

    with lD:
        st.markdown("**Lower Left**")
        L_strip_L = st.number_input("Stripping/IPR (L)", value=0.0, step=0.1, key="L_strip_L")
        L_exp_L = st.number_input("Expansion (treatment) (L)", value=0.0, step=0.1, key="L_exp_L")
        L_dist_L = st.number_input("Distalizing 6–6 (L)", value=0.0, step=0.1, key="L_dist_L")
        L_ext_L = st.number_input("Extraction space (L)", value=0.0, step=0.1, key="L_ext_L")

    L_initial_R = compute_initial_discrepancy(L_ant_R, L_cos_R, midline_L_R, L_inc_R)
    L_initial_L = compute_initial_discrepancy(L_ant_L, L_cos_L, midline_L_L, L_inc_L)

    L_gained_R, L_remaining_R = compute_remaining_dolphin(L_initial_R, L_strip_R, L_exp_R, L_dist_R, L_ext_R, growth_L_R)
    L_gained_L, L_remaining_L = compute_remaining_dolphin(L_initial_L, L_strip_L, L_exp_L, L_dist_L, L_ext_L, growth_L_L)

    st.session_state["remaining_L_R"] = float(L_remaining_R)
    st.session_state["remaining_L_L"] = float(L_remaining_L)

    lower_table = pd.DataFrame(
        [
            ["Ant. Crowding/Spacing", L_ant_R, L_ant_L],
            ["Curve of Spee", L_cos_R, L_cos_L],
            ["Midline (tracks Lower dental midline)", midline_L_R, midline_L_L],
            ["Incisor position", L_inc_R, L_inc_L],
            ["Initial Discrepancy", L_initial_R, L_initial_L],
            ["Stripping/IPR", L_strip_R, L_strip_L],
            ["Expansion (treatment)", L_exp_R, L_exp_L],
            ["Distalizing 6–6", L_dist_R, L_dist_L],
            ["Extraction space", L_ext_R, L_ext_L],
            [growth_label, growth_L_R, growth_L_L],
            ["Total Gained", L_gained_R, L_gained_L],
            ["Remaining Discrepancy", L_remaining_R, L_remaining_L],
        ],
        columns=["Lower (Component)", "R (mm)", "L (mm)"],
    )
    st.dataframe(lower_table, use_container_width=True, hide_index=True)

    st.markdown(
        f"<div class='band-gray'><b>Lower status:</b> Right {L_remaining_R:+.2f} ({remaining_status(L_remaining_R)}), "
        f"Left {L_remaining_L:+.2f} ({remaining_status(L_remaining_L)})</div>",
        unsafe_allow_html=True
    )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ---------- UPPER ARCH ----------
    st.markdown("## Upper Arch Discrepancy")
    st.markdown('<div class="band-blue">Initial Discrepancy Inputs (Upper 3–3)</div>', unsafe_allow_html=True)

    uA, uB = st.columns(2)
    with uA:
        st.markdown("**Upper Right (3–3)**")
        U_ant_R = st.number_input("U Ant. Crowding/Spacing (R)", value=0.0, step=0.1, key="U_ant_R")
        U_cos_R = st.number_input("U Curve of Spee (R)", value=0.0, step=0.1, key="U_cos_R")
        U_mid_R = st.number_input("U Midline component (R)", value=0.0, step=0.1, key="U_mid_R")
        U_inc_R = st.number_input("U Incisor position (R)", value=0.0, step=0.1, key="U_inc_R")

    with uB:
        st.markdown("**Upper Left (3–3)**")
        U_ant_L = st.number_input("U Ant. Crowding/Spacing (L)", value=0.0, step=0.1, key="U_ant_L")
        U_cos_L = st.number_input("U Curve of Spee (L)", value=0.0, step=0.1, key="U_cos_L")
        U_mid_L = st.number_input("U Midline component (L)", value=0.0, step=0.1, key="U_mid_L")
        U_inc_L = st.number_input("U Incisor position (L)", value=0.0, step=0.1, key="U_inc_L")

    st.markdown('<div class="band-green">Space Gained (Upper)</div>', unsafe_allow_html=True)

    uC, uD = st.columns(2)
    with uC:
        st.markdown("**Upper Right**")
        U_strip_R = st.number_input("U Stripping/IPR (R)", value=0.0, step=0.1, key="U_strip_R")
        U_exp_R = st.number_input("U Expansion (treatment) (R)", value=0.0, step=0.1, key="U_exp_R")
        U_dist_R = st.number_input("U Distalizing 6–6 (R)", value=0.0, step=0.1, key="U_dist_R")
        U_ext_R = st.number_input("U Extraction space (R)", value=0.0, step=0.1, key="U_ext_R")

    with uD:
        st.markdown("**Upper Left**")
        U_strip_L = st.number_input("U Stripping/IPR (L)", value=0.0, step=0.1, key="U_strip_L")
        U_exp_L = st.number_input("U Expansion (treatment) (L)", value=0.0, step=0.1, key="U_exp_L")
        U_dist_L = st.number_input("U Distalizing 6–6 (L)", value=0.0, step=0.1, key="U_dist_L")
        U_ext_L = st.number_input("U Extraction space (L)", value=0.0, step=0.1, key="U_ext_L")

    U_initial_R = compute_initial_discrepancy(U_ant_R, U_cos_R, U_mid_R, U_inc_R)
    U_initial_L = compute_initial_discrepancy(U_ant_L, U_cos_L, U_mid_L, U_inc_L)

    U_gained_R, U_remaining_R = compute_remaining_dolphin(U_initial_R, U_strip_R, U_exp_R, U_dist_R, U_ext_R, growth_U_R)
    U_gained_L, U_remaining_L = compute_remaining_dolphin(U_initial_L, U_strip_L, U_exp_L, U_dist_L, U_ext_L, growth_U_L)

    st.session_state["remaining_U_R"] = float(U_remaining_R)
    st.session_state["remaining_U_L"] = float(U_remaining_L)

    upper_table = pd.DataFrame(
        [
            ["Ant. Crowding/Spacing", U_ant_R, U_ant_L],
            ["Curve of Spee", U_cos_R, U_cos_L],
            ["Midline component", U_mid_R, U_mid_L],
            ["Incisor position", U_inc_R, U_inc_L],
            ["Initial Discrepancy", U_initial_R, U_initial_L],
            ["Stripping/IPR", U_strip_R, U_strip_L],
            ["Expansion (treatment)", U_exp_R, U_exp_L],
            ["Distalizing 6–6", U_dist_R, U_dist_L],
            ["Extraction space", U_ext_R, U_ext_L],
            [growth_label, growth_U_R, growth_U_L],
            ["Total Gained", U_gained_R, U_gained_L],
            ["Remaining Discrepancy", U_remaining_R, U_remaining_L],
        ],
        columns=["Upper (Component)", "R (mm)", "L (mm)"],
    )
    st.dataframe(upper_table, use_container_width=True, hide_index=True)

    st.markdown(
        f"<div class='band-gray'><b>Upper status:</b> Right {U_remaining_R:+.2f} ({remaining_status(U_remaining_R)}), "
        f"Left {U_remaining_L:+.2f} ({remaining_status(U_remaining_L)})</div>",
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# STEP 3
# =========================================================
with tabs[2]:
    left, right = st.columns([1.0, 1.35], gap="large")

    # Pull stored remaining
    remU_R = float(st.session_state["remaining_U_R"])
    remU_L = float(st.session_state["remaining_U_L"])
    remL_R = float(st.session_state["remaining_L_R"])
    remL_L = float(st.session_state["remaining_L_L"])

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Step 3 — Determine Expected Movement</div>', unsafe_allow_html=True)
        st.markdown(
            "<div class='band-gray'>"
            "<b>MVP allocator:</b> This computes a plausible movement distribution across 6 / 3 / incisors from remaining discrepancy. "
            "We will replace this later with McLaughlin/Dolphin rules. "
            "<br><span class='hint'>Upper and Lower are computed separately from their own remaining discrepancies.</span>"
            "</div>",
            unsafe_allow_html=True
        )

        st.markdown('<div class="band-blue">Treat-to (Case-level)</div>', unsafe_allow_html=True)

        allow_asym = st.checkbox("Allow asymmetry (different Right vs Left)", value=False, key="allow_asym")
        
        if not allow_asym:
            treat_case = st.radio("Treat to", ["Class I", "Class II", "Class III"], index=1, horizontal=True, key="treat_case")
            treat_R = treat_case
            treat_L = treat_case
        else:
            c1, c2 = st.columns(2)
            with c1:
                treat_R = st.radio("Right", ["Class I", "Class II", "Class III"], index=1, horizontal=True, key="treat_case_R")
            with c2:
                treat_L = st.radio("Left", ["Class I", "Class II", "Class III"], index=1, horizontal=True, key="treat_case_L")

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Dolphin-style Diagram (Upper + Lower)</div>', unsafe_allow_html=True)

        # Allocate per side per arch
        planU_R = expected_movement_allocation(remU_R, treat_R)
        planU_L = expected_movement_allocation(remU_L, treat_L)
        planL_R = expected_movement_allocation(remL_R, treat_R)
        planL_L = expected_movement_allocation(remL_L, treat_L)

        # Convert to signed movements (outward when crowding remains)
        signU_R = outward_sign(remU_R, "R")
        signU_L = outward_sign(remU_L, "L")
        signL_R = outward_sign(remL_R, "R")
        signL_L = outward_sign(remL_L, "L")

        # Upper segments
        U_R6 = signU_R * planU_R["6"]
        U_R3 = signU_R * planU_R["3"]
        U_Inc = (signU_R + signU_L) / 2.0 * ((planU_R["inc"] + planU_L["inc"]) / 2.0)
        U_L3 = signU_L * planU_L["3"]
        U_L6 = signU_L * planU_L["6"]

        # Lower segments
        L_R6 = signL_R * planL_R["6"]
        L_R3 = signL_R * planL_R["3"]
        L_Inc = (signL_R + signL_L) / 2.0 * ((planL_R["inc"] + planL_L["inc"]) / 2.0)
        L_L3 = signL_L * planL_L["3"]
        L_L6 = signL_L * planL_L["6"]

        svg = proposed_movement_svg_two_arch(
            u_r6=U_R6, u_r3=U_R3, u_inc=U_Inc, u_l3=U_L3, u_l6=U_L6,
            l_r6=L_R6, l_r3=L_R3, l_inc=L_Inc, l_l3=L_L3, l_l6=L_L6,
        )
        components.html(svg, height=700, scrolling=False)

        # Tables for transparency
        dfU = pd.DataFrame(
            [["R6", U_R6], ["R3", U_R3], ["Inc", U_Inc], ["L3", U_L3], ["L6", U_L6]],
            columns=["Upper segment", "Expected movement (mm)"],
        )
        dfL = pd.DataFrame(
            [["R6", L_R6], ["R3", L_R3], ["Inc", L_Inc], ["L3", L_L3], ["L6", L_L6]],
            columns=["Lower segment", "Expected movement (mm)"],
        )

        t1, t2 = st.columns(2)
        with t1:
            st.dataframe(dfU, use_container_width=True, hide_index=True)
        with t2:
            st.dataframe(dfL, use_container_width=True, hide_index=True)

        st.markdown(
            f"<div class='band-gray'><b>Goal check</b><br>"
            f"Upper remaining: R {remU_R:+.2f} ({remaining_status(remU_R)}), L {remU_L:+.2f} ({remaining_status(remU_L)})<br>"
            f"Lower remaining: R {remL_R:+.2f} ({remaining_status(remL_R)}), L {remL_L:+.2f} ({remaining_status(remL_L)})"
            f"</div>",
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)
