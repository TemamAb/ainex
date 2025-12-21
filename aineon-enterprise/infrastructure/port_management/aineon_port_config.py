#!/usr/bin/env python3
"""
AINEON Port Management Configuration System
==============================================

Enterprise-grade port configuration management for AINEON arbitrage engine.
Provides centralized configuration, validation, and deployment of port allocations.

Chief Architect: AINEON Enterprise Port Management
Version: 1.0.0
"""

import json
import os
import logging
import socket
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PortCategory(Enum):
    """Port categories for AINEON system"""
    ENGINE_PRIMARY = "engine_primary"
    FLASH_LOAN_SYSTEM = "flash_loan_system"
    MONITORING_SYSTEM = "monitoring_system"
    WEB_INTERFACE = "web_interface"
    API_GATEWAY = "api_gateway"
    DATA_LAYER = "data_layer"
    MEV_PROTECTION = "mev_protection"
    DEPLOYMENT_SYSTEM = "deployment_system"
    BACKUP_SYSTEM = "backup_system"

@dataclass
class PortAllocation:
    """Port allocation configuration"""
    service_name: str
    port: int
    category: PortCategory
    priority: int
    description: str
    protocol: str = "TCP"
    is_active: bool = True
    last_validated: Optional[str] = None
    failover_ports: List[int] = None

    def __post_init__(self):
        if self.failover_ports is None:
            self.failover_ports = []

