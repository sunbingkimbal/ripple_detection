import numpy as np
import matplotlib.pyplot as plt

# ────────────────────────────────────────────────
#  Parameters
# ────────────────────────────────────────────────
fs = 3906.0
f_carrier = 750.0

start_pulse_duration = 0.460
post_start_pause     = 0.407

bit_duration   = 0.150
pause_duration = 0.427

window_size_sec = 0.100
step_size_sec   = 0.050
rms_threshold   = 0.35          # ← you may need to lower this when noise is present

# ────────────────────────────────────────────────
#  Noise settings
# ────────────────────────────────────────────────
noise_level = 0.12              # std of noise (relative to carrier amp ≈1)
                                # Try values: 0.05 (light), 0.12 (moderate), 0.20–0.30 (heavy)

# ────────────────────────────────────────────────
#  Configuration
# ────────────────────────────────────────────────
n_bits = 50

np.random.seed(42)
start_offset = np.random.uniform(0.3, 3.0)
print(f"Start pulse begins at: {start_offset:.3f} s\n")

# bits (repeat pattern or randomize)
bits = [1,0,1,1,0,0,1,0,1,0] * 5
# bits = np.random.randint(0, 2, n_bits).tolist()

print_first_n_windows = 60

# ────────────────────────────────────────────────
#  Calculate realistic total duration
# ────────────────────────────────────────────────
last_bit_start = (start_offset +
                  start_pulse_duration +
                  post_start_pause +
                  (n_bits - 1) * (bit_duration + pause_duration))

last_bit_end = last_bit_start + bit_duration

margin_after_last_bit = 1.5
total_duration = last_bit_end + margin_after_last_bit + 0.5

print(f"Last bit ends ≈ {last_bit_end:.3f} s")
print(f"Total simulated duration = {total_duration:.2f} s (with margin)\n")

# ────────────────────────────────────────────────
#  Build signal + add noise
# ────────────────────────────────────────────────
N = int(total_duration * fs) + 1
t = np.arange(N) / fs
carrier = np.sin(2 * np.pi * f_carrier * t)
signal = np.zeros_like(t)

# Start pulse
t_start = start_offset
idx_s = int(t_start * fs)
idx_e = int((t_start + start_pulse_duration) * fs)
if idx_e < len(signal):
    signal[idx_s:idx_e] = carrier[idx_s:idx_e]

# Data bits + collect true timing
t_current = t_start + start_pulse_duration + post_start_pause
bit_info = []

for bit_val in bits:
    t_bit_start  = t_current
    t_bit_center = t_current + bit_duration / 2
    t_bit_end    = t_current + bit_duration

    idx_start = int(t_bit_start * fs)
    idx_end   = int(t_bit_end * fs)

    if bit_val == 1 and idx_end < len(signal):
        signal[idx_start:idx_end] = carrier[idx_start:idx_end]

    bit_info.append({
        'center': t_bit_center,
        'start':  t_bit_start,
        'end':    t_bit_end,
        'true':   bit_val
    })

    t_current += bit_duration + pause_duration

# ─── Add noise BEFORE normalization ───────────────────────────────
noise = noise_level * np.random.randn(len(signal))
signal_noisy = signal + noise

# Normalize (to keep peak ≈1 after noise)
max_abs = np.max(np.abs(signal_noisy))
signal_noisy /= (max_abs + 1e-12) if max_abs > 0 else 1

# Rough SNR estimate (signal power during on periods vs noise power)
signal_power = np.mean(signal[signal != 0]**2) if np.any(signal != 0) else 0
noise_power  = noise_level**2
snr_db = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')
print(f"Approximate SNR (on periods) ≈ {snr_db:.1f} dB  (noise std = {noise_level})\n")

# Use noisy signal for detection
signal = signal_noisy

# ────────────────────────────────────────────────
#  Sliding RMS
# ────────────────────────────────────────────────
w_samples = int(window_size_sec * fs)
step_samples = int(step_size_sec * fs)

rms_times = []
rms_values = []
detected_raw = []

