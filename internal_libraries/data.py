'''Data.py
Handles *** data reading and creation as well as path management.
'''

import logging, os, json, internal_libraries.util as util, datetime, dateutil.parser

#Logging configuration
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

logger.debug("Initializing data paths...")
#The path of this script
DATA_PY_SCRIPT_PATH = os.path.realpath(__file__)
#The main directory for where ***StatusPage is running
MAIN_DIR = os.path.dirname(os.path.dirname(DATA_PY_SCRIPT_PATH))
#Configuration directory
CONFIGURATION_DIR = os.path.join(MAIN_DIR, "configuration/")
#Top directory for monitor categories
CATEGORIES = os.path.join(CONFIGURATION_DIR, "monitors/categories")
#Server configuration
SERVER_CONFIGURATION = os.path.join(CONFIGURATION_DIR, "server.json")
STATUSES_CONFIGURATION = os.path.join(CONFIGURATION_DIR, "statuses.json")
logger.debug("Data paths initialized.")
DATA_PATHS = [
    DATA_PY_SCRIPT_PATH,
    MAIN_DIR,
    CONFIGURATION_DIR,
    CATEGORIES,
    SERVER_CONFIGURATION,
    STATUSES_CONFIGURATION
]#All data paths

#Validate data paths
logger.info("[CHECK] Validating data paths...")
validation_succeeded = True
for path in DATA_PATHS:
    if not os.path.exists(path):
        logger.critical(f"[FAILED]The path {path} is missing! *** will not continue to initialize before you have fixed this.")
    else:
        logger.info(f"[PASSED] Path {path} exists.")
logger.info("[CHECK] Data paths validation check completed.")
if not validation_succeeded:
    logger.critical("[FAILED] Data paths validation check failed. Exiting program...")
    exit()

def load_json(path):
    '''Function for loading JSON from a file to a dict.
    :param path:The path to the JSON file. Can be anything accepted by the Python open() function.'''
    return json.loads(open(path, "r").read())

def update_json(path, new_data):
    '''Function for updating a JSON file with new data from a dict a dict.
    :param path:The path to the JSON file. Can be anything accepted by the Python open() function.
    :param new_data:A dictionary/dict with the new data to write to the file.'''
    with open(path, "w") as json_file:
        json_file.write(json.dumps(new_data))

def subpath_str_to_path(subpath, is_json_file=True, perform_existence_check=True):
    '''
    The *** platform has a lot of configuration files in different places, which is why you want to specify a subpath
    :param subpath:The subpath to the configuration JSON file passed as a string relative path to /configuration without .JSON in the end.
    Example: monitors/example-monitor-1/config will return configuration/monitors/example-monitor-1/config.json as an os.path object.
    :param is_json_file: Set this to False to get the ability to not add the .json prefix at the end of the filename.
    Paths will be full, not relative.'''
    logger.debug(f"Getting OS path for {subpath}...")
    path = os.path.join(CONFIGURATION_DIR, subpath+".json" if is_json_file else subpath) #Paths are relative to the configuration directory
    logger.debug(f"Parsed path: {path}.")
    logger.debug("[CHECK] Checking path existence...")
    #Check that the path exists.
    if perform_existence_check and not os.path.exists(path):
        logger.critical("[FAILED] The requested path does not exist!")
        raise FileNotFoundError("The requested path does not exist.")
    else:
        logger.debug("Path exists.")
    logger.debug("[CHECK] Path existence check completed. Returning path...")
    return path #Return the path

def get_monitor_subpath(category_name, monitor_name):
    '''Quick shortcut function for getting the subpath of a monitor used with subpath_str_to_path.

    :param category_name: The category ID that the monitor is in.

    :param monitor_name: The monitor name'''
    return f"monitors/categories/{category_name}/{monitor_name}"

def get_monitor_dir(category_name, monitor_name):
    '''Quick shortcut function for getting the directory of a monitor.

    :param category_name: The category ID that the monitor is in.

    :param monitor_name: The monitor name'''
    return subpath_str_to_path(get_monitor_subpath(category_name, monitor_name), is_json_file=False, perform_existence_check=False)

