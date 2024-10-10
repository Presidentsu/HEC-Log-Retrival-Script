# Harmony Email & Collaboration Log Retrieval Script - Implementation Documentation

## Overview

There are 2 scripts scripts that are present in this repo, one with [HEC_log_retirval_Script.py](HEC_log_retirval_Script.py) is manual where one can get the logs for a specified time by mentioning the Client ID & Access Key (API Key), the other one [HEC_log_retirval_automated.py](HEC_log_retirval_automated.py) will run and pulls logs from console every 5 mins and writes it a file called HEC_log.txt

The 5 min parameter is hardcoded, one can simply edit it out and increase/decrease the number but make sure to not exhaust the API calls nor perform huge write action which can slow down or crash the machine where the script is running so test it manually to and then apply the automated script with relative time counter.

### Prerequisites

- **Python3.x**: Ensure Python 3.x is installed on your system

- `requests` **library**: Install using:

  - ```
        pip install requests
    ```
- **Harmony Email & Collaboration API**
  - `clientID`: Your Harmony API client ID.
  - `accessKey`: The access key (API Key) associated with your client ID.
  - `host`: API URI Host based on your data residecny location
    - `cloudinfra-gw.portal.checkpoint.com` - For those who have it EU
    - `cloudinfra-gw-us.portal.checkpoint.com` - For those who have it in US
    - `cloudinfra-gw.ap.portal.checkpoint.com` - For those who have it in AU
    - `cloudinfra-gw.in.portal.checkpoint.com` - For those who have it in India region

- **Input Parameters**
  - **ClientID**: The client ID for accessing the Harmony API.
  - **accessKey**: The access key associated with your client ID.
  - **host**: The API endpoint URL for your region.
  - **Time Frame**:
    - **Automated**: Automatically calculated as the last 5 minutes from the current time for each execution.
    - **Manual**: Both start & end time needs to be in ISO 8601 format, e.g., `2024-01-01T00:00:00Z` 

### How it works

1. **Authentication**
   - The script uses the provided `clientID` and `accessKey` to authenticate with the Harmony API.
   - retrieves a bearer token, which is refreshed automatically when it expires.

2. **Log Retrieval**:
  - The script calculates the `start_date` as 5 minutes before the current time and the `end_date` as the current time. (For Automated Script)
  - It queries the Harmony API for events within this time range.

3. **Error Handling**
    - Catches HTTP errors and prints messages for troubleshooting.
    - Catches general exceptions to handle unexpected errors during execution.

4. **Automated Execution**:
    - The script runs continuously in a loop with a 5-minute sleep interval.
    - To execute it in the background on Linux or macOS, use `nohup` or a scheduling tool like `cron`.
  
### Running the Script

1. **Clone the Repository** or download the script onto your local machine.

2. **Install Dependencies** using:
   - ```
     pip install requests
     ```
3. **Run the Script** using (**Automated script**):
   - ```
     nohup python3 hec_log_retrieval_automated.py --client-id YOUR_CLIENT_ID --access-key YOUR_ACCESS_KEY --host YOUR_HOST &
     ```
  - Examples
    -  ```
          nohup python3 hec_log_retrieval_automated.py --client-id 123456 --access-key abcdef123456 --host cloudinfra-gw-us.portal.checkpoint.com

       ```
    - **Manual**
    - ```
      pythong3 HEC_log_retrival.py
      ```
    - Post provide the inputs such as `clientID`, `accessKey`, `startTime`, `endtime` & `URI of the host`

## Output

- **Log File**: `HEC_log.txt` is created in the same directory as the script.
  - **PS**: Again one can change the target location by editing the script end section in `main()` function.
 
- Each entry in `HEC_log.txt` is appended with the latest events in JSON format.

**Example Output**

```
{
    "responseEnvelope": {
        "requestId": "9885c6dd-b22e-4ff1-999f-a18f0155fe28",
        "responseCode": 200,
        "recordsNumber": 5,
        "scrollId": null
    },
    "responseData": [
        {
            "eventId": "123456",
            "eventType": "phishing",
            "eventDate": "2024-01-01T12:00:00Z",
            "details": {
                "source": "email",
                "description": "Phishing attempt detected"
            }
        },
        {
            "eventId": "123457",
            "eventType": "malware",
            "eventDate": "2024-01-02T14:30:00Z",
            "details": {
                "source": "attachment",
                "description": "Malware detected in attachment"
            }
        }
    ]
}
```
### How to Stop the Script?

1. If you need to stop the script, follow these instructions:
   - Use the `ps` command to find the `PID` of the running script:
      ```
      ps aux | grep hec_log_retrieval_automated.py
      ```
   - Look for the process ID (PID) associated with hec_log_retrieval_automated.py.
    
2. Kill the Process:
   - Once you have the PID, use the `kill` command to stop the script:
     ```
     kill <PID>
     ```
   - Replace the `<PID>` with above PID
  
   - To force stop add a flag to `kill` i.e. `-9` then mention the `PID`.


## Notes & Issues Noticed Till Now

1. Ensure that the `clientID` and `accessKey` are kept secure and not shared.

2. Make sure the `HEC_log.txt` file or its containing directory has the proper write permissions.

3. In current automated script if in a certain time frame there are no logs it generates an output off:
```
    {
    "responseEnvelope": {
        "requestId": "9885c6dd-b22e-4ff1-999f-a18f0155fe28",
        "responseCode": 200,
        "responseText": "",
        "additionalText": "",
        "recordsNumber": 0,
        "scrollId": null
    },
    "responseData": []
    }
```

4. I am currently aware of this, PS this only happens if there are no security event generated in last 5 mins.

5. Fix is in place, doing last phase of test to see if its working as intended, provide a weeks time till Oct 3rd week, should be available where the script skips write if there is no log output in last 5 mins.





    



  
