import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from data_fetcher import fetch_tle_data, load_satellites
from propagator import generate_time_grid, compute_positions
from detector import find_conjunctions

app = Flask(__name__, static_folder='frontend')
CORS(app)

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/detect', methods=['POST'])
def run_detection():
    data = request.json or {}
    
    group = data.get('group', 'starlink')
    duration = int(data.get('duration', 60))
    step = int(data.get('step', 60))
    threshold = float(data.get('threshold', 20.0))
    limit = int(data.get('limit', 500))
    
    try:
        # 1. Fetch
        file_path = fetch_tle_data(group)
        sats, ts = load_satellites(file_path)
        
        if limit and len(sats) > limit:
            sats = sats[:limit]
            
        # 2. Propagate
        t_start = ts.now()
        t_array = generate_time_grid(t_start, duration_minutes=duration, step_seconds=step)
        positions = compute_positions(sats, t_array)
        
        # We also need satellite data (positions) to visualize
        # For sending to frontend, we just need the positions at t=0 so Globe.gl can plot the satellites initially.
        # It's better to pass orbital elements or a small subset of positions for visualization.
        
        # 3. Detect
        conjunctions = find_conjunctions(sats, t_array, positions, threshold_km=threshold)
        
        # Sort and limit
        conjunctions = sorted(conjunctions, key=lambda x: x['distance_km'])
        
        # We need satellite locations *at the time of conjunction* to draw arcs between them on the globe!
        # find_conjunctions returns sat names and time. Let's augment the return in API to include
        # approximate coordinates for visualization.
        # For simplicity in this endpoint: we just send back the alerts.
        # In a real app we'd map the name back to an index to pull the specific lat/lon.
        
        response = {
            'status': 'success',
            'summary': f'Evaluated {len(sats)} satellites over {duration} mins.',
            'conjunctions': conjunctions[:50], # Send top 50
            'total_satellites': len(sats),
            'start_time': t_start.utc_strftime()
        }
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/satellites', methods=['GET'])
def get_satellites():
    """Returns initial positions of satellites to populate the Globe."""
    group = request.args.get('group', 'starlink')
    limit = int(request.args.get('limit', 500))
    
    try:
        file_path = fetch_tle_data(group)
        sats, ts = load_satellites(file_path)
        if limit and len(sats) > limit:
            sats = sats[:limit]
            
        t_start = ts.now()
        
        # Calculate lat/lon/alt for the initial state for scattering on the globe
        sat_data = []
        for sat in sats:
            geocentric = sat.at(t_start)
            subpoint = geocentric.subpoint()
            sat_data.append({
                'name': sat.name,
                'lat': subpoint.latitude.degrees,
                'lng': subpoint.longitude.degrees,
                'alt': subpoint.elevation.km / 6371.0 # normalize altitude
            })
            
        return jsonify({
            'status': 'success',
            'satellites': sat_data
        })
    except Exception as e:
         return jsonify({'status': 'error', 'message': str(e)}), 500
         
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
