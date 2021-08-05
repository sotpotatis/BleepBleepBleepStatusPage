'''System_stats.py

Function that sends the statistics of a system (RAM usage, CPU, and more) to a ***StatusPage
instance.'''

import bleepbleepdata.client as client, psutil, logging
#Change these
SERVER_URL = "http://127.0.0.1"
SERVER_PORT = 80
USERNAME = "user-11"
TOKEN = "0e4D9r-RRERwvL_k_IT8ZQ"
#..and these... (what to report to)
CATEGORY_ID = "websites"
MONITOR_NAME = "example-monitor-1"
#...and, set the data to send
#(want to not report any of these? simply set their variable to None.
CPU_USAGE_DATA_NAME = "cpu_usage" #(in percent)
PHYSICAL_RAM_USAGE_DATA_NAME = "ram_usage" #(in gigabytes)
SWAP_RAM_USAGE_DATA_NAME = "swap_ram_usage" #(in gigabytes)
DISK_USAGE_DATA_NAME = "disk_usage"
#Settings
DISK_USAGE_PATH = "C:\\"
ROUND_UPLOADS_TO_N_DECIMALS = 2 #How many decimals to round uploaded data to
logging.info("Initializing client...")
c = client.Client(
    SERVER_URL,
    SERVER_PORT,
    USERNAME,
    TOKEN
)
logging.info("Grabbing statistics...")
#Set everything to None
cpu_usage = ram_usage = swap_ram_usage = disk_usage = None
if CPU_USAGE_DATA_NAME != None:
    logging.info("Grabbing CPU usage...")
    #Grab CPU usage if we want to report it
    cpu_usage = round(psutil.cpu_percent(), ROUND_UPLOADS_TO_N_DECIMALS)
if PHYSICAL_RAM_USAGE_DATA_NAME != None:
    logging.info("Grabbing physical RAM usage...")
    #Grap RAM usage if we want to report it
    ram_usage = round(psutil.virtual_memory().percent, ROUND_UPLOADS_TO_N_DECIMALS)
if SWAP_RAM_USAGE_DATA_NAME != None:
    logging.info("Grabbing SWAP RAM usage...")
    swap_ram_usage = round(psutil.swap_memory().percent, ROUND_UPLOADS_TO_N_DECIMALS)
if DISK_USAGE_DATA_NAME != None:
    logging.info("Grabbing disk usage...")
    #Grab disk space if we want to report it
    disk_usage = round(psutil.disk_usage(DISK_USAGE_PATH).percent, ROUND_UPLOADS_TO_N_DECIMALS)
#Upload stuff
logging.info("Uploading stuff...")
if cpu_usage != None:
    logging.info("Uploading CPU usage...")
    c.report_data(
        CATEGORY_ID,
        MONITOR_NAME,
        CPU_USAGE_DATA_NAME,
        cpu_usage
    )
    logging.info("CPU usage data sent.")
if ram_usage != None:
    logging.info("Uploading RAM usage...")
    c.report_data(
        CATEGORY_ID,
        MONITOR_NAME,
        PHYSICAL_RAM_USAGE_DATA_NAME,
        ram_usage
    )
    logging.info("RAM usage data sent.")
if swap_ram_usage != None:
    logging.info("Uploading SWAP RAM usage...")
    c.report_data(
        CATEGORY_ID,
        MONITOR_NAME,
        SWAP_RAM_USAGE_DATA_NAME,
        swap_ram_usage
    )
    logging.info("SWAP RAM usage data sent.")
if disk_usage != None:
    logging.info("Uploading disk usage...")
    c.report_data(
        CATEGORY_ID,
        MONITOR_NAME,
        DISK_USAGE_DATA_NAME,
        disk_usage
    )
    logging.info("Disk usage data sent.")
logging.info("Data sent.")
