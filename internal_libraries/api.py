'''API.py
This file handles a LOT of stuff and is used by both API-routes and pages that are rendered by the code.
Why?
To provide a uniform file for a LOT of stuff. This is so nice. Believe me.

--> ALL functions return a dictionary, even when an error occurs. This dictionary is the API response.
There is a key called "status" which will tell you the status of the function output.
'''
import internal_libraries.data as data, internal_libraries.util as util, internal_libraries.schema as schema, datetime, dateutil.parser, math #A LOT in this world is dependent on data. So are these functions.
import logging, re, pytz, os, shutil
from http import HTTPStatus
from werkzeug.security import check_password_hash, generate_password_hash #I don't know who is responsible for these function, but whoever is - you're amazing.

#Logging configuration
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

#API statuses
API_STATUS_SUCCESS = "success"
API_STATUS_ERROR = "error"

#API responses
def generate_api_response(status, data, status_code=200):
    '''Function for generating a response from the API. This is the output of any API function.

    :param status: The status of the request/data retrieval.

    :param data: Any other data that the function should return.

    :param status_code: Status code in HTTP/HTTPS response code format.
    '''
    logger.info(f"Generating API response for status {status}, data {data}...")
    data["status"] = status #Add status
    data["status_code"] = int(status_code) #Add status code
    logger.info("Generated. Returning...")
    logger.debug(f"Generated response: {data}.")
    return data

def generate_api_error(message, status_code, data={}):
    '''Function for generating an API response that is about an error.
    Every error includes a message and returns the status "error".

    :param message: The error message to show

    :param data: (optional) Any other data (dict) to add.'''
    logger.info(f"Generating API error with message {message}...")
    data["message"] = message #Add message
    return generate_api_response(API_STATUS_ERROR, data, status_code=status_code)

#Handy stuff when returning API responses
def get_status_code_from_api_response(api_response):
    '''Function for getting the status code from an API response. This is supplied in all API responses.

    :param api_response: The API response as a dict. Must have the "status_code" key set.'''
    return api_response["status_code"] #Return status code
#AUTH
'''
ABOUT API AUTHENTICATION
User access management for the API is handled by the information in the api_users.json file.
Authentication is done by providing an user ID and a token.
By default, users have access to everything, but that can be revoked.
'''
#These are the API endpoint names - hot!
API_ENDPOINT_ADD_USER = "add_user"
API_ENDPOINT_ADD_INCIDENT = "add_incident"
API_ENDPOINT_UPDATE_INCIDENT = "update_incident"
API_ENDPOINT_GET_INCIDENT = "get_incident"
API_ENDPOINT_LIST_INCIDENTS = "list_incidents"
API_ENDPOINT_REPORT_DATA = "report_data"
API_ENDPOINT_GET_DATA = "get_data"
API_ENDPOINT_GET_PERSONALIZATION_CONFIG = "get_personalization_config"
API_ENDPOINT_UPDATE_PERSONALIZATION_CONFIG = "update_personalization_config"
API_ENDPOINT_GET_MONITOR_STATUS = "get_monitor_status"
API_ENDPOINT_CREATE_MONITOR = "create_monitor"
API_ENDPOINT_UPDATE_MONITOR_CONFIG = "update_monitor_basic_config"
API_ENDPOINT_DELETE_MONITOR = "delete_monitor"
API_ENDPOINT_UPDATE_MONITOR_PINGS = "update_monitor_pings"
API_ENDPOINT_CREATE_CATEGORY = "create_category"
API_ENDPOINT_UPDATE_CATEGORY_CONFIG = "update_category_config"
API_ENDPOINT_DELETE_CATEGORY = "delete_category"
API_ENDPOINT_LIST_CATEGORIES = "list_categories"

def check_user_authentication(user_id, provided_token, endpoint_name):
    '''Yes, this is the function for checking if a user has access to an API endpoint!
    An endpoint is basically an API feature.'''
    logger.info(f"Checking user authentication for {user_id}...")
    #First, get users
    if user_id not in data.list_user_ids():
        logger.info("User ID does not exist! Returning error...")
        return generate_api_error("User not found", HTTPStatus.BAD_REQUEST)
    logger.info("User was found. Validating token...")
    #Now, let's validate the token - the membership card! Mwah!
    user_data = data.get_configuration("api_users")
    for user in user_data ["users"]:
        if user["id"] == user_id:
            logger.info("Found user!")
            break
    logger.info("Checking token...")
    if check_password_hash(user["token"], provided_token) is True: #Ofc we hash tokens in SHA256 in da database;)
        logger.info("Authentication is valid!")
        #Now, check if this route is in "revoke_permissions" of the user
        logger.info("Checking revoked permissions...")
        if "revoke_permissions" in user and endpoint_name in user["revoke_permissions"]:
            logger.warning(f"The user {user_id} does not have access to this route! Make sure this isn't a bad person.")
            return False
        else:
            logger.info("Authentication was successful - check!")
            return True
    else:
        logger.warning(f"Invalid auth for {user_id} was sent! Make sure this isn't a bad person.")
        return False

def check_user_authentication_from_request(request, endpoint_name):
    '''A function for checking user authentication from a provided request object.
    (request object as in a Flask.request object).

    :param request: A Flask request object.

    :param endpoint_name: The API endpoint (feature) that the user is trying to access.'''
    logger.info("Checking user authentication based on request...")
    #User authentication is done by supplying a Bearer token and a username.
    logger.info("Checking for token...")
    if "Authorization" not in request.headers:
        logger.warning("Access to API was attempted without authorization headers! Forbidding request...")
        return generate_api_error("Invalid authentication.", HTTPStatus.BAD_REQUEST)
    authorization = request.headers["Authorization"]
    authorization_without_bearer = authorization.strip("Bearer ")
    logger.info("Authorization is present. Looking for user ID...")
    #User ID should be present in JSON form body
    if request.json == None or "user_id" not in request.json:
        logger.warning("Access to API was attempting without user ID! Forbidding request...")
        return generate_api_error("Invalid authentication.", HTTPStatus.BAD_REQUEST)
    user_id = request.json["user_id"]
    logger.info("User ID is present. Validating details...")
    #The final policeman is here!
    authentication_valid = check_user_authentication(user_id, authorization_without_bearer, endpoint_name)
    if not authentication_valid:
        logger.warning(f"Authentication for {user_id} has failed. Forbidding request...")
        return generate_api_error("Invalid authentication.", HTTPStatus.BAD_REQUEST)
    logger.info("Authentication was valid! Returning success...")
    return generate_api_response(API_STATUS_SUCCESS, {"message": "The authorization check was successful."}, HTTPStatus.ACCEPTED)

#Key validation
def validate_present_keys(dictionary, mandatory_key_list):
    '''Yeah, some requests require some stuff specified, in JSON, headers, or whatever.
    This function should be passed a dict and a list of all keys that should be present in tuple format with their desired type afterwards.

    :param dictionary: A dict to check for the present keys in.

    :param mandatory_key_list: A list of all keys that should be present. The list of keys should contain tuples with the format (key index, required_types).
    Example: [("foobar", [str]), ("smiley/face/param1", [str, int])]. To make a key non-dependent of type, pass the second tuple argument as None, not within a list.
    '''
    logger.info("Validating present keys in a passed dict!")
    logger.debug(f"Passed dict: {dictionary}, mandatory key list: {mandatory_key_list}")
    logger.info("Validating keys according to list of mandatory keys...")
    for key_type_pair in mandatory_key_list:
        mandatory_key = key_type_pair[0]
        mandatory_types = key_type_pair[1]
        logger.debug(f"Mandatory key: {mandatory_key}. Mandatory types: {mandatory_types}.")
        logger.debug("Checking for key in passed dictionary...")
        #Split the key in parts, a slash marking each level to go down.
        key_parts = (mandatory_key).split("/")
        logger.debug(f"Key parts: {key_parts}.")
        logger.info(f"Mandatory key: {mandatory_key}")
        current_value = dictionary #The current dictionary that we're checking. This makes sense for subkeys.
        valid_key_parts = []
        for key_part in key_parts:
            try:
                #Try to access the key part.
                current_value = current_value[key_part]
                logger.debug(f"Key part {key_part} was accessible.")
                #Add valid key part
                valid_key_parts.append(key_part)
            except KeyError:
                logger.info(f"Key part {key_part} is missing from dict!")
                #TODO: Check this return string, it returns double? (example response: Key part data_to_update/data_to_update has invalid type (expected , and <class 'str'>, got <class 'dict'>).")
                return generate_api_error(f"Key part {'/'.join(valid_key_parts)}/{key_part} is missing.", HTTPStatus.BAD_REQUEST)
        logger.info("Validating type...")
        value_type = type(current_value)
        if mandatory_types != None and value_type not in mandatory_types:
            logger.info("The type for the key is invalid! Returning error...")
            return generate_api_error(f"Key part {'/'.join(valid_key_parts)}/{key_part} has invalid type (expected {util.pretty_format_list(mandatory_types, convert_to_str=True)}, got {value_type}).", HTTPStatus.BAD_REQUEST)
        else:
            logger.info(f"The type for the key is valid. ({value_type})")
    #If we get here, the key validation succeeded.
    logger.info("Key validation succeeded!")
    return generate_api_response(API_STATUS_SUCCESS, {"message": "Key validation is ok."}, 200)