def get_configuration(subpath):
    '''Function for getting a configuration.
    The *** platform has a lot of configuration files in different places, which is why you want to specify a subpath

    :param subpath:The subpath to the configuration JSON file passed as a string relative path to /configuration without .JSON in the end.
    Example: monitors/example-monitor-1/config will return configuration/monitors/example-monitor-1/config.json'''
    return load_json(subpath_str_to_path(subpath)) #Return the parsed path

#Quick shortcut functions - should implement more of these, it's a little *** scattered right now.
def get_statuses():
    '''Shortcut function for getting configured statuses.'''
    logger.debug("Getting statuses...")
    return get_configuration("statuses")

def get_status(status_name):
    '''Shortcut function for getting configuration for a status based on its type.

    :param status_name: The status name. This must be a valid status name from "statuses.json".'''
    logger.debug(f"Getting information for status {status_name}...")
    return get_statuses()["statuses"][status_name] #Return configuration for the status

def get_monitor_config(category_name, monitor_name, config_type="basic_config"):
    '''Shortcut function for getting the config of a monitor based on its category and its name..

    :param category_name: The category name (ID)

    :param monitor_name: The monitor name (ID)

    :param config_type: The type of config that you want to return, relative to the monitor's directory.'''
    logger.info(f"Getting config type {config_type} for monitor {monitor_name} in category {category_name}...")
    return get_configuration(get_monitor_subpath(category_name, monitor_name) + f"/{config_type}") #Get the basic config

def get_category_config(category_name):
    '''Shortcut function for getting the config of a category.

    :param category_name: The category name.'''
    logger.info(f"Getting config for category {category_name}...")
    return get_configuration(f"monitors/categories/{category_name}/config")

def get_personalization_config():
    '''Function for getting personalization config.'''
    return get_configuration("personalization")

#List stuff (lists are great!)
def list_categories():
    '''A function that lists all the configured category names for monitors.'''
    logger.debug("Listing categories...")
    categories = []
    for category_name in os.listdir(CATEGORIES):
        categories.append(category_name) #This will append the directory name, i.e. the category name.
    logger.debug("Category listing complete. Returning...")
    return categories #Return list of categories

def list_user_ids():
    '''A function that lists all the configured API users using their ID.'''
    logger.info("Listing user IDs...")
    user_ids = []
    for user in get_configuration("api_users")["users"]:
        user_ids.append(user["id"])
    logger.info("User ID listing complete. Returning...")
    return user_ids

def list_incidents_ids():
    '''Function for getting IDs of all incidents.'''
    return os.listdir(subpath_str_to_path("incidents/",  is_json_file=False))

def list_monitors(category_name):
    '''Function for listing monitors for a specific category name.

    :param category_name: The category name.'''
    monitor_names = os.listdir(subpath_str_to_path(f"monitors/categories/{category_name}", is_json_file=False))
    monitor_names.remove("config.json")
    #Remove the generic configuration file for monitors.
    return monitor_names #Return a list of monitors.

def list_all_monitor_ids():
    '''Function for listing all monitor IDs that are configured.'''
    logger.info("Listing all monitors...")
    monitor_ids_list = []
    for category_name in list_categories():
        logger.debug(f"Adding monitors for {category_name}...")
        monitor_ids_list.append(list_monitors(category_name))
        logger.debug("Monitors added.")
    logger.info("Monitor ID listing complete. Returning...")
    return monitor_ids_list

#Monitor data stuff
'''Monitors can report data, which is one thing that is so beautiful with *** status pages.
This data can be anything from a ping number to a CPU utilization to the amount of coffee consumed by your engineers.
(who will be the first to build a status page for their coffee machines)?

Data will be stored under {monitor directory}/data/{reported data name}/{date}/data.json (nice!)
'''
def get_data_subpath(date, category, monitor_name, data_name):
    '''Function for getting the subpath to the data for a monitor.
    :param date: The date as a string.
    :param category: The category for the monitor
    :param monitor_name: The monitor directory name
    :param data_name: The data name that should be retrieved.
    '''
    return f"{get_monitor_subpath(category, monitor_name)}/data/{data_name}/" + f"{date}/data" if date != None else ""

