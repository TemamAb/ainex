#!/usr/bin/env python3
"""
AINEON SMART DASHBOARD LAUNCHER
Intelligent dashboard launcher with automatic failover and health monitoring

Automatically selects the best available dashboard:
1. Primary: master_dashboard.html (if available)
2. Backup: master_dashboard_backup.py (if HTML fails)
3. Emergency: backup_dashboard.html (static backup)
4. Fallback: emergency_dashboard.py (terminal ASCII)

Usage:
    python dashboard_launcher.py
    python dashboard_launcher.py --force-backup
    python dashboard_launcher.py --emergency
"""

import os
import sys
import time
import subprocess
import threading
import signal
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import webbrowser
import http.server
import socketserver
from datetime import datetime

# Configuration
class LauncherConfig:
    """Smart Launcher Configuration"""
    PRIMARY_DASHBOARD = "master_dashboard.html"
    BACKUP_DASHBOARD = "master_dashboard_backup.py"
    EMERGENCY_DASHBOARD = "backup_dashboard.html"
    FALLBACK_DASHBOARD = "emergency_dashboard.py"
    
    # Health check settings
    HEALTH_CHECK_INTERVAL = 30  # seconds
    DASHBOARD_TIMEOUT = 10      # seconds
    MAX_RETRIES = 3
    
    # Port settings
    PRIMARY_PORT = 8080
    BACKUP_PORT = 8081
    EMERGENCY_PORT = 8082
    
    # URLs
    PRIMARY_URL = f"http://0.0.0.0:{PRIMARY_PORT}"
    BACKUP_URL = f"http://0.0.0.0:{BACKUP_PORT}"
    EMERGENCY_URL = f"http://0.0.0.0:{EMERGENCY_PORT}"

class HealthMonitor:
    """Health monitoring for dashboard services"""
    
    def __init__(self):
        self.services = {}
        self.monitoring = False
        self.logger = self.setup_logging()
    
    def setup_logging(self) -> logging.Logger:
        """Setup logging for the health monitor"""
        logger = logging.getLogger('HealthMonitor')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def check_http_service(self, url: str, timeout: int = 5) -> bool:
        """Check if HTTP service is responding"""
        try:
            import urllib.request
            import urllib.error
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'AINEON-Dashboard-Health-Check/1.0')
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.getcode() == 200
        except Exception as e:
            self.logger.debug(f"Health check failed for {url}: {e}")
            return False
    
    def check_process(self, pid: int) -> bool:
        """Check if process is still running"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def register_service(self, name: str, url: str = None, pid: int = None):
        """Register a service for monitoring"""
        self.services[name] = {
            'url': url,
            'pid': pid,
            'last_check': None,
            'status': 'unknown',
            'failures': 0
        }
    
    def start_monitoring(self):
        """Start health monitoring"""
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                for name, service in self.services.items():
                    try:
                        # Check HTTP service
                        if service['url']:
                            is_healthy = self.check_http_service(service['url'])
                        # Check process
                        elif service['pid']:
                            is_healthy = self.check_process(service['pid'])
                        else:
                            is_healthy = False
                        
                        service['last_check'] = datetime.now()
                        
                        if is_healthy:
                            if service['status'] != 'healthy':
                                self.logger.info(f"✅ {name} is now healthy")
                            service['status'] = 'healthy'
                            service['failures'] = 0
                        else:
                            service['failures'] += 1
                            if service['status'] != 'unhealthy':
                                self.logger.warning(f"❌ {name} is unhealthy ({service['failures']} failures)")
                            service['status'] = 'unhealthy'
                    
                    except Exception as e:
                        self.logger.error(f"Error checking {name}: {e}")
                        service['status'] = 'error'
                        service['failures'] += 1
                
                time.sleep(LauncherConfig.HEALTH_CHECK_INTERVAL)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        self.logger.info("🔍 Health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring = False
        self.logger.info("🔍 Health monitoring stopped")
    
    def get_service_status(self, name: str) -> Dict:
        """Get status of specific service"""
        return self.services.get(name, {'status': 'unknown'})
    
    def get_all_status(self) -> Dict:
        """Get status of all services"""
        return self.services.copy()

class DashboardLauncher:
    """Smart dashboard launcher with failover capabilities"""
    
    def __init__(self):
        self.current_dashboard = None
        self.current_process = None
        self.health_monitor = HealthMonitor()
        self.logger = self.setup_logging()
        self.start_time = time.time()
    
    def setup_logging(self) -> logging.Logger:
        """Setup logging for the launcher"""
        logger = logging.getLogger('DashboardLauncher')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def print_banner(self):
        """Print launcher banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                   🚀 AINEON SMART DASHBOARD LAUNCHER          ║
