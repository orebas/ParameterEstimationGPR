# GPR-Enhanced Parameter Estimation

Research paper and analysis code for Gaussian Process Regression-based parameter estimation in dynamical systems.

## Quick Start

### Prerequisites

- **Python 3.10+**
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package installer

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup

Clone and set up the environment:
```bash
git clone <repository-url>
cd ParameterEstimationGPR
./setup.sh
```

### Build the Paper

Generate all tables, figures, and compile the PDF:
```bash
python build_paper.py
```

The compiled paper will be at `paper/paper.pdf`.

## Repository Structure

```
├── build_paper.py          # Automated build pipeline
├── setup.sh                # Environment setup script
├── scripts/                # Figure and table generation
├── dataset_package/        # Benchmark datasets
├── paper/                  # LaTeX source and outputs
├── config/                 # Plotting configuration
└── pyproject.toml          # Python dependencies
```

## Development

Activate the virtual environment:
```bash
source .venv/bin/activate
```

Install development dependencies:
```bash
uv pip install -e ".[dev]"
```

## Requirements

All Python dependencies are managed via `pyproject.toml` and installed automatically by `setup.sh`.

Key packages:
- pandas, numpy, scipy
- matplotlib, seaborn, plotly
- scikit-learn, statsmodels
- Jupyter (for exploratory analysis)
