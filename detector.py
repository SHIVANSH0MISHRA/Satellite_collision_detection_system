import numpy as np
from scipy.spatial.distance import pdist, squareform

def find_conjunctions(satellites, time_array, positions, threshold_km=10.0):
    """
    Finds close approaches (conjunctions) between satellites.
    
    Args:
        satellites: list of Skyfield EarthSatellite objects
        time_array: Skyfield Time array object
        positions: numpy array (num_sats, num_times, 3) 
        threshold_km: maximum distance in km to be considered a conjunction
        
    Returns:
        conjunctions: list of dicts with keys: 
           'sat1', 'sat2', 'time', 'distance'
    """
    num_sats, num_times, _ = positions.shape
    conjunctions = []
    
    # Iterate over time steps.
    # We could vectorize over time, but memory usage would be high for many satellites.
    # A time-step loop is memory efficient and pdist is fast in C.
    for t_idx in range(num_times):
        # pos_at_t is (num_sats, 3)
        pos_at_t = positions[:, t_idx, :]
        time_obj = time_array[t_idx]
        
        # Calculate pairwise distances (flattened upper triangle)
        # Returns a condensed distance matrix of shape (num_sats * (num_sats - 1) / 2,)
        distances = pdist(pos_at_t)
        
        # Find indices where distance < threshold
        close_indices = np.where(distances < threshold_km)[0]
        
        if len(close_indices) > 0:
            # We need to map 1D condensed indices back to (i, j) 2D indices
            # squareform is heavy for large matrices, we can use a helper to convert index
            for idx in close_indices:
                i, j = condensed_to_square(idx, num_sats)
                dist = distances[idx]
                conjunctions.append({
                    'sat1': satellites[i].name,
                    'sat2': satellites[j].name,
                    'time': time_obj.utc_strftime(),
                    'distance_km': dist
                })
                
    return conjunctions

def condensed_to_square(condensed_index, n):
    """
    Converts a condensed index from pdist to a square matrix index (i, j).
    """
    # Math derivation for inverse of k = n*i - i*(i+1)/2 + j - i - 1
    # i = n - 2 - int(sqrt(-8*k + 4*n*(n-1)-7)/2.0 - 0.5)
    # j = k + i + 1 - n*(n-1)/2 + (n-i)*(n-i-1)/2
    # Simplified approach using numpy:
    b = 1 - 2 * n 
    i = int((-b - np.sqrt(b**2 - 8 * condensed_index)) / 2)
    j = int(condensed_index + i * (b + i + 2) // 2 + 1)
    return i, j

if __name__ == "__main__":
    from data_fetcher import fetch_tle_data, load_satellites
    from propagator import generate_time_grid, compute_positions
    import time

    file_path = fetch_tle_data('starlink')
    sats, ts = load_satellites(file_path)
    
    test_sats = sats[:200]  # Test with 200 satellites (~20k pairs)
    print(f"Testing with {len(test_sats)} satellites.")
    
    t_start = ts.now()
    t_array = generate_time_grid(t_start, duration_minutes=60, step_seconds=60)
    
    start_prop = time.time()
    pos = compute_positions(test_sats, t_array)
    print(f"Propagation took {time.time() - start_prop:.2f} s")
    
    start_det = time.time()
    # Use a large threshold just to see if we catch anything in a small sample
    conjunctions = find_conjunctions(test_sats, t_array, pos, threshold_km=50.0)
    print(f"Detection took {time.time() - start_det:.2f} s")
    
    print(f"Found {len(conjunctions)} conjunctions < 50 km in the next hour.")
    for c in conjunctions[:5]:
        print(f"{c['time']}: {c['sat1']} AND {c['sat2']} at {c['distance_km']:.2f} km")
