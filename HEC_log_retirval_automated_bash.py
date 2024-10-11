import requests
import logging
from uuid import uuid4
from time import time, sleep
import json
import csv
import re
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

def extract_recipient(description):
    """
    Extracts the recipient's email from the description using a regular expression.
    """
    match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", description)
    return match.group(1) if match else ""

def adjust_entity_link(entity_link, host):
    """
    Adjusts the entity link based on the provided host.
    If the host is 'cloudinfra-gw.in.portal.checkpoint.com', replace 'portal.checkpoint.com'
    in the entity link with 'in.portal.checkpoint.com'.
    """
    if host == 'cloudinfra-gw.in.portal.checkpoint.com' and 'portal.checkpoint.com' in entity_link:
        return entity_link.replace('portal.checkpoint.com', 'in.portal.checkpoint.com')
    return entity_link


def save_logs_to_txt(events, end_date, host):
    with open("HEC_log.txt", "a") as file:
        for event in events.get('responseData', []):
            # Adjust the entity link if needed
            event['entityLink'] = adjust_entity_link(event.get('entityLink', ''), host)
        file.write(json.dumps(events, indent=4))
        file.write("\n")
    logging.info(f"Events successfully appended to 'HEC_log.txt' at {end_date}.")

def save_logs_to_csv(events, end_date, host):
    response_data = events.get('responseData', [])
    
    if response_data:
        try:
            with open("HEC_log.csv", "a", newline='') as file:
                writer = csv.writer(file)
                # Write the header if the file is empty
                if file.tell() == 0:
                    writer.writerow([
                        "eventId", 
                        "customerId", 
                        "saas", 
                        "entityId", 
                        "state", 
                        "type", 
                        "confidenceIndicator", 
                        "eventCreated", 
                        "severity", 
                        "description", 
                        "senderAddress", 
                        "data",
                        "recipients",
                        "entityLink", 
                        "actionType", 
                        "actionCreateTime", 
                        "actionRelatedEntityId"
                    ])
                
                for event in response_data:
                    description = event.get('description', '')
                    recipients = extract_recipient(description)
                    entity_link = adjust_entity_link(event.get('entityLink', ''), host)
                    
                    base_data = [
                        event.get('eventId', ''),
                        event.get('customerId', ''),
                        event.get('saas', ''),
                        event.get('entityId', ''),
                        event.get('state', ''),
                        event.get('type', ''),
                        event.get('confidenceIndicator', ''),
                        event.get('eventCreated', ''),
                        event.get('severity', ''),
                        description,
                        event.get('senderAddress', ''),
                        json.dumps(event.get('data', '')),
                        recipients,
                        entity_link
                    ]

                    actions = event.get('actions', [])
                    if actions:
                        for action in actions:
                            writer.writerow(base_data + [
                                action.get('actionType', ''),
                                action.get('createTime', ''),
                                action.get('relatedEntityId', '')
                            ])
                    else:
                        writer.writerow(base_data + ['', '', ''])
                        
            logging.info(f"Events successfully appended to 'HEC_log.csv' at {end_date}.")
        except PermissionError as e:
            logging.error(f"Failed to write to log.csv due to permission error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while saving logs: {e}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch events from Harmony API.')
    parser.add_argument('--client-id', required=True, help='Your Client ID')
    parser.add_argument('--access-key', required=True, help='Your Access Key')
    parser.add_argument('--host', required=True, help='API Host (e.g., cloudinfra-gw-us.portal.checkpoint.com)')
    parser.add_argument('--output-format', required=True, choices=['txt', 'csv'], help='Output format: txt or csv')
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
            if args.output_format == 'txt':
                save_logs_to_txt(events, end_date)
            elif args.output_format == 'csv':
                save_logs_to_csv(events, end_date)
        except Exception as e:
            logging.error(f"An error occurred: {e}")

        # Wait for 5 minutes before the next execution
        sleep(300)

if __name__ == "__main__":
    main()
