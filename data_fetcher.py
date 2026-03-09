import os
import requests
from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite

CELESTRAK_URLS = {
    'active': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle',
    'starlink': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle',
    'iridium': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-NEXT&FORMAT=tle',
}

def fetch_tle_data(group='active', output_dir='data'):
    """Fetches TLE data from CelesTrak for a given group."""
    if group not in CELESTRAK_URLS:
        raise ValueError(f"Unknown TLE group: {group}. Options are {list(CELESTRAK_URLS.keys())}")
    
    url = CELESTRAK_URLS[group]
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f'{group}.txt')
    
    print(f"Downloading {group} TLE data from CelesTrak...")
    response = requests.get(url)
    response.raise_for_status()
    
    with open(file_path, 'w') as f:
        f.write(response.text)
        
    print(f"Saved to {file_path}")
    return file_path

def load_satellites(file_path):
    """Loads Skyfield EarthSatellite objects from a TLE file."""
    # Skyfield provides a convenient method to load TLE files
    ts = load.timescale()
    satellites = load.tle_file(file_path)
    print(f"Loaded {len(satellites)} satellites from {file_path}")
    return satellites, ts

if __name__ == "__main__":
    # Test downloading and parsing Starlink as a smaller test set
    file_path = fetch_tle_data('starlink')
    sats, ts = load_satellites(file_path)
    if sats:
        print(f"First satellite: {sats[0].name}")
