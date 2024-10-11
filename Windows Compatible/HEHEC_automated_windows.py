import requests
import logging
from uuid import uuid4
from time import time, sleep
import json
from datetime import datetime, timedelta
import argparse

# Configure logging
logging.basicConfig(filename='HEC_log_retrieval.log', 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

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
        if self.should_refresh_token():
            payload = {
                "clientId": self.client_id,
                "accessKey": self.access_key
            }
            timestamp = time()
            try:
                res = requests.post(f'https://{self.host}/auth/external', json=payload, timeout=10)
                res.raise_for_status()
                res_data = res.json()['data']
                self.token = res_data['token']
                self.token_expiry = timestamp + res_data['expiresIn']
                logging.info("Bearer token retrieved successfully.")
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to retrieve bearer token: {e}")
                raise e
        return self.token

    def headers(self):
        token = self.generate_authorization_token()
        request_id = str(uuid4())
        headers = {
            'Authorization': f'Bearer {token}',
            'x-av-req-id': request_id
        }
        return headers

    def call_api(self, method: str, endpoint: str, params: dict = None, body: dict = None):
        try:
            res = requests.request(
                method, 
                f'https://{self.host}/app/hec-api/{self.api_version}/{endpoint}',
                headers=self.headers(), 
                params=params, 
                json=body,
                timeout=10
            )
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            raise e

    def query_events(self, start_date: str, end_date: str = None):
        request_data = {
            'startDate': start_date,
            'endDate': end_date
        }
        payload = {
            'requestData': request_data
        }
        return self.call_api('POST', 'event/query', body=payload)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch events from Harmony API.')
    parser.add_argument('--client-id', required=True, help='Your Client ID')
    parser.add_argument('--access-key', required=True, help='Your Access Key')
    parser.add_argument('--host', required=True, help='API Host (e.g., cloudinfra-gw-us.portal.checkpoint.com)')
    args = parser.parse_args()

    # Create the API client with command-line arguments
    client = ApiClient(args.client_id, args.access_key, args.host)

    # Continuously run every 5 minutes
    while True:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)

        start_date = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_date = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        logging.info(f"Querying events from {start_date} to {end_date}...")

        try:
            events = client.query_events(start_date, end_date)
            if events.get('responseEnvelope', {}).get('recordsNumber', 0) > 0:
                with open("HEC_log.txt", "a") as file:
                    file.write(json.dumps(events, indent=4))
                    file.write("\n")
                logging.info(f"Events successfully appended to 'HEC_log.txt' at {end_date}.")
            else:
                logging.info("No events found for the given time frame. Skipping log write.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

        # Wait for 5 minutes before the next execution
        sleep(300)

if __name__ == "__main__":
    main()