i = 0
while i + w_samples <= len(signal):
    chunk = signal[i:i + w_samples]
    rms = np.sqrt(np.mean(chunk**2))
    mid_t = t[i + w_samples//2]
    rms_times.append(mid_t)
    rms_values.append(rms)
    detected_raw.append(1 if rms > rms_threshold else 0)
    i += step_samples

# ────────────────────────────────────────────────
#  Per-bit detection decision + error flagging
# ────────────────────────────────────────────────
bit_detected_as_1 = []
bit_errors = []
timing_errors = []
detected_1_centers = []

for info in bit_info:
    t_c = info['center']
    window_indices = [
        j for j, mt in enumerate(rms_times)
        if mt - window_size_sec/2 < info['end'] and mt + window_size_sec/2 > info['start']
    ]

    detected = any(detected_raw[j] == 1 for j in window_indices)
    bit_detected_as_1.append(detected)

    true_val = info['true']
    if true_val == 1 and not detected:
        bit_errors.append("Miss (FN)")
    elif true_val == 0 and detected:
        bit_errors.append("False alarm (FP)")
    else:
        bit_errors.append("OK")

    if true_val == 1 and detected:
        strong_in_slot = [rms_times[j] for j in window_indices if detected_raw[j] == 1]
        if strong_in_slot:
            det_center = min(strong_in_slot)  # or np.mean(strong_in_slot)
            err = det_center - t_c
            timing_errors.append(err)
            detected_1_centers.append(det_center)

# ────────────────────────────────────────────────
#  Statistics
# ────────────────────────────────────────────────
n_miss = bit_errors.count("Miss (FN)")
n_fp   = bit_errors.count("False alarm (FP)")
n_ok   = bit_errors.count("OK")
ber    = (n_miss + n_fp) / n_bits if n_bits > 0 else 0

print("Bit detection summary:")
print(f"  Total bits     : {n_bits}")
print(f"  Correct (OK)   : {n_ok}")
print(f"  Missed 1s (FN) : {n_miss}")
print(f"  False alarms (FP): {n_fp}")
print(f"  Bit Error Rate : {ber:.4f}  ({n_miss + n_fp} / {n_bits})\n")

if timing_errors:
    print("Timing error stats (only correctly detected 1s):")
    print(f"  Mean error : {np.mean(timing_errors)*1000:6.1f} ms")
    print(f"  Std dev    : {np.std(timing_errors)*1000:6.1f} ms")
    print(f"  Max |err|  : {max(map(abs, timing_errors))*1000:6.1f} ms\n")

# ────────────────────────────────────────────────
#  Plot
# ────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 12))

ax1 = plt.subplot(5,1,1)
plt.plot(t, signal, lw=1, color='C0', alpha=0.9)
plt.axvline(start_offset, color='gold', ls='--', alpha=0.7)
plt.grid(True, alpha=0.3)
plt.title(f"Noisy OOK signal  (start @ {start_offset:.2f} s) • noise std = {noise_level}")
plt.ylabel("amp")
plt.xlim(0, total_duration)

ax2 = plt.subplot(5,1,2, sharex=ax1)
plt.step(rms_times, rms_values, where='mid', color='C1', lw=1.4)
plt.axhline(rms_threshold, color='0.5', ls='--', lw=0.8)
plt.grid(True, alpha=0.3)
plt.ylabel("RMS")
plt.ylim(0, 0.9)

ax3 = plt.subplot(5,1,3, sharex=ax1)
plt.step(rms_times, detected_raw, where='mid', color='C2', lw=1.8, label='raw detection')
plt.grid(True, alpha=0.3)
plt.ylabel("raw win")
plt.ylim(-0.3, 1.3)

ax4 = plt.subplot(5,1,4, sharex=ax1)
y_ok    = 0.65
y_error = 0.35

for i, info in enumerate(bit_info):
    if bit_errors[i] == "OK":
        plt.plot(info['center'], y_ok, 's', ms=10, color='limegreen', alpha=0.9, zorder=10)
    else:
        plt.plot(info['center'], y_error, 's', ms=10, color='red', alpha=0.9, zorder=10)

for info in bit_info:
    plt.axvspan(info['start'], info['end'], color='0.97', alpha=0.5, zorder=1)

plt.plot([], [], 's', ms=10, color='limegreen', label='OK / correct')
plt.plot([], [], 's', ms=10, color='red',      label='Error (miss / false alarm)')

plt.yticks([])
plt.grid(True, alpha=0.25)
plt.ylabel("bit outcome")
plt.ylim(0, 1.1)
plt.legend(loc='upper right', fontsize=10, framealpha=0.92)

ax5 = plt.subplot(5,1,5, sharex=ax1)
if timing_errors:
    plt.plot(detected_1_centers, np.array(timing_errors)*1000, 'o', color='purple', ms=6)
    plt.axhline(0, color='k', ls='--', lw=0.8)
    plt.grid(True, alpha=0.3)
    plt.ylabel("timing err [ms]")
    plt.xlabel("time [s]")
else:
    plt.text(0.5, 0.5, "No correct 1s detected", ha='center', va='center', transform=ax5.transAxes)
    plt.axis('off')

plt.tight_layout()
plt.show()

# ────────────────────────────────────────────────
#  Detailed bit table
# ────────────────────────────────────────────────
print("Per-bit detection results:")
print(" Bit | True | Det | Error type       | Center [s]")
print("───────────────────────────────────────────────────")
for i, info in enumerate(bit_info):
    err_type = bit_errors[i]
    det_str  = "1" if bit_detected_as_1[i] else "0"
    print(f"{i:4d} |  {info['true']}  |  {det_str}  | {err_type:14} | {info['center']:9.3f}")