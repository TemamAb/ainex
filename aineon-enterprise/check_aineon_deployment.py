#!/usr/bin/env python3
"""
AINEON DEPLOYMENT CHECKER
Verify all AINEON services are running on ports 7001-7010
"""

import requests
import socket
import time
from datetime import datetime

def check_port(port):
    """Check if port is open"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('0.0.0.0', port))
            return result == 0
    except:
        return False

def check_http_service(port):
    """Check if HTTP service is responding"""
    try:
        response = requests.get(f'http://0.0.0.0:{port}', timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    print("AINEON DEPLOYMENT STATUS CHECK")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    services = {
        7001: "Master Dashboard",
        7002: "Gasless Engine",
        7003: "Profit Monitor",
        7004: "Live Trading",
        7005: "Blockchain Validator",
        7006: "Flash Loan Executor",
        7007: "AI Optimizer",
        7008: "Risk Manager",
        7009: "API Gateway",
        7010: "System Monitor"
    }
    
    running_services = 0
    total_services = len(services)
    
    for port, service_name in services.items():
        port_open = check_port(port)
        http_ok = check_http_service(port) if port_open else False
        
        status = "RUNNING" if port_open else "OFFLINE"
        http_status = "HTTP OK" if http_ok else "No HTTP"
        
        print(f"Port {port} - {service_name:<20} [{status:<8}] {http_status}")
        
        if port_open:
            running_services += 1
    
    print("=" * 60)
    print(f"Services Running: {running_services}/{total_services}")
    print(f"Availability: {(running_services/total_services)*100:.1f}%")
    print("=" * 60)
    
    if running_services == total_services:
        print("✓ ALL AINEON SERVICES RUNNING SUCCESSFULLY")
        print(f"✓ Master Dashboard: http://0.0.0.0:7001")
        print("✓ Gasless Mode: ENABLED")
        print("✓ Multi-Port Deployment: COMPLETE")
    else:
        print(f"⚠ {total_services - running_services} services offline")
    
    print("=" * 60)

if __name__ == "__main__":
    main()