def get_data_for_date(date, category, monitor_name, data_name):
    '''Function for getting the registered data for a monitor for a specific date.
    Return the data if found, if not, returns None.
    :param date: The date as a string.
    :param category: The category for the monitor
    :param monitor_name: The monitor directory name
    :param data_name: The data name that should be retrieved.'''
    logger.info(f"Checking for data for {category}/{monitor_name}, date: {date}")
    #We've got a pretty function that can give us this data or an error if it doesn't exist. Fair enough.
    try:
        data = get_configuration(get_data_subpath(date, category, monitor_name, data_name))
        logger.info("Data for day was found, returning...")
        return data["data"]
    except FileNotFoundError as e:
        logger.info("Data for the requested day was not found.", exc_info=True)
        return None

def add_data_for_date(date, category, monitor_name, data_name, value):
    '''Function for adding data for a monitor for a specific date.
    If data does not exist, this function creates it.'''
    logger.info(f"Adding data for {category}/{monitor_name}, date: {date}, data type: {data_name}")
    #Check if a data directory for the data name has been created
    logger.info("Checking for data directory existence...")
    data_directory = subpath_str_to_path(f"{get_monitor_subpath(category, monitor_name)}/data/{data_name}/", perform_existence_check=False, is_json_file=False)
    if not os.path.exists(data_directory):
        logger.info("Data directory was not found.")
        logger.info("Creating data directory...")
        os.mkdir(data_directory)
        logger.info("Directory created!")
    #Check for date directory
    date_directory = os.path.join(data_directory, date)
    logger.debug(f"Date directory path: {date_directory}.")
    if not os.path.exists(date_directory):
        logger.info("Date directory was not found.")
        logger.info("Creating date directory...")
        os.mkdir(date_directory)
        logger.info("Directory created!")
    #Generate the data to be saved
    data = {
        "value": value,
        "reported_at": str(util.get_now())
    }
    #Now, check for that yummy day data!
    existing_day_data = get_data_for_date(date, category, monitor_name, data_name)
    #Get some paths for this new yummy data
    logger.info("Getting paths for day...")
    data_file_subpath = get_data_subpath(date, category, monitor_name, data_name)
    data_file_path = subpath_str_to_path(data_file_subpath, perform_existence_check=False)
    if existing_day_data == None:
        logger.info("Day data is None - a new file will be created.")
        data_to_write_to_data_file = {
            "data": [
                data
            ]
        }
    else:
        logger.info("Day data exists. Adding value...")
        data_to_write_to_data_file = {"data": existing_day_data}
        data_to_write_to_data_file["data"].append(data)
    logger.debug(f"New JSON for data file is {data_to_write_to_data_file}")
    logger.info("Updating file...")
    update_json(data_file_path, data_to_write_to_data_file)
    logger.info("Data file updated.")

