import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.collections as mcoll

# read the file into a dataframe
df = pd.read_csv("data/formatted/eamon copy.csv", usecols = ['WSFR', 'Yaw'])


# forward fill WSFR and Yaw values
df["Yaw"]  = df["Yaw"].ffill()
df["WSFR"] = df["WSFR"].ffill()
print("after forward filling")
print(df.describe())

# offset the yaw and convert to radians / s, offset wheel speed and convert to mps
yaw_offset_deg = -1.0  
df["Yaw"] = df["Yaw"] + yaw_offset_deg
df["Yaw"] = np.deg2rad(df["Yaw"]) 

df["WSFR"] = df["WSFR"] * 0.44704  # mph → m/s
print("after correcting units")
print(df.describe()) # WSFR is now in meters per second, Yaw is now in radians / second

# define dt, the timestep between values in the dataframe
dt = 0.020 # in seconds


# add rows for x, y vals to dataframe
n = len(df)
df["x"] = np.zeros(n)
df["y"] = np.zeros(n)
df["theta"] = np.zeros(n)

print("after adding x, y cols")
print(df.describe()) # WSFR is now in meters per second, Yaw is now in radians / second

for i in range(1, n):
    df.loc[i, "theta"] = df.loc[i - 1, "theta"] + df.loc[i, "Yaw"] * dt
    
    # Update x and y position using the previous heading.
    # (Assuming the speed in the current row applies over this time step.)
    df.loc[i, "x"] = df.loc[i - 1, "x"] + df.loc[i, "WSFR"] * dt * np.cos(df.loc[i - 1, "theta"])
    df.loc[i, "y"] = df.loc[i - 1, "y"] + df.loc[i, "WSFR"] * dt * np.sin(df.loc[i - 1, "theta"])

print("after calculating x, y, heading")
print(df.describe())

# export to csv
df.to_csv("exp.csv")

# plot the result
plt.figure(figsize=(8, 6))
plt.plot(df["x"], df["y"], label="Car Path")
plt.xlabel("x (m)")
plt.ylabel("y (m)")
plt.title("Car Path from Sensor Data")
plt.legend()
plt.grid(True)
plt.axis("equal")  # Ensures the x and y axes have the same scale
plt.show()
