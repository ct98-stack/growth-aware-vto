# vto_growth_app.py
# Streamlit MVP: Growth-aware Dental VTO (McLaughlin/Dolphin-inspired UI)
# Dolphin sign convention:
#   - crowding is NEGATIVE
#   - spacing is POSITIVE
#   - space gained (IPR/Expansion/Distalization/Extraction/Growth) is POSITIVE
# Goal: Remaining Discrepancy ≈ 0

from __future__ import annotations

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Growth-aware Dental VTO", layout="wide")


# =========================================================
# Growth Priors (MVP placeholders — replace with your data)
# =========================================================
# Units: (IMW mm/year, ICW mm/year)
GROWTH_PRIORS = {
    "Female": {
        "pre-peak": {"low": (0.20, 0.10), "avg": (0.50, 0.30), "high": (0.80, 0.50)},
        "peak": {"low": (0.15, 0.08), "avg": (0.35, 0.20), "high": (0.60, 0.35)},
        "post-peak": {"low": (0.05, 0.02), "avg": (0.10, 0.05), "high": (0.20, 0.10)},
    },
    "Male": {
        "pre-peak": {"low": (0.25, 0.12), "avg": (0.60, 0.35), "high": (0.90, 0.55)},
        "peak": {"low": (0.20, 0.10), "avg": (0.45, 0.25), "high": (0.70, 0.40)},
        "post-peak": {"low": (0.06, 0.03), "avg": (0.12, 0.06), "high": (0.25, 0.12)},
    },
}


def growth_space_equivalent_mm(
    sex: str,
    cvm_stage: str,
    profile: str,
    horizon_months: int,
    coeff_imw_to_perimeter: float = 0.75,
    coeff_icw_to_perimeter: float = 0.55,
) -> tuple[float, float, float]:
    """
    Returns: (ΔIMW, ΔICW, ΔArchPerimeterSpaceEquiv) over horizon.
    Space equiv is used as a "space gained" term in Dolphin accounting.
    """
    years = horizon_months / 12.0
    imw_per_year, icw_per_year = GROWTH_PRIORS[sex][cvm_stage][profile]
    delta_imw = imw_per_year * years
    delta_icw = icw_per_year * years
    delta_perimeter = coeff_imw_to_perimeter * delta_imw + coeff_icw_to_perimeter * delta_icw
    return float(delta_imw), float(delta_icw), float(delta_perimeter)


# =========================================================
# Dolphin/McLaughlin-style accounting (sign conventions)
# =========================================================
def compute_initial_discrepancy(*components: float) -> float:
    """
    Dolphin convention:
    - Crowding is negative, spacing is positive
    - COS often entered negative (as in Dolphin UI)
    Initial Discrepancy = sum of component inputs.
    """
    return float(sum(components))


def compute_remaining_dolphin(
    initial_discrepancy: float,
    stripping: float,
    expansion: float,
    distalization: float,
    extraction: float,
    growth_space: float,
) -> tuple[float, float]:
    """
    Dolphin convention:
    - Space-gaining mechanics are positive.
    Remaining Discrepancy = Initial Discrepancy + Total Gained
    Target is near 0.
    """
    total_gained = float(stripping + expansion + distalization + extraction + growth_space)
    remaining = float(initial_discrepancy + total_gained)
    return total_gained, remaining


def remaining_status(rem: float) -> str:
    if abs(rem) < 0.25:
        return "On target (≈ 0)"
    if rem < 0:
        return "Still short on space (crowding remains)"
    return "Excess space (over-corrected / spacing remaining)"


# =========================================================
# Dolphin-ish SVG for Step 1 (Initial Position)
# =========================================================

