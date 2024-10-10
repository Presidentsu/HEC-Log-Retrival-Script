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

