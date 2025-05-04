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

    all_lats, all_lons = [], []
    data = {}

    for run in runs:
        df = pd.read_csv(run)
        gps = df.dropna(subset=['Latitude', 'Longitude']).reset_index(drop=True)
        data[run] = gps
        all_lats.extend(gps['Latitude'].tolist())
        all_lons.extend(gps['Longitude'].tolist())

    lat0, lon0 = np.mean(all_lats), np.mean(all_lons)
    m_lat = 111132.92 - 559.82 * np.cos(2 * np.deg2rad(lat0)) + 1.175 * np.cos(4 * np.deg2rad(lat0))
    m_lon = 111412.84 * np.cos(np.deg2rad(lat0)) - 93.5 * np.cos(3 * np.deg2rad(lat0))
        
    for run, gps in data.items():
        gps = gps.copy()
        # Project to metric coordinates
        gps['x'] = (gps['Longitude'] - lon0) * m_lon
        gps['y'] = (gps['Latitude'] - lat0) * m_lat

        # Compute dt for start alignment
        dt = gps['Utc'].diff().fillna(0) / 1000.0
        dist = np.hypot(gps['x'].diff(), gps['y'].diff())
        speed = (dist / dt).fillna(0)
        valid = np.where(speed > 0)[0]
        start_idx = valid[0] if valid.size > 0 else 0

        # Compute signed curvature
        x = gps['x'].values
        y = gps['y'].values
        dx = np.gradient(x)
        dy = np.gradient(y)
        ddx = np.gradient(dx)
        ddy = np.gradient(dy)
        curvature = (dx * ddy - dy * ddx) / (dx**2 + dy**2)**1.5
        curvature = np.nan_to_num(curvature)

        # Smooth curvature
        N = len(curvature)
        if N >= 31:
            wl = 31 if 31 <= N and 31 % 2 == 1 else (N-1 if (N-1) % 2 == 1 else N-2)
            curvature_s = savgol_filter(curvature, window_length=wl, polyorder=2, mode='interp')
        else:
            curvature_s = curvature

        # Take magnitude
        curvature_mag = np.abs(curvature_s)

        # Align start at origin
        x0, y0 = gps.at[start_idx, 'x'], gps.at[start_idx, 'y']
        xs = gps['x'] - x0
        ys = gps['y'] - y0

        # Build line segments
        points = np.vstack([xs, ys]).T
        segments = np.stack([points[:-1], points[1:]], axis=1)
        curv_seg = curvature_mag[1:]

        # Color scale: 0 to 95th percentile
        vmin, vmax = 0, np.nanpercentile(curv_seg, 95)
        norm = plt.Normalize(vmin=vmin, vmax=vmax)

        # Plot
        fig, ax = plt.subplots(figsize=(6, 6))
        lc = LineCollection(segments, cmap='viridis', norm=norm, linewidth=2)
        lc.set_array(curv_seg)
        ax.add_collection(lc)

        # Mark start/end
        ax.plot(0, 0, 'o', color='red', markersize=6, label='Start')
        ax.plot(xs.iloc[-1], ys.iloc[-1], 'o', color='pink', markersize=6, label='End')

        # Colorbar
        cbar = fig.colorbar(lc, ax=ax, label='Curvature Magnitude (1/m)')

        ax.set_aspect('equal', 'box')
        ax.set_xlabel('East displacement (m) from Start')
        ax.set_ylabel('North displacement (m) from Start')
        ax.set_title(f'{run}: Curvature Magnitude Heatmap')
        ax.legend(loc='lower left', frameon=False)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    parser = argp.ArgumentParser(description="graph input files")
    parser.add_argument("filenames", nargs='+', help="A list of csvs")
    args = parser.parse_args()
    main(args)