import requests
import logging
from uuid import uuid4
from time import time
import json
from datetime import datetime, timedelta
import argparse

# Configure logging
logging.basicConfig(
    filename='HEC_log_retrieval.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

def save_logs_to_file(events, end_date):
    # Check if there are any records to write before saving to the file
    if events.get('responseEnvelope', {}).get('recordsNumber', 0) > 0:
        try:
            with open("log_HEC.txt", "a") as file:
                file.write(json.dumps(events, indent=4))
                file.write("\n")
            logging.info(f"Events successfully appended to 'log.txt' at {end_date}.")
        except PermissionError as e:
            logging.error(f"Failed to write to log.txt due to permission error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while saving logs: {e}")
    else:
        logging.info("No events found for the given time frame. Skipping log write.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch events from Harmony API.')
    parser.add_argument('--client-id', required=True, help='Your Client ID')
    parser.add_argument('--access-key', required=True, help='Your Access Key')
    parser.add_argument('--host', required=True, help='API Host (e.g., cloudinfra-gw-us.portal.checkpoint.com)')
    parser.add_argument('--start-time', required=True, help='Start time (ISO 8601 format, e.g., 2024-01-01T00:00:00Z)')
    parser.add_argument('--end-time', required=True, help='End time (ISO 8601 format, e.g., 2024-01-01T05:00:00Z)')
    args = parser.parse_args()

    # Create the API client with command-line arguments
    client = ApiClient(args.client_id, args.access_key, args.host)

    logging.info(f"Querying events from {args.start_time} to {args.end_time}...")

    try:
        events = client.query_events(args.start_time, args.end_time)
        save_logs_to_file(events, args.end_time)
    except Exception as e:
        logging.error(f"An error occurred during log retrieval: {e}")

if __name__ == "__main__":
    main()