#Incident parsing
#Handy stuff
INCIDENT_OPEN = "open"
INCIDENT_RESOLVED = "resolved"

def get_incidents(status="open", monitor=None, category=None, start_date=None, end_date=None):
    '''Function for getting incidents.

    :param status: either "open" or "resolved". Can also be None, if you want to return all incidents.

    :param monitor: Optional argument: return open incidents for monitor with monitor name. Can be a str or a list.

    :param category: Optional argument: return open incidents for category with category name. Can be a str or a list.

    :param start_date: Optional argument. The start date for when we should check for incidents. Datetime.

    :param end_date: Optional argument. The end date for when we should check for incidents. Datetime.
    '''
    logger.info(f"Getting {status} incidents!")
    logger.info(f"Specified monitor: {monitor}, specified category {category}.")
    logger.info(f"Filters: start date: {start_date}, end date {end_date}")
    #Iterate through all incidents to find open ones
    incident_ids = data.list_incidents_ids()
    response_data = {"found_incidents": []} #Response to provide
    for incident in incident_ids:
        logger.info(f"Checking incident {incident}...")
        #An incident is resolved if it has a specified resolved date and "current_status" is "resolved".
        incident_data = data.get_configuration(f"incidents/{incident}/data")
        incident_timestamps = incident_data["timestamps"]
        logger.debug("Incident data retrieved.")
        incident_solved_at = incident_timestamps["solved_at"]
        if incident_timestamps["solved_at"] != None and incident_data["current_status"] == "resolved":
            logger.info("Incident is resolved.")
            incident_status = "resolved"
        else:
            logger.info("Incident is not resolved!")
            incident_status = "open"
        if status != None and status != incident_status:
            logger.info("Incident is not relevant due to status selection.")
            continue
        #Filters can be provided, see top comment. We want to check for them
        if monitor != None or category != None:
            logger.debug("Filters provided. Checking against provided filters...")
            #Check what services are affected
            affected_categories = affected_monitors = []
            affected_things = incident_data["affected"] #Things affected by the incident
            logger.debug(f"Affected things: {affected_things}")
            for affected_thing in affected_things:
                affected_id = affected_thing["id"]
                affected_type = affected_thing["type"] #Should either be "category" or "monitor"
                logger.debug(f"Checking affected ID: {affected_id}, affected type: {affected_type}")
                if affected_type == "monitor":
                    affected_monitors.append(affected_id)
                elif affected_type == "category":
                    affected_categories.append(affected_id)
                else:
                    logger.warning(f"Format warning: Incident {incident} has an invalid affected type, {affected_type}.")
            #Check if thing is affected
            logger.debug(f"Affected monitors: {affected_monitors}, affected categories: {affected_categories}")
            if monitor != None and monitor in affected_monitors:
                logger.info("Monitor is affected by this incident.")
            elif category != None and category in affected_categories:
                logger.info("Category is affected by this incident.")
            elif monitor != None or category != None:
                logger.info("Monitor or monitor category is not affected by this incident. Skipping...")
                continue
            #else, ignore, and continue checking
        else:
            logger.debug("Monitor-category filters are not provided.")
        #Check for date filters
        if start_date != None or end_date != None:
            logger.info("Date filter is provided. Checking...")
            #Parse the latest available date, which will be the resolved date if it exists.
            incident_created_at = incident_timestamps["created_at"]
            #(we have the solved date higher above!)
            if incident_solved_at != None:
                logger.info("Using solved at as latest date reference...")
                incident_latest_date = check_date(incident_solved_at) #This will provide parsed output.
            else:
                logger.info("Incident solved date has not been set. Using creation date for base...")
                incident_latest_date = check_date(incident_created_at)
            logger.info("Performing incident date checks...")
            if start_date != None and incident_latest_date < start_date:
                logger.info("Relevant incident date is earlier than start date. Skipping...")
                continue
            else:
                logger.debug("Incident start date check passed.")
            if end_date != None and incident_latest_date > end_date:
                logger.info("Relevant incident date is later than end date. Skipping...")
                continue
            else:
                logger.debug("Incident end date check passed.")
        logger.info("Incident is relevant for selection, adding to list of open incidents...")
        response_data["found_incidents"].append(incident)
    return generate_api_response(API_STATUS_SUCCESS, response_data)

#Yummy, finger-licking good functions for parsing data into dictionaries
def generate_categories_dict():
    '''Combines the config.json file from all categories into one dictionary.
    This is basically the categories information dictionary.
    Bang boom. Sounds great, right? Gotcha, it does!'''
    logging.info("Generating category dict...")
    category_dict = {}
    for category_name in data.list_categories():
        logging.info(f"Getting configuration for category {category_name}...")
        #Generate config path (this is config.json - wholesome!)
        try:
            category_config = data.get_configuration(f"monitors/categories/{category_name}/config")
        except FileNotFoundError as e: #If the file was not found
            logger.warning(f"A configuration for the category {category_name} does not exist! Oops. You might want to fix that!", exc_info=True)
            continue
        logger.info("Adding config...")
        category_dict[category_name] = category_config
    logger.info("Category configuration has been retrieved. Returning...")
    return generate_api_response(API_STATUS_SUCCESS, {"categories": category_dict})

def get_status_for_monitor(category_name, monitor_name):
    '''This function parses the status for a monitor based on its name.
    A monitor status can be affected in case it has a ping trigger (see monitor/pings.json)'''
    logger.info(f"Getting status for monitor {monitor_name} in category {category_name}...")
    monitor_base_subpath = f"monitors/categories/{category_name}/{monitor_name}"
    now = util.get_now() #Current time
    logger.info("Getting monitor config...")
    monitor_config = data.get_configuration(monitor_base_subpath + "/basic_config")
    logger.info("Getting monitor ping config...")
    monitor_ping_config = data.get_configuration(monitor_base_subpath + "/pings")
    #Pings and incidents can affect the monitor status. We want to save all monitor statuses and find the one that has the most weight
    monitor_statuses = [monitor_config["default_status"]]
    #Check if pings are enabled
    if monitor_ping_config["enabled"]:
        logger.info("Pings are enabled. Checking when latest ping was received...")
        #Iterate through pings, multiple might be configured.
        for ping in monitor_ping_config["pings"]:
            logger.debug(f"Checking timeout for ping {ping}")
            data_name = ping["ping_name"] #The data name for the ping
            timeout = ping["timeout_minutes"] #This unit is in minutes if that isn't clear
            report_every = ping["reporting_frequency_minutes"] #This is in minutes too
            status_on_timeout = ping["status_on_timeout"]
            ping_tolerance = report_every+timeout #+/- reporting difference in minute that we tolerate with this ping
            earliest_expected_ping = now - datetime.timedelta(minutes=ping_tolerance)
            latest_expected_ping = now + datetime.timedelta(minutes=ping_tolerance)
            latest_ping = data.get_data(True, category_name, monitor_name, data_name, earliest_expected_ping, latest_expected_ping)
            if latest_ping == []:
                logger.info("Monitor seems to be missing recent ping data!")
                if status_on_timeout not in monitor_statuses: monitor_statuses.append(status_on_timeout)
    else:
        logger.info("Pings are not enabled.")
    #While no received pings are bad, an active incident will naturally be of higher priority.
    logger.info("Checking for active incident...")
    active_monitor_incidents = get_incidents("open", monitor=monitor_name, category=category_name)["found_incidents"]
    logger.debug(f"List of monitor incidents: {active_monitor_incidents}")
    if len(active_monitor_incidents) > 0:
        logger.info("Active monitor incident(s) was found.")
        for incident in active_monitor_incidents:
            #Since get_incidents() will only provide us with the found incident IDs, we want to get the data too.
            logger.debug(f"Getting data for active monitor incident {incident}...")
            incident_data = data.get_incident_data(incident)
            logger.debug(f"Data retrieved. Incident data: {incident_data}.")

            for affected_thing in incident_data["affected"]:
                affected_thing_type = affected_thing["type"]
                affected_thing_id = affected_thing["id"]
                affected_thing_status = affected_thing["status"]
                if affected_thing_type == "monitor" and affected_thing_id == monitor_name:
                    logger.info("Found affected monitor.")
                    monitor_statuses.append(affected_thing_status) #Add the status to the global list to be able to determinate the monitor's status later
                elif affected_thing_type == "category" and affected_thing_id == category_name:
                    logger.info("Found affected category.")
                    monitor_statuses.append(affected_thing_status) #Add the status to the global list to be able to determinate the monitor's status later
    else:
        logger.info("No active incidents were found.")
    logger.info("Monitor status checks performed. Finding heaviest status...")
    #Oh yeah heavy statuses! Heavy! Heavy stuff!
    most_heavy_status = util.get_heaviest_status(monitor_statuses)
    logger.info(f"Heaviest status found: {most_heavy_status}. Returning...")
    return generate_api_response(API_STATUS_SUCCESS, {"current_status": most_heavy_status})