def get_data(latest, category_name, monitor_name, data_name, start_day=datetime.datetime(2021,6,1,0,1,0,0), end_day=None, return_list=True):
    '''Function for getting the
    If no data report is found or it exceeds "check after"-related kwargs, this function returns None when latest=True and an empty list when latest=False.

    :param latest: If True, only the latest data report from a monitor will be return. If False, all data within the boundaries will be returned.

    :param category_name: The category for the monitor

    :param monitor_name: The monitor directory name

    :param data_name: The data name that should be retrieved.

    :param start_day: A datetime object of the start timestamp to look for data for. Data earlier that this will be ignored in the return.

    :param end_day: A datetime object of the end timestamp to look for data for. Data after this will be ignored in the return.

    :param return_list: If True, a list will always be returned even if no data is available.
    '''
    logger.info(f"Getting{' latest ' if latest else ' '}data for {category_name}, monitor {monitor_name}, data name {data_name}")
    #Mmmmmmmmm look what you can do... you can leave out end date and this function will automagically use the current date! So *** sexy!
    if end_day == None: end_day = util.get_now() #The end date to search for
    current_check_day = start_day #The date to check with
    #Determinate which variables to use
    if latest: #Latest data should be retrieved - use variable set containing the latest data and the latest data timestamp
        logger.info("The latest data should be retrieved.")
        latest_data = latest_data_parsed_timestamp = latest_data_raw_timestamp = None
    else: #All data should be retrieved - use variable set containing a list for all data.
        logger.info("Latest data should not be retrieved, using variable set...")
        datapoints_list = []
    while current_check_day <= end_day:
        logger.info(f"Checking {current_check_day.date()}...")
        data_for_check_day = get_data_for_date(
            str(current_check_day.date()),
            category_name,
            monitor_name,
            data_name,
        )
        if data_for_check_day != None:
            logger.debug("Data was found. Iterating through and finding latest datapoints...")
            #What if end_date or start_date has time data in it? Then, we have to check that, so we aren't too late nor too early!
            for datapoint in data_for_check_day if not latest else data_for_check_day[:-1]: #It will be faster to reverse the list when we want the latest data
                logger.debug("Checking if the datapoint is within set boundaries...")
                data_timestamp_parsed = dateutil.parser.parse(datapoint["reported_at"])
                if data_timestamp_parsed < start_day or data_timestamp_parsed > end_day:
                    logger.debug("Datapoint should not be used as latest data since it is outside set boundaries.")
                else:
                    #Now, we have found a datapoint! Depending on if we only want the latest data, we can break here.
                    if latest:
                        #This check shouldn't trigger because of how we store stuff (latest stuff appended to the end of the data list), but better safe than sorry!
                        if latest_data_parsed_timestamp != None and data_timestamp_parsed < latest_data_parsed_timestamp:
                            logger.debug("Datapoint is earlier than latest data. Skipping...")
                            continue
                        logger.debug("Checks ok, using as latest data...")
                        latest_data = data_for_check_day[-1] #Get latest data
                        latest_data_raw_timestamp = data_timestamp_parsed
                        latest_data_parsed_timestamp = data_timestamp_parsed
                    else:
                        logger.debug("Option is all data, appending to list...")
                        datapoints_list.append(datapoint)
        else:
            logger.debug("Data was not found.")
        current_check_day += datetime.timedelta(days=1)
    #Now, check what to return
    if latest:
        logger.info("Processing returns for latest data...")
        logger.debug(f"List should be returned even if no data: {return_list}.")
        if latest_data == None:
            logger.info("No data was found. Returning None or empty list (depending on option)...")
            return None if not return_list else []
        else:
            logger.info("Returning latest data...")
            #Return the latest data
            return latest_data
    else:
        logger.info("Returning all data...")
        if datapoints_list == []: #If no data was found, we want to return None so we know it, as long as list returns aren't forced.
            logger.info("No data was found. Returning or empty list (depending on option)...")
            return None if not return_list else datapoints_list
        else:
            logger.info("Data was found. Returning list...")
            return datapoints_list

#Incident stuff
def get_incident_subpath(incident_id):

    return f"incidents/{incident_id}"

def get_incident_path(incident_id):
    '''Function for getting the path to an incident.
    Takes the subpath as a string, look higher up in the code for an explaination.

    :param incident_id: The incident ID.'''
    logger.debug(f"Getting incident path for {incident_id}...")
    return subpath_str_to_path(get_incident_subpath(incident_id), is_json_file=False, perform_existence_check=False) #Generate the path and return it

def write_to_incident_data_file(incident_id, data_to_write):
    '''Function for writing data to the data file of an incident.

    :param incident_id: The incident ID.

    :param data_to_write: The data to write as a dict. Must be JSON-serializable, duh.
    '''
    logger.info(f"Writing to incident data file of {incident_id}...")
    incident_subpath = get_incident_subpath(incident_id)
    incident_configuration_file_path = subpath_str_to_path(f"{incident_subpath}/data", perform_existence_check=False)
    update_json(incident_configuration_file_path, data_to_write)
    logger.info("Data file written to.")

