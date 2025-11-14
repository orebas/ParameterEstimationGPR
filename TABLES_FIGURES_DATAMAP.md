# Tables and Figures Data Mapping

## Quick Reference for Creating Paper Visualizations

### Table 1: Overall Performance Comparison
**Source:** `dataset_package/summary_statistics/overall_performance.csv`
**Format:**
```
| Method | Success Rate | Mean Error | Median Error | Runtime (s) |
```
**Key message:** GPR methods maintain >99% success with competitive errors

### Table 2: Performance by Noise Level
**Source:** `dataset_package/summary_statistics/performance_by_noise.csv`
**Focus on:** ODEPE vs SciML vs AMIGO comparison
**Key message:** GPR degrades gracefully with noise

### Table 3: Performance by System
**Source:** `dataset_package/summary_statistics/performance_by_system.csv`
**Systems to highlight:**
- Simple: harmonic, vanderpol (2 params)
- Medium: lotka_volterra, seir (3-4 params)
- Complex: crauste (13 params), hiv (10 params)

### Table 4: System Characteristics
**Source:** `dataset_package/systems.json`
**Columns needed:**
- System name
- # Parameters
- # States
- # Measured variables
- Domain/Application

### Figure 1: AAA vs GPR Comparison
**Source:** Already exists as `gpr_vs_aaa_comparison.pdf`
**Location:** Referenced in `pres2.tex`
**Shows:** Dramatic difference in handling noisy data

### Figure 2: Error vs Noise Level (Log-Log Plot)
**Data source:** `dataset_package/summary_statistics/performance_by_noise.csv`
**Python code snippet:**
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('dataset_package/summary_statistics/performance_by_noise.csv')
noise_levels = [0, 1e-8, 1e-6, 1e-4, 1e-2]

plt.figure(figsize=(8, 6))
plt.loglog(noise_levels[1:], df['odepe'][1:], 'o-', label='ODEPE (GPR)')
plt.loglog(noise_levels[1:], df['sciml'][1:], 's-', label='SciML')
plt.loglog(noise_levels[1:], df['amigo2_0_10'][1:], '^-', label='AMIGO2')
plt.xlabel('Noise Level')
plt.ylabel('Mean Relative Error')
plt.legend()
plt.grid(True, which="both", ls="-", alpha=0.2)
```

### Figure 3: Runtime Comparison (Bar Chart)
**Data source:** `dataset_package/summary_statistics/overall_performance.csv`
**Key insight:** ODEPE is slower than SciML but faster than ODEPE_polish

### Supporting Evidence from Derivative Benchmark
**Source:** `EstimationDerivativsfromNoisyData.pdf`
**Key metrics to extract:**
- Table 2 (p.8): Overall rankings showing GP-TaylorAD-Julia as #1
- Figure 3 (p.10): Performance across derivative orders
- Table 3 (p.11): Noise robustness comparison

### Data Extraction Commands

```bash
# View overall performance
cat dataset_package/summary_statistics/overall_performance.csv

# Get system-specific results for featured example
grep "lotka_volterra" dataset_package/combined_results_filtered.csv | head -20

# Count successful runs per method
cut -d',' -f2,16 dataset_package/combined_results_filtered.csv | grep -c "true"
```

### LaTeX Table Templates

```latex
% Performance comparison table
\begin{table}[h]
\centering
\caption{Overall Performance on Benchmark Suite}
\begin{tabular}{lcccc}
\toprule
Method & Success Rate & Mean Error & Median Error & Time (s) \\
\midrule
ODEPE (GPR) & 99.6\% & 0.409 & 0.003 & 528 \\
SciML & 99.6\% & 0.148 & 0.004 & 222 \\
AMIGO2 & 99.5\% & 0.501 & 0.001 & 706 \\
\bottomrule
\end{tabular}
\end{table}

% System characteristics
\begin{table}[h]
\centering
\caption{Benchmark ODE Systems}
\begin{tabular}{lcccc}
\toprule
System & Parameters & States & Measurements & Domain \\
\midrule
Lotka-Volterra & 3 & 2 & 1 & Ecology \\
SEIR & 3 & 4 & 2 & Epidemiology \\
Crauste & 13 & 5 & 4 & Immunology \\
\bottomrule
\end{tabular}
\end{table}
```

## Priority Order for Figures/Tables

1. **Must have:** AAA vs GPR comparison (exists)
2. **Must have:** Overall performance table
3. **Must have:** Error vs noise plot
4. **Should have:** System characteristics table
5. **Should have:** Performance by system (select 5-6 systems)
6. **Nice to have:** Runtime comparison
7. **Nice to have:** Derivative order performance from benchmark paper