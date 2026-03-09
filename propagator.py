import numpy as np
from skyfield.api import load
from datetime import timedelta

def generate_time_grid(start_time, duration_minutes=60, step_seconds=60):
    """
    Generates a list of Skyfield Time objects from a start time
    for a given duration with a specific time step.
    """
    ts = load.timescale()
    
    # Generate array of time deltas
    time_deltas = [timedelta(seconds=i*step_seconds) for i in range(0, int(duration_minutes*60/step_seconds))]
    times = [start_time + delta for delta in time_deltas]
    
    # Create an array of Skyfield Time objects natively using the timescale
    t_array = ts.utc([t.utc_datetime() for t in times])
    return t_array

def compute_positions(satellites, time_array):
    """
    Computes the GCRS (Geocentric Celestial Reference System) positions of a list of satellites
    over a given array of times.
    
    Args:
        satellites: list of Skyfield EarthSatellite objects
        time_array: Skyfield Time array object
        
    Returns:
        positions: numpy array of shape (num_satellites, num_time_steps, 3) representing (x, y, z) in km.
    """
    num_sats = len(satellites)
    num_times = len(time_array)
    
    positions = np.zeros((num_sats, num_times, 3))
    
    print(f"Propagating orbits for {num_sats} satellites over {num_times} time steps...")
    
    for i, sat in enumerate(satellites):
        # Resulting position is a (3, num_times) numpy array of GCRS X,Y,Z coordinates in km
        # e.g. sat.at(time_array).position.km
        pos = sat.at(time_array).position.km
        # Transpose to (num_times, 3) and store
        positions[i] = pos.T
        
    print("Propagation complete.")
    return positions

if __name__ == "__main__":
    from data_fetcher import fetch_tle_data, load_satellites
    
    # Test propagation
    file_path = fetch_tle_data('starlink')
    sats, ts = load_satellites(file_path)
    
    # Take first 50 sats to test quickly
    test_sats = sats[:50]
    
    # 10 minutes, 1 minute steps (10 steps)
    t_start = ts.now()
    t_array = generate_time_grid(t_start, duration_minutes=10, step_seconds=60)
    
    pos = compute_positions(test_sats, t_array)
    print(f"Computed positions shape: {pos.shape}")