def generate_daddy_dict():
    '''This is a PRETTY one. One for the dictionary and JSON lovers.
    MWAH! You'll like this, bestie<3

    It combines the configuration of all categories and its submonitors into ONE single dictionary. Hard to beat that, ehh?
    '''
    final_data = {}
    logger.info("Generating category dict...")
    categories = generate_categories_dict()["categories"]
    final_data["categories"] = categories
    #And now, iterate through categories to add monitors... yikes wow this will be some yummy output...
    monitor_statuses = [] #We want to determinate an overall platform status... ah omg this is too... this is so beautiful
    now = util.get_now() #...And the time!!!
    for category in categories:
        logger.info(f"Adding stuff for {category}...")
        #Get config
        logger.info("Getting category config...")
        category_config = data.get_category_config(category)
        logger.info("Category config retrieved.")
        monitor_names = data.list_monitors(category)
        logger.debug(f"Monitor names: {monitor_names}")
        final_data["categories"][category] = {"monitors": [], "config": category_config} #Add basic stuff!
        for monitor_name in monitor_names:
            logger.info(f"Current monitor: {monitor_name}. Adding config and current status...")
            monitor_config = data.get_monitor_config(category, monitor_name)
            monitor_status = get_status_for_monitor(category, monitor_name)["current_status"]
            monitor_statuses.append(monitor_status)
            final_monitor_data = {
                "config": monitor_config,
                "status": monitor_status,
                "plots": []
            }
            #OMG... more yummy things on the way! Because look - we also want to provide any plotted data
            monitor_pings = data.get_monitor_config(category, monitor_name, "pings")
            for ping in monitor_pings["pings"]:
                ping_name = ping["ping_name"]
                ping_plot_data = ping["plot"]
                if not ping_plot_data["plot_data"]:
                    logger.info("The ping should not be plotted. Ignoring...")
                    continue
                else:
                    logger.info(f"Ping should be plotted. Getting ping data for ping {ping_name}...")
                    #Generate ping start time and ping end time (start time and end time to search for data, that is)
                    ping_reporting_frequency_minutes = ping["reporting_frequency_minutes"]
                    ping_timeout_minutes = ping["timeout_minutes"]
                    ping_plot_readable_information = ping_plot_data["plot_information"]
                    ping_plot_amount = ping_plot_readable_information["plot_number_of_datapoints"] #The number of datapoints to plot
                    ping_tolerance = ping_reporting_frequency_minutes+ping_timeout_minutes #Total acceptable delay for a ping
                    start_ping_time = now - datetime.timedelta(minutes=ping_tolerance*ping_plot_amount)
                    end_ping_time = now
                    logger.info(f"Start search time: {start_ping_time}. End search time: {end_ping_time}")
                    #Get data (False to get all data and not the latest data)
                    data_dataset = data.get_data(False, category, monitor_name, ping_name, start_ping_time, end_ping_time, return_list=True)
                    logger.info("Data retrieved. Generating data for plotting...")
                    '''Data on the page is plotted using the magnificent Chart.js! Therefore, we generate the data to plot right here... because why not?
                    OMG!'''
                    data_to_plot = data_to_graph_labels(data_dataset, #Generate data to plot
                                                        ping_plot_readable_information["title"],
                                                        ping_reporting_frequency_minutes,
                                                        ping_timeout_minutes,
                                                        ping_plot_readable_information["plot_number_of_datapoints"])["data"]
                    logger.info("Data plot retrieved. Adding plot data...")
                    ping["plot_data"] = data_to_plot #Add the data
                    logger.info("Data appended. Appending to final list.")
                    final_monitor_data["plots"].append(ping) #Add the whole ping information... mwah, great, eh?
            logger.info("Adding monitor data to final data...")
            final_monitor_data["id"] = monitor_name
            final_data["categories"][category]["monitors"].append(final_monitor_data)
    final_data["monitor_statuses"] = monitor_statuses #This will be beautifully parsed in ui_frontend.py!
    logger.info("Returning final data...")
    logger.debug(f"Final data: {final_data}.")
    #Return the final data
    return final_data

def data_to_graph_labels(dataset, dataset_label, data_reporting_frequency_minutes, data_tolerance, graph_datapoints=25):
    '''When we render graphs on the webpage, we use the magnificent Chart.js. It's interactive and sexy. What else, really?
    And, with this function, we basically make the output to send to Chart.js. Yeah, I know :rolling_eyes: This is HOT!
    Returns a dictionary with the "barest" data to send to Chart.js. (is "barest" a word? I'm Swedish, it sounds great)
    The barest data as in labels and the dataset mapped to these labels. The data is mapped automatically and will to fill the
    datapoints limit in all cases. Missing data will be rendered as empty.

    :param dataset: The dataset to use. This is the list that you will find under the data plot in the device data/ directory.
    NOTE: The dataset should be ordered in such way that the earliest reported data should come first. This is how the reporting of data over here works, so it shouldn't be a problem.

    :param dataset_label: A human-readable description of the dataset. Rendered by Chart.js as a title.

    :param data_tolerance: The reporting frequency for the data PLUS the tolerance in reporting. This is used to base how the dataset is split up.

    :param graph_datapoints: The amount of graph datapoints to plot. Keep in mind that a high number will impact browser performance negatively.
    '''
    logger.info("Converting a dataset to graph labels...")
    #First, get the dataset to use
    logger.debug(f"Dataset: {dataset}, dataset label: {dataset_label}, data tolerance: {data_tolerance}, number of datapoints to plot: {graph_datapoints}")
    logger.info("Determining dataset to use...")
    dataset_to_use = dataset[:graph_datapoints]
    reversed_dataset_to_use = dataset_to_use
    reversed_dataset_to_use.reverse()
    logger.info("Dataset determined.")
    #Get current time
    last_datapoint_timestamp = now = util.get_now()
    logger.info("Iterating through and adding datapoints...")
    '''Generate graph datapoints in this way:
    - Check each datapoint and parse the time for when it was reported.
    - If that difference is too large, we add labels to the right matching how many missed reports that there has been.
    '''
    minute_offset = 0 #Offset to now to apply when checking the current datapoint
    #Chart.js data
    chartjs_data = []
    chartjs_labels = []
    format_label_for_chartjs = lambda dt: dt.strftime("%Y-%m-%d %H:%M")
    for datapoint in reversed_dataset_to_use:
        logger.debug("Parsing datapoint...")
        datapoint_timestamp = dateutil.parser.parse(datapoint["reported_at"])
        difference_to_now_minutes = round((now - datapoint_timestamp).total_seconds() / 60, 3) - minute_offset
        if difference_to_now_minutes > data_tolerance:
            logger.debug("Difference is bigger than data tolerance, this is a gapped datapoint. Adding label(s) to right...")
            #Calculate how many datapoints that is missing
            logger.debug("Calculating amount of missed uploads...")
            #Here we do: difference between this and prev valid datapoint in minutes divided by data tolerance, floored (2.9 missed uploads shouldn't be rounded to 3 in this case)
            missed_upload_amount = math.floor(((datapoint_timestamp - last_datapoint_timestamp).total_seconds() / 60) / data_tolerance)
            for missed_upload_number in reversed(list(range(missed_upload_amount))): #Reverse the list so that the latest dataset gets added to the right
                logger.debug(f"Adding missed upload number {missed_upload_number+1}")
                #This nice thing below will format a label based on the last datapoint timestamp - data_reporting_frequency in minutes times the missed upload number
                chartjs_labels.append(format_label_for_chartjs(last_datapoint_timestamp-datetime.timedelta(minutes=data_reporting_frequency_minutes*missed_upload_number)))
                chartjs_data.extend(None) #Add None to the data
        else:
            logger.debug("The datapoint has reported w/o latency compared to the previous one. Adding it to the list of labels...")
        logger.debug("Adding datapoint...")
        #Add the stuff, then great!
        chartjs_data.append(datapoint["value"])
        chartjs_labels.append(format_label_for_chartjs(datapoint_timestamp))
        last_datapoint_timestamp = datapoint_timestamp
        minute_offset += difference_to_now_minutes
    '''If you take a little look below, you will notice that the way this is written,
   the dataset needs to have at least one datapoint.'''
    if len(dataset_to_use) == 0:
        logger.info("Dataset is empty: adding fallback datapoints...")
        for missed_upload_number in reversed(list(range(25))): #Reverse the list so that the latest timestamp gets added to the right
            logger.debug(f"Adding missed upload number {missed_upload_number+1}")
            #This nice thing below will format a label based on the last datapoint timestamp - data_reporting_frequency in minutes times the missed upload number
            chartjs_labels.append(format_label_for_chartjs(now-datetime.timedelta(minutes=data_reporting_frequency_minutes*missed_upload_number)))
            chartjs_data.append(None) #Add None to the data
    logger.info("Iteration done, generating data JSON...")
    #Here, we have to apply some personalization. Do so.
    graph_personalization_config = data.get_configuration("personalization")["graphs"]
    chartjs_full_data = {
        "labels": chartjs_labels,
        "datasets": [{
            "label": dataset_label,
            "data": chartjs_data,
            "backgroundColor": graph_personalization_config["line_background_color"], #Add background color
            "borderColor": graph_personalization_config["line_border_color"], #Add border color
            "tension": graph_personalization_config["line_tension"], #Line tension. 0 = no smoothing, >0 = draw yummy bezier curves!
            "fill": graph_personalization_config["fill_line"] #This will make the graph look good where we are putting it.
        }]
    } #This is what is under "data": in the Chart.js options.
    #Generate the data to pass to Chart.js
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"data": chartjs_full_data},
       200
    )

