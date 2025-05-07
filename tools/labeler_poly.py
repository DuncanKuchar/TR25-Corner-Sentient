import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import TwoSlopeNorm
from matplotlib.path import Path
from scipy.signal import savgol_filter
import argparse as argp
import os


def tupleSub(tlist, tsub):
    result = []
    for t in tlist:
        result.append(tuple(map(lambda i, j: i - j, t, tsub)))
    return result

def main(args):
    # Runs to plot separately
    folder_path = args.input_folder 

    frames = []
    originals = []
    for filename in os.listdir(folder_path):
        run = os.path.join(folder_path, filename)
        if os.path.isfile(run):  # Ensure it's a file, not a subdirectory
            df = pd.read_csv(run)
            gps = df.dropna(subset=['Latitude', 'Longitude']).copy()
            gps['run'] = filename.replace('.csv', '')
            frames.append(gps)
    all_gps = pd.concat(frames, ignore_index=True)

    lat0 = all_gps['Latitude'].mean()
    lon0 = all_gps['Longitude'].mean()
    m_lat = 111132.92 - 559.82*np.cos(2*np.deg2rad(lat0)) + 1.175*np.cos(4*np.deg2rad(lat0))
    m_lon = 111412.84*np.cos(np.deg2rad(lat0)) - 93.5*np.cos(3*np.deg2rad(lat0))
    all_gps['x'] = (all_gps['Longitude'] - lon0) * m_lon
    all_gps['y'] = (all_gps['Latitude'] - lat0) * m_lat

    origin_x, origin_y = all_gps['x'].iloc[0], all_gps['y'].iloc[0]

    # Define bounding-box regions
    regions = {
        'straight': [
            (-50, -40), 
            (-10, -50), 
            (-20, 10)
        ],
        'hairpin': [
            (5, -20), 
            (15, -20), 
            (15, -5), 
            (5, -5)
        ]
    }

    region_paths = {name: Path(tupleSub(verts, (-origin_x, -origin_y))) for name, verts in regions.items()}

    all_gps['label'] = 'unlabeled'

    for name, path in region_paths.items():
        mask = path.contains_points(all_gps[['x', 'y']].values)
        all_gps.loc[mask, 'label'] = name

    # Plot with axes labeled
    fig, ax = plt.subplots(figsize=(10,8))

    color_map = {
        'straight': 'purple',
        'corner':   'red',
        'slalom':   'blue',
        'hairpin':  'green',
        'unlabeled': 'lightgray'
    }

    scatters = {}
    for region, color in color_map.items():
        pts = all_gps[all_gps['label'] == region]
        sc = plt.scatter(pts['x']-origin_x, pts['y']-origin_y,
                    s=5, c=color, label=region, alpha=0.4)
        scatters[region] = sc
        
    for name, verts in regions.items():
        poly = np.array(verts + [verts[0]])
        plt.plot(poly[:,0], poly[:,1], linestyle='--', color= color_map[name], lw=2)
    
    if args.output_folder is not None:
        if args.output_file.endswith('csv'):
            all_gps.to_csv(os.path.join(args.output_folder, args.output_file))
        elif args.output_file.endswith('xlsx'):
            all_gps.to_excel(os.path.join(args.output_folder, args.output_file))

    plt.gca().set_aspect('equal', 'box')
    plt.xlabel('X (m)')
    plt.ylabel('Y (m)')
    plt.title('Overlay of runs with polygonal bounding labels')
    plt.legend(title='Region')
    plt.grid(True)
    plt.tight_layout()

    annot = ax.annotate(
        "", xy=(0,0), xytext=(10,10), textcoords="offset points",
        bbox=dict(boxstyle="round", fc="w"),
        arrowprops=dict(arrowstyle="->")
    )
    annot.set_visible(False)

    def update_annot(sc, ind, region):
        x,y = sc.get_offsets()[ind["ind"][0]]
        annot.xy = (x, y)
        annot.set_text(f"{region}\nX: {x:.1f}\nY: {y:.1f}")

    def hover(event):
        visible = annot.get_visible()
        if event.inaxes == ax:
            for region, sc in scatters.items():
                cont, ind = sc.contains(event)
                if cont:
                    update_annot(sc, ind, region)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
            if visible:
                annot.set_visible(False)
                fig.canvas.draw_idle()

    if args.show_plot == 'y':
        fig.canvas.mpl_connect("motion_notify_event", hover)
        plt.show()

if __name__ == "__main__":
    parser = argp.ArgumentParser(description="Process log data from an folder file")
    parser.add_argument("-i", "--input_folder", required=True, help = "Path to the input folder")
    parser.add_argument("-o", "--output_folder", required=False, help = "Path to the output folder")
    parser.add_argument("-t", "--output_file", required=False, help = "filename")
    parser.add_argument("-s", "--show_plot", required=False, help = "show plot", choices = ['y', 'n'])
    args = parser.parse_args()
    main(args)