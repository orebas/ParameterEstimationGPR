#!/usr/bin/env python3
"""
Generate Figure 1: GPR Smoothing and Derivative Estimation Demo
================================================================
Two-panel figure demonstrating:
- Panel (a): GPR smoothing of noisy FitzHugh-Nagumo trajectory
- Panel (b): GPR derivative estimation vs. finite differences
  * Shows true derivative (black dashed line)
  * Finite differences on noisy data (red X markers - noisy)
  * GPR derivative (blue line - smooth and accurate)
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configure paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = ROOT_DIR / "outputs" / "figures" / "corrected"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# FitzHugh-Nagumo parameters (from benchmark)
PARAMS = {'g': 0.502, 'a': 0.854, 'b': 0.607}
INITIAL_CONDITIONS = {'VV': 0.794, 'R': 0.852}
TIME_SPAN = (-1.0, 1.0)
NOISE_LEVEL = 0.01  # 1% noise
ZOOM_WINDOW = (-0.3, 0.5)  # Zoom to interesting region with dynamics

def fitzhugh_nagumo(t, y, g, a, b):
    """FitzHugh-Nagumo ODE system."""
    VV, R = y
    dVV_dt = g * (VV - VV**3/3 + R)
    dR_dt = -(VV - a + b*R) / g
    return [dVV_dt, dR_dt]

def generate_clean_trajectory(n_points=1001):
    """Generate clean FitzHugh-Nagumo trajectory."""
    t_eval = np.linspace(TIME_SPAN[0], TIME_SPAN[1], n_points)
    y0 = [INITIAL_CONDITIONS['VV'], INITIAL_CONDITIONS['R']]

    sol = solve_ivp(
        lambda t, y: fitzhugh_nagumo(t, y, **PARAMS),
        TIME_SPAN,
        y0,
        t_eval=t_eval,
        method='RK45',
        rtol=1e-10,
        atol=1e-12
    )

    return sol.t, sol.y[0, :]  # Return time and V (membrane potential)

def compute_true_derivative(t, V_true):
    """Compute true derivative using finite differences on clean data."""
    # Use central differences
    dV_dt = np.gradient(V_true, t)
    return dV_dt

def compute_finite_diff_derivative(t, y):
    """Compute derivative using simple central finite differences."""
    # This will be noisy when applied to noisy data
    dV_dt = np.gradient(y, t)
    return dV_dt

def fit_gpr_with_derivatives(t_train, y_train, t_eval):
    """
    Fit GPR and compute predictions + derivatives.

    Adapted from /home/orebas/tmp/deriv-estimation-study/methods/python/gp/gaussian_process.py
    """
    # Heuristic initialization
    dists = np.abs(np.subtract.outer(t_train, t_train))
    nonzero_dists = dists[dists > 0]
    ell0 = float(np.median(nonzero_dists)) / np.sqrt(2) if len(nonzero_dists) > 0 else 1.0
    amp0 = 1.0  # normalize_y=True makes amplitude ~1.0

    # Kernel with appropriate bounds
    kernel = ConstantKernel(amp0, (1e-4, 1e4)) * \
             RBF(length_scale=ell0, length_scale_bounds=(3e-3, 3e2)) + \
             WhiteKernel(noise_level=1e-6, noise_level_bounds=(1e-10, 0.2))

    # Fit GPR
    gp = GaussianProcessRegressor(
        kernel=kernel,
        n_restarts_optimizer=20,
        alpha=1e-10,
        normalize_y=True,
        optimizer="fmin_l_bfgs_b"
    )

    X_train = t_train.reshape(-1, 1)
    gp.fit(X_train, y_train)

    # Predictions
    X_eval = t_eval.reshape(-1, 1)
    y_pred, y_std = gp.predict(X_eval, return_std=True)

    # Extract fitted parameters for derivative computation
    fitted = gp.kernel_
    amp = 1.0
    ell = 1.0
    try:
        if hasattr(fitted, 'k1') and hasattr(fitted, 'k2'):
            k1 = fitted.k1
            if hasattr(k1, 'k1') and hasattr(k1, 'k2') and isinstance(k1.k2, RBF):
                amp = float(getattr(k1.k1, 'constant_value', 1.0))
                ell = float(k1.k2.length_scale)
            elif isinstance(k1, RBF):
                ell = float(k1.length_scale)
        elif isinstance(fitted, RBF):
            ell = float(fitted.length_scale)
    except Exception:
        pass

    # Compute first derivatives using kernel derivative (Hermite polynomial)
    alpha = gp.alpha_.ravel()
    y_std_norm = float(getattr(gp, "_y_train_std", 1.0))

    derivatives = []
    for x_star in t_eval:
        u = (x_star - t_train) / ell
        u_safe = np.clip(u, -50.0, 50.0)
        base = np.exp(-0.5 * u_safe**2)
        # First derivative: H_1(u) = u
        h1 = u_safe
        scale = amp / ell
        k_1 = (-scale) * h1 * base  # negative sign for first derivative
        deriv = float(y_std_norm * (k_1 @ alpha))
        derivatives.append(deriv)

    return y_pred, y_std, np.array(derivatives)

def create_figure():
    """Generate the two-panel figure."""
    print("Generating Figure 1: GPR Smoothing Demo")

    # Generate clean trajectory
    print("  - Generating clean FitzHugh-Nagumo trajectory...")
    t_fine, V_true_fine = generate_clean_trajectory(n_points=1001)

    # Subsample for training (sparse observations)
    n_train = 40  # Sparse sampling to show GPR interpolation
    train_indices = np.linspace(0, len(t_fine)-1, n_train, dtype=int)
    t_train = t_fine[train_indices]
    V_train_clean = V_true_fine[train_indices]

    # Add noise to training data
    print(f"  - Adding {NOISE_LEVEL*100:.0f}% noise to {n_train} observations...")
    np.random.seed(42)  # Reproducible
    noise_std = NOISE_LEVEL * np.std(V_train_clean)
    V_train_noisy = V_train_clean + np.random.normal(0, noise_std, len(V_train_clean))

    # Fit GPR
    print("  - Fitting Gaussian Process...")
    V_pred, V_std, dV_pred = fit_gpr_with_derivatives(t_train, V_train_noisy, t_fine)

    # Compute true derivative
    print("  - Computing true derivatives...")
    dV_true = compute_true_derivative(t_fine, V_true_fine)

    # Compute finite differences on noisy training data (for comparison)
    print("  - Computing finite differences on noisy data (for comparison)...")
    dV_finitediff_train = compute_finite_diff_derivative(t_train, V_train_noisy)

    # Apply zoom window to focus on interesting dynamics
    print(f"  - Zooming to region {ZOOM_WINDOW}...")
    zoom_mask = (t_fine >= ZOOM_WINDOW[0]) & (t_fine <= ZOOM_WINDOW[1])
    zoom_mask_train = (t_train >= ZOOM_WINDOW[0]) & (t_train <= ZOOM_WINDOW[1])

    t_zoom = t_fine[zoom_mask]
    V_true_zoom = V_true_fine[zoom_mask]
    V_pred_zoom = V_pred[zoom_mask]
    V_std_zoom = V_std[zoom_mask]
    dV_true_zoom = dV_true[zoom_mask]
    dV_pred_zoom = dV_pred[zoom_mask]

    t_train_zoom = t_train[zoom_mask_train]
    V_train_noisy_zoom = V_train_noisy[zoom_mask_train]
    dV_finitediff_train_zoom = dV_finitediff_train[zoom_mask_train]

    # Create figure
    print("  - Creating figure...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Panel (a): Trajectory smoothing (zoomed to show detail)
    ax1.scatter(t_train_zoom, V_train_noisy_zoom, c='darkgray', s=100, alpha=0.8,
                label='Noisy observations', zorder=3, edgecolors='black', linewidths=0.8)
    ax1.plot(t_zoom, V_true_zoom, 'k--', linewidth=2.5,
             label='True signal', zorder=2)
    ax1.plot(t_zoom, V_pred_zoom, 'b-', linewidth=3,
             label='GPR posterior mean', zorder=4)
    ax1.fill_between(t_zoom, V_pred_zoom - 2*V_std_zoom, V_pred_zoom + 2*V_std_zoom,
                      color='blue', alpha=0.2,
                      label='95% confidence', zorder=1)

    ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Membrane Potential (V)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) GPR Smoothing of Noisy Observations',
                  fontsize=13, fontweight='bold', pad=10)
    ax1.legend(loc='upper right', fontsize=10, framealpha=0.95)
    ax1.grid(True, alpha=0.3, linewidth=0.5)
    ax1.tick_params(labelsize=10)

    # Panel (b): Derivative estimation comparison (zoomed to show detail)
    ax2.plot(t_zoom, dV_true_zoom, 'k--', linewidth=2.5,
             label='True derivative', zorder=2)
    ax2.scatter(t_train_zoom, dV_finitediff_train_zoom, c='red', s=70, alpha=0.7,
                label='Finite differences', zorder=3, marker='x', linewidths=2)
    ax2.plot(t_zoom, dV_pred_zoom, 'b-', linewidth=3,
             label='GPR derivative', zorder=4)

    ax2.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Rate of Change (dV/dt)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Derivative Estimation: GPR vs. Finite Differences',
                  fontsize=13, fontweight='bold', pad=10)
    ax2.legend(loc='upper right', fontsize=10, framealpha=0.95)
    ax2.grid(True, alpha=0.3, linewidth=0.5)
    ax2.tick_params(labelsize=10)

    plt.tight_layout()

    # Save figure
    output_path_png = OUTPUT_DIR / 'figure1_gpr_demo.png'
    output_path_pdf = OUTPUT_DIR / 'figure1_gpr_demo.pdf'

    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved to {output_path_png}")
    print(f"  ✓ Saved to {output_path_pdf}")

    return output_path_pdf

def main():
    """Generate Figure 1."""
    print("="*60)
    print("GENERATING FIGURE 1: GPR SMOOTHING DEMONSTRATION")
    print("="*60)
    print(f"System: FitzHugh-Nagumo (neural dynamics)")
    print(f"Noise level: {NOISE_LEVEL*100:.0f}% (10^-2)")
    print(f"Training points: 40 (sparse)")
    print(f"Evaluation points: 1001 (dense)")
    print(f"Zoom window: {ZOOM_WINDOW}")
    print()

    output_path = create_figure()

    print("\n" + "="*60)
    print("FIGURE 1 GENERATED SUCCESSFULLY")
    print("="*60)
    print(f"\nTo use in paper, add to paper.tex:")
    print(f"\\begin{{figure}}[H]")
    print(f"\\centering")
    print(f"\\includegraphics[width=0.95\\textwidth]{{../visualization/outputs/figures/corrected/figure1_gpr_demo.pdf}}")
    print(f"\\caption{{Gaussian Process Regression for derivative estimation...")
    print(f"\\label{{fig:gpr_demo}}")
    print(f"\\end{{figure}}")

if __name__ == "__main__":
    main()
