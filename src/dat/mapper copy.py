import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.collections as mcoll

def forward_fill(series):
    """
    Forward-fill missing values (NaNs) in a pandas Series
    using only the previous valid entry.
    """
    return series.ffill()

# -------------------------
# Read your CSV file
# -------------------------
df = pd.read_csv("data/formatted/eamon copy.csv")  # Replace with your actual filename

# -------------------------
# Forward-fill missing Yaw and WSFR
# -------------------------
df["Yaw"]  = forward_fill(df["Yaw"])
df["WSFR"] = forward_fill(df["WSFR"])

# -------------------------
# Adjust Yaw Offset & Convert to Radians
# -------------------------
yaw_offset_deg = 0.0  # If sensor reads +1 deg at rest
df["Yaw"] = df["Yaw"] - yaw_offset_deg
df["Yaw_rad"] = np.deg2rad(df["Yaw"])  # degrees → radians

# -------------------------
# Convert WSFR from mph to m/s
# -------------------------
df["WSFR_mps"] = df["WSFR"] * 0.44704  # mph → m/s

# -------------------------
# Integrate (x, y) using Euler steps
# -------------------------
df["Interval"] = df["Interval"] / 1000
time_vals = df["Interval"].values
yaw_vals  = df["Yaw_rad"].values
v_vals    = df["WSFR_mps"].values

N = len(df)
x = np.zeros(N)
y = np.zeros(N)

# Starting position
x[0], y[0] = 0.0, 0.0

for k in range(N-1):
    dt = (time_vals[k+1] - time_vals[k])
    x[k+1] = x[k] + v_vals[k] * dt * np.cos(yaw_vals[k])
    y[k+1] = y[k] + v_vals[k] * dt * np.sin(yaw_vals[k])

df["x_m"] = x
df["y_m"] = y

# -------------------------
# Visualization
# -------------------------
fig, ax = plt.subplots(figsize=(8,6))

# Prepare a line segment collection that is color-coded by velocity
points = np.array([x, y]).T.reshape(-1,1,2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)

norm_vel = plt.Normalize(v_vals.min(), v_vals.max())
lc = mcoll.LineCollection(segments, cmap='jet', norm=norm_vel)
lc.set_array(v_vals[:-1])  # color by velocity
lc.set_linewidth(2)

line = ax.add_collection(lc)
cbar = fig.colorbar(line, ax=ax)
cbar.set_label("Velocity [m/s]")

ax.set_aspect('equal', 'datalim')
ax.set_xlabel("X position [m]")
ax.set_ylabel("Y position [m]")
ax.set_title("Trajectory from Yaw & WSFR (Forward-Filled)")

df.to_csv("exp.csv")

plt.tight_layout()
plt.show()