def proposed_movement_svg(
    r6: float,
    r3: float,
    inc: float,
    l3: float,
    l6: float,
    highlight: dict[str, bool] | None = None,
) -> str:
    """
    Dolphin-ish Step 3 diagram (lower arch simplified):
    Teeth order: R6, R3, Incisor, L3, L6
    Values are shown above (numbers) and arrows below.
    Positive = move to patient's LEFT (screen right if you keep that convention consistent).
    For now we just show direction by sign: >0 arrow right, <0 arrow left.
    """
    highlight = highlight or {}

    W, H = 860, 420
    cx = W // 2
    y_line = 210

    # positions
    x_r6 = 120
    x_r3 = 280
    x_inc = cx
    x_l3 = 580
    x_l6 = 740

    # helpers
    def tooth(x, y, label, hl=False):
        stroke = "#2aa6a6" if hl else "#333"
        stroke_w = "3" if hl else "2"
        return f"""
        <path d="M {x-20} {y-70}
                 C {x-40} {y-50}, {x-40} {y-10}, {x-20} {y+10}
                 C {x-10} {y+35}, {x+10} {y+35}, {x+20} {y+10}
                 C {x+40} {y-10}, {x+40} {y-50}, {x+20} {y-70}
                 Z"
              fill="white" stroke="{stroke}" stroke-width="{stroke_w}"/>
        <circle cx="{x}" cy="{y-25}" r="16" fill="white" stroke="{stroke}" stroke-width="{stroke_w}"/>
        <text x="{x}" y="{y-20}" text-anchor="middle" font-family="Arial" font-size="14">{label}</text>
        """

    def value_box(x, y, val):
        return f"""
        <rect x="{x-34}" y="{y-20}" width="68" height="40" rx="5"
              fill="white" stroke="#999" stroke-width="2"/>
        <text x="{x}" y="{y+6}" text-anchor="middle"
              font-family="Arial" font-size="18" fill="#111">{val:.1f}</text>
        """

    def arrow_under(x, y, val):
        # draw a simple arrow under the tooth indicating direction/magnitude
        # length scaled but capped for display
        L = max(18, min(90, abs(val) * 20))
        if val > 0:
            x1, x2 = x - 10, x - 10 + L
        elif val < 0:
            x1, x2 = x + 10, x + 10 - L
        else:
            x1, x2 = x - 25, x + 25
        return f"""
        <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"
              stroke="#1f77b4" stroke-width="5" marker-end="url(#arrow)"/>
        """

    html = f"""
    <div style="border:1px solid rgba(49,51,63,.15); border-radius:14px; padding:10px; background:white;">
      <svg width="100%" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="#1f77b4"/>
          </marker>
        </defs>

        <text x="{cx}" y="34" text-anchor="middle" font-family="Arial" font-size="22" font-weight="800">
          Dental VTO (Proposed Dental Movement)
        </text>

        <!-- baseline -->
        <line x1="80" y1="{y_line}" x2="{W-80}" y2="{y_line}" stroke="#333" stroke-width="4"/>

        <!-- value boxes (top) -->
        {value_box(x_r6, 90, r6)}
        {value_box(x_r3, 90, r3)}
        {value_box(x_inc, 90, inc)}
        {value_box(x_l3, 90, l3)}
        {value_box(x_l6, 90, l6)}

        <!-- labels above boxes -->
        <text x="{x_r6}" y="62" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">R6</text>
        <text x="{x_r3}" y="62" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">R3</text>
        <text x="{x_inc}" y="62" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">Inc</text>
        <text x="{x_l3}" y="62" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">L3</text>
        <text x="{x_l6}" y="62" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">L6</text>

        <!-- teeth -->
        {tooth(x_r6, y_line+60, "6", hl=highlight.get("R6", False))}
        {tooth(x_r3, y_line+60, "3", hl=highlight.get("R3", False))}
        {tooth(x_inc, y_line+60, "1", hl=highlight.get("Inc", False))}
        {tooth(x_l3, y_line+60, "3", hl=highlight.get("L3", False))}
        {tooth(x_l6, y_line+60, "6", hl=highlight.get("L6", False))}

        <!-- arrows under -->
        {arrow_under(x_r6, y_line+150, r6)}
        {arrow_under(x_r3, y_line+150, r3)}
        {arrow_under(x_inc, y_line+150, inc)}
        {arrow_under(x_l3, y_line+150, l3)}
        {arrow_under(x_l6, y_line+150, l6)}

        <!-- numeric under arrows -->
        <text x="{x_r6}" y="{y_line+190}" text-anchor="middle" font-family="Arial" font-size="14">{r6:.1f}</text>
        <text x="{x_r3}" y="{y_line+190}" text-anchor="middle" font-family="Arial" font-size="14">{r3:.1f}</text>
        <text x="{x_inc}" y="{y_line+190}" text-anchor="middle" font-family="Arial" font-size="14">{inc:.1f}</text>
        <text x="{x_l3}" y="{y_line+190}" text-anchor="middle" font-family="Arial" font-size="14">{l3:.1f}</text>
        <text x="{x_l6}" y="{y_line+190}" text-anchor="middle" font-family="Arial" font-size="14">{l6:.1f}</text>

      </svg>
    </div>
    """
    return html
    
