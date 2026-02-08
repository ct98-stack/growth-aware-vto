import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Growth-aware Dental VTO (MVP)", layout="wide")

# -----------------------------
# Core model: growth priors (MVP)
# -----------------------------
# These are placeholder priors you will replace with your dataset.
# Units: mm/year for dental arch width changes.
GROWTH_PRIORS = {
    # CVM: pre-peak, peak, post-peak
    "Female": {
        "pre-peak": {"low": (0.2, 0.1), "avg": (0.5, 0.3), "high": (0.8, 0.5)},  # (IMW, ICW)
        "peak":     {"low": (0.15,0.08), "avg": (0.35,0.2), "high": (0.6, 0.35)},
        "post-peak":{"low": (0.05,0.02), "avg": (0.1, 0.05), "high": (0.2, 0.1)},
    },
    "Male": {
        "pre-peak": {"low": (0.25,0.12), "avg": (0.6, 0.35), "high": (0.9, 0.55)},
        "peak":     {"low": (0.2, 0.1),  "avg": (0.45,0.25), "high": (0.7, 0.4)},
        "post-peak":{"low": (0.06,0.03), "avg": (0.12,0.06), "high": (0.25,0.12)},
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
    Returns (delta_imw, delta_icw, delta_perimeter_space_equiv) over the horizon.
    """
    years = horizon_months / 12.0
    imw_per_year, icw_per_year = GROWTH_PRIORS[sex][cvm_stage][profile]
    delta_imw = imw_per_year * years
    delta_icw = icw_per_year * years
    delta_perimeter = coeff_imw_to_perimeter * delta_imw + coeff_icw_to_perimeter * delta_icw
    return delta_imw, delta_icw, delta_perimeter

# -----------------------------
# Core model: McLaughlin-style accounting (simplified MVP)
# -----------------------------
def compute_discrepancy(
    ant_cs: float,
    cos: float,
    midline: float = 0.0,
    incisor_pos: float = 0.0,
):
    # Convention: crowding negative? spacing positive? Your screenshot looks like COS is negative when "leveled".
    # For MVP: treat ant_cs as (spacing positive, crowding negative),
    # COS leveling adds space (enter as negative => becomes +space). We'll just sum as-is.
    return ant_cs + cos + midline + incisor_pos

def compute_remaining(
    initial: float,
    stripping: float,
    expansion: float,
    distalization: float,
    extraction: float,
    growth_space: float,
):
    # All "space-gaining" terms should be entered as positive mm.
    # If you use opposite sign in clinic, enforce via UI labels.
    gained = stripping + expansion + distalization + extraction + growth_space
    remaining = initial - gained
    return gained, remaining

# -----------------------------
# UI
# -----------------------------
import streamlit as st
import pandas as pd

# -----------------------------
# Keep your existing functions:
# - growth_space_equivalent_mm(...)
# - compute_discrepancy(...)
# - compute_remaining(...)
# -----------------------------

st.set_page_config(page_title="Growth-aware Dental VTO", layout="wide")

# --- Dolphin-ish styling ---
st.markdown(
    """
    <style>
      /* tighten overall spacing a bit */
      .block-container {padding-top: 1.0rem; padding-bottom: 2rem;}
      h1, h2, h3 {letter-spacing: -0.5px;}
      /* panel look */
      .panel {
        border: 1px solid rgba(49, 51, 63, 0.15);
        border-radius: 10px;
        padding: 14px 14px 8px 14px;
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
      /* colored “bands” like Dolphin sections */
      .band-blue   {background:#d9edf7; padding:10px; border-radius:8px; border:1px solid rgba(49,51,63,.08);}
      .band-yellow {background:#f9f2d0; padding:10px; border-radius:8px; border:1px solid rgba(49,51,63,.08);}
      .band-green  {background:#dff0d8; padding:10px; border-radius:8px; border:1px solid rgba(49,51,63,.08);}
      .band-gray   {background:#f5f6f8; padding:10px; border-radius:8px; border:1px solid rgba(49,51,63,.08);}
      /* make number inputs more compact */
      div[data-baseweb="input"] > div {height: 36px;}
      /* tabs spacing */
      button[role="tab"] {font-weight: 650;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Growth-aware Dental VTO (McLaughlin-style)")
st.caption("Workflow: Step 1 → Step 2 → Step 3. Growth is added as a space contributor (with optional uncertainty later).")

# -----------------------------
# Shared session state defaults
# -----------------------------
def ss_init(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# Basic toggles
ss_init("move_both", True)
ss_init("override", False)

# -----------------------------
# Tabs = Steps
# -----------------------------
step1, step2, step3 = st.tabs(
    ["Step 1: Initial Tooth Positions", "Step 2: Lower Arch", "Step 3: Determining Movement"]
)

# =========================================================
# STEP 1: Initial Tooth Positions
# =========================================================
with step1:
    left, right = st.columns([1.05, 1.15], gap="large")

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Initial Position</div>', unsafe_allow_html=True)

        st.checkbox("Move both sides (R+L)", key="move_both")
        c1, c2, c3 = st.columns([1, 1, 1])

        with c1:
            r6 = st.number_input("R6 (mm)", value=2.0, step=0.1)
        with c2:
            midline = st.number_input("Midline (mm)", value=0.0, step=0.1)
        with c3:
            l6 = st.number_input("L6 (mm)", value=0.5, step=0.1)

        d = st.number_input("D (mm)", value=1.5, step=0.1)
        s = st.number_input("S (mm)", value=0.0, step=0.1)

        st.divider()

        st.markdown('<div class="panel-title">Growth Module (MVP)</div>', unsafe_allow_html=True)
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            sex = st.selectbox("Sex", ["Female", "Male"])
        with g2:
            cvm_stage = st.selectbox("CVM bucket", ["pre-peak", "peak", "post-peak"])
        with g3:
            profile = st.selectbox("Growth profile", ["low", "avg", "high"], index=1)
        with g4:
            horizon = st.selectbox("Horizon (months)", [12, 18, 24], index=1)

        coeff_imw = st.slider("IMW → perimeter coeff", 0.0, 1.5, 0.75, 0.05)
        coeff_icw = st.slider("ICW → perimeter coeff", 0.0, 1.5, 0.55, 0.05)

        # Call your existing growth function
        delta_imw, delta_icw, growth_space = growth_space_equivalent_mm(
            sex=sex,
            cvm_stage=cvm_stage,
            profile=profile,
            horizon_months=horizon,
            coeff_imw_to_perimeter=coeff_imw,
            coeff_icw_to_perimeter=coeff_icw,
        )

        st.markdown(
            f'<div class="band-gray"><b>Predicted growth over {horizon} months</b><br>'
            f'ΔIMW = {delta_imw:.2f} mm<br>'
            f'ΔICW = {delta_icw:.2f} mm<br>'
            f'ΔArch perimeter (space equiv) = <b>{growth_space:.2f} mm</b></div>',
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)  # close panel

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Visual Preview (placeholder)</div>', unsafe_allow_html=True)
        st.caption("Streamlit can’t replicate Dolphin’s tooth graphics perfectly, but we can approximate next (SVG drawing).")
        st.markdown(
            f"""
            <div class="band-gray">
              <b>Initial Position Summary</b><br>
              R6: {r6:.1f} mm &nbsp; | &nbsp; Midline: {midline:.1f} mm &nbsp; | &nbsp; L6: {l6:.1f} mm<br>
              D: {d:.1f} mm &nbsp; | &nbsp; S: {s:.1f} mm
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# STEP 2: Lower Arch (Dolphin-like table blocks)
# =========================================================
with step2:
    left, right = st.columns([1.15, 1.05], gap="large")

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Lower Arch Discrepancy</div>', unsafe_allow_html=True)
        st.checkbox("Move both sides (R+L)", key="move_both")

        st.markdown('<div class="band-blue"><b>Initial Discrepancy Inputs</b></div>', unsafe_allow_html=True)
        cA, cB = st.columns(2)

        with cA:
            st.markdown("**3 to 3 — Right**")
            ant_R = st.number_input("Ant. Crowding/Spacing (R)", value=0.0, step=0.1, key="ant_R")
            cos_R = st.number_input("Curve of Spee (R)", value=0.0, step=0.1, key="cos_R")
            mid_R = st.number_input("Midline component (R)", value=0.0, step=0.1, key="mid_R")
            inc_R = st.number_input("Incisor position (R)", value=0.0, step=0.1, key="inc_R")

        with cB:
            st.markdown("**3 to 3 — Left**")
            ant_L = st.number_input("Ant. Crowding/Spacing (L)", value=0.0, step=0.1, key="ant_L")
            cos_L = st.number_input("Curve of Spee (L)", value=0.0, step=0.1, key="cos_L")
            mid_L = st.number_input("Midline component (L)", value=0.0, step=0.1, key="mid_L")
            inc_L = st.number_input("Incisor position (L)", value=0.0, step=0.1, key="inc_L")

        st.markdown('<div class="band-green"><b>Space Gained</b> (treatment + growth)</div>', unsafe_allow_html=True)
        cC, cD = st.columns(2)
        with cC:
            st.markdown("**Right**")
            strip_R = st.number_input("Stripping (R)", value=0.0, step=0.1, key="strip_R")
            exp_R = st.number_input("Expansion (R)", value=0.0, step=0.1, key="exp_R")
            dist_R = st.number_input("Distalizing 6–6 (R)", value=0.0, step=0.1, key="dist_R")
            ext_R = st.number_input("Extraction space (R)", value=0.0, step=0.1, key="ext_R")
        with cD:
            st.markdown("**Left**")
            strip_L = st.number_input("Stripping (L)", value=0.0, step=0.1, key="strip_L")
            exp_L = st.number_input("Expansion (L)", value=0.0, step=0.1, key="exp_L")
            dist_L = st.number_input("Distalizing 6–6 (L)", value=0.0, step=0.1, key="dist_L")
            ext_L = st.number_input("Extraction space (L)", value=0.0, step=0.1, key="ext_L")

        # Apply growth symmetrically for now (we can later allocate by midline/unilateral mechanics)
        growth_R = growth_space / 2.0
        growth_L = growth_space / 2.0

        # Compute using your existing functions
        initial_R = compute_discrepancy(ant_R, cos_R, mid_R, inc_R)
        initial_L = compute_discrepancy(ant_L, cos_L, mid_L, inc_L)

        gained_R, remaining_R = compute_remaining(initial_R, strip_R, exp_R, dist_R, ext_R, growth_R)
        gained_L, remaining_L = compute_remaining(initial_L, strip_L, exp_L, dist_L, ext_L, growth_L)

        st.markdown('<div class="band-yellow"><b>Totals</b></div>', unsafe_allow_html=True)

        totals = pd.DataFrame(
            [
                ["Initial Discrepancy", initial_R, initial_L],
                ["Treatment Gained", strip_R+exp_R+dist_R+ext_R, strip_L+exp_L+dist_L+ext_L],
                ["Growth (space equiv)", growth_R, growth_L],
                ["Total Gained", gained_R, gained_L],
                ["Remaining Discrepancy", remaining_R, remaining_L],
            ],
            columns=["Component", "R (mm)", "L (mm)"]
        )
        st.dataframe(totals, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Dental VTO (Preview)</div>', unsafe_allow_html=True)
        st.caption("Next iteration: draw simplified tooth line + arrows as SVG so it looks much closer to Dolphin.")
        st.markdown(
            f"""
            <div class="band-gray">
              <b>Remaining Discrepancy</b><br>
              Right: <b>{remaining_R:.2f} mm</b><br>
              Left: <b>{remaining_L:.2f} mm</b><br><br>
              <span class="hint">Growth included: {growth_space:.2f} mm total perimeter-equivalent</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# STEP 3: Determining Movement (class targets, override)
# =========================================================
with step3:
    left, right = st.columns([1.0, 1.2], gap="large")

    with left:
        st.markdown('<div class="panel"><div class="panel-title">Treat to</div>', unsafe_allow_html=True)

        st.checkbox("Move both sides (R+L)", key="move_both")
        st.checkbox("Override calculated values", key="override")

        st.markdown("**Right**")
        treat_right = st.radio("Right side", ["Class I", "Class II", "Class III"], index=1, horizontal=True, key="treat_R")

        st.markdown("**Left**")
        treat_left = st.radio("Left side", ["Class I", "Class II", "Class III"], index=1, horizontal=True, key="treat_L")

        st.divider()
        st.markdown('<div class="band-gray"><b>What we do next</b><br>'
                    'We convert remaining discrepancy + class targets into a proposed movement distribution '
                    '(molars vs cuspids vs incisors) and an anchorage risk index.</div>',
                    unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="panel-title">Dental VTO (Proposed Dental Movement)</div>', unsafe_allow_html=True)

        st.caption("MVP: display movement allocation numbers. Next: SVG diagram with arrows.")
        # Placeholder “allocation” logic (we’ll replace with your McLaughlin rules)
        # Example: allocate remaining discrepancy to anterior vs posterior based on class target
        def simple_allocation(rem, treat):
            if treat == "Class II":
                # more posterior anchorage demand / anterior retraction
                return {"Anterior": 0.7*rem, "Posterior": 0.3*rem}
            if treat == "Class III":
                return {"Anterior": 0.4*rem, "Posterior": 0.6*rem}
            return {"Anterior": 0.55*rem, "Posterior": 0.45*rem}

        alloc_R = simple_allocation(remaining_R, treat_right)
        alloc_L = simple_allocation(remaining_L, treat_left)

        df_alloc = pd.DataFrame(
            [
                ["Right", treat_right, alloc_R["Anterior"], alloc_R["Posterior"]],
                ["Left", treat_left, alloc_L["Anterior"], alloc_L["Posterior"]],
            ],
            columns=["Side", "Treat to", "Anterior (mm)", "Posterior (mm)"]
        )

        st.dataframe(df_alloc, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)
