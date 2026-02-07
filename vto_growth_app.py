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
st.title("Growth-aware Dental VTO (MVP)")
st.caption("McLaughlin-style space accounting + Growth Contribution (transverse → arch perimeter equivalent). Replace priors with your data as you validate.")

left, right = st.columns([1.2, 1.0], gap="large")

with left:
    st.subheader("Dental VTO Inputs")

    st.markdown("**Conventions (for this MVP):**")
    st.markdown("- Crowding is **positive mm of crowding** (e.g., 4 mm crowding → enter **4**).")
    st.markdown("- Space-gaining mechanics (IPR/expansion/distalization/extraction) are **positive mm gained**.")
    st.markdown("- COS: enter **mm of leveling space needed** (positive). If leveling *creates* space in your method, keep it positive here for simplicity.")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Right")
        ant_R = st.number_input("Anterior crowding (R) (mm)", value=0.0, step=0.1)
        cos_R = st.number_input("Curve of Spee leveling (R) (mm)", value=0.0, step=0.1)
        mid_R = st.number_input("Midline component (R) (mm)", value=0.0, step=0.1)
        inc_R = st.number_input("Incisor position component (R) (mm)", value=0.0, step=0.1)

        strip_R = st.number_input("Stripping/IPR gained (R) (mm)", value=0.0, step=0.1)
        exp_R = st.number_input("Expansion (treatment) gained (R) (mm)", value=0.0, step=0.1)
        dist_R = st.number_input("Distalization 6–6 gained (R) (mm)", value=0.0, step=0.1)
        ext_R = st.number_input("Extraction space allocated (R) (mm)", value=0.0, step=0.1)

    with c2:
        st.markdown("### Left")
        ant_L = st.number_input("Anterior crowding (L) (mm)", value=0.0, step=0.1)
        cos_L = st.number_input("Curve of Spee leveling (L) (mm)", value=0.0, step=0.1)
        mid_L = st.number_input("Midline component (L) (mm)", value=0.0, step=0.1)
        inc_L = st.number_input("Incisor position component (L) (mm)", value=0.0, step=0.1)

        strip_L = st.number_input("Stripping/IPR gained (L) (mm)", value=0.0, step=0.1)
        exp_L = st.number_input("Expansion (treatment) gained (L) (mm)", value=0.0, step=0.1)
        dist_L = st.number_input("Distalization 6–6 gained (L) (mm)", value=0.0, step=0.1)
        ext_L = st.number_input("Extraction space allocated (L) (mm)", value=0.0, step=0.1)

    st.divider()
    st.subheader("Growth Module (MVP)")

    g1, g2, g3, g4 = st.columns(4)
    with g1:
        sex = st.selectbox("Sex", ["Female", "Male"])
    with g2:
        cvm_stage = st.selectbox("Growth stage (CVM bucket)", ["pre-peak", "peak", "post-peak"])
    with g3:
        profile = st.selectbox("Growth profile", ["low", "avg", "high"], index=1)
    with g4:
        horizon = st.selectbox("Horizon (months)", [12, 18, 24], index=1)

    coeff_imw = st.slider("IMW → perimeter coefficient", 0.0, 1.5, 0.75, 0.05)
    coeff_icw = st.slider("ICW → perimeter coefficient", 0.0, 1.5, 0.55, 0.05)

    delta_imw, delta_icw, growth_space = growth_space_equivalent_mm(
        sex=sex,
        cvm_stage=cvm_stage,
        profile=profile,
        horizon_months=horizon,
        coeff_imw_to_perimeter=coeff_imw,
        coeff_icw_to_perimeter=coeff_icw,
    )

    st.info(
        f"Predicted over {horizon} months: ΔIMW={delta_imw:.2f} mm, ΔICW={delta_icw:.2f} mm → "
        f"Growth space equivalent (Δarch perimeter)={growth_space:.2f} mm (applied symmetrically here)."
    )

    # For MVP: apply growth space symmetrically, split half/half per side
    growth_R = growth_space / 2.0
    growth_L = growth_space / 2.0

with right:
    st.subheader("Results")

    # Compute initial discrepancy per side
    initial_R = compute_discrepancy(ant_R, cos_R, mid_R, inc_R)
    initial_L = compute_discrepancy(ant_L, cos_L, mid_L, inc_L)

    gained_R, remaining_R = compute_remaining(initial_R, strip_R, exp_R, dist_R, ext_R, growth_R)
    gained_L, remaining_L = compute_remaining(initial_L, strip_L, exp_L, dist_L, ext_L, growth_L)

    df = pd.DataFrame(
        [
            ["Initial discrepancy", initial_R, initial_L],
            ["Treatment gained (IPR+Exp+Dist+Ext)", (strip_R+exp_R+dist_R+ext_R), (strip_L+exp_L+dist_L+ext_L)],
            ["Growth contribution (space equiv)", growth_R, growth_L],
            ["Total gained", gained_R, gained_L],
            ["Remaining discrepancy", remaining_R, remaining_L],
        ],
        columns=["Component", "Right (mm)", "Left (mm)"],
    )

    st.dataframe(df, use_container_width=True)

    st.markdown("### Interpretation (MVP)")
    st.write(
        f"- Right remaining: **{remaining_R:.2f} mm**  | Left remaining: **{remaining_L:.2f} mm**"
    )
    if remaining_R > 0 or remaining_L > 0:
        st.warning("Positive remaining suggests residual crowding/space need under current inputs.")
    else:
        st.success("Zero/negative remaining suggests space is sufficient (or excess space) under current inputs.")

    st.divider()
    st.caption("Next: add midline mechanics, molar relationship targets, and anchorage risk as separate outputs (don’t mix them into perimeter space).")