def initial_position_svg(r6: float, l6: float, d: float, s: float) -> str:
    """
    A simple, Dolphin-inspired SVG that updates with R6/L6/D/S.
    We removed Midline from Step 1 per your request.
    """
    W, H = 760, 360
    cx = W // 2
    y_line = 190

    scale = 18  # px per mm
    r6_px = r6 * scale
    l6_px = l6 * scale

    x_r6 = 140 + r6_px
    x_l6 = W - 140 - l6_px
    x_mid = cx

    def arrow(x1, x2, y, color="#1f77b4"):
        return f"""
        <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"
              stroke="{color}" stroke-width="4" marker-end="url(#arrow)"/>
        """

    def box(x, y, text):
        return f"""
        <rect x="{x-28}" y="{y-18}" width="56" height="36" rx="4"
              fill="white" stroke="#999" stroke-width="2"/>
        <text x="{x}" y="{y+6}" text-anchor="middle"
              font-family="Arial" font-size="18" fill="#111">{text}</text>
        """

    def tooth(x, y, label):
        return f"""
        <path d="M {x-18} {y-50}
                 C {x-35} {y-35}, {x-35} {y-5}, {x-18} {y+10}
                 C {x-10} {y+25}, {x+10} {y+25}, {x+18} {y+10}
                 C {x+35} {y-5}, {x+35} {y-35}, {x+18} {y-50}
                 Z"
              fill="white" stroke="#333" stroke-width="2"/>
        <circle cx="{x}" cy="{y-12}" r="14" fill="white" stroke="#333" stroke-width="2"/>
        <text x="{x}" y="{y-7}" text-anchor="middle" font-family="Arial" font-size="14">{label}</text>
        """

    html = f"""
    <div style="border:1px solid rgba(49,51,63,.15); border-radius:10px; padding:10px; background:white;">
      <svg width="100%" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="#1f77b4"/>
          </marker>
        </defs>

        <text x="{cx}" y="30" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">
          Initial Position
        </text>

        <!-- Axis -->
        <line x1="80" y1="{y_line}" x2="{W-80}" y2="{y_line}" stroke="#333" stroke-width="4"/>
        <line x1="{cx-160}" y1="{y_line-10}" x2="{cx-160}" y2="{y_line+10}" stroke="#333" stroke-width="3"/>
        <line x1="{cx+160}" y1="{y_line-10}" x2="{cx+160}" y2="{y_line+10}" stroke="#333" stroke-width="3"/>

        <!-- Teeth placeholders -->
        # Teeth placeholders
        {tooth(x_r6, y_line+35, "6")}
        {tooth(x_mid, y_line+35, "1")}
        {tooth(x_l6, y_line+35, "6")}

        <!-- Input boxes (visual only) -->
        <text x="150" y="70" font-family="Arial" font-size="16" font-weight="700">R6</text>
        {box(150, 95, f"{r6:.1f}")}

        <text x="{W-150}" y="70" font-family="Arial" font-size="16" font-weight="700" text-anchor="end">L6</text>
        {box(W-150, 95, f"{l6:.1f}")}

        <!-- Arrows -->
        {arrow(120, x_r6-30, 125)}
        {arrow(W-120, x_l6+30, 125)}

        <!-- D and S boxes -->
        <text x="{cx-20}" y="{y_line+150}" font-family="Arial" font-size="16" font-weight="700">D=</text>
        {box(cx+30, y_line+145, f"{d:.1f}")}

        <text x="{cx-20}" y="{y_line+210}" font-family="Arial" font-size="16" font-weight="700">S=</text>
        {box(cx+30, y_line+205, f"{s:.1f}")}

      </svg>
    </div>
    """
    return html


