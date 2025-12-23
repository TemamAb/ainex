#!/usr/bin/env python3
"""
AINEON Elite Dashboard - Flask Application
Serves the complete HTML dashboard with all analytics features
"""

from flask import Flask, render_template, jsonify, send_file, request
import os
import datetime
import json
from threading import Thread
import time

app = Flask(__name__)

# Global variables for real-time data
dashboard_data = {
    "total_profit": 135200,
    "profit_per_hour": 125.50,
    "profit_per_trade": 8.75,
    "trades_per_hour": 14.3,
    "success_rate": 94.7,
    "ai_learning": 87.3,
    "uptime_days": 247,
    "optimizations_today": 96,
    "last_update": datetime.datetime.now().isoformat()
}

@app.route('/')
def index():
    """Serve the main dashboard HTML"""
    # Priority order for dashboard files
    html_files = [
        'aineon_master_dashboard_local.html',
        'master_dashboard.html',
        'master_dashboard_final.html'
    ]
    
    for html_file in html_files:
        if os.path.exists(html_file):
            return send_file(html_file)
    
    # Fallback to index if no dashboard found
    return "Dashboard file not found. Please ensure aineon_master_dashboard_local.html exists."

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "AINEON Elite Dashboard"
    })

@app.route('/api/data')
def api_data():
    """API endpoint for dashboard data"""
    return jsonify(dashboard_data)

@app.route('/api/update', methods=['POST'])
def update_data():
    """Update dashboard data"""
    try:
        data = request.get_json()
        dashboard_data.update(data)
        dashboard_data["last_update"] = datetime.datetime.now().isoformat()
        return jsonify({"status": "success", "data": dashboard_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

def simulate_real_time_updates():
    """Simulate real-time data updates"""
    while True:
        try:
            # Simulate small variations in metrics
            import random
            
            # Update profit metrics with small variations
            dashboard_data["total_profit"] += random.uniform(-100, 200)
            dashboard_data["profit_per_hour"] += random.uniform(-2, 3)
            dashboard_data["trades_per_hour"] += random.uniform(-1, 2)
            
            # Update AI metrics
            dashboard_data["ai_learning"] += random.uniform(-0.5, 1.0)
            dashboard_data["ai_learning"] = max(0, min(100, dashboard_data["ai_learning"]))
            
            dashboard_data["last_update"] = datetime.datetime.now().isoformat()
            
            time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            print(f"Update error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    # Start real-time update thread
    update_thread = Thread(target=simulate_real_time_updates, daemon=True)
    update_thread.start()
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 AINEON Elite Dashboard starting on port {port}")
    print(f"📊 Dashboard available at: http://0.0.0.0:{port}")
    print(f"💚 Health check: http://0.0.0.0:{port}/health")
    
    app.run(host='0.0.0.0', port=port, debug=False)
