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
    # Collect all lat/lon for a common projection center
    all_lats, all_lons = [], []
    data = {}
    for run in runs:
        df = pd.read_csv(run)
        gps = df.dropna(subset=['Latitude', 'Longitude']).reset_index(drop=True)
        data[run] = gps
        all_lats.extend(gps['Latitude'])
        all_lons.extend(gps['Longitude'])

    # Global projection center
    lat0, lon0 = np.mean(all_lats), np.mean(all_lons)
    m_lat = 111132.92 - 559.82*np.cos(2*np.deg2rad(lat0)) + 1.175*np.cos(4*np.deg2rad(lat0))
    m_lon = 111412.84*np.cos(np.deg2rad(lat0)) - 93.5*np.cos(3*np.deg2rad(lat0))

    # Plot each run with Savitzky-Golay smoothing
    for run, gps in data.items():
        gps = gps.copy()
        # Project
        gps['x'] = (gps['Longitude'] - lon0) * m_lon
        gps['y'] = (gps['Latitude'] - lat0) * m_lat
        
        # Compute dt, speed, raw acceleration
        dt = gps['Utc'].diff().fillna(0) / 1000.0
        dist = np.hypot(gps['x'].diff(), gps['y'].diff())
        speed = (dist / dt).fillna(0)
        accel = (speed.diff() / dt).fillna(0)
        
        # Savitzky-Golay smoothing
        A = accel.values
        N = len(A)
        if N >= 7:
            # choose window length <= N, odd
            wl = min(51, N if N%2 else N-1)
            wl = max(7, wl)  # at least 7
            acc_smooth = savgol_filter(A, window_length=wl, polyorder=2, mode='interp')
        else:
            acc_smooth = A
        
        # Align start
        valid = np.where(speed > 0)[0]
        start = valid[0] if valid.size>0 else 0
        x0, y0 = gps.at[start, 'x'], gps.at[start, 'y']
        xs = gps['x'] - x0
        ys = gps['y'] - y0
        
        # Build line segments
        pts = np.vstack([xs, ys]).T
        segs = np.stack([pts[:-1], pts[1:]], axis=1)
        accel_seg = acc_smooth[1:]
        
        # Color normalization: center at 0
        vmin, vmax = np.nanpercentile(accel_seg, 5), np.nanpercentile(accel_seg, 95)
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
        
        # Plot
        fig, ax = plt.subplots(figsize=(6, 6))
        lc = LineCollection(segs, cmap='RdYlGn', norm=norm, linewidth=3)
        lc.set_array(accel_seg)
        ax.add_collection(lc)
        
        # Mark start/end
        ax.plot(0, 0, 'o', color='red', markersize=8, label='Start')
        ax.plot(xs.iloc[-1], ys.iloc[-1], 'o', color='pink', markersize=8, label='End')
        
        # Colorbar
        cbar = fig.colorbar(lc, ax=ax, label='Smoothed Acceleration (m/s²)')
        
        ax.set_aspect('equal', 'box')
        ax.set_xlabel('East displacement (m) from Start')
        ax.set_ylabel('North displacement (m) from Start')
        ax.set_title(f'{run}: Savitzky-Golay Smoothed Accel')
        ax.legend(loc='lower left', frameon=False)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    parser = argp.ArgumentParser(description="graph input files")
    parser.add_argument("filenames", nargs='+', help="A list of csvs")
    args = parser.parse_args()
    main(args)