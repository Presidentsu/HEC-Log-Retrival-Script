import requests
from uuid import uuid4
from time import time
import json
from typing import List

class ApiClient:
    def __init__(self, client_id: str, access_key: str, host: str, api_version: str = 'v1.0'):
        self.client_id = client_id
        self.access_key = access_key
        self.token = None
        self.token_expiry = None
        self.host = host
        self.api_version = api_version

    def should_refresh_token(self):
        return not self.token or time() >= self.token_expiry

    def generate_authorization_token(self):
        """
        Perform authentication and return access token.
        """
        if self.should_refresh_token():
            payload = {
                "clientId": self.client_id,
                "accessKey": self.access_key
            }
            timestamp = time()
            res = requests.post(f'https://{self.host}/auth/external', json=payload)
            res.raise_for_status()
            res_data = res.json()['data']
            self.token = res_data['token']
            self.token_expiry = timestamp + res_data['expiresIn']
        return self.token

    def headers(self):
        """
        Generate request headers with authorization token.
        """
        token = self.generate_authorization_token()
        request_id = str(uuid4())
        headers = {
            'Authorization': f'Bearer {token}',
            'x-av-req-id': request_id
        }
        return headers

    def call_api(self, method: str, endpoint: str, params: dict = None, body: dict = None):
        """
        Perform call to the Harmony Email & Collaboration Smart API.
        """
        res = requests.request(
            method, 
            f'https://{self.host}/app/hec-api/{self.api_version}/{endpoint}',
            headers=self.headers(), 
            params=params, 
            json=body
        )
        res.raise_for_status()
        return res.json()

    def query_events(self, start_date: str, end_date: str = None):
        """
        Query Security Events for a given date range.
        """
        request_data = {
            'startDate': start_date,
            'endDate': end_date
        }
        payload = {
            'requestData': request_data
        }
        return self.call_api('POST', 'event/query', body=payload)

def main():
    # Take user input
    client_id = input("Enter your Client ID: ")
    access_key = input("Enter your Access Key: ")
    start_date = input("Enter the start date (ISO 8601 format, e.g., 2024-01-01T00:00:00Z): ")
    end_date = input("Enter the end date (ISO 8601 format, e.g., 2024-01-31T23:59:59Z): ")

    # Define the host based on your region
    # Choose one of the following:
    # host = 'cloudinfra-gw.portal.checkpoint.com'  # EU
    # host = 'cloudinfra-gw-us.portal.checkpoint.com'  # US
    # host = 'cloudinfra-gw.ap.portal.checkpoint.com'  # AU
    host = input("Enter the host (e.g., 'cloudinfra-gw-us.portal.checkpoint.com'): ")

    # Create the API client
    client = ApiClient(client_id, access_key, host)

    # Query events within the specified date range
    try:
        events = client.query_events(start_date, end_date)
        # Append the parsed events to the file in a readable format
        with open("HEC_log.txt", "a") as file:
            file.write(json.dumps(events, indent=4))
            file.write("\n")  # Add a newline for better separation between appends
        print("Events successfully appended to 'HEC_log.txt'.")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