#Validation
def validate_category_and_monitor_name(category_name, monitor_name):
    '''Function for validating that the category and monitor name passed with a request is valid.

    :param category_name: The category name to check.

    :param monitor_name: The monitor name to check.'''
    try:
        data.get_monitor_subpath(category_name, monitor_name)
        return generate_api_response(API_STATUS_SUCCESS,
                                     {"message": "The category name and monitor name is valid"},
                                     200)
    except FileNotFoundError:
        return generate_api_error("The monitor or category name is invalid/could not be found..", HTTPStatus.NOT_FOUND)

#Add data API
def add_data_api(category_name, monitor_name, data_name, value):
    '''Function for adding data as reported from a monitor.'''
    logger.info(f"Adding data for category {category_name}, monitor {monitor_name}, data {data_name}...")
    #Validate category and monitor name
    category_and_monitor_name_validation = validate_category_and_monitor_name(category_name,
                                                                              monitor_name)
    if category_and_monitor_name_validation["status"] != API_STATUS_SUCCESS:
        logger.info("Category name or monitor name is invalid! Returning error...")
        return category_and_monitor_name_validation

    #Get valid data names
    monitor_ping_data = data.get_configuration(f"monitors/categories/{category_name}/{monitor_name}/pings")
    if not monitor_ping_data["enabled"]:
        logger.info("Pings for the monitor is not enabled! Returning error...")
        return generate_api_error("This monitor does not have the data reporting feature enabled. Please enable it first.",
                                  HTTPStatus.FORBIDDEN)
    valid_data_names = [ping["ping_name"] for ping in monitor_ping_data["pings"]]
    if data_name not in valid_data_names:
        logger.info("Data name is not valid! Returning error...")
        return generate_api_error("The data name is invalid.", HTTPStatus.BAD_REQUEST)
    logger.info("Everything is valid! Adding data...")
    data.add_data_for_date(
        str(util.get_now().date()),
        category_name,
        monitor_name,
        data_name,
        value
    )
    logger.info("Data added. Returning response...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"message": "Data was added successfully."},
        200
    )
VALID_DATE_REGEX = "[0-9]{4}(-(0|1)[1-9])(-[0-3][0-9])" #This will work even in 3022 - futuristic stuff, eh!?
INVALID_DATE_RESPONSE = False
def check_date(date_str, return_offset_aware=True):
    '''Function for validating if a date is valid.
    Returns parsed date if valid, False if invalid.

    :param date_str: A string of the date.

    :param return_offset_aware: Whether the datetime (if a datetime is returned) should be offset-aware (timezone info
    included) or offset-naive (timezone info excluded). Note that the timezone info will be the server's timezone.'''
    try:
        date_parsed = dateutil.parser.parse(date_str)
        logger.info("The date is valid!")
        if return_offset_aware:
            logger.debug("The return should be offset-aware. Returning offset-aware datetime...")
            date_parsed = date_parsed.astimezone(tz=pytz.timezone(util.get_timezone()))
        else:
            logger.debug("The return should not be offset-aware.")
        return date_parsed
    except Exception as e:
        logger.info(f"The date seems invalid, parsing error! (exception: {e})", exc_info=True)
        return INVALID_DATE_RESPONSE

#Get data API
def get_data_api(category_name, monitor_name, data_name, start_date, end_date):
    '''Function for getting reported data for a monitor.'''
    logger.info(f"Getting data for monitor {monitor_name} in category {category_name}, data type: {data_name}")
    #Validate category and monitor name
    category_and_monitor_name_validation = validate_category_and_monitor_name(category_name,
                                                                              monitor_name)
    if category_and_monitor_name_validation["status"] != API_STATUS_SUCCESS:
        logger.info("Category name or monitor name is invalid! Returning error...")
        return category_and_monitor_name_validation
    #Validate date
    logger.info(f"Validating passed dates, start date {start_date} and end date {end_date}...")
    #Attempt parsing of start and end date.

    start_date_parsed = check_date(start_date)
    if start_date_parsed == INVALID_DATE_RESPONSE:
        logger.info("Could not parse start date! Error.")
        return generate_api_error("The passed start date to search for data with is invalid.", HTTPStatus.BAD_REQUEST) #Answer with error and BAD_REQUEST status code
    end_date_parsed = check_date(end_date)
    if end_date_parsed == INVALID_DATE_RESPONSE:
        logger.info("Could not parse end date! Error.")
        return generate_api_error("The passed end date to search for data with is invalid.", HTTPStatus.BAD_REQUEST) #Answer with error and BAD_REQUEST status code
    logger.info("Data is valid! Looking for data...")
    data_for_date = data.get_data(False,
                                  category_name,
                                  monitor_name,
                                  data_name,
                                  start_date_parsed,
                                  end_date_parsed
                                  )
    logger.info("Data retrieved. Checking if it was found...")
    if data_for_date in [None, []]:
        logger.info("Data for day was not found. Returning error...")
        return generate_api_error("Data for the requested day was not found.", HTTPStatus.NOT_FOUND) #Answer with error and NOT_FOUND status code
    logger.info("Data for day was found! Returning response...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"data": data_for_date}
    )

VALID_CURRENT_STATUS_VALUES = ["open", "resolved"]
#Create incident API
def create_incident_api(incident_data):
    logger.info("Got a request to create a incident!")
    #Check for required keys
    incident_keys_validation = validate_present_keys(
        incident_data,
        [
            ("text/title", [str]),
            ("text/description", [str]),
            ("affected", [list])
        ]
    )
    if incident_keys_validation["status"] != API_STATUS_SUCCESS: #If the key validation failed
        logger.info("The key validation failed. Returning it...")
        return incident_keys_validation
    logger.info("The key validation succeeded.")
    incident_text =  incident_data["text"] #This contains the title and the description, see above
    incident_title = incident_text["title"]
    incident_description = incident_text["description"]
    incident_affected = incident_data["affected"] #(if you're wondering why the *** this is required, you can pass it as an empty list, hope that's ok for ya!)
    #Check for optional keys
    current_status = "open"
    if "current_status" in incident_data:
        #Validate current status
        logger.info("Custom current status is present. Validating...")
        if current_status not in VALID_CURRENT_STATUS_VALUES:
            logger.info("Current status value is invalid. Returning error...")
            return generate_api_error(
                f"The current_status is invalid. It must be one of {','.join(VALID_CURRENT_STATUS_VALUES)}",
                HTTPStatus.BAD_REQUEST
            )
        logger.info("Custom current status is valid. Using...")
        current_status = incident_data["current_status"]
    incident_created_at_ts = util.pretty_format_datetime((util.get_now()))
    if "timestamps" in incident_data and "created_at" in incident_data["timestamps"]:
        logger.info("Custom creation date is specified. Checking...")
        if check_date(incident_data["timestamps"]["created_at"]) == INVALID_DATE_RESPONSE:
            logger.info("Custom creation date is invalid. Returning error...")
            return generate_api_error(
                "The custom creation date for this incident seems invalid.",
                HTTPStatus.BAD_REQUEST
            )
    if incident_keys_validation["status"] != API_STATUS_SUCCESS:
        logger.info("The keys for the new incident is invalid! (keys are missing) Returning error...")
        return incident_keys_validation
    #Generate an ID for the incident. This follows the "incident_id_format" in the personalization config
    logger.info("Getting personalization settings...")
    personalization_settings = data.get_configuration("personalization")
    incident_id_format = personalization_settings["incidents"]["incident_id_format"]
    #Get current incident number, so we can determine the number for the new incident
    logger.info("Generating current incident number...")
    current_incidents_len = len(data.list_incidents_ids())
    current_incident_number = current_incidents_len + 1
    logger.info(f"New incident number: {current_incident_number}. Incident ID format: {incident_id_format}.")
    #Generate new incident ID
    logger.info("Formatting number..")
    new_incident_id = incident_id_format.format(number=current_incident_number)
    logger.info(f"New incident ID: {new_incident_id}")
    #Create incident config (this is the data.json in the incident directory)
    logger.info("Creating incident config...")
    incident_config = {
        "current_status": current_status,
        "id": new_incident_id,
        "timestamps": {
            "created_at": incident_created_at_ts,
            "solved_at": None #To set this, please update the incident, see the update API!
        },
        "text": {
            "title": incident_title,
            "description": incident_description
        },
        "events": [{
            "title": incident_title,
            "description": incident_description,
            "posted_at": incident_created_at_ts,
            "posted_by": personalization_settings["incidents"]["posted_by_name"]
        }],
        "affected": incident_affected
    }
    logger.info("Config created. Pushing changes...")
    data.create_new_incident(new_incident_id, incident_config)
    logger.info("Changes pushed. Returning success...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"message": "The creation was successful.",
         "new_incident_id": new_incident_id},
        200
    )

