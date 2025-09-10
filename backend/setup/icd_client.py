# Enhanced ICD-11 Client with Token Management
# Builds upon your existing setup.py with better error handling and token management

import requests
import base64
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from fastapi import HTTPException

class IcdEndpoint(Enum):
    """
    Enum for ICD API endpoints
    """
    CHECK = '/icd/entity/'
    SEARCH = '/icd/entity/search'
    ENTITY = '/icd/entity'
    AUTO_CODE = '/icd/entity/autocode'
    LINEARIZATION = '/icd/release/11/{releaseId}/{linearizationname}'
    
    def __str__(self):
        return self.value
    
    def format(self, **kwargs):
        """Format the endpoint string with provided arguments"""
        return self.value.format(**kwargs)

class IcdApiClient:
    """
    Enhanced ICD API client with proper authentication and token management
    Builds upon your original design with production-ready features
    """
    
    def __init__(self, 
                 local_base_url: str = "http://localhost",
                 global_base_url: str = "https://id.who.int"):
        
        self.local_base_url = local_base_url
        self.global_base_url = global_base_url
        self.token_endpoint = 'https://icdaccessmanagement.who.int/connect/token'
        
        self.client_id = None
        self.client_secret = None
        # Token management
        self.access_token = None
        self.token_expires = None
             
        # Base headers for all requests
        self.base_headers = {
            "accept": "application/json",
            "API-Version": "v2",
            "Accept-Language": "en"
        }
        # Determine active server
        self.active_base_url = self._get_active_server()
        
    
    def _get_active_server(self) -> str:
        """
        Enhanced server detection with better error handling
        """
        # First try local server
        try:
            response = requests.get(
                f"{self.local_base_url}{IcdEndpoint.CHECK.value}",
                headers=self.base_headers,
                timeout=3,
                verify=False
            )
            if response.status_code in [200, 401]:  # 401 is ok, means server is up but needs auth
                print("✅ Local ICD server found and working")
                return self.local_base_url
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Local server not available: {e}")
        
        # Fallback to global server
        print("🌐 Using global WHO ICD server")
        self.client_id = os.getenv("ICD_CLIENT_ID", "your_client_id")
        self.client_secret = os.getenv("ICD_CLIENT_SECRET", "your_client_secret")
       
        if self.client_id == "your_client_id" or self.client_secret == "your_client_secret": raise HTTPException(
            status_code=500, 
            detail="ICD-11 credentials not configured. Please set ICD_CLIENT_ID and ICD_CLIENT_SECRET environment variables."
        )
        return self.global_base_url
    
    def _get_access_token(self) -> str:
        """
        Token management with automatic refresh
        """
        # Return existing token if still valid
        if (self.access_token and 
            self.token_expires and 
            datetime.now() < self.token_expires):
            return self.access_token
        
        # Get new token
        print("🔑 Requesting new ICD-11 access token...")
        
        # Prepare credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        payload = {
            "grant_type": "client_credentials",
            "scope": "icdapi_access"
        }
        
        try:
            response = requests.post(
                self.token_endpoint, 
                headers=headers, 
                data=payload,
                verify=False
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            
            # Set expiration (subtract 60 seconds for safety margin)
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
            
            print("✅ Successfully obtained ICD-11 access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to obtain ICD-11 access token: {str(e)}"
            )
    
    def get(self, endpoint: IcdEndpoint, params: Dict | None = None, headers: Dict | None = None, **kwargs) -> requests.Response:
        """
        GET method with authentication and error handling
        """

        if not self.active_base_url:
            raise HTTPException(status_code=503, detail="No ICD API server available")
        
        # Build full URL
        full_url = self.active_base_url + endpoint.format(**kwargs)
        
        # Prepare headers
        request_headers = self.base_headers.copy()
        
        # Add authentication for global server
        if self.active_base_url == self.global_base_url:
            token = self._get_access_token()
            request_headers["Authorization"] = f"Bearer {token}"
        
        # Add custom headers
        if headers:
            request_headers.update(headers)
        
        print(f"🌐 Making GET request to: {full_url}")
        
        try:
            response = requests.get(
                full_url, 
                params=params, 
                headers=request_headers,
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"ICD API request failed: {str(e)}"
            )
    
    def search_conditions(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for medical conditions in ICD-11
        """
        params = {
            "q": query,
            "subtreeFilterUsesFoundationDescendants": "false",
            "includeKeywordResult": "false", 
            "useFlexisearch": "true",
            "flatResults": "true",
            "highlightingEnabled": "false",
            " medicalCodingMode": "true",
            "maxList": limit
        }
        
        response = self.get(IcdEndpoint.SEARCH, params=params)
        return response.json()
    
    def get_entity_details(self, entity_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific ICD-11 entity
        """
        # Handle both full URIs and entity IDs
        if entity_id.startswith("http"):
            # Extract entity ID from URI
            entity_id = entity_id.split("/")[-1]
        
        endpoint_path = f"{IcdEndpoint.ENTITY.value}/{entity_id}"
        full_url = self.active_base_url + endpoint_path
        
        request_headers = self.base_headers.copy()
        if self.active_base_url == self.global_base_url:
            token = self._get_access_token()
            request_headers["Authorization"] = f"Bearer {token}"
        
        try:
            response = requests.get(full_url, headers=request_headers, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to get entity details: {str(e)}"
            )
    
    def get_root_categories(self) -> Dict[str, Any]:
        """
        Get main ICD-11 categories/chapters
        """
        response = self.get(IcdEndpoint.LINEARIZATION, releaseId='2025-01', linearizationname='mms')

        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the ICD API connection
        """
        try:
            response = self.get(IcdEndpoint.CHECK)
            return {
                "status": "healthy",
                "server": self.active_base_url,
                "response_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "server": self.active_base_url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
