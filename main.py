import argparse
from data_fetcher import fetch_tle_data, load_satellites
from propagator import generate_time_grid, compute_positions
from detector import find_conjunctions
import pandas as pd
import time

def main():
    parser = argparse.ArgumentParser(description="Satellite Collision Detection System")
    parser.add_argument('--group', type=str, default='starlink',
                        help='TLE group to download (active, starlink, iridium)')
    parser.add_argument('--duration', type=int, default=60,
                        help='Duration to simulate in minutes (default 60)')
    parser.add_argument('--step', type=int, default=60,
                        help='Time step in seconds (default 60)')
    parser.add_argument('--threshold', type=float, default=10.0,
                        help='Collision distance threshold in km (default 10.0)')
    parser.add_argument('--limit', type=int, default=1000,
                        help='Limit number of satellites to analyze (for speed)')
    parser.add_argument('--output', type=str, default='conjunctions.csv',
                        help='Output CSV file name')
                        
    args = parser.parse_args()
    
    # 1. Fetch Data
    print(f"\n--- 1. Fetching TLE Data ---")
    start_time = time.time()
    file_path = fetch_tle_data(args.group)
    sats, ts = load_satellites(file_path)
    print(f"Time: {time.time() - start_time:.2f}s")
    
    # Optional limit for testing
    if args.limit and len(sats) > args.limit:
        print(f"Limiting to first {args.limit} satellites from {len(sats)}")
        sats = sats[:args.limit]
        
    # 2. Propagate Orbits
    print(f"\n--- 2. Propagating Orbits ---")
    start_time = time.time()
    t_start = ts.now()
    print(f"Start time (UTC): {t_start.utc_strftime()}")
    t_array = generate_time_grid(t_start, duration_minutes=args.duration, step_seconds=args.step)
    
    positions = compute_positions(sats, t_array)
    print(f"Time: {time.time() - start_time:.2f}s")
    
    # 3. Detect Conjunctions
    print(f"\n--- 3. Detecting Close Approaches ---")
    start_time = time.time()
    conjunctions = find_conjunctions(sats, t_array, positions, threshold_km=args.threshold)
    print(f"Time: {time.time() - start_time:.2f}s")
    
    # 4. Report
    print(f"\n--- 4. Reporting ---")
    if not conjunctions:
        print(f"No conjunctions detected below {args.threshold} km.")
    else:
        df = pd.DataFrame(conjunctions)
        # Sort by distance
        df = df.sort_values('distance_km')
        print(f"Top 10 Closest Approaches (< {args.threshold} km):")
        print(df.head(10).to_string(index=False))
        
        # Save to CSV
        df.to_csv(args.output, index=False)
        print(f"\nSaved all {len(conjunctions)} conjunctions to {args.output}")

if __name__ == "__main__":
    main()
