"""
AINEON Enterprise Python SDK Example
"""

import requests
import json
from typing import Dict, List, Optional

class AINEONClient:
    def __init__(self, api_key: str, base_url: str = "https://api.ainex.enterprise/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "AINEON-Python-SDK/1.0.0"
        })
    
    def get_health(self) -> Dict:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_transactions(self, limit: int = 50, offset: int = 0, wallet: Optional[str] = None) -> Dict:
        """Get transactions with pagination"""
        params = {"limit": limit, "offset": offset}
        if wallet:
            params["wallet"] = wallet
        
        response = self.session.get(f"{self.base_url}/transactions", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_wallet(self, address: str) -> Dict:
        """Get wallet details"""
        response = self.session.get(f"{self.base_url}/wallets/{address}")
        response.raise_for_status()
        return response.json()
    
    def execute_flash_loan(self, amount: str, token: str, protocol: str, strategy: Optional[str] = None) -> Dict:
        """Execute flash loan"""
        data = {
            "amount": amount,
            "token": token,
            "protocol": protocol
        }
        if strategy:
            data["strategy"] = strategy
        
        response = self.session.post(f"{self.base_url}/flash-loans", json=data)
        response.raise_for_status()
        return response.json()
    
    def screen_wallet(self, address: str, providers: Optional[List[str]] = None) -> Dict:
        """Screen wallet for compliance"""
        data = {"address": address}
        if providers:
            data["providers"] = providers
        
        response = self.session.post(f"{self.base_url}/compliance/screen", json=data)
        response.raise_for_status()
        return response.json()
    
    def generate_report(self, report_type: str, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None, format: str = "pdf") -> Dict:
        """Generate institutional report"""
        data = {"type": report_type, "format": format}
        if start_date:
            data["startDate"] = start_date
        if end_date:
            data["endDate"] = end_date
        
        response = self.session.post(f"{self.base_url}/reports/generate", json=data)
        response.raise_for_status()
        return response.json()

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = AINEONClient(api_key="your_api_key_here")
    
    # Check API health
    health = client.get_health()
    print(f"API Status: {health['status']}")
    
    # Get wallet information
    wallet = client.get_wallet("0x742d35Cc6634C0532925a3b844Bc9e98D3E9c6b3")
    print(f"Wallet Balance: {wallet.get('balance')}")
    
    # Screen wallet for compliance
    screening = client.screen_wallet("0x742d35Cc6634C0532925a3b844Bc9e98D3E9c6b3")
    print(f"Risk Score: {screening.get('riskScore')}")
    print(f"Risk Level: {screening.get('riskLevel')}")
    
    # Generate monthly report
    report = client.generate_report("monthly")
    print(f"Report Generated: {report.get('reportId')}")
    print(f"Download URL: {report.get('url')}")
