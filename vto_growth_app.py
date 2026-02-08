# vto_growth_app.py
# Streamlit MVP: Growth-aware Dental VTO (McLaughlin-inspired)
# Sign convention: crowding is NEGATIVE, spacing is POSITIVE.
# Space gained rows (IPR/Expansion/Distalization/Extraction/Growth) are POSITIVE.

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Growth-aware Dental VTO", layout="wide")


# =========================================================
# 1) Growth Priors (MVP placeholders — replace with your data)
# =========================================================
# Units: (IMW mm/year, ICW mm/year)
GROWTH_PRIORS = {
    "Female": {
        "pre-peak": {"low": (0.20, 0.10), "avg": (0.50, 0.30), "high": (0.80, 0.50)},
        "peak":     {"low": (0.15, 0.08), "avg": (0.35, 0.20), "high": (0.60, 0.35)},
        "post-peak":{"low": (0.05, 0.02), "avg": (0.10, 0.05), "high": (0.20, 0.10)},
    },
    "Male": {
        "pre-peak": {"low": (0.25, 0.12), "avg": (0.60, 0.35), "high": (0.90, 0.55)},
        "peak":     {"low": (0.20, 0.10), "avg": (0.45, 0.25), "high": (0.70, 0.40)},
        "post-peak":{"low": (0.06, 0.03), "avg": (0.12, 0.06), "high": (0.25, 0.12)},
    },
}


