'''View_time.py

Function that reports the entire view time of a page to ***StatusPage.'''

import bleepbleepdata.client as client, requests, time

#Change these
SERVER_URL = "http://127.0.0.1"
SERVER_PORT = 80
USERNAME = "user-11"
TOKEN = "0e4D9r-RRERwvL_k_IT8ZQ"
#..and these... (what to report to)
CATEGORY_ID = "websites"
MONITOR_NAME = "example-monitor-1"
DATA_NAME = "ping"
#...and these (not related to the *** instance)
URL_TO_CHECK = "https://google.com"
c = client.Client(
    SERVER_URL,
    SERVER_PORT,
    USERNAME,
    TOKEN
)
request_start = time.time()
r = requests.get(URL_TO_CHECK)
if r.status_code == 200:
    view_time_seconds = time.time() - request_start
    c.report_data(
        CATEGORY_ID,
        MONITOR_NAME,
        DATA_NAME,
        view_time_seconds
    )

