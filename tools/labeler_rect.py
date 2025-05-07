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

    # Define bounding-box regions
    regions = {
        'straight': {'xmin': -10, 'xmax':  60, 'ymin':  -5, 'ymax':   5},
        'corner':   {'xmin':  10, 'xmax':  30, 'ymin': -40, 'ymax': -10},
        'slalom':   {'xmin': -50, 'xmax': -20, 'ymin':  20, 'ymax':  50},
        'hairpin':   {'xmin': -20, 'xmax': 0, 'ymin':  20, 'ymax':  50},
    }

    all_gps['label'] = 'unlabeled'
    origin_x, origin_y = all_gps['x'].iloc[0], all_gps['y'].iloc[0]
    for name, b in regions.items():
        mask = (
            (all_gps['x'] - origin_x >= b['xmin']) & (all_gps['x'] - origin_x  <= b['xmax']) &
            (all_gps['y'] - origin_y >= b['ymin']) & (all_gps['y'] - origin_y  <= b['ymax'])
        )
        all_gps.loc[mask, 'label'] = name

    # Plot with axes labeled
    plt.figure(figsize=(10,8))

    color_map = {
        'straight': 'yellow',
        'corner':   'red',
        'slalom':   'blue',
        'hairpin':  'green',
        'unlabeled': 'gray'
    }

    for region, color in color_map.items():
        pts = all_gps[all_gps['label'] == region]
        plt.scatter(pts['x']-origin_x, pts['y']-origin_y,
                    s=5, c=color, label=region, alpha=0.4)
        
    for name, box in regions.items():
        color = color_map.get(name)
        rect_x = [box['xmin'], box['xmax'], box['xmax'], box['xmin'], box['xmin']]
        rect_y = [box['ymin'], box['ymin'], box['ymax'], box['ymax'], box['ymin']]
        plt.plot(rect_x, rect_y, 'b--', color = color)
    
    if args.output_folder is not None:
        if args.output_file.endswith('csv'):
            all_gps.to_csv(os.path.join(args.output_folder, args.output_file))
        elif args.output_file.endswith('xlsx'):
            all_gps.to_excel(os.path.join(args.output_folder, args.output_file))

    plt.gca().set_aspect('equal', 'box')
    plt.xlabel('X (m)')
    plt.ylabel('Y (m)')
    plt.title('Overlay of runs with Bounding-Box Labels')
    plt.legend(title='Region')
    plt.grid(True)
    plt.tight_layout()

    if args.show_plot == 'y':
        plt.show()

if __name__ == "__main__":
    parser = argp.ArgumentParser(description="Process log data from an folder file")
    parser.add_argument("-i", "--input_folder", required=True, help = "Path to the input folder")
    parser.add_argument("-o", "--output_folder", required=False, help = "Path to the output folder")
    parser.add_argument("-t", "--output_file", required=False, help = "filename")
    parser.add_argument("-s", "--show_plot", required=False, help = "show plot", choices = ['y', 'n'])
    args = parser.parse_args()
    main(args)