║                   Elite-Grade Dashboard System               ║
║                                                              ║
║  🎯 Automatic Failover    📊 Real-time Monitoring            ║
║  🔄 Health Checks         🛡️  Redundancy System             ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_file_exists(self, filename: str) -> bool:
        """Check if dashboard file exists"""
        return Path(filename).exists()
    
    def start_html_dashboard(self, port: int = LauncherConfig.PRIMARY_PORT) -> Optional[subprocess.Popen]:
        """Start HTML dashboard with built-in HTTP server"""
        if not self.check_file_exists(LauncherConfig.PRIMARY_DASHBOARD):
            self.logger.error(f"❌ Primary dashboard not found: {LauncherConfig.PRIMARY_DASHBOARD}")
            return None
        
        try:
            # Create simple HTTP server for HTML dashboard
            os.chdir(Path.cwd())
            
            class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
                def end_headers(self):
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    super().end_headers()
                
                def log_message(self, format, *args):
                    pass  # Suppress HTTP request logs
            
            httpd = socketserver.TCPServer(("", port), DashboardHTTPRequestHandler)
            
            # Start server in background thread
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()
            
            self.logger.info(f"🌐 HTML Dashboard started on port {port}")
            self.health_monitor.register_service('html_dashboard', f"http://0.0.0.0:{port}")
            
            return httpd
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start HTML dashboard: {e}")
            return None
    
    def start_python_dashboard(self, port: int = LauncherConfig.BACKUP_PORT) -> Optional[subprocess.Popen]:
        """Start Python backup dashboard"""
        if not self.check_file_exists(LauncherConfig.BACKUP_DASHBOARD):
            self.logger.error(f"❌ Backup dashboard not found: {LauncherConfig.BACKUP_DASHBOARD}")
            return None
        
        try:
            env = os.environ.copy()
            env['DASHBOARD_PORT'] = str(port)
            env['DASHBOARD_DEBUG'] = 'False'
            
            process = subprocess.Popen([
                sys.executable, 
                LauncherConfig.BACKUP_DASHBOARD
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment for startup
            time.sleep(3)
            
            if process.poll() is None:
                self.logger.info(f"🐍 Python Dashboard started on port {port}")
                self.health_monitor.register_service('python_dashboard', f"http://0.0.0.0:{port}", process.pid)
                return process
            else:
                stdout, stderr = process.communicate()
                self.logger.error(f"❌ Python dashboard failed to start: {stderr.decode()}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start Python dashboard: {e}")
            return None
    
    def start_emergency_dashboard(self, port: int = LauncherConfig.EMERGENCY_PORT) -> Optional[subprocess.Popen]:
        """Start emergency static dashboard"""
        if not self.check_file_exists(LauncherConfig.EMERGENCY_DASHBOARD):
            self.logger.warning(f"⚠️ Emergency dashboard not found: {LauncherConfig.EMERGENCY_DASHBOARD}")
            return None
        
        try:
            os.chdir(Path.cwd())
            
            class EmergencyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
                def end_headers(self):
                    self.send_header('Cache-Control', 'no-cache')
                    super().end_headers()
                
                def log_message(self, format, *args):
                    pass
            
            httpd = socketserver.TCPServer(("", port), EmergencyHTTPRequestHandler)
            
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()
            
            self.logger.info(f"🚨 Emergency Dashboard started on port {port}")
            self.health_monitor.register_service('emergency_dashboard', f"http://0.0.0.0:{port}")
            
            return httpd
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start emergency dashboard: {e}")
            return None
    
    def try_launch_primary(self) -> Tuple[bool, str, object]:
        """Try to launch primary HTML dashboard"""
        self.logger.info("🎯 Attempting to launch PRIMARY dashboard...")
        
        dashboard = self.start_html_dashboard()
        if dashboard:
            url = LauncherConfig.PRIMARY_URL
            self.logger.info(f"✅ PRIMARY dashboard launched successfully!")
            self.logger.info(f"🔗 Access URL: {url}")
            
            # Auto-open browser after delay
            threading.Timer(2.0, lambda: webbrowser.open(url)).start()
            
            return True, url, dashboard
        
        return False, None, None
    
    def try_launch_backup(self) -> Tuple[bool, str, object]:
        """Try to launch backup Python dashboard"""
        self.logger.info("🔄 PRIMARY failed, attempting BACKUP dashboard...")
        
        dashboard = self.start_python_dashboard()
        if dashboard:
            url = LauncherConfig.BACKUP_URL
            self.logger.info(f"✅ BACKUP dashboard launched successfully!")
            self.logger.info(f"🔗 Access URL: {url}")
            
            threading.Timer(2.0, lambda: webbrowser.open(url)).start()
            
            return True, url, dashboard
        
        return False, None, None
    
    def try_launch_emergency(self) -> Tuple[bool, str, object]:
        """Try to launch emergency dashboard"""
        self.logger.info("🚨 BACKUP failed, attempting EMERGENCY dashboard...")
        
        dashboard = self.start_emergency_dashboard()
        if dashboard:
            url = LauncherConfig.EMERGENCY_URL
            self.logger.info(f"✅ EMERGENCY dashboard launched successfully!")
            self.logger.info(f"🔗 Access URL: {url}")
            
            threading.Timer(2.0, lambda: webbrowser.open(url)).start()
            
            return True, url, dashboard
        
        return False, None, None
    
    def launch_dashboard(self, force_mode: str = None) -> bool:
        """Launch dashboard with automatic failover"""
        self.print_banner()
        
        # Determine launch mode
        if force_mode == 'backup':
            self.logger.info("🔧 Forced backup mode selected")
            success, url, dashboard = self.try_launch_backup()
        elif force_mode == 'emergency':
            self.logger.info("🔧 Forced emergency mode selected")
            success, url, dashboard = self.try_launch_emergency()
        else:
            # Automatic failover sequence
            self.logger.info("🚀 Starting automatic dashboard selection...")
            
            # Try primary first
            success, url, dashboard = self.try_launch_primary()
            
            # If primary fails, try backup
            if not success:
                success, url, dashboard = self.try_launch_backup()
            
            # If backup fails, try emergency
            if not success:
                success, url, dashboard = self.try_launch_emergency()
        
        if success:
            self.current_dashboard = dashboard
            self.current_url = url
            
            # Start health monitoring
            self.health_monitor.start_monitoring()
            
            self.logger.info("🎉 Dashboard launch completed successfully!")
            self.print_dashboard_info(url)
            
            return True
        else:
            self.logger.error("❌ All dashboard launch attempts failed!")
            self.logger.error("💡 Manual recovery options:")
            self.logger.error("   1. Check if dashboard files exist")
            self.logger.error("   2. Install required dependencies: pip install flask flask-socketio")
            self.logger.error("   3. Run manually: python master_dashboard_backup.py")
            
            return False
    
    def print_dashboard_info(self, url: str):
        """Print dashboard information"""
        uptime = time.time() - self.start_time
        
        info = f"""
╔══════════════════════════════════════════════════════════════╗
║                      🎯 DASHBOARD LAUNCHED                    ║
╠══════════════════════════════════════════════════════════════╣
║  🔗 Dashboard URL: {url:<47} ║
║  🕐 Launch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<47} ║
║  ⏱️  Uptime: {uptime:.1f} seconds{'':<40} ║
╠══════════════════════════════════════════════════════════════╣
║  📊 Features Available:                                     ║
║     • Real-time profit monitoring                           ║
║     • Integrated withdrawal system                          ║
║     • Engine status tracking                                ║
║     • Market data analytics                                 ║
║     • Settings & configuration                              ║
╠══════════════════════════════════════════════════════════════╣
║  🛡️  Redundancy System:                                     ║
║     • Primary: HTML Dashboard (Port 8080)                   ║
║     • Backup: Python Dashboard (Port 8081)                  ║
║     • Emergency: Static Dashboard (Port 8082)               ║
║     • Auto-failover: Enabled                                ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(info)
    
    def monitor_dashboard(self):
        """Monitor dashboard health and handle failover"""
        self.logger.info("🔍 Starting dashboard health monitoring...")
        
        while True:
            try:
                # Check if dashboard is still healthy
                if hasattr(self, 'current_url'):
                    is_healthy = self.health_monitor.check_http_service(self.current_url)
                    
                    if not is_healthy:
                        self.logger.warning(f"⚠️ Dashboard at {self.current_url} is unhealthy, initiating failover...")
                        
                        # Try to restart current dashboard
                        self.restart_dashboard()
                
                time.sleep(LauncherConfig.HEALTH_CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(5)
    
    def restart_dashboard(self):
        """Restart current dashboard"""
        try:
            self.logger.info("🔄 Attempting dashboard restart...")
            
            # Kill current process if Python dashboard
            if self.current_process and hasattr(self.current_process, 'pid'):
                try:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
            
            # Try to relaunch
            time.sleep(2)
            success, url, dashboard = self.try_launch_primary()
            
            if not success:
                success, url, dashboard = self.try_launch_backup()
            
            if success:
                self.current_dashboard = dashboard
                self.current_url = url
                self.logger.info("✅ Dashboard restarted successfully")
            else:
                self.logger.error("❌ Dashboard restart failed")
                
        except Exception as e:
            self.logger.error(f"❌ Restart error: {e}")
    
    def shutdown(self):
        """Shutdown launcher and dashboard"""
        self.logger.info("🛑 Shutting down dashboard launcher...")
        
        # Stop health monitoring
        self.health_monitor.stop_monitoring()
        
        # Kill dashboard process if Python
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
        
        self.logger.info("✅ Shutdown completed")
    
    def run_interactive(self):
        """Run launcher in interactive mode"""
        try:
            # Launch dashboard
            if not self.launch_dashboard():
                return False
            
            # Monitor dashboard
            self.monitor_dashboard()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            return False
        finally:
            self.shutdown()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AINEON Smart Dashboard Launcher')
    parser.add_argument('--force-backup', action='store_true', 
                       help='Force launch backup Python dashboard')
    parser.add_argument('--emergency', action='store_true',
                       help='Force launch emergency dashboard')
    parser.add_argument('--test', action='store_true',
                       help='Test dashboard availability without launching')
    parser.add_argument('--status', action='store_true',
                       help='Show dashboard status and health')
    
    args = parser.parse_args()
    
    launcher = DashboardLauncher()
    
    if args.test:
        # Test dashboard availability
        print("🧪 Testing dashboard availability...")
        
        dashboards = [
            (LauncherConfig.PRIMARY_DASHBOARD, "Primary HTML"),
            (LauncherConfig.BACKUP_DASHBOARD, "Backup Python"),
            (LauncherConfig.EMERGENCY_DASHBOARD, "Emergency HTML")
        ]
        
        for filename, name in dashboards:
            exists = launcher.check_file_exists(filename)
            status = "✅ Available" if exists else "❌ Missing"
            print(f"   {name}: {status}")
        
        return
    
    if args.status:
        # Show status
        monitor = HealthMonitor()
        print("📊 Dashboard Status:")
        
        services = monitor.get_all_status()
        for name, service in services.items():
            status = service.get('status', 'unknown')
            last_check = service.get('last_check')
            check_time = last_check.strftime('%H:%M:%S') if last_check else 'Never'
            print(f"   {name}: {status} (Last check: {check_time})")
        
        return
    
    # Launch dashboard
    force_mode = None
    if args.force_backup:
        force_mode = 'backup'
    elif args.emergency:
        force_mode = 'emergency'
    
    success = launcher.launch_dashboard(force_mode=force_mode)
    
    if success:
        print("\n🎯 Dashboard is now running!")
        print("📝 To stop: Press Ctrl+C")
        print("🔧 For help: python dashboard_launcher.py --help")
        
        try:
            # Keep running and monitor
            launcher.run_interactive()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
    else:
        print("\n❌ Failed to launch dashboard")
        print("💡 Try manual launch: python master_dashboard_backup.py")
        sys.exit(1)

if __name__ == "__main__":
    main()