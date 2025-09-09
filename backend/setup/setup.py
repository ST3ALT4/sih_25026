#This file init the icd and provide icd api
import requests
from enum import Enum

class IcdEndpoint(Enum):
    """
        ENUM for specific icd api as i dont want to hard code it
        in every place
    """
    
    CHECK = '/icd/entity'
    SEARCH = '/icd/entity/search'
    AUTO_CODE = '/icd/entity/autocode'

    def __str__(self):
        return self.value

    def format(self, **kwargs):
        """Format the end point of string with provided argument"""
        return self.value.format(**kwargs)

class IcdApiClient:
    """
        Weather to use the local deployment or global
    """

    def __init__(self, local_base_url, global_base_url):
        self.local_base_url = local_base_url
        self.global_base_url = global_base_url
        self.acitve_base_url = self._get_active_server()

    def _get_active_server(self):
        """
            Checks the working of local server. If found use it,
            Otherwise fall back to global server if local one is 
            unavailable
        """

        try:
            res = requests.get(self.local_base_url+IcdEndpoint.CHECK.value,
                               timeout=2
                               )
            res.raise_for_status()
            print("local host found working")
            return self.local_base_url
        except requests.exceptions.RequestException as e:
            print(f"Error accessing local server: {e}")
            print(f"Falling back to global server")
            return self.global_base_url

    def get(self, endpoint: IcdEndpoint, params=None, headers=None, **kwargs):
        """
            define GET method for active server...
        """
        
        if not self.acitve_base_url:
            raise Exception("Cannot access api server")

        full_url = self.acitve_base_url + endpoint.format(**kwargs)
        print(f"making get request to {full_url}")
        
        header = {
            "Api-Version": "v2",
            "Accept-Language": "en"
        }
        if headers:
            header.update(headers)

        return requests.get(full_url, params=params, headers=header)
