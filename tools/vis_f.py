import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import TwoSlopeNorm
from scipy.signal import savgol_filter
import argparse as argp
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
import os

sensor_cols = ['AccelX', 'AccelY', 'TPS', 'Speed', 'FrontBP', 'SteerAng']
state_colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # colors for states 0,1,2

def compute_states(gps):
    N = len(gps)
    # Prepare arrays
    statehistory = np.zeros(N, dtype=int)
    currentstate = 0
    
    # Iterate through each sample
    for i in range(N):
        # Fill NaNs from previous
        if i > 0:
            for col in sensor_cols:
                if np.isnan(gps.at[i, col]):
                    gps.at[i, col] = gps.at[i-1, col]
        
        # Read sensors
        accel_x = gps.at[i, 'AccelX']
        accel_y = gps.at[i, 'AccelY']
        TPS = gps.at[i, 'TPS']
        speed = gps.at[i, 'Speed']
        brakepress = gps.at[i, 'FrontBP']
        steering_angle = gps.at[i, 'SteerAng']
        
        # Transition logic
        nextstate = currentstate
        if currentstate == 1:
            if (brakepress > 30 or accel_x > 0.3) or (steering_angle > 40 or abs(accel_y) > 1.1):
                nextstate = 0
            elif abs(accel_y) < 0.5 and steering_angle < 20 and TPS > 20:
                nextstate = 2
        elif currentstate == 2:
            if TPS < 20 and ((steering_angle > 40 or abs(accel_y) > 1.1) or (brakepress > 30 or accel_x > 0.3)):
                nextstate = 0
            elif speed > 15 and (abs(accel_y) > 0.5 or steering_angle > 20):
                nextstate = 1
        else:  # state 0
            if TPS > 20 and steering_angle < 30 and abs(accel_y) < 0.5 and brakepress < 30:
                nextstate = 2
            elif speed > 15 and abs(accel_y) < 1.1 and steering_angle < 30 and (brakepress < 50 and accel_x < 0.4):
                nextstate = 1
        
        currentstate = nextstate
        statehistory[i] = currentstate
    
    return statehistory

def main(args):
    # Runs to plot separately
    runs = args.filenames
    

    for run in runs:
        df = pd.read_csv(run)
        gps = df[df['Latitude'].notna() & df['Longitude'].notna()].reset_index(drop=True)

        statehist = compute_states(gps)

        # Project lat/lon ➔ local meters
        lat0, lon0 = gps['Latitude'].mean(), gps['Longitude'].mean()
        m_lat = 111132.92 - 559.82 * np.cos(2 * np.deg2rad(lat0)) + 1.175 * np.cos(4 * np.deg2rad(lat0))
        m_lon = 111412.84 * np.cos(np.deg2rad(lat0)) - 93.5 * np.cos(3 * np.deg2rad(lat0))
        gps['x'] = (gps['Longitude'] - lon0) * m_lon
        gps['y'] = (gps['Latitude']  - lat0) * m_lat

        # Identify start/end
        spd = gps['Speed'].to_numpy()
        valid = np.where(spd > 0)[0]
        if valid.size == 0:
            continue
        start_idx, end_idx = valid[0], valid[-1]

        # Shift origin to start
        x0, y0 = gps.at[start_idx, 'x'], gps.at[start_idx, 'y']
        gps['xs'] = gps['x'] - x0
        gps['ys'] = gps['y'] - y0

        # Build colored line segments
        pts = gps[['xs', 'ys']].to_numpy()
        segs = np.stack([pts[:-1], pts[1:]], axis=1)
        seg_states = statehist[1:]


        # Plot
        cmap = ListedColormap(state_colors)
        norm = BoundaryNorm([0,1,2,3], cmap.N)
        lc = LineCollection(segs, cmap=cmap, norm=norm, linewidth=3)
        lc.set_array(seg_states)
        lc.set_linewidth(2)

        fig, ax = plt.subplots(figsize=(6,6))  
        ax.add_collection(lc)

        ax.plot(0, 0, 'o', color='red', markersize=6, label='Start')
        ax.plot(gps.at[end_idx, 'xs'], gps.at[end_idx, 'ys'], 'o', color='pink', markersize=6, label='End')
        ax.set_aspect('equal', 'box')
        ax.set_xlabel('East displacement (m) from Start')
        ax.set_ylabel('North displacement (m) from Start')
        ax.set_title(f"{os.path.basename(run)}: UTC-based Speed Heatmap")
        ax.legend(loc='lower left', frameon=False)

        cbar = fig.colorbar(lc, ax=ax, ticks=[0.5,1.5,2.5])
        cbar.set_ticklabels(['State 0','State 1','State 2'])
        cbar.set_label('FSM State')

        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    parser = argp.ArgumentParser(description="graph input files")
    parser.add_argument("filenames", nargs='+', help="A list of csvs")
    args = parser.parse_args()
    main(args)