def create_new_incident(incident_id, incident_data):
    '''Function for creating a new incident and adding it to the database.
    Creates a directory for the incident.

    :param incident_id: The ID of the new incident. This will be the directory name.

    :param incident_data: The data for the incident. This will be put in a data.json file.'''
    logger.info(f"Creating new incident with ID {incident_id}!")
    logger.debug(f"Incident data: {incident_data}.")
    #And woah omg ajsajdkasjdasdjskladn here we gooooo!
    logger.info("Getting incident path...")
    incident_path = get_incident_path(incident_id)
    logger.info("And now, creating the directory!")
    os.mkdir(incident_path)
    logger.info("Incident directory created. Creating configuration file...")
    #Create the incident configuration file
    write_to_incident_data_file(incident_id, incident_data)
    logger.info("Configuration file created. Creation of new incident data file succeeded.")

def get_incident_data(incident_id):
    '''Function for getting the data file of an incident.

    :param incident_id: The incident ID.'''
    logger.info(f"Getting incident data for {incident_id}...")
    return load_json(subpath_str_to_path(f"{get_incident_subpath(incident_id)}/data")) #nested stuff omg this looks cool!

#Related to creation
def create_category(category_name, category_config):
    '''Function for creating a new category. This one does do checking on whether the category exists or not,
    but error handling is up to everyone calling this function:))

    :param category_name: The new category name

    :param category_config: The new category config'''
    logger.info(f"Creating category {category_name}...")
    #Generate the category path
    category_dir_path = subpath_str_to_path(f"monitors/categories/{category_name}", is_json_file=False, perform_existence_check=False)
    category_config_path = os.path.join(category_dir_path, "config.json")
    if os.path.exists(category_dir_path) or os.path.exists(category_config_path):
        logger.warning(f"The category {category_name} has files already existing! Returning error...")
        return FileExistsError(f"The category name {category_name} already has files associated with it.")

    logger.info("Creating category directory...")
    os.mkdir(category_dir_path)
    logger.info("Category directory created. Creating JSON file...")
    update_json(category_config_path, category_config) #Create the category configuration file.
    logger.info("JSON file written to. Category created.")

DEFAULT_PINGS_CONFIG = {"enabled":  False, "pings": []}

def create_monitor(category, monitor_id, basic_config, pings_config=None):
    '''Function for creating a new monitor. Note that this function does not do any additional checks, like checking if the category and monitor name is valid
    and that the category does exist previously, but that the monitor ID doesn't.

    :param category: The category ID to put the monitor in.

    :param monitor_id: The ID of the monitor to create.

    :param basic_config: The monitor basic config.

    :param pings_config: None if you don't want to provide a configuration related to pings for the monitor, a dict if you want to provide one.'''
    logger.info(f"Creating monitor {monitor_id} in category {category}!")
    monitor_subpath = get_monitor_subpath(category, monitor_id)
    monitor_directory_path = subpath_str_to_path(monitor_subpath, perform_existence_check=False, is_json_file=False)
    monitor_data_directory_path = os.path.join(monitor_directory_path, "data/") #The data directory path
    monitor_basic_config_path = os.path.join(monitor_directory_path, "basic_config.json") #The path for the monitor basic config
    monitor_pings_config = os.path.join(monitor_directory_path, "pings.json") #Configuration for the "pings" or "data" features (determined by the pings_config argument)
    logger.info("Creating monitor directory...")
    os.mkdir(monitor_directory_path)
    logger.info("Monitor directory created. Creating basic config...")
    update_json(monitor_basic_config_path, basic_config)
    logger.info("Basic config created. Checking pings config...")
    #If pings == None, we want to use the default pings configuration
    if pings_config == None:
        logger.info("Using default pings config...")
        pings_config = DEFAULT_PINGS_CONFIG
    else:
        logger.info("Using user-provided pings config.")
    logger.info("Creating pings config file...")
    update_json(monitor_pings_config, pings_config)
    logger.info("Pings config created. Creating data directory...")
    os.mkdir(monitor_data_directory_path)
    logger.info("Data directory created. Monitor creation succeeded.")