class AINEONPortConfig:
    """
    AINEON Port Configuration Management System
    ===========================================
    
    Centralized configuration and deployment system for AINEON port allocations.
    Provides validation, deployment, and monitoring capabilities.
    """
    
    def __init__(self, config_dir: str = "infrastructure/port_management"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "aineon_port_allocations.json"
        self.deployment_file = self.config_dir / "aineon_port_deployment.yaml"
        self.validation_log = self.config_dir / "port_validation.log"
        
        # Port allocation matrix
        self.port_allocations: Dict[str, PortAllocation] = {}
        
        # Active ports tracking
        self.active_ports: Set[int] = set()
        self.reserved_ports: Set[int] = set()
        
        # Load existing configuration
        self._load_configuration()
        
        # Initialize default port matrix
        self._initialize_port_matrix()
    
    def _load_configuration(self):
        """Load existing port configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for service_name, allocation_data in data.items():
                        allocation_data['category'] = PortCategory(allocation_data['category'])
                        self.port_allocations[service_name] = PortAllocation(**allocation_data)
                logger.info(f"Loaded {len(self.port_allocations)} port allocations")
            else:
                logger.info("No existing configuration found, will create default matrix")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def _initialize_port_matrix(self):
        """Initialize the complete AINEON port allocation matrix"""
        if not self.port_allocations:
            # Engine Primary Ports
            self._add_allocation("engine_1_api", 8001, PortCategory.ENGINE_PRIMARY, 1, "Engine 1 REST API")
            self._add_allocation("engine_1_websocket", 8002, PortCategory.ENGINE_PRIMARY, 1, "Engine 1 WebSocket")
            self._add_allocation("engine_1_grpc", 8003, PortCategory.ENGINE_PRIMARY, 1, "Engine 1 gRPC")
            self._add_allocation("engine_2_api", 8005, PortCategory.ENGINE_PRIMARY, 1, "Engine 2 REST API")
            self._add_allocation("engine_2_websocket", 8006, PortCategory.ENGINE_PRIMARY, 1, "Engine 2 WebSocket")
            self._add_allocation("engine_2_grpc", 8007, PortCategory.ENGINE_PRIMARY, 1, "Engine 2 gRPC")
            
            # Flash Loan System Ports
            self._add_allocation("aave_connector", 8101, PortCategory.FLASH_LOAN_SYSTEM, 2, "Aave Protocol Connector")
            self._add_allocation("dydx_connector", 8102, PortCategory.FLASH_LOAN_SYSTEM, 2, "dYdX Protocol Connector")
            self._add_allocation("balancer_connector", 8103, PortCategory.FLASH_LOAN_SYSTEM, 2, "Balancer Protocol Connector")
            self._add_allocation("uniswap_connector", 8104, PortCategory.FLASH_LOAN_SYSTEM, 2, "Uniswap Protocol Connector")
            self._add_allocation("flash_loan_orchestrator", 8105, PortCategory.FLASH_LOAN_SYSTEM, 1, "Flash Loan Orchestrator")
            
            # Monitoring System Ports
            self._add_allocation("profit_tracker", 8301, PortCategory.MONITORING_SYSTEM, 1, "Real-time Profit Tracker")
            self._add_allocation("performance_monitor", 8302, PortCategory.MONITORING_SYSTEM, 1, "Performance Monitor")
            self._add_allocation("alert_manager", 8303, PortCategory.MONITORING_SYSTEM, 1, "Alert Manager")
            self._add_allocation("metrics_exporter", 8304, PortCategory.MONITORING_SYSTEM, 1, "Metrics Exporter")
            
            # Web Interface Ports
            self._add_allocation("main_dashboard", 8401, PortCategory.WEB_INTERFACE, 1, "Main Dashboard")
            self._add_allocation("admin_panel", 8402, PortCategory.WEB_INTERFACE, 1, "Admin Panel")
            self._add_allocation("profit_viewer", 8403, PortCategory.WEB_INTERFACE, 1, "Profit Viewer")
            
            # API Gateway Ports
            self._add_allocation("api_gateway", 8501, PortCategory.API_GATEWAY, 1, "API Gateway")
            self._add_allocation("auth_service", 8502, PortCategory.API_GATEWAY, 1, "Authentication Service")
            
            # Data Layer Ports
            self._add_allocation("redis_cache", 8601, PortCategory.DATA_LAYER, 1, "Redis Cache")
            self._add_allocation("postgres_db", 8602, PortCategory.DATA_LAYER, 1, "PostgreSQL Database")
            self._add_allocation("elasticsearch", 8603, PortCategory.DATA_LAYER, 1, "Elasticsearch")
            
            # MEV Protection Ports
            self._add_allocation("mev_protection", 8701, PortCategory.MEV_PROTECTION, 1, "MEV Protection Service")
            self._add_allocation("mempool_monitor", 8702, PortCategory.MEV_PROTECTION, 1, "Mempool Monitor")
            
            # Deployment System Ports
            self._add_allocation("deployment_api", 8801, PortCategory.DEPLOYMENT_SYSTEM, 1, "Deployment API")
            self._add_allocation("container_registry", 8802, PortCategory.DEPLOYMENT_SYSTEM, 1, "Container Registry")
            
            # Backup System Ports
            self._add_allocation("backup_service", 8901, PortCategory.BACKUP_SYSTEM, 1, "Backup Service")
            self._add_allocation("log_aggregator", 8902, PortCategory.BACKUP_SYSTEM, 1, "Log Aggregator")
            
            logger.info(f"Initialized port matrix with {len(self.port_allocations)} allocations")
    
    def _add_allocation(self, service_name: str, port: int, category: PortCategory, 
                       priority: int, description: str, failover_ports: List[int] = None):
        """Add a port allocation to the matrix"""
        allocation = PortAllocation(
            service_name=service_name,
            port=port,
            category=category,
            priority=priority,
            description=description,
            failover_ports=failover_ports or []
        )
        self.port_allocations[service_name] = allocation
        self.reserved_ports.add(port)
    
    def save_configuration(self):
        """Save current configuration to file"""
        try:
            config_data = {}
            for service_name, allocation in self.port_allocations.items():
                allocation_dict = asdict(allocation)
                allocation_dict['category'] = allocation.category.value
                config_data[service_name] = allocation_dict
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def validate_port_availability(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('', port))
                return True
        except OSError:
            return False
    
    def deploy_configuration(self) -> Dict[str, bool]:
        """Deploy port configuration and validate all allocations"""
        deployment_results = {}
        
        logger.info("Starting AINEON port configuration deployment...")
        
        for service_name, allocation in self.port_allocations.items():
            if not allocation.is_active:
                continue
                
            # Validate port availability
            is_available = self.validate_port_availability(allocation.port)
            
            # Check failover ports if primary is not available
            if not is_available and allocation.failover_ports:
                for failover_port in allocation.failover_ports:
                    if self.validate_port_availability(failover_port):
                        allocation.port = failover_port
                        is_available = True
                        break
            
            deployment_results[service_name] = is_available
            
            if is_available:
                self.active_ports.add(allocation.port)
                allocation.last_validated = datetime.now().isoformat()
                logger.info(f"✓ {service_name}: Port {allocation.port} - DEPLOYED")
            else:
                logger.warning(f"✗ {service_name}: Port {allocation.port} - FAILED")
        
        # Save updated configuration
        self.save_configuration()
        
        # Generate deployment report
        self._generate_deployment_report(deployment_results)
        
        return deployment_results
    
    def _generate_deployment_report(self, results: Dict[str, bool]):
        """Generate deployment report"""
        report_file = self.config_dir / "deployment_report.json"
        
        report = {
            "deployment_timestamp": datetime.now().isoformat(),
            "total_services": len(results),
            "successful_deployments": sum(1 for success in results.values() if success),
            "failed_deployments": sum(1 for success in results.values() if not success),
            "success_rate": sum(1 for success in results.values() if success) / len(results) * 100,
            "deployment_details": results,
            "active_ports": list(self.active_ports),
            "reserved_ports": list(self.reserved_ports)
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Deployment report saved to {report_file}")
    
    def get_port_by_service(self, service_name: str) -> Optional[PortAllocation]:
        """Get port allocation by service name"""
        return self.port_allocations.get(service_name)
    
    def get_ports_by_category(self, category: PortCategory) -> List[PortAllocation]:
        """Get all ports by category"""
        return [alloc for alloc in self.port_allocations.values() if alloc.category == category]
    
    def generate_docker_compose(self) -> str:
        """Generate Docker Compose configuration with port mappings"""
        compose_config = {
            "version": "3.8",
            "services": {},
            "networks": {
                "aineon_network": {
                    "driver": "bridge"
                }
            }
        }
        
        # Add services with port mappings
        for service_name, allocation in self.port_allocations.items():
            if not allocation.is_active:
                continue
                
            service_config = {
                "image": f"aineon-{service_name}:latest",
                "container_name": f"aineon-{service_name}",
                "networks": ["aineon_network"],
                "environment": {
                    f"SERVICE_PORT": str(allocation.port),
                    f"SERVICE_NAME": service_name
                }
            }
            
            # Add port mapping
            service_config["ports"] = [f"{allocation.port}:{allocation.port}"]
            
            compose_config["services"][service_name] = service_config
        
        # Generate YAML
        compose_yaml = yaml.dump(compose_config, default_flow_style=False, sort_keys=False)
        return compose_yaml
    
    def get_status_report(self) -> Dict:
        """Generate comprehensive status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_allocations": len(self.port_allocations),
            "active_allocations": len([a for a in self.port_allocations.values() if a.is_active]),
            "categories": {},
            "port_ranges": {},
            "validation_status": {},
            "active_ports": list(self.active_ports),
            "reserved_ports": list(self.reserved_ports)
        }
        
        # Category breakdown
        for category in PortCategory:
            allocations = self.get_ports_by_category(category)
            report["categories"][category.value] = {
                "count": len(allocations),
                "ports": [a.port for a in allocations],
                "services": [a.service_name for a in allocations]
            }
        
        # Port ranges by category
        for category in PortCategory:
            allocations = self.get_ports_by_category(category)
            if allocations:
                ports = [a.port for a in allocations]
                report["port_ranges"][category.value] = {
                    "min_port": min(ports),
                    "max_port": max(ports),
                    "port_count": len(ports)
                }
        
        # Validation status
        for service_name, allocation in self.port_allocations.items():
            is_available = self.validate_port_availability(allocation.port)
            report["validation_status"][service_name] = {
                "port": allocation.port,
                "available": is_available,
                "last_validated": allocation.last_validated
            }
        
        return report
    
    def export_kubernetes_config(self) -> str:
        """Generate Kubernetes deployment configurations"""
        k8s_configs = []
        
        for service_name, allocation in self.port_allocations.items():
            if not allocation.is_active:
                continue
            
            # Service definition
            service_config = f"""
apiVersion: v1
kind: Service
metadata:
  name: aineon-{service_name}
  namespace: aineon-system
spec:
  selector:
    app: aineon-{service_name}
  ports:
  - name: http
    port: {allocation.port}
    targetPort: {allocation.port}
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aineon-{service_name}
  namespace: aineon-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: aineon-{service_name}
  template:
    metadata:
      labels:
        app: aineon-{service_name}
    spec:
      containers:
      - name: {service_name}
        image: aineon-{service_name}:latest
        ports:
        - containerPort: {allocation.port}
        env:
        - name: SERVICE_PORT
          value: "{allocation.port}"
        - name: SERVICE_NAME
          value: "{service_name}"
"""
            k8s_configs.append(service_config)
        
        return "\n---\n".join(k8s_configs)

