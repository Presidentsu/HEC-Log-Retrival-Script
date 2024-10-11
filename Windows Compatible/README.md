# Windows Compaitable scripts

## Overview

This documentation covers two versions of the Harmony Email & Collaboration log retrieval script:

1. **Manual** Manual Script: Allows the user to specify the start and end times for log retrieval and the desired output format (`txt` or `csv`). The script runs once per invocation.

2. **Automated** Script: Runs continuously every 5 minutes, automatically adjusting the time frame, and saves the results in the user-specified format (`txt` or `csv`).


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
-----

## Section 1: Manual Script

The manual version of the script allows the user to specify the time range for which logs are retrieved and choose the output format (`txt` or `csv`). It is suitable for one-time or ad-hoc log retrieval.

### Running the Manual Script

1. Download the Script:
   - Save the script on your system `(e.g., C:\Path You want to store to\HEC_log_retrieval.py)`.

2. Install Required Libraries:
   - Open Command Prompt and run:
```
pip install requests
```

3. Run the Script with Command-Line Arguments:
    - Open Command Prompt and navigate to the directory where the script is saved.
    - Run the script using:

```
python "C:\<Path you saved the file to>\HEC_log_retrieval.py" --client-id YOUR_CLIENT_ID --access-key YOUR_ACCESS_KEY --host YOUR_HOST --start-time 2024-01-01T00:00:00Z --end-time 2024-01-01T05:00:00Z --output-format txt
```
    - This will output results into `log.txt`
    - Replace `YOUR_CLIENT_ID`, `YOUR_ACCESS_KEY`, `YOUR_HOST`, and `time arguments` as required.
```
python "C:\<Path you saved the file to>\HEC_log_retrieval.py" --client-id YOUR_CLIENT_ID --access-key YOUR_ACCESS_KEY --host YOUR_HOST --start-time 2024-01-01T00:00:00Z --end-time 2024-01-01T05:00:00Z --output-format csv
```
    - This will output results into a CSV
    - Replace `YOUR_CLIENT_ID`, `YOUR_ACCESS_KEY`, `YOUR_HOST`, and `time arguments` as required.

4. Output
   - Logs are saved as `log.txt` or `log.csv` based on the specified format.
   - 
   - If `csv` is chosen, the output will include detailed fields like recipients extracted from the event description.

   - A log file named `HEC_log_retrieval.log` records activities and errors.
  

## Section 2: Automated Script

### Overview

The automated script runs continuously, retrieving logs every 5 minutes. It automatically adjusts the time frame for each interval and saves results to log.txt or log.csv based on user preference.

**Running the Automated Script**
1. Download the Script:

   - Save the script on your system.

2. Install Required Libraries:
   - Open Command Prompt and run:
   - ```
      pip install requests
     ```
3. Run the Script with Command-Line Arguments:
   - Run the script using:
   - ```
      python "C:\Users\krishnama\HEC_log_retrieval.py" --client-id YOUR_CLIENT_ID --access-key YOUR_ACCESS_KEY --host YOUR_HOST --output-format txt
     ```
   - Replace `YOUR_CLIENT_ID`, `YOUR_ACCESS_KEY`, and `YOUR_HOST` with your actual credentials - Output is in .txt for above.
   - For CSV output:
   - ```
      python "C:\file path\krishnama\HEC_log_retrieval.py" --client-id YOUR_CLIENT_ID --access-key YOUR_ACCESS_KEY --host YOUR_HOST --output-format csv
     ```
4. Run the script in the background
   - Use Task Scheduler or create a .bat file (as described below) to keep the script running continuously.
  
### Running the Script Using Task Scheduler

1. Open Task Scheduler:

    - Press Win + R, type **taskschd.msc**, and press Enter.
2. Create a New Task:
    
    - Click on **Create Task** and give it a name (e.g., "HEC Log Retrieval").

3. Set the Trigger:

    - In the **Triggers** tab, click **New**.
    - Set the trigger to start **Daily** or At **startup**, and repeat every 5 minutes.

4. Set the Action:

    - In the **Actions** tab, click **New**.
    - For **Program/script**, browse to `python.exe`.
    - For **Add arguments**, add:
    - ```
      "C:\File path\HEC_log_retrieval.py" --client-id YOUR_CLIENT_ID --access-key YOUR_ACCESS_KEY --host YOUR_HOST --output-format [txt/csv]
      ```
5. Finish:

    - Click OK to save the task and start it.
  

### Running the Script Using a `.bat` File

1. Create `.bat` file
   - Open Notepad and add:
      ```
      @echo off
      :start
      python "C:\Users\krishnama\HEC_log_retrieval.py" --client-id YOUR_CLIENT_ID --access-key YOUR_ACCESS_KEY --host YOUR_HOST --output-format txt
      timeout /t 300
      goto start
    ```
  - Replace the script path and credentials as needed.
  - Save as `run_hec_log.bat`.

2. Run the `.bat` File:
   - Double-click the .bat file to start.
   - The script will run in a loop, executing every 5 minutes.

3. Stoppging the Script:
   - Close the command window or stop the task from Task Scheduler.

## Output

-Logs are saved as `log.txt` or `log.csv` based on the chosen format.

- Each retrieval appends new data to the respective file.

- For CSV format, fields like recipients are extracted from the description field.

- Activities and errors are recorded in HEC_log_retrieval.log.

- If one ones to customize it to the likes off interval, or change in file names, simply open the script and make the require changes.

# Stay Safe & Secure <3
### For any requests, can reach out to me :)





