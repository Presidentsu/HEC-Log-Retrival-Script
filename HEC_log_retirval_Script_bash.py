import requests
from uuid import uuid4
from time import time
import json
import csv
import re
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

def save_logs_to_txt(events, host):
    """
    Saves logs to a .txt file.
    """
    with open("HEC_log.txt", "a") as file:
        for event in events.get('responseData', []):
            # Adjust the entity link if needed
            event['entityLink'] = adjust_entity_link(event.get('entityLink', ''), host)
        file.write(json.dumps(events, indent=4))
        file.write("\n")  # Add a newline for better separation between appends
    print("Events successfully appended to 'HEC_log.txt'.")

def save_logs_to_csv(events, host):
    """
    Saves logs to a .csv file.
    """
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
                        
            print("Events successfully appended to 'HEC_log.csv'.")
        except Exception as e:
            print(f"An error occurred while saving to CSV: {e}")

def main():
    # Take user input
    client_id = input("Enter your Client ID: ")
    access_key = input("Enter your Access Key: ")
    start_date = input("Enter the start date (ISO 8601 format, e.g., 2024-01-01T00:00:00Z): ")
    end_date = input("Enter the end date (ISO 8601 format, e.g., 2024-01-31T23:59:59Z): ")
    host = input("Enter the host (e.g., 'cloudinfra-gw-us.portal.checkpoint.com'): ")
    output_format = input("Enter the output format ('txt' or 'csv'): ").strip().lower()

    # Create the API client
    client = ApiClient(client_id, access_key, host)

    # Query events within the specified date range
    try:
        events = client.query_events(start_date, end_date)
        # Save the logs in the specified format
        if output_format == 'txt':
            save_logs_to_txt(events, host)
        elif output_format == 'csv':
            save_logs_to_csv(events, host)
        else:
            print("Invalid output format. Please specify 'txt' or 'csv'.")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
