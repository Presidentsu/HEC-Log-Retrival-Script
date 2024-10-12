import requests
from uuid import uuid4
from time import time, sleep
import json
import csv
import argparse
import logging
import syslog
import os
import re
from datetime import datetime, timedelta

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
            res = requests.post(f'https://{self.host}/auth/external', json=payload)
            res.raise_for_status()
            res_data = res.json()['data']
            self.token = res_data['token']
            self.token_expiry = timestamp + res_data['expiresIn']
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
        request_data = {
            'startDate': start_date,
            'endDate': end_date
        }
        payload = {
            'requestData': request_data
        }
        return self.call_api('POST', 'event/query', body=payload)


# Helper function to extract recipient from the description
def extract_recipient(description):
    match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", description)
    return match.group(1) if match else ""

# Helper function to adjust the entity link based on the host
def adjust_entity_link(entity_link, host):
    if host == 'cloudinfra-gw.in.portal.checkpoint.com' and 'portal.checkpoint.com' in entity_link:
        return entity_link.replace('portal.checkpoint.com', 'in.portal.checkpoint.com')
    return entity_link

# Function to save logs to TXT
def save_to_txt(log_data, file_path, append=True):
    mode = 'a' if append else 'w'
    with open(file_path, mode) as file:
        file.write(json.dumps(log_data, indent=4))
        file.write("\n")
    print(f"Logs appended to {file_path}")

# Function to save logs to CSV
def save_to_csv(log_data, file_path, host, append=True):
    mode = 'a' if append else 'w'
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode, newline='') as file:
        writer = csv.writer(file)
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

        for event in log_data.get('responseData', []):
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

    print(f"Logs appended to {file_path}")

# Function to send logs to syslog
def save_to_syslog(log_data):
    for event in log_data.get('responseData', []):
        message = f"Event ID: {event.get('eventId')}, Data: {json.dumps(event)}"
        syslog.syslog(syslog.LOG_INFO, message)
    print("Logs sent to syslog")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch events from Harmony API and log them.')
    parser.add_argument('--client-id', required=True, help='Your Client ID')
    parser.add_argument('--access-key', required=True, help='Your Access Key')
    parser.add_argument('--host', required=True, help='API Host (e.g., cloudinfra-gw-us.portal.checkpoint.com)')
    parser.add_argument('--file-type', choices=['txt', 'csv', 'syslog'], required=True, help='Choose file type for log output')
    parser.add_argument('--output-file', required=False, help='File path to save logs (required for txt/csv output)')
    args = parser.parse_args()

    # Create the API client with command-line arguments
    client = ApiClient(args.client_id, args.access_key, args.host)

    # Check if output file is needed (txt/csv)
    if args.file_type in ['txt', 'csv'] and not args.output_file:
        raise ValueError("You must provide an output file path for txt or csv file type.")

    # Continuously run every 5 minutes
    while True:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)

        start_date = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_date = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"Querying events from {start_date} to {end_date}...")

        try:
            events = client.query_events(start_date, end_date)

            # Save logs based on the file type
            if args.file_type == 'txt':
                save_to_txt(events, args.output_file)
            elif args.file_type == 'csv':
                save_to_csv(events, args.output_file, args.host)
            elif args.file_type == 'syslog':
                save_to_syslog(events)

            print(f"Events successfully logged in {args.file_type} format.")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

        # Wait for 5 minutes before the next execution
        sleep(300)

if __name__ == "__main__":
    main()