def get_incident_api(incident_id):
    '''API endpoint for getting an incident based on its ID.

    :param incident_id: The incident ID. Does not have to be valid (has to if you want to get a response that isn't an error though, duh?).'''
    logger.info(f"Getting incident with ID {incident_id}...")
    #Validate incident ID
    #List existing incident IDs
    existing_incident_ids = data.list_incidents_ids()
    if incident_id not in existing_incident_ids:
        logger.info("Incident ID does not exist! Returning error...")
        return generate_api_error("The requested incident ID could not be found.",
                                  HTTPStatus.NOT_FOUND)
    logger.info("Incident ID exists! Returning incident data...")
    incident_data = data.get_incident_data(incident_id)
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"data": incident_data},
        200
    )

def list_incidents_api():
    '''API endpoint for listing incidents.'''
    logger.info("Listing incident IDs...")
    incident_ids = data.list_incidents_ids()
    logger.info("Incident IDs gotten. Returning response...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"incident_ids": incident_ids},
        200
    )

VALID_INCIDENT_KEYS = [
    "/current_status",
    "/events",
    "/affected",
    "/timestamps/created_at",
    "/timestamps/solved_at",
    "/text/title",
    "/text/description"
]
REQUIRED_INCIDENT_EVENT_KEYS = [
    "/title",
    "/description",
    "/posted_by",
    "/posted_at"
]
REQUIRED_INCIDENT_AFFECTED_KEYS = [
    "/type",
    "/id",
    "/status"
]

def list_keys_in_dict(dictionary, current_step=""):
    '''A function for getting the keys in the dictionary to
    a list of strings.'''
    logger.info("Converting dict to key list...")
    present_keys = []
    for key, value in dictionary.items(): #Iterate through dictionary
        if type(value) == dict: #If the value is another dict...
            logger.debug("Value is dict, extending...")
            present_keys.extend(list_keys_in_dict(
                value,
                current_step=f"{current_step}/{key}"
            ))
        else:
            logger.debug("Value is not dict, adding...")
            present_keys.append(f"{current_step}/{key}")
    logger.info("Returning key list...")
    return present_keys

#Constants related to the function below
EXPLICIT_KEYS_CHECK_SUCCEEDED = True
def check_for_explicit_key_format(key_list, dictionary, explicit_order=False):
    '''Another function for checking present keys in a dictionary.
    However, this one explicitly enforces a format. If a key that is not in the key_list
    is found, the check fails.

    :param key_list: A list of all keys that should be checked for

    :param dictionary: The dictionary to check in.

    :param explicit_order: Whether the order of the keys can be anything (False), or
    should be the same as in key_list (True)'''
    logger.info("Checking for explicit keys in dictionary...")
    logger.debug(f"Key list: {key_list}, dictionary: {dictionary}.")
    keys_in_dictionary = list_keys_in_dict(dictionary)
    logger.info(f"Keys in dictionary (unsorted): {keys_in_dictionary}.")
    if not explicit_order:
        logger.debug("Order is not explicit, sorting lists...")
        key_list.sort() #Sort lists, we don't have to be that explicit:))
        keys_in_dictionary.sort()
    else:
        logger.debug("Lists should not be sorted (order is explicit).")
    logger.debug(f"Key list: {key_list}, keys in dictionary: {keys_in_dictionary}")
    '''#Find invalid keys
    invalid_keys = []
    for key_index in range(len(keys_in_dictionary)):
        current_key = key_list[key_index]
        key_list_value = key_list[key_index]
        key_in_dictionary_value = keys_in_dictionary[key_index]
        logger.debug(f"Key index: {key_index}. Key list value: {key_list_value}. Key in dictionary value: {key_in_dictionary_value}")
        if key_list_value != key_in_dictionary_value and key_in_dictionary_value not in key_list:
            logger.info(f"Found abnormal key {current_key}. Adding to list of invalid keys...")
            invalid_keys.append(current_key)'''
    #Find invalid keys
    invalid_keys = []
    for key in keys_in_dictionary:
        if key not in key_list:
            invalid_keys.append(key)
    if invalid_keys != []:
        logger.info("Check failed. Returning invalid keys...")
        return invalid_keys
    else:
        logger.info("Check passed! Returning True...")
        return True

