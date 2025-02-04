import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def extract_columns(file_path):
    # Load the CSV file into a pandas DataFrame
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("File not found. Please check the file path.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    # List of columns to extract
    columns_to_extract = [
        "Interval", "AccelX", "AccelY", "AccelZ", "ElapsedTime",
        "FBrakePress", "SteeringAng", "WSFL", "WSFR", "Yaw"
    ]

    # Check if all required columns are present in the DataFrame
    missing_columns = [col for col in columns_to_extract if col not in df.columns]
    if missing_columns:
        print(f"Missing columns in the data frame: {missing_columns}")
        return

    # Extract and save each column as an array
    extracted_arrays = {}
    for column in columns_to_extract:
        extracted_arrays[column] = df[column].to_numpy()
        print(f"{column}: {extracted_arrays[column]}")

    return extracted_arrays

def process_elapsed_time(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("File not found. Please check the file path.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    if "ElapsedTime" not in df.columns:
        print("ElapsedTime column is missing from the data frame.")
        return

    # Create the ElapsedTimeInterpolated array
    elapsed_time = df["ElapsedTime"].to_numpy()
    elapsed_time_interpolated = np.interp(
        np.arange(len(elapsed_time)),
        np.where(~np.isnan(elapsed_time))[0],
        elapsed_time[~np.isnan(elapsed_time)]
    )

    # Create the ElapsedTimeInterpolated_Zeroed array
    elapsed_time_interpolated_zeroed = elapsed_time_interpolated - elapsed_time_interpolated[0]

    # Save ElapsedTimeInterpolated_Zeroed to ElapsedTimeInterpolated_Zeroed.csv
    testing_values3_df = pd.DataFrame({"ElapsedTimeInterpolated_Zeroed": elapsed_time_interpolated_zeroed})
    testing_values3_df.to_csv("ElapsedTimeInterpolated_Zeroed.csv", index=False)

    # Create the ElapsedTimeInterpolated_Seconds array
    elapsed_time_interpolated_seconds = elapsed_time_interpolated_zeroed * 60.0

    # Save ElapsedTimeInterpolated_Seconds to ElapsedTimeInterpolated_Seconds.csv
    testing_values2_df = pd.DataFrame({"ElapsedTimeInterpolated_Seconds": elapsed_time_interpolated_seconds})
    testing_values2_df.to_csv("ElapsedTimeInterpolated_Seconds.csv", index=False)

    

    print("Files have been created.")

def calculate_velocity_and_position(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("File not found. Please check the file path.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    if "Yaw" not in df.columns or "WSFR" not in df.columns:
        print("Yaw or WSFR column is missing from the data frame.")
        return

    # Load and preprocess ElapsedTimeInterpolated_Seconds
    elapsed_time_interpolated_seconds_zeroed = pd.read_csv("ElapsedTimeInterpolated_Seconds.csv")["ElapsedTimeInterpolated_Seconds"].to_numpy()

    # Preprocess Yaw array (replace nan with the previous value)
    yaw = df["Yaw"].to_numpy()
    for i in range(1, len(yaw)):
        if np.isnan(yaw[i]):
            yaw[i] = yaw[i - 1]

    # Preprocess WSFR array (replace nan with the previous value)
    wsfr = df["WSFR"].to_numpy()
    for i in range(1, len(wsfr)):
        if np.isnan(wsfr[i]):
            wsfr[i] = wsfr[i - 1]

    # Create WSFR_mps array
    wsfr_mps = wsfr * 0.44704

    # Save WSFR_mps array to LinearVelocities_mps.csv
    linear_velocities_df = pd.DataFrame({"LinearVelocities_mps": wsfr_mps})
    linear_velocities_df.to_csv("LinearVelocities_mps.csv", index=False)

    # Save Yaw array as AngularVelocities_degrees_per_second.csv
    angular_velocities_df = pd.DataFrame({"AngularVelocities_degrees_per_second": yaw})
    angular_velocities_df.to_csv("AngularVelocities_degrees_per_second.csv", index=False)

    # Calculate Yaw_Static (cumulative angle in radians)
    yaw_static = [0]
    for i in range(1, len(elapsed_time_interpolated_seconds_zeroed)):
        dt = elapsed_time_interpolated_seconds_zeroed[i] - elapsed_time_interpolated_seconds_zeroed[i - 1]
        yaw_change = np.deg2rad(yaw[i]) * dt
        yaw_static.append(yaw_static[-1] + yaw_change)

    yaw_static = np.array(yaw_static)

    # Save Yaw_Static array to Yaw_Static_radians.csv
    yaw_static_df = pd.DataFrame({"Yaw_Static_radians": yaw_static})
    yaw_static_df.to_csv("Yaw_Static_radians.csv", index=False)

    # Calculate position vectors
    position_vectors = [(0, 0)]  # Start at (0, 0)
    for i in range(1, len(elapsed_time_interpolated_seconds_zeroed)):
        dt = elapsed_time_interpolated_seconds_zeroed[i] - elapsed_time_interpolated_seconds_zeroed[i - 1]
        angle = yaw_static[i]  # Use Yaw_Static for the angle
        dx = wsfr_mps[i] * np.cos(angle) * dt
        dy = wsfr_mps[i] * np.sin(angle) * dt
        x, y = position_vectors[-1]
        position_vectors.append((x + dx, y + dy))

    # Save position vectors to PositionVectors.csv
    position_vectors_df = pd.DataFrame(position_vectors, columns=["Position_X", "Position_Y"])
    position_vectors_df.to_csv("PositionVectors.csv", index=False)

    print("Files LinearVelocities_mps.csv, AngularVelocities_degrees_per_second.csv, Yaw_Static_radians.csv, and PositionVectors.csv have been created.")

def plot_position_vectors():
    try:
        # Load position vectors from PositionVectors.csv
        position_vectors_df = pd.read_csv("PositionVectors.csv")
    except FileNotFoundError:
        print("PositionVectors.csv not found. Please ensure it has been created.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    # Extract x and y positions
    x_positions = position_vectors_df["Position_X"].to_numpy()
    y_positions = position_vectors_df["Position_Y"].to_numpy()

    # Plot the position vectors
    plt.figure(figsize=(8, 6))
    plt.plot(x_positions, y_positions, marker="o", linestyle="-", color="b")
    plt.title("Position Vectors")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.grid(True)
    plt.axis("equal")
    plt.show()

def plot_angle_over_time():
    try:
        # Load elapsed time and yaw static data
        elapsed_time_interpolated_seconds_zeroed = pd.read_csv("ElapsedTimeInterpolated_Seconds.csv")["ElapsedTimeInterpolated_Seconds"].to_numpy()
        yaw_static = pd.read_csv("Yaw_Static_radians.csv")["Yaw_Static_radians"].to_numpy()
    except FileNotFoundError:
        print("Required files not found. Please ensure they have been created.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    # Convert yaw_static to degrees for plotting
    yaw_static_degrees = np.rad2deg(yaw_static)

    # Plot yaw_static angle over time
    plt.figure(figsize=(8, 6))
    plt.plot(elapsed_time_interpolated_seconds_zeroed, yaw_static_degrees, marker="o", linestyle="-", color="r")
    plt.title("Yaw Angle Over Time")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Yaw Angle (degrees)")
    plt.grid(True)
    plt.show()

# Example usage:
extracted_data = extract_columns("eamon2.csv")
process_elapsed_time("eamon2.csv")
calculate_velocity_and_position("eamon2.csv")
plot_position_vectors()
plot_angle_over_time()
