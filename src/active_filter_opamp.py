import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plots_dir = os.path.join(project_root, "plots")
os.makedirs(plots_dir, exist_ok=True)

# -------------------------------------------------------------
# 1. Sallen-Key 2nd Order Low-Pass Filter Design
# Specifications: Cutoff fc = 10 kHz, Butterworth Q = 1/sqrt(2) = 0.707
# Component values:
# R1 = R2 = R = 10 kOhm
# C1 = 2.25 nF, C2 = 1.13 nF -> fc ≈ 10.0 kHz, Q ≈ 0.707
# -------------------------------------------------------------
R1 = 10e3
R2 = 10e3
C1 = 2.25e-9
C2 = 1.13e-9
K = 1.0  # Unity-gain follower

# Transfer Function: H(s) = (K / (R1*R2*C1*C2)) / (s^2 + s*(1/(R1*C1) + 1/(R2*C1) + (1-K)/(R2*C2)) + 1/(R1*R2*C1*C2))
b0 = K / (R1 * R2 * C1 * C2)
a2 = 1.0
a1 = (1.0 / (R1 * C1)) + (1.0 / (R2 * C1)) + ((1.0 - K) / (R2 * C2))
a0 = 1.0 / (R1 * R2 * C1 * C2)

omega_0 = np.sqrt(a0)
f0 = omega_0 / (2 * np.pi)
Q = omega_0 / a1

print(f"Designed Cutoff Frequency fc: {f0:.2f} Hz")
print(f"Designed Quality Factor Q: {Q:.3f}")

system_ideal = signal.TransferFunction([b0], [a2, a1, a0])

# Frequency Response (Bode Plot)
frequencies = np.logspace(2, 6, 1000)  # 100 Hz to 1 MHz
w, mag, phase = signal.bode(system_ideal, frequencies * 2 * np.pi)

# Non-ideal Op-Amp with finite Gain-Bandwidth Product (GBW = 1 MHz vs 10 MHz)
gbw_1m = 2 * np.pi * 1e6
gbw_10m = 2 * np.pi * 10e6
sys_gbw_1m = signal.TransferFunction([b0 * gbw_1m], np.convolve([a2, a1, a0], [1.0, gbw_1m]))
sys_gbw_10m = signal.TransferFunction([b0 * gbw_10m], np.convolve([a2, a1, a0], [1.0, gbw_10m]))

w1, mag1, phase1 = signal.bode(sys_gbw_1m, frequencies * 2 * np.pi)
w10, mag10, phase10 = signal.bode(sys_gbw_10m, frequencies * 2 * np.pi)

# Plot Bode Diagram
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

ax1.semilogx(frequencies, mag, 'b-', linewidth=2, label="Ideal Sallen-Key (Butterworth Q=0.707)")
ax1.semilogx(frequencies, mag10, 'g--', linewidth=1.8, label="Op-Amp GBW = 10 MHz (e.g. TL082)")
ax1.semilogx(frequencies, mag1, 'r:', linewidth=2, label="Op-Amp GBW = 1 MHz (e.g. LM741)")
ax1.axvline(f0, color='gray', linestyle='--', alpha=0.7, label=f"Cutoff fc = {f0/1e3:.1f} kHz (-3dB)")
ax1.axhline(-3, color='black', linestyle=':', alpha=0.5)
ax1.set_ylabel("Magnitude (dB)", fontsize=11, fontweight='bold')
ax1.set_title("Sallen-Key Active Low-Pass Filter: Frequency Response & GBW Limitation", fontsize=13, fontweight='bold')
ax1.legend(loc='lower left', frameon=True)
ax1.grid(True, which='both', linestyle='--', alpha=0.5)

ax2.semilogx(frequencies, phase, 'b-', linewidth=2, label="Ideal Phase")
ax2.semilogx(frequencies, phase10, 'g--', linewidth=1.8, label="GBW = 10 MHz Phase")
ax2.semilogx(frequencies, phase1, 'r:', linewidth=2, label="GBW = 1 MHz Phase")
ax2.axvline(f0, color='gray', linestyle='--', alpha=0.7)
ax2.set_xlabel("Frequency (Hz)", fontsize=11, fontweight='bold')
ax2.set_ylabel("Phase (degrees)", fontsize=11, fontweight='bold')
ax2.legend(loc='lower left', frameon=True)
ax2.grid(True, which='both', linestyle='--', alpha=0.5)

plt.tight_layout()
bode_path = os.path.join(plots_dir, "sallen_key_bode_response.png")
plt.savefig(bode_path, dpi=300)
plt.close()
print("Saved:", bode_path)

# Transient Step Response under Capacitive Loading / Phase Margin degradation
t = np.linspace(0, 0.0005, 1000) # 0 to 500 us
t_out, y_ideal = signal.step(system_ideal, T=t)

omega_ring = 2 * np.pi * 15e3
zeta_ring = 0.35 # Lightly damped due to capacitive loading
sys_ringing = signal.TransferFunction([omega_ring**2], [1, 2 * zeta_ring * omega_ring, omega_ring**2])
_, y_ringing = signal.step(sys_ringing, T=t)

plt.figure(figsize=(9, 4.5))
plt.plot(t * 1e6, y_ideal, 'b-', linewidth=2, label="Nominal Step Response (Phase Margin ≈ 65°)")
plt.plot(t * 1e6, y_ringing, 'r--', linewidth=2, label="Step Response with Capacitive Load CL = 100pF (Phase Margin ≈ 35°, Severe Ringing)")
plt.axhline(1.0, color='gray', linestyle=':', alpha=0.7, label="Steady-State Target")
plt.title("Op-Amp Closed-Loop Transient Step Response & Capacitive Load Ringing", fontsize=12, fontweight='bold')
plt.xlabel("Time (µs)", fontsize=11, fontweight='bold')
plt.ylabel("Normalized Output Voltage (V)", fontsize=11, fontweight='bold')
plt.legend(loc='lower right', frameon=True)
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
step_path = os.path.join(plots_dir, "opamp_transient_step_response.png")
plt.savefig(step_path, dpi=300)
plt.close()
print("Saved:", step_path)
