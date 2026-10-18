from magnetometer_tilt_corr import GY271
import numpy as np
from time import sleep

mag = GY271()

print("make a figure-8")
print("Collecting 500 samples...")
print()

samples = []

for i in range(500):
    x, y, z = mag.read_magnetometer()
    samples.append([x, y, z])

    if (i + 1) % 50 == 0:
        print(f"Collected {i + 1}/500 samples...")

    sleep(0.05)

samples = np.array(samples)

x_min, x_max = samples[:, 0].min(), samples[:, 0].max()
y_min, y_max = samples[:, 1].min(), samples[:, 1].max()
z_min, z_max = samples[:, 2].min(), samples[:, 2].max()

# offsets hard iron)
x_offset = (x_max + x_min) / 2
y_offset = (y_max + y_min) / 2
z_offset = (z_max + z_min) / 2

# scaleings soft iron
x_range = x_max - x_min
y_range = y_max - y_min
z_range = z_max - z_min
avg_range = (x_range + y_range + z_range) / 3

x_scale = avg_range / x_range
y_scale = avg_range / y_range
z_scale = avg_range / z_range

print("COMPLETE!")
print("= = = = = = = = = =")
print("\nValues:")
print(f"""
mag.set_calibration(
    x_offset={x_offset},
    y_offset={y_offset},
    z_offset={z_offset},
    x_scale={x_scale},
    y_scale={y_scale},
    z_scale={z_scale}
)
""")