def main():
    """Main execution function"""
    logger.info("Initializing AINEON Port Configuration System...")
    
    # Initialize configuration manager
    config_manager = AINEONPortConfig()
    
    # Deploy configuration
    deployment_results = config_manager.deploy_configuration()
    
    # Generate comprehensive report
    status_report = config_manager.get_status_report()
    
    # Print deployment summary
    print("\n" + "="*80)
    print("AINEON PORT CONFIGURATION DEPLOYMENT SUMMARY")
    print("="*80)
    print(f"Total Services: {status_report['total_allocations']}")
    print(f"Active Services: {status_report['active_allocations']}")
    print(f"Success Rate: {status_report.get('success_rate', 0):.1f}%")
    print(f"Active Ports: {len(status_report['active_ports'])}")
    print(f"Reserved Ports: {len(status_report['reserved_ports'])}")
    
    print("\nDEPLOYMENT RESULTS:")
    for service, success in deployment_results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {service}: {status}")
    
    print("\nCATEGORY BREAKDOWN:")
    for category, details in status_report['categories'].items():
        print(f"  {category}: {details['count']} services")
    
    # Save deployment report
    report_file = config_manager.config_dir / "status_report.json"
    with open(report_file, 'w') as f:
        json.dump(status_report, f, indent=2)
    
    logger.info(f"Configuration deployment completed. Status report saved to {report_file}")
    
    return config_manager

if __name__ == "__main__":
    main()