def growth_space_equivalent_mm(
    sex: str,
    cvm_stage: str,
    profile: str,
    horizon_months: int,
    coeff_imw_to_perimeter: float = 0.75,
    coeff_icw_to_perimeter: float = 0.55,
):
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
# 2) Dolphin/McLaughlin-style accounting (sign conventions)
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
):
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
# 3) Styling (Dolphin-ish)
# =========================================================
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.0rem; padding-bottom: 2rem;}
      h1, h2, h3 {letter-spacing: -0.5px;}
      .panel {
        border: 1px solid rgba(49, 51, 63, 0.15);
        border-radius: 10px;
        padding: 14px 14px 10px 14px;
        background: white;
      }
      .panel-title{
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 10px;
      }
      .hint{
        color: rgba(49, 51, 63, 0.65);
        font-size: 0.9rem;
      }
      .band-blue   {background:#d9edf7; padding:10px; border-radius:8px; border:1px solid rgba(49,51,63,.08);}
      .band-yellow {background:#f9f2d0; padding:10px; border-radius:8px; border:1px solid rgba(49,51,63,.08);}
      .band-green  {background:#dff0d8; padding:10px; border-radius:8px; border:1px solid rgba(49,51,63,.08);}
      .band-gray   {background:#f5f6f8; padding:10px; border-radius:8px; border:1px solid rgba(49,51,63,.08);}
      div[data-baseweb="input"] > div {height: 36px;}
      button[role="tab"] {font-weight: 650;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Growth-aware Dental VTO (McLaughlin-inspired)")
st.caption("Sign convention: Crowding is negative, spacing positive. Space gained rows are positive. Goal: Remaining Discrepancy ≈ 0.")


## Graphics
def initial_position_svg(r6: float, midline: float, l6: float, d: float, s: float) -> str:
    # Simple, Dolphin-inspired “line + landmarks” SVG.
    # You can swap in more detailed tooth drawings later.
    # Coordinates in pixels
    W, H = 760, 360
    cx = W // 2
    y_line = 190

    # Map mm to pixels for arrow displacement (tweak scale)
    scale = 18  # px per mm
    r6_px = r6 * scale
    l6_px = l6 * scale
    mid_px = midline * scale

    # Positions
    x_r6 = 140 + r6_px
    x_l6 = W - 140 - l6_px
    x_mid = cx + mid_px

    # Arrows
    def arrow(x1, x2, y, color="#1f77b4"):
        # marker-end arrow
        return f"""
        <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"
              stroke="{color}" stroke-width="4" marker-end="url(#arrow)"/>
        """

    # Boxed number input look
    def box(x, y, text):
        return f"""
        <rect x="{x-28}" y="{y-18}" width="56" height="36" rx="4"
              fill="white" stroke="#999" stroke-width="2"/>
        <text x="{x}" y="{y+6}" text-anchor="middle"
              font-family="Arial" font-size="18" fill="#111">{text}</text>
        """

    # Tooth-ish placeholders (replace with real tooth outlines later)
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

    svg = f"""
    <div style="border:1px solid rgba(49,51,63,.15); border-radius:10px; padding:10px; background:white;">
    <svg width="100%" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
          <path d="M0,0 L0,6 L9,3 z" fill="#1f77b4"/>
        </marker>
      </defs>

      <text x="{cx}" y="30" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">Initial Position</text>

      <!-- Axis line -->
      <line x1="80" y1="{y_line}" x2="{W-80}" y2="{y_line}" stroke="#333" stroke-width="4"/>
      <line x1="{cx-160}" y1="{y_line-10}" x2="{cx-160}" y2="{y_line+10}" stroke="#333" stroke-width="3"/>
      <line x1="{cx+160}" y1="{y_line-10}" x2="{cx+160}" y2="{y_line+10}" stroke="#333" stroke-width="3"/>

      <!-- Teeth placeholders -->
      {tooth(x_r6, y_line+35, "6")}
      {tooth(x_mid, y_line+35, "1")}
      {tooth(x_mid+35, y_line+35, "1")}
      {tooth(x_l6, y_line+35, "6")}

      <!-- Value boxes -->
      <text x="140" y="70" font-family="Arial" font-size="16" font-weight="700">R6</text>
      {box(150, 95, f"{r6:.1f}")}

      <text x="{cx}" y="70" font-family="Arial" font-size="16" font-weight="700" text-anchor="middle">Midline</text>
      {box(cx, 95, f"{midline:.1f}")}

      <text x="{W-140}" y="70" font-family="Arial" font-size="16" font-weight="700" text-anchor="end">L6</text>
      {box(W-150, 95, f"{l6:.1f}")}

      <!-- Arrows (illustrative) -->
      {arrow(120, x_r6-30, 125)}
      {arrow(W-120, x_l6+30, 125)}
      {arrow(cx, x_mid, y_line+95)}

      <!-- D and S boxes -->
      <text x="{cx-20}" y="{y_line+150}" font-family="Arial" font-size="16" font-weight="700">D=</text>
      {box(cx+30, y_line+145, f"{d:.1f}")}

      <text x="{cx-20}" y="{y_line+210}" font-family="Arial" font-size="16" font-weight="700">S=</text>
      {box(cx+30, y_line+205, f"{s:.1f}")}

    </svg>
    </div>
    """
    return svg

# =========================================================
# 4) Session state defaults
# =========================================================
def ss_init(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

st.sidebar.markdown("## Global")
st.sidebar.checkbox("Move both sides (R+L)", key="move_both")
st.sidebar.checkbox("Override calculated values", key="override")
st.sidebar.checkbox("Include growth contribution", key="include_growth", value=True)

move_both = st.session_state["move_both"]
override = st.session_state["override"]
include_growth = st.session_state["include_growth"]

ss_init("move_both", True)
ss_init("override", False)
ss_init("treat_R", "Class II")
ss_init("treat_L", "Class II")


# =========================================================
# 5) 3-step workflow (tabs)
# =========================================================
step1, step2, step3 = st.tabs(
    ["Step 1: Initial Tooth Positions", "Step 2: Lower Arch", "Step 3: Determining Movement"]
)

# Shared growth state (computed in Step 1, used in Step 2/3)
if "growth_space_total" not in st.session_state:
    st.session_state["growth_space_total"] = 0.0


# ---------------------------------------------------------
# STEP 1: Initial Tooth Positions
# ---------------------------------------------------------
with step1:
    left, right = st.columns([1.05, 1.15], gap="large")

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Initial Position</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            r6 = st.number_input("R6 (mm)", value=2.0, step=0.1, key="r6")
        with c2:
            midline_init = st.number_input("Midline (mm)", value=0.0, step=0.1, key="midline_init")
        with c3:
            l6 = st.number_input("L6 (mm)", value=0.5, step=0.1, key="l6")

        d = st.number_input("D (mm)", value=1.5, step=0.1, key="d")
        s = st.number_input("S (mm)", value=0.0, step=0.1, key="s")

        st.divider()

        st.markdown('<div class="panel-title">Growth Module (MVP)</div>', unsafe_allow_html=True)
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
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

        with right:
            svg = initial_position_svg(r6=r6, midline=midline_init, l6=l6, d=d, s=s)
            components.html(svg, height=420, scrolling=False)  
            
            st.markdown(
                initial_position_svg(
                    r6=r6,
                    midline=midline_init,
                    l6=l6,
                    d=d,
                    s=s
                ),
                unsafe_allow_html=True
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
            unsafe_allow_html=True
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

            growth_total_raw = float(st.session_state.get("growth_space_total", 0.0))
            growth_total = growth_total_raw if include_growth else 0.0
            
            growth_R = growth_total / 2.0
            growth_L = growth_total / 2.0

        initial_R = compute_initial_discrepancy(ant_R, cos_R, mid_R, inc_R)
        initial_L = compute_initial_discrepancy(ant_L, cos_L, mid_L, inc_L)

        gained_R, remaining_R = compute_remaining_dolphin(initial_R, strip_R, exp_R, dist_R, ext_R, growth_R)
        gained_L, remaining_L = compute_remaining_dolphin(initial_L, strip_L, exp_L, dist_L, ext_L, growth_L)

        st.markdown('<div class="band-yellow"><b>Totals</b></div>', unsafe_allow_html=True)

        growth_label = "Growth (space equiv) [ON]" if include_growth else "Growth (space equiv) [OFF]"

        totals = pd.DataFrame(
            [
                ["Initial Discrepancy", initial_R, initial_L],
                ["Treatment Gained", strip_R + exp_R + dist_R + ext_R,
                                     strip_L + exp_L + dist_L + ext_L],
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
        st.caption("Next iteration: render an SVG diagram with arrows like Dolphin.")
        st.markdown(
            f"""
            <div class="band-gray">
              <b>Remaining Discrepancy</b><br>
              Right: <b>{remaining_R:.2f} mm</b> &nbsp; <span class="hint">({remaining_status(remaining_R)})</span><br>
              Left: <b>{remaining_L:.2f} mm</b> &nbsp; <span class="hint">({remaining_status(remaining_L)})</span><br><br>
              <span class="hint">Growth included: +{growth_total:.2f} mm total perimeter-equivalent</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# STEP 3: Determining Movement
# ---------------------------------------------------------
with step3:
    left, right = st.columns([1.0, 1.2], gap="large")

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Treat to</div>', unsafe_allow_html=True)

        st.markdown("**Right**")
        treat_right = st.radio("Right side", ["Class I", "Class II", "Class III"], index=1, horizontal=True, key="treat_R")

        st.markdown("**Left**")
        treat_left = st.radio("Left side", ["Class I", "Class II", "Class III"], index=1, horizontal=True, key="treat_L")

        st.divider()
        st.markdown(
            '<div class="band-gray"><b>Next build step</b><br>'
            "We’ll implement McLaughlin movement allocation rules (molars/cuspids/incisors + midline), "
            "and add anchorage risk with growth considered.</div>",
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Dental VTO (Proposed Dental Movement)</div>', unsafe_allow_html=True)
        st.caption("MVP: numeric allocation placeholder. Next: SVG arrows like Dolphin.")

        # Pull remaining from session (computed in Step 2). If user visits Step 3 first, compute lightweight fallback.
        try:
            remaining_R  # noqa: F821
            remaining_L  # noqa: F821
        except NameError:
            remaining_R, remaining_L = 0.0, 0.0

        def simple_allocation(rem: float, treat: str):
            # Placeholder: replace with real McLaughlin logic later
            if treat == "Class II":
                return {"Anterior": 0.7 * rem, "Posterior": 0.3 * rem}
            if treat == "Class III":
                return {"Anterior": 0.4 * rem, "Posterior": 0.6 * rem}
            return {"Anterior": 0.55 * rem, "Posterior": 0.45 * rem}

        alloc_R = simple_allocation(remaining_R, treat_right)
        alloc_L = simple_allocation(remaining_L, treat_left)

        df_alloc = pd.DataFrame(
            [
                ["Right", treat_right, alloc_R["Anterior"], alloc_R["Posterior"]],
                ["Left", treat_left, alloc_L["Anterior"], alloc_L["Posterior"]],
            ],
            columns=["Side", "Treat to", "Anterior (mm)", "Posterior (mm)"],
        )

        st.dataframe(df_alloc, use_container_width=True, hide_index=True)

        st.markdown(
            f"""
            <div class="band-gray">
              <b>Goal check</b><br>
              Right remaining: <b>{remaining_R:.2f}</b> ({remaining_status(remaining_R)})<br>
              Left remaining: <b>{remaining_L:.2f}</b> ({remaining_status(remaining_L)})<br>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)
