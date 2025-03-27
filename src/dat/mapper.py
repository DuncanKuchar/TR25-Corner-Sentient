import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def forward_propagate(arr):
    most_recent_number = 0
    for i in range(len(arr)):
        if np.isnan(arr[i]):
            arr[i] = most_recent_number
        else:
            most_recent_number = arr[i]
        #print(arr[i])
    valid = arr
    return valid

def process_csv(filename):
    # Load CSV file
    df = pd.read_csv(filename, usecols=["Interval", "WSFR", "Yaw"])
    
    # Extract columns as arrays
    interval = df["Interval"].to_numpy()
    wsfr = df["WSFR"].to_numpy()
    yaw = df["Yaw"].to_numpy()
    
    # Forward propagation for NaN values
    wsfr = forward_propagate(wsfr)
    yaw = forward_propagate(yaw)
    
    # Create x_pos and y_pos arrays of zeros
    x_pos = np.zeros(42546)
    y_pos = np.zeros(42546)
    psi = np.zeros(42546)
    
    # Remove first 310 values from each relevant array
    interval = interval[310:]
    wsfr = wsfr[310:]
    yaw = yaw[310:]
    #yaw = yaw - 1.2
    
    # Save arrays to CSV for inspection
    output_df = pd.DataFrame({
        "Interval": interval,
        "WSFR": wsfr,
        "Yaw": yaw,
        "X_Pos": x_pos,
        "Y_Pos": y_pos
    })
    output_df.to_csv("processed_data.csv", index=False)
    
    return interval, wsfr, yaw, x_pos, y_pos, psi

def plot_position(interval, wsfr, yaw, x_pos, y_pos, psi):
    # 1mph = 0.44704 m/s
    dt = 0.020
    for i in range(len(interval) - 1):
        #print("WS = ", wsfr[i])
        #print("YAW = ", yaw[i])
        psi[i+1] = psi[i] + yaw[i]*dt
        #y_pos[i+1] = y_pos[i] + wsfr[i]*0.44704*math.cos(math.radians(psi[i]))*dt
        #x_pos[i+1] = x_pos[i] + wsfr[i]*0.44704*math.sin(math.radians(psi[i]))*dt
        y_pos[i+1] = y_pos[i] + wsfr[i]*0.44704*math.cos((psi[i]))*dt
        x_pos[i+1] = x_pos[i] + wsfr[i]*0.44704*math.sin((psi[i]))*dt
    # Save arrays to CSV for inspection
    output_df = pd.DataFrame({
        "Interval": interval,
        "WSFR": wsfr,
        "Yaw": yaw,
        "X_Pos": x_pos,
        "Y_Pos": y_pos
    })
    output_df.to_csv("processed_data.csv", index=False)

    # Create a plot
    plt.plot(x_pos, y_pos, label="Position", color='b', marker='o')  # Plot with label, blue color, and circle markers

    # Add labels and title
    plt.xlabel("X Axis")
    plt.ylabel("Y Axis")
    plt.title("X vs Y Plot")

    # Add a grid
    plt.grid(True)

    # Show the legend
    plt.legend()

    # Display the plot
    plt.show()

    timesteps = 40000  # Number of timesteps
    dt = 0.000001  # Time per step in seconds

    # Create figure and axis
    fig, ax = plt.subplots()
    ax.set_xlim(-200, 200)
    ax.set_ylim(-200, 200)
    ax.set_xlabel("X Position")
    ax.set_ylabel("Y Position")
    ax.set_title("Moving Red Dot with Trail")

    # Create the red dot and trail
    dot, = ax.plot([], [], 'ro', markersize=8)  # Red dot
    trail, = ax.plot([], [], 'r-', alpha=0.5)   # Red trail

    # Ensure x and y are lists
    x_data, y_data = [], []

    # Update function for animation
    def update(frame):
        print(x_pos[frame], y_pos[frame])
        x_data.append(float(x_pos[frame]))  # Store past x positions
        y_data.append(float(y_pos[frame]))  # Store past y positions
        #print(x_data, y_data)
        
        dot.set_data([x_pos[frame]], [y_pos[frame]])  # Move dot
        trail.set_data(x_data, y_data)  # Update trail
        #print(dot, trail)
        return dot, trail

    # Create animation
    ani = animation.FuncAnimation(fig, update, frames=len(x_pos), interval=dt * 1000, blit=False)

    # Show the animation
    plt.show()



# Run the function
filepath = "C:/Users/dunca/Documents/TerpsRacing/ActiveAerodynamicsProcessing/TR25-Corner-Sentient/src/eamon.csv"
interval, wsfr, yaw, x_pos, y_pos, psi = process_csv(filepath)
plot_position(interval, wsfr, yaw, x_pos, y_pos, psi)

