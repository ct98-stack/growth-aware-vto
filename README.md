# Growth-Aware Dental VTO (McLaughlin-Inspired)

A comprehensive Streamlit application for orthodontic Visual Treatment Objectives (VTO) with integrated growth prediction based on the McLaughlin/Bennett/Trevisi methodology.

## Features

- **Initial Position Tracking**: Record R6, L6, D, S, and midline measurements
- **Growth Assessment**: CVMS-based growth prediction integration
- **Arch Discrepancy Analysis**: Separate calculations for upper and lower arches
- **McLaughlin VTO Calculations**: 8-step methodology for treatment planning
- **Visual Treatment Objectives**: Interactive SVG visualizations

## Live Demo

[Deploy link will be here after deployment]

## Local Installation

```bash
pip install -r requirements.txt
streamlit run vto_growth_app.py
```

## Usage

1. **Step 1**: Enter initial tooth positions and midline measurements
2. **Step 1B**: Configure growth assessment parameters (CVMS stage)
3. **Step 2**: Input arch discrepancy data and treatment procedures
4. **Step 3**: Review calculated dental movements and visual treatment plan

## Technology Stack

- Python 3.9+
- Streamlit
- Pandas
- NumPy

## Author

Created for orthodontic treatment planning and education.