def update_incident_api(incident_id, things_to_update):
    '''Function for updating an incident.

    :param incident_id: The incident ID.

    :param things_to_update: A dictionary containing the things to update.
    Remember: it is not enough to add data to APPEND, if you want to update a list, you need to
    provide the whole list and not just the stuff to add. Use the GET API to do that, babe! <3'''
    logger.info(f"Updating incident with {incident_id}...")
    logger.info("Checking length of things to update...")
    #Validate that passed data isn't empty.
    if "incident_id" in things_to_update: #...so do thos, so we can check the length
        logger.info("Deleting incident ID from things to update...")
        del things_to_update["incident_id"]
    if len(things_to_update.keys()) == 0:
        logger.info("Passed things to update is empty! Returning error...")
        return generate_api_error("You have passed empty data for what to update in this incident. Pleas try again.", HTTPStatus.BAD_REQUEST)
    logger.info("Validating incident existence...")
    #List existing incident IDs
    existing_incident_ids = data.list_incidents_ids()
    if incident_id not in existing_incident_ids:
        logger.info("Incident ID does not exist! Returning error...")
        return generate_api_error("The requested incident ID could not be found.",
                                  HTTPStatus.NOT_FOUND)
    logger.info("Incident exists! Getting incident data...")
    incident_data = data.get_incident_data(incident_id)
    #Validate that the things_to_update does not contain keys that can't exist in an incident configuration
    logger.info("Checking for invalid keys...")
    explicit_key_check = check_for_explicit_key_format(VALID_INCIDENT_KEYS, things_to_update)
    if explicit_key_check != EXPLICIT_KEYS_CHECK_SUCCEEDED:
        logger.info("Explicit key check failed! Returning error...")
        return generate_api_error(
            f"You have some keys there in your incident that are invalid. You can't upload non-existing keys! Invalid keys: {explicit_key_check}.",
            #I made a function that returns what's wrong. SO GOOD!
            HTTPStatus.BAD_REQUEST
        )
    logger.info("Explicit keys checked! Checking for things that are specified...")
    #Check for things that are specified
    current_status = None if "current_status" not in things_to_update else things_to_update["current_status"]
    timestamp_data = None if "timestamps" not in things_to_update else things_to_update["timestamps"]
    solved_at = None if timestamp_data == None else timestamp_data["solved_at"]
    created_at = None if timestamp_data == None else timestamp_data["created_at"]
    text = None if "text" not in things_to_update else things_to_update["text"]
    title = None if text == None else text["title"]
    description = None if text == None else text["description"]
    events = None if "events" not in things_to_update else things_to_update["events"]
    affected = None if "affected" not in things_to_update else things_to_update["affected"]
    #"Events" and "affected" should be double-checked if present, so invalid things are not sent!
    if events is not None:
        logger.info("Events is present. Checking events...")
        for event in events:
            logger.debug(f"Checking event {event}...")
            event_explicit_key_check = check_for_explicit_key_format(REQUIRED_INCIDENT_EVENT_KEYS,
                                                                     event)
            logger.debug(f"Explicit key check result: {event_explicit_key_check}.")
            if event_explicit_key_check != EXPLICIT_KEYS_CHECK_SUCCEEDED:
                logger.info("Explicit key check for event failed! Returning error...")
                return generate_api_error(
                    f"""You have some keys there in your event list that are invalid. You can't update non-existing keys! "
                    The event {event} has some keys that are not used by ***StatusPage and therefore can't be specified: {event_explicit_key_check}.""",
                    #I made a function that returns what's wrong. SO GOOD!
                    HTTPStatus.BAD_REQUEST
                )
            logger.debug("Explicit key check for individual event succeeded.")
        logger.info("Explicit key check for all events succeeded.")
    if affected is not None:
        logger.info("Affected is present. Checking affected...")
        for affected_component in affected:
            logger.debug(f"Checking affected component {affected_component}...")
            affected_component_explicit_key_check = check_for_explicit_key_format(REQUIRED_INCIDENT_AFFECTED_KEYS,
                                                                     affected_component)
            logger.debug(f"Explicit key check result: {affected_component_explicit_key_check}.")
            if affected_component_explicit_key_check != EXPLICIT_KEYS_CHECK_SUCCEEDED:
                logger.info("Explicit key check for affected component failed! Returning error...")
                return generate_api_error(
                    f"""You have some keys there in your affected component list that are invalid. You can't update non-existing keys! 
                    The affected component {affected_component} has some keys that are not used by ***StatusPage and therefore can't be specified: {affected_component_explicit_key_check}.""",
                    #I made a function that returns what's wrong. SO GOOD! /sotpotatis, July 20, 2021
                    HTTPStatus.BAD_REQUEST
                )
            logger.debug("""Explicit key check for individual affected component succeeded. 
            Performing additional checks...""")
            #Now, we have to check a few things here.
            affected_component_type = affected_component["type"] #We now know that this is specified because of the key validation above
            affected_component_id = affected_component["id"] #...and this too!
            #First, the affected type.
            if affected_component_type not in schema.VALID_INCIDENT_AFFECTED_COMPONENT_TYPES:
                logger.info("Affected component type is invalid. Returning error...")
                return generate_api_error(
                    f"Affected component type key for the affected component {affected_component} is invalid (must be one of {util.pretty_format_list(schema.VALID_INCIDENT_AFFECTED_COMPONENT_TYPES)}",
                    HTTPStatus.BAD_REQUEST
                )
            logger.debug("Affected component type is valid.")
            #Then, the category or the monitor, make sure they actually exist
            if affected_component_type == schema.AFFECTED_COMPONENT_CATEGORY:
                logger.debug("Type is category. Checking that it exists...")
                if affected_component_id not in data.list_categories():
                    logger.info("""Affected component ID is invalid! (is category, and not in list of category IDs). 
                    Returning error...""")
                    return generate_api_error(
                        f"Affected category ID value for the affected component {affected_component} is invalid (category does not exist)",
                        HTTPStatus.NOT_FOUND
                    )
            elif affected_component_type == schema.AFFECTED_COMPONENT_MONITOR:
                logger.debug("Type is monitor. Checking that it exists...")
                if affected_component_id not in data.list_all_monitor_ids():
                    logger.info("""Affected component ID is invalid! (is monitor, and not in list of monitor IDs). 
                    Returning error...""")
                    return generate_api_error(
                        f"""Affected monitor ID value for the affected component {affected_component} "
                        is invalid (monitor does not exist)""",
                        HTTPStatus.NOT_FOUND
                    )
            logger.debug("Checks for affected component succeeded.")
    logger.info("Updating things...")
    '''Now, check for everything to update, and update it
    (all variables that are not None should be updated!)'''
    if current_status != None:
        logger.info(f"Updating incident current status to {current_status}...")
        incident_data["current_status"] = current_status #Update the value
    if timestamp_data != None:
        logger.info(f"Updating timestamp data status to {timestamp_data}...")
        if solved_at != None:
            incident_data["timestamps"]["solved_at"] = solved_at #Update the value
        if created_at != None:
            incident_data["timestamps"]["created_at"] = created_at
    if text != None:
        logger.info(f"Updating incident text to {text}...")
        incident_data["text"] = text
    if title != None:
        logger.info(f"Updating incident title to {title}...")
        incident_data["title"] = title
    if description != None:
        logger.info(f"Updating incident description to {description}...")
        incident_data["description"] = description
    if events != None:
        logger.info(f"Updating incident events to {events}...")
        incident_data["events"] = events
    if affected != None:
        logger.info(f"Updating incident affected to {affected}...")
        incident_data["affected"] = affected
    logger.info("Updating incident data...")
    #Update the incident data
    data.write_to_incident_data_file(
        incident_id,
        incident_data
    )
    logger.info("Incident data updated successfully. Returning success message...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"message": "The incident has been successfully updated.", "associated_incident_id": incident_id},
        200
    )

def get_monitor_status_api(category_name, monitor_name):
    '''API for getting the current status of a monitor.

    :param category_name: The category name that the monitor is in.

    :param monitor_name: The monitor name.'''
    logger.info(f"Got a request to get the current status for monitor {monitor_name} in {category_name}.")
    #Validate monitor and category name
    logger.info("Validating monitor and category name...")
    monitor_validation_result = validate_category_and_monitor_name(category_name,
                                                                   monitor_name)
    if not monitor_validation_result["status"] != API_STATUS_SUCCESS:
        logger.info("The monitor name is invalid. Returning error...")
        return monitor_validation_result #Return the validation itself
    logger.info("Monitor and category name is valid. Getting current status for monitor...")
    monitor_status = get_status_for_monitor(category_name,
                                            monitor_name)
    logger.info(f"Monitor status response: {monitor_status}")
    #The response from get_status_for_monitor will look like this: {"current_status": "XXXXXXX"}
    logger.info("Generating and returning response...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        monitor_status,
        200
    )

def get_personalization_api():
    '''API endpoint for getting the current personalization settings.'''
    logger.info("Got a request to the personalization API. Getting config...")
    personalization_config = data.get_personalization_config()
    logger.info("Personalization retrieved. Returning...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"personalization": personalization_config},
        200
    )

PERSONALIZATION_CONFIG_KEY_FORMAT = [
    "/colors/base_value",
    "/header/title",
    "/header/logo/enabled",
    "/header/logo/source_url",
    "/header/logo/classes_add",
    "/header/logo/on_click_url",
    "/icons",
    "/graphs/width",
    "/graphs/height",
    "/graphs/graph_type",
    #"graphs/chart_js_options/*" - this thing can contain anything so we don't have to check for it,
    "incidents/incident_id_format",
    "incidents/posted_by_name",
    "language",
    "website_title"
]
def update_personalization_api(things_to_add_to_personalization_config):
    '''API endpoint for updating the personalization settings.'''
    logger.info("Got a request to update the website personalization settings!")
    #Validate that no invalid keys exist in the new config
    format_validation_result = check_for_explicit_key_format(PERSONALIZATION_CONFIG_KEY_FORMAT,
                                                             things_to_add_to_personalization_config)
    if format_validation_result != EXPLICIT_KEYS_CHECK_SUCCEEDED:
        logger.info("Invalid keys found. Returning error...")
        return generate_api_error("You have provided some invalid keys that can not be added to the personalization config.",
                                  HTTPStatus.BAD_REQUEST)
    logger.info("Personalization config is valid! Getting previous config and adding new stuff...")
    #Get previous personalization config
    personalization_config = data.get_personalization_config()
    logger.info("Previous configuration retrieved. Checking what to add...")
    #Check all keys and if we want to add something
    color_base_value = things_to_add_to_personalization_config["colors"] if "colors" in things_to_add_to_personalization_config and "base_value" in things_to_add_to_personalization_config else None #okay sorry this line got a bit too long. PEP violation!
    #Header stuff
    header_title = header_logo_enabled = header_logo_source_url = header_logo_classes_add = header_logo_on_click_url = None
    if "header" in things_to_add_to_personalization_config:
        logger.debug("Header config is present in things to update.")
        header_config = things_to_add_to_personalization_config["header"]
        header_title = header_config["title"] if "title" in header_config else None
        if "logo" in header_config:
            logger.debug("Logo config is present in things to update.")
            logo_config = header_config["logo"]
            header_logo_enabled = logo_config["enabled"] if "enabled" in logo_config else None
            header_logo_source_url = logo_config["source_url"] if "source_url" in logo_config else None
            header_logo_classes_add = logo_config["classes_add"] if "classes_add" in logo_config else None
            header_logo_on_click_url = logo_config["on_click_url"] if "on_click_url" in logo_config else None
    icons_config = things_to_add_to_personalization_config["icons"] if "icon" in things_to_add_to_personalization_config else None
    graphs_width = graphs_height = graphs_chart_js_options = None
    if "graphs" in things_to_add_to_personalization_config:
        graphs_config = things_to_add_to_personalization_config["graph"]
        graphs_width = graphs_config["width"] if "width" in graphs_config else None
        graphs_height = graphs_config["height"] if "height" in graphs_config else None
        graphs_chart_js_options = graphs_config["chart_js_options"] if "chart_js_options" in graphs_config else None
    incident_id_format = incidents_posted_by_name = None
    if "incidents" in things_to_add_to_personalization_config:
        incidents_config = things_to_add_to_personalization_config["incidents"]
        incident_id_format = incidents_config["incident_id_format"] if "incident_id_format" in incidents_config else None
        incidents_posted_by_name = incidents_config["posted_by_name"] if "posted_by_name" in incidents_config else None
    language = None if "language" not in things_to_add_to_personalization_config else things_to_add_to_personalization_config["language"]
    website_title = None if "website_title" not in things_to_add_to_personalization_config else things_to_add_to_personalization_config["website_title"]
    logger.info("Possible configuration values retrieved. Updating relevant values...")
    #Update relevant values
    if header_title != None:
        logger.info(f"Updating header title to {header_title}...")
        personalization_config["header"]["title"] = header_title
    if header_logo_enabled != None:
        logger.info(f"Updating header logo enabled to {header_logo_enabled}...")
        personalization_config["header"]["logo"]["enabled"] = header_logo_enabled
    if header_logo_source_url != None:
        logger.info(f"Updating header logo source URL {header_logo_source_url}...")
        personalization_config["header"]["logo"]["source_url"] = header_logo_source_url
    if header_logo_classes_add != None:
        logger.info(f"Updating header logo classes add {header_logo_classes_add}...")
        personalization_config["header"]["logo"]["classes_add"] = header_logo_classes_add
    if header_logo_on_click_url != None:
        logger.info(f"Updating header logo on click URL to {header_logo_on_click_url}...")
        personalization_config["header"]["logo"]["on_click_url"] = header_logo_on_click_url
    if icons_config != None:
        logger.info(f"Updating icon config to {icons_config}...")
        personalization_config["icons"] = icons_config
    if graphs_width != None:
        logger.info(f"Updating graphs width to {graphs_width}...")
        personalization_config["graphs"]["width"] = graphs_width
    if graphs_height != None:
        logger.info(f"Updating graphs width to {graphs_height}...")
        personalization_config["graphs"]["height"] = graphs_height
    if graphs_chart_js_options != None:
        logger.info(f"Updating graphs chart.js options to {graphs_chart_js_options}...")
        personalization_config["graphs"]["chart_js_options"] = graphs_chart_js_options
    if incident_id_format != None:
        logger.info(f"Updating incident ID format to {incident_id_format}...")
        personalization_config["incidents"]["incident_id_format"] = incident_id_format
    if incidents_posted_by_name != None:
        logger.info(f"Updating incidents posted by name to {incident_id_format}...")
        personalization_config["incidents"]["incidents_posted_by_name"] = incidents_posted_by_name
    if language != None:
        logger.debug("Language specified. Validating...")
        #Validate so that the language is valid
        if language not in schema.PLATFORM_SUPPORTED_LANGUAGES:
            logger.info("Unsupported language requested!")
            return generate_api_error(f"""You have requested to update that language config to an unsupported 
            language (supported ones, case sensitive: {util.pretty_format_list(schema.PLATFORM_SUPPORTED_LANGUAGES)})""",
                                      HTTPStatus.BAD_REQUEST) #Oops, that previous line is a bit long...
        logger.debug("Language is valid. Updating...")
        logger.info(f"Updating language to {language}...")
        personalization_config["language"] = language
    if website_title != None:
        logger.info(f"Updating website title to {website_title}...")
        personalization_config["website_title"] = website_title
    logger.info("Personalization information updated. Writing updated data...")
    data.update_json(
        data.subpath_str_to_path("personalization"),
        personalization_config
    )
    logger.info("Data updated. Returning response...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"message": "The personalizations config has been updated successfully."},
        200
    )

