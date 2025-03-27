import pandas as pd
import numpy as np
import matplotlib as mpl

t = 0
df = pd.read_csv("data/formatted/eamon copy.csv")
x = [0] * 42546
y = [0] * 42546
psi = [0] * 42546
dt = 0.020

print(x)

for i in range(0, 42545):
    psi[i + 1] = psi[i] + df["Yaw"][i + 310] * dt
    y[i + 1] = y[i] + df["WSFR"][i + 310] * np.cos(psi[i] * np.pi / 180) * dt
    x[i + 1] = x[i] + df["WSFR"][i + 310] * np.sin(psi[i] * np.pi / 180) * dt
