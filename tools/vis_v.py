import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import TwoSlopeNorm
from scipy.signal import savgol_filter
import argparse as argp
import os

def main(args):
    # Runs to plot separately
    runs = args.filenames

    for run in runs:
        df = pd.read_csv(run)
        gps = df[df['Latitude'].notna() & df['Longitude'].notna()].reset_index(drop=True)

        # Project lat/lon ➔ local meters
        lat0, lon0 = gps['Latitude'].mean(), gps['Longitude'].mean()
        m_lat = 111132.92 - 559.82 * np.cos(2 * np.deg2rad(lat0)) + 1.175 * np.cos(4 * np.deg2rad(lat0))
        m_lon = 111412.84 * np.cos(np.deg2rad(lat0)) - 93.5 * np.cos(3 * np.deg2rad(lat0))
        gps['x'] = (gps['Longitude'] - lon0) * m_lon
        gps['y'] = (gps['Latitude']  - lat0) * m_lat

        # Compute dt from Utc, distance & speed
        gps['dt'] = gps['Utc'].diff() / 1000.0
        gps['dist'] = np.hypot(gps['x'].diff(), gps['y'].diff())
        gps['speed_mps'] = gps['dist'] / gps['dt']
        gps['speed_mph'] = gps['speed_mps'] * 2.2369362920544

        # Identify start/end
        spd = gps['speed_mph'].to_numpy()
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
        seg_spd = (spd[:-1] + spd[1:]) / 2
        vmin, vmax = np.nanpercentile(seg_spd, 5), np.nanpercentile(seg_spd, 95)

        lc = LineCollection(segs, cmap='viridis', norm=plt.Normalize(vmin=vmin, vmax=vmax))
        lc.set_array(seg_spd)
        lc.set_linewidth(2)

        # Plot
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.add_collection(lc)

        # Overlay GPS measurement dots
        sc = ax.scatter(
            gps['xs'], gps['ys'],
            c=gps['speed_mph'], cmap='viridis',
            norm=plt.Normalize(vmin=vmin, vmax=vmax),
            s=16,  # roughly twice the line width
            marker='o',
            edgecolors='none'
        )

        # Start/end markers
        ax.plot(0, 0, 'o', color='red', markersize=6, label='Start')
        ax.plot(gps.at[end_idx, 'xs'], gps.at[end_idx, 'ys'], 'o', color='pink', markersize=6, label='End')

        ax.set_aspect('equal', 'box')
        ax.set_xlabel('East displacement (m) from Start')
        ax.set_ylabel('North displacement (m) from Start')
        ax.set_title(f"{os.path.basename(run)}: UTC-based Speed Heatmap")
        ax.legend(loc='lower left', frameon=False)

        # Colorbar
        cbar = fig.colorbar(lc, ax=ax, label='Speed (mph)')
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    parser = argp.ArgumentParser(description="graph input files")
    parser.add_argument("filenames", nargs='+', help="A list of csvs")
    args = parser.parse_args()
    main(args)