import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize, TwoSlopeNorm, ListedColormap, BoundaryNorm
from scipy.signal import savgol_filter

# FSM state computation
def compute_states(gps):
    sensor_cols = ['AccelX', 'AccelY', 'TPS', 'Speed', 'FrontBP', 'SteerAng']
    N = len(gps)
    states = np.zeros(N, dtype=int)
    cs = 0
    for i in range(N):
        # forward-fill missing sensor data
        if i > 0:
            gps.loc[i, sensor_cols] = gps.loc[i, sensor_cols].fillna(gps.loc[i-1, sensor_cols])
        ax = gps.at[i,'AccelX']
        ay = gps.at[i,'AccelY']
        tps = gps.at[i,'TPS']
        sp = gps.at[i,'Speed']
        bp = gps.at[i,'FrontBP']
        # sa = gps.at[i,'SteerAng'] #TODO this is the CORRECT calculation
        sa = 0 #! this is a PLACEEHOLDER line while the steer angle sensor is getting fixed

        ns = cs
        if cs == 1:
            if bp>30 or ax>0.3 or sa>40 or abs(ay)>1.1: ns = 0
            elif abs(ay)<0.5 and sa<20 and tps>20: ns = 2
        elif cs == 2:
            if tps<20 and ((sa>40 or abs(ay)>1.1) or (bp>30 or ax>0.3)): ns = 0
            elif sp>15 and (abs(ay)>0.5 or sa>20): ns = 1
        else:
            if tps>20 and sa<30 and abs(ay)<0.5 and bp<30: ns = 2
            elif sp>15 and abs(ay)<1.1 and sa<30 and (bp<50 and ax<0.4): ns = 1
        cs = ns
        states[i] = cs
    return states

def plot_all_metrics(run):
    # load data
    df = pd.read_csv(run)
    df[['AccelX','AccelY','TPS','Speed','FrontBP','SteerAng']] = df[['AccelX','AccelY','TPS','Speed','FrontBP','SteerAng']].ffill().bfill()
    gps = df.dropna(subset=['Latitude','Longitude']).reset_index(drop=True)
    
    # projection center per-run
    lat0, lon0 = gps['Latitude'].mean(), gps['Longitude'].mean()
    m_lat = 111132.92 - 559.82*np.cos(2*np.deg2rad(lat0)) + 1.175*np.cos(4*np.deg2rad(lat0))
    m_lon = 111412.84*np.cos(np.deg2rad(lat0)) - 93.5*np.cos(3*np.deg2rad(lat0))
    gps['x'] = (gps['Longitude'] - lon0) * m_lon
    gps['y'] = (gps['Latitude'] - lat0) * m_lat
    
    # time delta
    dt = gps['Utc'].diff().fillna(0)/1000.0
    dist = np.hypot(gps['x'].diff(), gps['y'].diff())
    speed = (dist/dt).fillna(0)
    speed_mph = speed * 2.2369362920544
    accel = (speed.diff() / dt).fillna(0)

    # Savitzky-Golay smoothing
    A = accel.values
    N = len(A)
    if N >= 7:
        # choose window length <= N, odd
        wl = min(51, N if N%2 else N-1)
        wl = max(7, wl)  # at least 7
        accel_smooth = savgol_filter(A, window_length=wl, polyorder=2, mode='interp')
    else:
        accel_smooth = A

    
    x, y = gps['x'].values, gps['y'].values
    dx, dy = np.gradient(x), np.gradient(y)
    ddx, ddy = np.gradient(dx), np.gradient(dy)
    curv = (dx*ddy - dy*ddx)/(dx*dx + dy*dy)**1.5
    curv = np.nan_to_num(curv)
    if len(curv) >= 31:
        wl = 31 if 31 <= len(curv) and 31%2 else (len(curv)-1 if (len(curv)-1)%2 else len(curv)-2)
        curv = savgol_filter(curv, window_length=wl, polyorder=2, mode='interp')
    curv_mag = np.abs(curv)
    
    states = compute_states(gps)
    
    # align origin at first movement
    valid = np.where(speed_mph>0)[0]
    start = valid[0] if valid.size>0 else 0
    x0, y0 = gps.at[start,'x'], gps.at[start,'y']
    xs = gps['x']-x0; ys = gps['y']-y0
    
    # build segments
    pts = np.vstack([xs, ys]).T
    segs = np.stack([pts[:-1], pts[1:]], axis=1)
    
    # set up 2x2 figure
    fig, axes = plt.subplots(2,2, figsize=(12,12))
    titles = ['Speed (mph)','Acceleration (m/s²)','Curvature Magnitude (1/m)','FSM State']
    # Speed
    ax = axes[0,0]
    sp = speed_mph.values[1:]
    norm_sp = Normalize(vmin=np.nanpercentile(sp,5), vmax=np.nanpercentile(sp,95))
    lc = LineCollection(segs, cmap='viridis', norm=norm_sp, linewidth=4)
    lc.set_array(sp); ax.add_collection(lc)
    fig.colorbar(lc, ax=ax, label='mph')
    ax.set_title(titles[0])
    # Accel
    ax = axes[0,1]
    ac = accel_smooth[1:]
    norm_ac = TwoSlopeNorm(vmin=np.nanpercentile(ac,5), vcenter=0, vmax=np.nanpercentile(ac,95))
    lc = LineCollection(segs, cmap='RdYlGn', norm=norm_ac, linewidth=4)
    lc.set_array(ac); ax.add_collection(lc)
    fig.colorbar(lc, ax=ax, label='m/s²')
    ax.set_title(titles[1])
    # Curvature
    ax = axes[1,0]
    cm = curv_mag[1:]
    norm_cm = Normalize(vmin=0, vmax=np.nanpercentile(cm,95))
    lc = LineCollection(segs, cmap='viridis', norm=norm_cm, linewidth=4)
    lc.set_array(cm); ax.add_collection(lc)
    fig.colorbar(lc, ax=ax, label='1/m')
    ax.set_title(titles[2])
    # FSM State
    ax = axes[1,1]
    st = states[1:]
    cmap_st = ListedColormap(['#00FFFF', '#0000FF', '#FF00FF'])
    norm_st = BoundaryNorm([0,1,2,3], cmap_st.N)
    lc = LineCollection(segs, cmap=cmap_st, norm=norm_st, linewidth=4)
    lc.set_array(st); ax.add_collection(lc)
    cbar = fig.colorbar(lc, ax=ax, ticks=[0.5,1.5,2.5])
    cbar.set_ticklabels(['0','1','2']); cbar.set_label('State')
    ax.set_title(titles[3])
    
    # common formatting
    for ax in axes.flat:
        ax.plot(0,0,'o',color='red',markersize=6)
        ax.set_aspect('equal','box')
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(os.path.basename(run), fontsize=16)
    plt.tight_layout(rect=[0,0,1,0.96])
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize speed, acceleration, curvature, and FSM")
    parser.add_argument('filenames', nargs='+', help='CSV files to process')
    args = parser.parse_args()
    for f in args.filenames:
        plot_all_metrics(f)