def create_category_api(category_id, category_config):
    '''API for creating a category.

    :param category_id: The ID for the new category.

    :param category_config. The config for the category to create.'''
    logger.info(f"Got a request to create a new category with ID {category_id}!")
    logger.debug("Checking if category exists...")
    category_id_list = data.list_categories()
    if category_id in category_id_list:
        logger.info("Category ID exists already! Returning error...")
        return generate_api_error("A category with this ID exists already.", HTTPStatus.CONFLICT)
    logger.debug("Category ID is valid. Checking config for validity...")
    #Check the category config for the required keys
    category_config_validation_result = validate_present_keys(
        category_config,
        [("name", [str]),
          ("description", [str])]
    )
    if category_config_validation_result["status"] != API_STATUS_SUCCESS:
        logger.info("The validation of the new category's configuration file failed. Returning error...")
        return category_config_validation_result #Return the result of the configuration file validation
    logger.info("Configuration file is valid, creating category...")
    #Create the new category
    data.create_category(category_id, category_config)
    logger.info("Category created. Returning successful response...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"message": "The category was created successfully."},
        200
    )

PING_CONFIG_VALIDATION_SUCCEEDED = True
def validate_ping_config(ping_config):
    '''Function for validating the ping config for a monitor.
    If the validation succeeded, the function returns PING_CONFIG_VALIDATION_SUCCEEDED. If not, it returns an API error
    that can be passed on to the user.

     :param ping_config: The ping config to validate.'''
    logger.debug(f"Ping config: {ping_config}.")
    logger.debug("Validating ping config...")
    monitor_ping_key_validation = validate_present_keys(ping_config,
                                                        [
                                                            ("enabled", [bool]),
                                                            ("pings", [list])
                                                        ])
    if monitor_ping_key_validation["status"] != API_STATUS_SUCCESS:
        logger.info("The key validation was not successful. Returning error...")
        return monitor_ping_key_validation #Return the response of the unsuccessful request
    logger.debug("Key validation was successful. Validating pings list...")
    #The list "pings" should contain dicts following a desired format
    ping_number = 0
    for ping in ping_config["pings"]: #Iterate through all pings and check
        logger.debug(f"Checking ping {ping}...")
        if type(ping) != dict: #The ping should be a dict
            logger.info("The ping is not a dictionary! Returning error...")
            return generate_api_error("One of the pings you are trying to set has not been passed as a dictionary.",
                                      HTTPStatus.BAD_REQUEST) #Return an error
        logger.debug("Dictionary type validation succeeded, checking keys...")
        ping_key_validation = validate_present_keys(ping, #Validate the keys in the ping
                                                    [
                                                        ("ping_name", [str]),
                                                        ("timeout_minutes", [int]),
                                                        ("data_prefix", [str]),
                                                        ("reporting_frequency_minutes", [int]),
                                                        ("status_on_timeout", [int]),
                                                        ("plot/plot_data", [bool]),
                                                        ("plot/plot_information/title", [str]),
                                                        ("plot/plot_information/description", [str]),
                                                        ("plot/plot_information/plot_number_of_datapoints", [int, None])
                                                    ])
        if ping_key_validation["status"] != API_STATUS_SUCCESS:
            logger.info("The ping key validation failed! Returning error...")
            return ping_key_validation
        logger.debug("The ping key validation succeeded. All good, moving on to next ping...")
        ping_number += 1
    logger.debug("Passed ping key config validated. Returning success...")
    return PING_CONFIG_VALIDATION_SUCCEEDED #Return an indication of success

def create_monitor_api(new_monitor_category, new_monitor_id, new_monitor_basic_config, new_monitor_ping_config):
    '''API endpoint for creating a new monitor.

    :param new_monitor_category: The category that the new monitor is in.

    :param new_monitor_id: The ID of the new monitor

    :param new_monitor_basic_config: The basic configuration file for the new monitor.

    :param new_monitor_ping_config: The ping configuration of the new monitor.'''
    logger.info(f"Got a request to create a new monitor with ID {new_monitor_id}.")
    #Validate that the monitor category exists
    logger.debug("Checking category existence...")
    if new_monitor_category not in data.list_categories():
        logger.info("Invalid monitor category - category does not exist! Returning error...")
        return generate_api_error("The category that you are trying to put the monitor in does not exist! (ID does not exist)",
                                  HTTPStatus.BAD_REQUEST)
    logger.debug("Monitor category exists. Checking for ID...")
    #Make sure that the monitor ID doesn't previously exist
    logger.debug("Checking for monitor ID conflict...")
    if new_monitor_id in data.list_monitors(new_monitor_category):
        logger.info("Monitor ID does already exist. Returning error...")
        return generate_api_error("The monitor ID does already exist. You can't create duplicate monitors!",
                                  HTTPStatus.CONFLICT)
    logger.debug("Monitor ID is valid. Validating basic config...")
    monitor_basic_config_validation = validate_present_keys(new_monitor_basic_config,
                                                            [("name", [str]),
                                                             ("id", [str]),
                                                             ("description", [str]),
                                                             ("default_status", [str])])
    if monitor_basic_config_validation["status"] != API_STATUS_SUCCESS: #Check if the basic config key validation succeeded
        logger.info("The key validation was not successful! Returning error...")
        return monitor_basic_config_validation
    logger.debug("Monitor basic config is valid. Checking ping (if exists)...")
    #The ping config is optional. It can be passed as None, but we want to validate it if it has been passed
    if new_monitor_ping_config != None:
        logger.debug("Ping config has been passed. Validating keys...")
        ping_config_validation = validate_ping_config(new_monitor_ping_config)
        if ping_config_validation != PING_CONFIG_VALIDATION_SUCCEEDED:
            logger.info("The ping config failed. Returning error...")
            return ping_config_validation
        else:
            logger.debug("The ping config validation succeeded.")
    logger.info("Creating monitor...")
    data.create_monitor(new_monitor_category, new_monitor_id, new_monitor_basic_config, new_monitor_ping_config)
    logger.info("Monitor created successfully. Returning success...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"message": "Monitor created successfully."},
        200
    )