# =========================================================
# Styling
# =========================================================
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.0rem; padding-bottom: 2rem;}
      h1, h2, h3 {letter-spacing: -0.5px;}
      .panel {
        border: 1px solid rgba(49, 51, 63, 0.15);
        border-radius: 14px;
        padding: 16px 16px 12px 16px;
        background: white;
      }
      .panel-title{
        font-weight: 800;
        font-size: 1.15rem;
        margin-bottom: 10px;
      }
      .hint{
        color: rgba(49, 51, 63, 0.65);
        font-size: 0.9rem;
      }
      .band-blue   {background:#d9edf7; padding:10px; border-radius:10px; border:1px solid rgba(49,51,63,.08);}
      .band-yellow {background:#f9f2d0; padding:10px; border-radius:10px; border:1px solid rgba(49,51,63,.08);}
      .band-green  {background:#dff0d8; padding:10px; border-radius:10px; border:1px solid rgba(49,51,63,.08);}
      .band-gray   {background:#f5f6f8; padding:10px; border-radius:10px; border:1px solid rgba(49,51,63,.08);}
      div[data-baseweb="input"] > div {height: 42px;}
      button[role="tab"] {font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Growth-aware Dental VTO (McLaughlin-inspired)")
st.caption(
    "Sign convention: Crowding is negative, spacing positive. Space gained rows are positive. Goal: Remaining Discrepancy ≈ 0."
)


# =========================================================
# Session state defaults
# =========================================================
def ss_init(key: str, default):
    if key not in st.session_state:
        st.session_state[key] = default


ss_init("move_both", True)
ss_init("override", False)
ss_init("include_growth", True)
ss_init("growth_space_total", 0.0)

# Step 3 defaults
ss_init("treat_R", "Class II")
ss_init("treat_L", "Class II")


# =========================================================
# Sidebar (GLOBAL controls)
# =========================================================
st.sidebar.markdown("## Global")
st.sidebar.checkbox("Move both sides (R+L)", key="move_both")
st.sidebar.checkbox("Override calculated values", key="override")
st.sidebar.checkbox("Include growth contribution", key="include_growth", value=True)

move_both = st.session_state["move_both"]
override = st.session_state["override"]
include_growth = st.session_state["include_growth"]


# =========================================================
# 3-step workflow (tabs)
# =========================================================
step1, step2, step3 = st.tabs(
    ["Step 1: Initial Tooth Positions", "Step 2: Lower Arch", "Step 3: Determining Movement"]
)


# ---------------------------------------------------------
# STEP 1: Initial Tooth Positions
# ---------------------------------------------------------
with step1:
    left, right = st.columns([1.05, 1.15], gap="large")

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Initial Position</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            r6 = st.number_input("R6 (mm)", value=0.0, step=0.1, key="r6")
        with c2:
            l6 = st.number_input("L6 (mm)", value=0.5, step=0.1, key="l6")

        d = st.number_input("D (mm)", value=1.5, step=0.1, key="d")
        s = st.number_input("S (mm)", value=0.0, step=0.1, key="s")

        st.divider()

        st.markdown('<div class="panel-title">Growth Module (MVP)</div>', unsafe_allow_html=True)

        if include_growth:
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                sex = st.selectbox("Sex", ["Female", "Male"], key="sex")
            with g2:
                cvm_stage = st.selectbox("CVM bucket", ["pre-peak", "peak", "post-peak"], key="cvm_stage")
            with g3:
                profile = st.selectbox("Growth profile", ["low", "avg", "high"], index=1, key="growth_profile")
            with g4:
                horizon = st.selectbox("Horizon (months)", [12, 18, 24], index=1, key="horizon")

            coeff_imw = st.slider("IMW → perimeter coeff", 0.0, 1.5, 0.75, 0.05, key="coeff_imw")
            coeff_icw = st.slider("ICW → perimeter coeff", 0.0, 1.5, 0.55, 0.05, key="coeff_icw")

            delta_imw, delta_icw, growth_space_total = growth_space_equivalent_mm(
                sex=sex,
                cvm_stage=cvm_stage,
                profile=profile,
                horizon_months=horizon,
                coeff_imw_to_perimeter=coeff_imw,
                coeff_icw_to_perimeter=coeff_icw,
            )
            st.session_state["growth_space_total"] = growth_space_total

            st.markdown(
                f'<div class="band-gray"><b>Predicted growth over {horizon} months</b><br>'
                f'ΔIMW = {delta_imw:.2f} mm<br>'
                f'ΔICW = {delta_icw:.2f} mm<br>'
                f'ΔArch perimeter (space equiv) = <b>+{growth_space_total:.2f} mm</b></div>',
                unsafe_allow_html=True,
            )
        else:
            st.session_state["growth_space_total"] = 0.0
            st.markdown(
                "<div class='band-gray'><b>Growth is OFF</b><br>"
                "Enable <i>Include growth contribution</i> in the left sidebar to configure growth.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Initial Position</div>', unsafe_allow_html=True)

        svg_html = initial_position_svg(r6=r6, l6=l6, d=d, s=s)
        components.html(svg_html, height=420, scrolling=False)

        st.markdown(
            f"<div class='band-gray'><span class='hint'>Growth space equiv stored for Step 2/3: "
            f"+{st.session_state['growth_space_total']:.2f} mm</span></div>",
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# STEP 2: Lower Arch
# ---------------------------------------------------------
with step2:
    left, right = st.columns([1.15, 1.05], gap="large")

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Lower Arch Discrepancy</div>', unsafe_allow_html=True)

        st.markdown(
            "<div class='band-gray'><b>Sign convention (Dolphin):</b> Crowding = negative, Spacing = positive. "
            "Space gained rows (IPR/Expansion/Distalization/Extraction/Growth) = positive. Target Remaining ≈ 0.</div>",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="band-blue"><b>Initial Discrepancy Inputs (3 to 3)</b></div>', unsafe_allow_html=True)
        cA, cB = st.columns(2)

        with cA:
            st.markdown("**Right (3–3)**")
            ant_R = st.number_input("Ant. Crowding/Spacing (R)", value=0.0, step=0.1, key="ant_R")
            cos_R = st.number_input("Curve of Spee (R)", value=-1.5, step=0.1, key="cos_R")
            mid_R = st.number_input("Midline component (R)", value=0.0, step=0.1, key="mid_R")
            inc_R = st.number_input("Incisor position (R)", value=0.0, step=0.1, key="inc_R")

        with cB:
            st.markdown("**Left (3–3)**")
            ant_L = st.number_input("Ant. Crowding/Spacing (L)", value=0.0, step=0.1, key="ant_L")
            cos_L = st.number_input("Curve of Spee (L)", value=-1.5, step=0.1, key="cos_L")
            mid_L = st.number_input("Midline component (L)", value=0.0, step=0.1, key="mid_L")
            inc_L = st.number_input("Incisor position (L)", value=0.0, step=0.1, key="inc_L")

        st.markdown('<div class="band-green"><b>Space Gained</b> (treatment + growth)</div>', unsafe_allow_html=True)
        cC, cD = st.columns(2)

        with cC:
            st.markdown("**Right**")
            strip_R = st.number_input("Stripping/IPR (R)", value=0.0, step=0.1, key="strip_R")
            exp_R = st.number_input("Expansion (treatment) (R)", value=0.0, step=0.1, key="exp_R")
            dist_R = st.number_input("Distalizing 6–6 (R)", value=0.0, step=0.1, key="dist_R")
            ext_R = st.number_input("Extraction space (R)", value=0.0, step=0.1, key="ext_R")

        with cD:
            st.markdown("**Left**")
            strip_L = st.number_input("Stripping/IPR (L)", value=0.0, step=0.1, key="strip_L")
            exp_L = st.number_input("Expansion (treatment) (L)", value=0.0, step=0.1, key="exp_L")
            dist_L = st.number_input("Distalizing 6–6 (L)", value=0.0, step=0.1, key="dist_L")
            ext_L = st.number_input("Extraction space (L)", value=0.0, step=0.1, key="ext_L")

        # Growth is applied only if the global toggle is ON
        growth_total_raw = float(st.session_state.get("growth_space_total", 0.0))
        growth_total = growth_total_raw if include_growth else 0.0

        growth_R = growth_total / 2.0
        growth_L = growth_total / 2.0

        initial_R = compute_initial_discrepancy(ant_R, cos_R, mid_R, inc_R)
        initial_L = compute_initial_discrepancy(ant_L, cos_L, mid_L, inc_L)

        gained_R, remaining_R = compute_remaining_dolphin(initial_R, strip_R, exp_R, dist_R, ext_R, growth_R)
        gained_L, remaining_L = compute_remaining_dolphin(initial_L, strip_L, exp_L, dist_L, ext_L, growth_L)

        growth_label = "Growth (space equiv) [ON]" if include_growth else "Growth (space equiv) [OFF]"

        st.markdown('<div class="band-yellow"><b>Totals</b></div>', unsafe_allow_html=True)
        totals = pd.DataFrame(
            [
                ["Initial Discrepancy", initial_R, initial_L],
                ["Treatment Gained", strip_R + exp_R + dist_R + ext_R, strip_L + exp_L + dist_L + ext_L],
                [growth_label, growth_R, growth_L],
                ["Total Gained", gained_R, gained_L],
                ["Remaining Discrepancy", remaining_R, remaining_L],
            ],
            columns=["Component", "R (mm)", "L (mm)"],
        )
        st.dataframe(totals, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Dental VTO (Preview)</div>', unsafe_allow_html=True)
        st.caption("Next iteration: render Step 2 preview diagram (tooth line + arrows).")
        st.markdown(
            f"""
            <div class="band-gray">
              <b>Remaining Discrepancy</b><br>
              Right: <b>{remaining_R:.2f} mm</b> &nbsp; <span class="hint">({remaining_status(remaining_R)})</span><br>
              Left: <b>{remaining_L:.2f} mm</b> &nbsp; <span class="hint">({remaining_status(remaining_L)})</span><br><br>
              <span class="hint">{growth_label}: +{growth_total:.2f} mm total perimeter-equivalent</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

st.session_state["remaining_R"] = remaining_R
st.session_state["remaining_L"] = remaining_L

# ---------------------------------------------------------
# STEP 3: Determining Movement
# ---------------------------------------------------------
with step3:
    left, right = st.columns([1.0, 1.35], gap="large")

    # --- A simple, explicit allocator (MVP) ---
    # We take remaining discrepancy (mm) and allocate across:
    #  - molars (6), canines (3), incisors (1 segment)
    # Treat-to influences the ratio anterior/posterior.
    def expected_movement_allocation(remaining: float, treat_to: str) -> dict[str, float]:
        """
        remaining < 0 means still crowded (need space) in Dolphin convention.
        For the *movement diagram*, we express a "plan" as numbers per segment.
        This is MVP math — you’ll replace with McLaughlin rules later.

        Convention here:
          - Positive value = movement to patient's LEFT
          - Negative value = movement to patient's RIGHT
        (You can flip if you want — just be consistent.)
        """
        # How much of the "plan" is anterior vs posterior
        if treat_to == "Class II":
            # more posterior correction (distalize post / anchor anterior)
            ant_w, post_w = 0.65, 0.35
        elif treat_to == "Class III":
            ant_w, post_w = 0.45, 0.55
        else:  # Class I
            ant_w, post_w = 0.55, 0.45

        # Use magnitude; sign will be handled as directional plan per side later
        mag = abs(remaining)

        anterior = mag * ant_w
        posterior = mag * post_w

        # Split anterior into canine/incisor
        inc = anterior * 0.55
        canine = anterior * 0.45

        # Posterior all to molar for MVP
        molar = posterior

        return {"6": molar, "3": canine, "inc": inc}

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Treat to</div>', unsafe_allow_html=True)

        treat_right = st.radio("Right side", ["Class I", "Class II", "Class III"], index=1, horizontal=True, key="treat_R")
        treat_left = st.radio("Left side", ["Class I", "Class II", "Class III"], index=1, horizontal=True, key="treat_L")

        st.markdown(
            "<div class='band-gray'><b>About this step</b><br>"
            "This panel computes an <i>expected movement</i> plan from Step 2 remaining discrepancy, "
            "then renders a Dolphin-style diagram. Turn on <b>Override calculated values</b> (sidebar) "
            "to manually edit segment movements.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Dental VTO (Proposed Dental Movement)</div>', unsafe_allow_html=True)

        # Pull latest remaining discrepancies computed in Step 2
        # (These names exist in the full file I gave you; if not, compute again or store in session_state.)
        remR = float(st.session_state.get("remaining_R", remaining_R if "remaining_R" in globals() else 0.0))
        remL = float(st.session_state.get("remaining_L", remaining_L if "remaining_L" in globals() else 0.0))

        # Compute expected movement magnitudes per side
        planR = expected_movement_allocation(remR, treat_right)
        planL = expected_movement_allocation(remL, treat_left)

        # Convert to signed movements for the diagram:
        # Here’s a simple interpretation:
        # - Right side movements shown as "to the RIGHT" (negative) if we need space (rem<0),
        # - Left side movements shown as "to the LEFT" (positive) if we need space (rem<0).
        # That mirrors “expand outward” visually.
        # If rem > 0 (excess space), reverse the direction.
        def dir_sign(rem: float, outward_positive: bool) -> float:
            # If still crowded (rem < 0), go outward; if excess (rem > 0), go inward.
            if rem < 0:
                return 1.0 if outward_positive else -1.0
            if rem > 0:
                return -1.0 if outward_positive else 1.0
            return 0.0

        # Right outward is to patient's RIGHT => negative in our screen convention
        sign_R = dir_sign(remR, outward_positive=False)
        # Left outward is to patient's LEFT => positive
        sign_L = dir_sign(remL, outward_positive=True)

        # Expected values for each segment
        exp_R6 = sign_R * planR["6"]
        exp_R3 = sign_R * planR["3"]
        exp_Inc = (sign_R + sign_L) / 2.0 * ((planR["inc"] + planL["inc"]) / 2.0)  # center segment
        exp_L3 = sign_L * planL["3"]
        exp_L6 = sign_L * planL["6"]

        # Allow override (global sidebar toggle)
        if override:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                exp_R6 = st.number_input("R6", value=float(exp_R6), step=0.1, key="mv_R6")
            with c2:
                exp_R3 = st.number_input("R3", value=float(exp_R3), step=0.1, key="mv_R3")
            with c3:
                exp_Inc = st.number_input("Inc", value=float(exp_Inc), step=0.1, key="mv_Inc")
            with c4:
                exp_L3 = st.number_input("L3", value=float(exp_L3), step=0.1, key="mv_L3")
            with c5:
                exp_L6 = st.number_input("L6", value=float(exp_L6), step=0.1, key="mv_L6")
        else:
            # show computed values in a small table (like Dolphin “calculated values”)
            df = pd.DataFrame(
                [["R6", exp_R6], ["R3", exp_R3], ["Inc", exp_Inc], ["L3", exp_L3], ["L6", exp_L6]],
                columns=["Segment", "Expected movement (mm)"],
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

        # Highlight teeth that move more than a threshold
        hl = {
            "R6": abs(exp_R6) >= 0.5,
            "R3": abs(exp_R3) >= 0.5,
            "Inc": abs(exp_Inc) >= 0.5,
            "L3": abs(exp_L3) >= 0.5,
            "L6": abs(exp_L6) >= 0.5,
        }

        # Render Dolphin-like diagram
        svg = proposed_movement_svg(
            r6=exp_R6,
            r3=exp_R3,
            inc=exp_Inc,
            l3=exp_L3,
            l6=exp_L6,
            highlight=hl,
        )
        components.html(svg, height=520, scrolling=False)

        # Goal check (keep your existing)
        st.markdown(
            f"""
            <div class="band-gray">
              <b>Goal check</b><br>
              Right remaining: <b>{remR:.2f}</b> ({remaining_status(remR)})<br>
              Left remaining: <b>{remL:.2f}</b> ({remaining_status(remL)})<br>
              <span class="hint">Tip: Turn on Override calculated values to edit the movement plan.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)
