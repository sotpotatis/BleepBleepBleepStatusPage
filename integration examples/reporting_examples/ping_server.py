'''Ping_server.py

Function that PINGS an IP address and reports the ping to ***StatusPage.'''

import bleepbleepdata.client as client, ping3, logging
#Change these
SERVER_URL = "http://127.0.0.1"
SERVER_PORT = 80
USERNAME = "user-11"
TOKEN = "0e4D9r-RRERwvL_k_IT8ZQ"
#..and these... (what to report)
CATEGORY_ID = "websites"
MONITOR_NAME = "example-monitor-1"
DATA_NAME = "ping"
#...and set the URL to ping
URL_TO_PING = "google.com"
logging.info("Initializing client...")
c = client.Client(
    SERVER_URL,
    SERVER_PORT,
    USERNAME,
    TOKEN
)
logging.info("Pinging...")
ping_time = ping3.ping(URL_TO_PING)
logging.info("Ping completed. Sending data...")
c.report_data(
    CATEGORY_ID,
    MONITOR_NAME,
    DATA_NAME,
    ping_time
)
logging.info("Data sent.")