def update_category_api(category_id, things_to_update):
    '''API function for updating the configuration of a category.

    :param category_id: The category ID to udpate.

    :param things_to_update: The things to update in a dict.'''
    logger.info(f"Updating category with ID {category_id}...")
    #First, we neeed to check if the category ID is valid (duh!)
    logger.debug("Checking category ID...")
    category_id_list = data.list_categories()
    if category_id not in category_id_list:
        logger.info("Category ID does not exist. Returning error...")
        return generate_api_error("A category with this ID could not be found.", HTTPStatus.NOT_FOUND)
    logger.debug("Category ID is valid. Validating things to update...")
    category_explicit_keys_check = check_for_explicit_key_format(["/name", "/description"], things_to_update)
    if category_explicit_keys_check != EXPLICIT_KEYS_CHECK_SUCCEEDED:
        logger.info("Some of the keys in the category things to update is invalid. Returning error...")
        return generate_api_error("You have provided some keys for the category config that is invalid.", HTTPStatus.BAD_REQUEST)
    logger.debug("The category keys to update is ok! Getting current config and updating keys...")
    #Get the current config
    current_category_config = data.get_category_config(category_id)
    if "name" in things_to_update:
        logger.debug("Updating name...")
        current_category_config["name"] = things_to_update["name"]
    if "description" in things_to_update:
        logger.info("Updating description...")
        current_category_config["description"] = things_to_update["description"]
    logger.debug("Writing updated config...")
    category_config_path = data.subpath_str_to_path(f"monitors/categories/{category_id}/config")
    data.update_json(category_config_path, current_category_config)
    logger.info("Category updated. Returning response...")
    return generate_api_response(API_STATUS_SUCCESS,
                                 {"message": "The category config has been updated."},
                                 200)

def update_monitor_api(category_id, monitor_id, things_to_update):
    '''Function for updating a monitor's configuration.

    :param category_id: The ID for the category that the monitor is in

    :param monitor_id: The ID of the monitor.

    :param things_to_update: A dictionary with the things to update.'''
    logger.info(f"Got a request to update monitor {monitor_id} in category {category_id}...")
    #Validate that the monitor and category exists
    logger.debug("Validating that monitor and category exists...")
    if not os.path.exists(data.get_monitor_dir(category_id, monitor_id)):
        logger.info("The monitor or category does not exist! Returning error...")
        return generate_api_error("The requested monitor or category does not exist.", HTTPStatus.BAD_REQUEST)
    logger.debug("The monitor and category exists. Validating things to update format...")
    #The things_to_update does not have to include all of this, but it can't have anything that looks wacky and is an invalid key!
    things_to_update_validation = check_for_explicit_key_format(["/name", "/id", "/description", "/default_status"], things_to_update)
    if things_to_update_validation != EXPLICIT_KEYS_CHECK_SUCCEEDED:
        logger.info("Some of the keys in the monitor things to update is invalid. Returning error...")
        return generate_api_error("You have provided some keys for the monitor config that is invalid.", HTTPStatus.BAD_REQUEST)
    logger.debug("Config for monitor is valid. Getting previous config and updating parameters...")
    monitor_config = data.get_monitor_config(category_id, monitor_id)
    #Update stuff that should be updated
    if "name" in things_to_update:
        logger.debug("Updating name...")
        monitor_config["name"] = things_to_update["name"]
    if "id" in things_to_update:
        logger.debug("Updating ID...")
        monitor_config["id"] = things_to_update["id"]
    if "description" in things_to_update:
        logger.debug("Updating description...")
        monitor_config["description"] = things_to_update["description"]
    if "default_status" in things_to_update:
        logger.debug("Updating default status...")
        monitor_config["default_status"] = things_to_update["default_status"]
    logger.debug("Set things updated. Writing changes...")
    monitor_config_path = data.subpath_str_to_path(f"{data.get_monitor_subpath(category_id, monitor_id)}/basic_config") #The path for the monitor configuration file (basic_config.json)
    data.update_json(monitor_config_path, monitor_config)
    logger.info("Monitor config updated. Returning response...")
    return generate_api_response(API_STATUS_SUCCESS,
                                 {"message": "The monitor config has been successfully updated."},
                                 200)

def update_monitor_ping_config(category_id, monitor_id, ping_config):
    '''API to update the ping config for a monitor.

    :param category_id: The category ID that the monitor is in.

    :param monitor_id: The monitor ID for the monitor

    :param new_ping_config: The new ping config. Must be complete, aka the complete ping configuration file, not just the ping to add.'''
    logger.info(f"Got a request to update the monitor ping config for monitor {monitor_id}, category {category_id}.")
    #Validate that the monitor and the category ID exists
    monitor_subpath = data.get_monitor_subpath(category_id, monitor_id)
    monitor_path = data.get_monitor_dir(category_id, monitor_id)
    if not os.path.exists(monitor_path):
        logger.info("The monitor or category does not exist! Returning error...")
        return generate_api_error("The requested monitor or category does not exist.", HTTPStatus.NOT_FOUND)
    logger.debug("The monitor exists! Validating ping config...")
    ping_config_validation = validate_ping_config(ping_config)
    if ping_config_validation != PING_CONFIG_VALIDATION_SUCCEEDED:
        logger.info("The ping config validation failed! Returning error...")
        return ping_config_validation #The validate_ping_config will return the error
    logger.debug("Ping config validation succeeded. Updating ping JSON config...")
    #Get the ping JSON configuration path
    ping_json_path = data.subpath_str_to_path(f"{monitor_subpath}/pings")
    data.update_json(ping_json_path, ping_config)
    logger.debug("JSON config file updated.")
    logger.info("Ping configuration successfully updated. Returning success response...")
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"message": "The ping configuration was updated successfully."},
        200
    )

def delete_category_api(category_id):
    '''API to delete a category.

    :param category_id: The category ID to delete'''
    logger.info(f"Got a request to delete the category ID {category_id}...")
    #Check if the category ID exists
    category_id_list = data.list_categories()
    if category_id not in category_id_list:
        logger.info("Category ID does not exist. Returning error...")
        return generate_api_error("A category with this ID could not be found.", HTTPStatus.NOT_FOUND)
    logger.debug("Category exists. Getting directory path...")
    category_path = data.subpath_str_to_path(f"monitors/categories/{category_id}", is_json_file=False)
    logger.debug(f"Category path: {category_path}. Deleting...")
    #Delete the category path using shutil.rmtree
    shutil.rmtree(category_path)
    logger.info("The category has been deleted successfully.")
    return generate_api_response(API_STATUS_SUCCESS,
                                 {"message": "The category has been successfully deleted."},
                                 200)

def delete_monitor_api(category_id, monitor_id):
    '''API to delete a monitor.

    :param category_id: The category ID that the monitor has.

    :param monitor_id: The monitor ID to delete'''
    logger.info(f"Got a request to delete the monitor ID {monitor_id}, monitor category {category_id}...")
    #Check if the monitor ID exists
    monitor_subpath = data.get_monitor_subpath(category_id, monitor_id)
    logger.debug(f"Monitor subpath: {monitor_subpath}.")
    monitor_path = data.subpath_str_to_path(monitor_subpath, is_json_file=False)
    if not os.path.exists(monitor_path):
        logger.info("Category or monitor ID does not exist. Returning error...")
        return generate_api_error("The requested monitor could not be found.", HTTPStatus.NOT_FOUND)
    logger.debug("Monitor exists. Deleting...")
    #Delete the monitor path using shutil.rmtree. This works even if there are files in the monitor directory.
    shutil.rmtree(monitor_path)
    logger.info("The monitor has been deleted successfully.")
    return generate_api_response(API_STATUS_SUCCESS,
                                 {"message": "The monitor has been successfully deleted."},
                                 200)

def list_categories_api():
    '''API endpoint to list categories. Really simple since it is mostly dependent on another function.'''
    logger.info("Got a request to the categories API! Generating and returning response...")
    #List categories
    category_list = data.list_categories()
    logger.debug("Categories listed. Returning response...")
    return generate_api_response(API_STATUS_SUCCESS,
                                 {"category_ids": category_list},
                                 200)

def list_monitors_api(category_id):
    '''API endpoint to list monitors in a given category.

    :param category_id: The category ID to list monitors in.'''
    logger.info("Got a request to the list monitors API!")
    #Validate that the category ID exists
    logger.debug(f"Validating passed category ID: {category_id}...")
    if category_id not in data.list_categories():
        logger.info("The category ID is invalid (does not exist)! Returning error...")
        return generate_api_error("The category ID that you have passed does not exist.",
                                  HTTPStatus.NOT_FOUND)
    logger.debug("Category ID is valid. Returning response...")
    monitor_list = data.list_monitors(category_id)
    return generate_api_response(
        API_STATUS_SUCCESS,
        {"monitors": monitor_list}
    )
