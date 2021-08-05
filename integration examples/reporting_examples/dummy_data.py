'''Dummy_data.py

Script that reports random data ***StatusPage.'''

import bleepbleepdata.client as client, random, logging, time
#Change these
SERVER_URL = "http://127.0.0.1"
SERVER_PORT = 80
USERNAME = "user-11"
TOKEN = "0e4D9r-RRERwvL_k_IT8ZQ"
#..and these... (what to report)
CATEGORY_ID = "websites"
MONITOR_NAME = "example-monitor-1"
DATA_NAME = "ping"
#Information about each datapoint
SEND_N_DATAPOINTS = 50
DATAPOINT_START = 0
DATAPOINT_END = 200
SLEEP_BETWEEN_UPLOADS = 0.25
ROUND_TO_DECIMALS = 3
logging.basicConfig(level=logging.INFO)
logging.info("Initializing client...")
c = client.Client(
    SERVER_URL,
    SERVER_PORT,
    USERNAME,
    TOKEN
)
for i in range(SEND_N_DATAPOINTS):
    c.report_data(
        CATEGORY_ID,
        MONITOR_NAME,
        DATA_NAME,
        round(random.uniform(DATAPOINT_START, DATAPOINT_END), ROUND_TO_DECIMALS)
    )
    time.sleep(SLEEP_BETWEEN_UPLOADS) #Sleep a little (or a lot, depending on your configuration)
    logging.info("Data sent.")
