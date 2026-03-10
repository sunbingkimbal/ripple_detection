# Sliding-Window RMS Ripple Detection

Simple Python simulator + detector for classical **OOK (On-Off Keying)** modulation in the presence of AWGN noise.

Main purpose:
- Generate synthetic noisy OOK signal with realistic timing (start pulse + variable-length pauses)
- Perform energy detection using **sliding RMS window**
- Evaluate bit error rate (BER), false alarms, misses, and timing error statistics
- Visualize signal, RMS trace, detection decisions and per-bit outcomes

Used mainly for:
- Understanding basic non-coherent OOK detection performance
- Testing threshold sensitivity under different noise levels
- Quick prototyping / teaching of energy-based demodulation

## Features

- Configurable start pulse, bit duration, inter-bit pause
- Repeatable pattern or random bits
- Additive white Gaussian noise (AWGN)
- Normalization after noise addition (peak ≈ 1)
- Rough SNR estimation (on-periods only)
- Sliding RMS-based energy detection
- Miss / false alarm classification
- Timing error statistics for correctly detected '1's
- Multi-panel visualization + detailed per-bit table

## Requirements

```text
Python 3.8+
numpy
matplotlib
```

No other external packages required.

## Typical Parameters (as in the code)

| Parameter              | Default value | Meaning                                      |
|-----------------------|---------------|----------------------------------------------|
| `fs`                  | 3906 Hz       | Sampling frequency                           |
| `f_carrier`           | 750 Hz        | Carrier frequency                            |
| `start_pulse_duration`| 0.460 s       | Long start/sync pulse                        |
| `post_start_pause`    | 0.407 s       | Pause after start pulse                      |
| `bit_duration`        | 0.150 s       | Duration of each data bit                    |
| `pause_duration`      | 0.427 s       | Pause after each bit                         |
| `noise_level`         | 0.12          | Noise std (relative to carrier amp ≈1)      |
| `rms_threshold`       | 0.35          | Detection threshold on RMS                   |
| `window_size_sec`     | 0.100 s       | RMS analysis window length                   |
| `step_size_sec`       | 0.050 s       | Step between consecutive RMS windows         |
| `n_bits`              | 50            | Number of data bits                          |

## How to Use

1. Adjust parameters at the top of the script (especially `noise_level`, `rms_threshold`, bit pattern)
2. Run the script

```bash
python ripple_detect.py
```

You will see:

- Printed summary (start time, SNR estimate, BER, timing error stats)
- 5-panel matplotlib figure:
  1. Noisy OOK waveform
  2. Sliding RMS values
  3. Raw per-window detection (1 = above threshold)
  4. Bit outcome markers (green = correct, red = error)
  5. Timing error scatter (only for correctly detected 1s)
- Detailed per-bit table (true value vs detected vs error type)

## Quick Tuning Tips

**More noise → lower threshold**

```python
noise_level = 0.22
rms_threshold = 0.24     # ← lower when noise increases
```

**Cleaner signal → can raise threshold**

```python
noise_level = 0.05
rms_threshold = 0.42     # ← higher → fewer false alarms
```

**Want to see more false alarms?**

Increase `noise_level` **and** keep threshold relatively high.

## Limitations / Known Issues

- Very simple energy detection — no clock recovery, no matched filtering
- Fixed threshold (not adaptive)
- Timing error reported only for correctly detected '1's
- No forward error correction / packet structure
- Start pulse is detected only visually (not used in logic)

## Possible Extensions

- Matched filter / correlation-based detection
- Automatic threshold estimation (e.g. noise floor + k·σ)
- Bit synchronization / clock recovery loop
- Packet structure with header / CRC
- Monte-Carlo simulation over many realizations
- BER vs. Eb/N0 or SNR curves

## License

MIT / Unlicense — feel free to use, modify, share.

Happy experimenting!
