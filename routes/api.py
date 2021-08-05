'''API.py
Routes responsible for the REST API bit.
And [bleep] yeah, this API will do a lot of stuff! JSON <3
'''
from flask import Blueprint, request, jsonify
import logging, internal_libraries.data as data, internal_libraries.api as api
from http import HTTPStatus
api_app = Blueprint(__name__, "api") #API blueprint

#Logging!
logger = logging.getLogger(__name__)
#Main configuration for logging
logging.basicConfig(level=logging.DEBUG)

#API routes, there we go!
@api_app.route("/api/data", methods=["GET", "POST"])
def data():
    '''This endpoint allows a monitor to report data. This data will be grouped by day
    and can be used for plotting things, for instance.
    A GET request retrieves data. A POST request posts data.'''
    logger.info("Got a request to /api/data!")
    logger.info("Validating authorization...")
    #Validate authorization
    authorization_validation_result = api.check_user_authentication_from_request(request, api.API_ENDPOINT_REPORT_DATA if request.method == "POST" else api.API_ENDPOINT_GET_DATA)
    if authorization_validation_result["status"] != api.API_STATUS_SUCCESS:
        logger.info("Authorization was not successful! Handling error...")
        return jsonify(authorization_validation_result), authorization_validation_result["status_code"]
    logger.info("Authorization is valid.")
    #We can assume that request.json != None and that JSON actually has been specified since it's required for an approved auth
    request_json = request.json
    del request_json["user_id"] #Remove the user ID from the request
    #Check which method to use.
    if request.method == "GET":
        logger.info("Request method is GET! Checking for required request parameters...")
        present_keys_validation = api.validate_present_keys(request_json,
                                                            [("category_id", [str]), ("monitor_id", [str]), ("data_name", [str]), ("start_ts", [str]),
                                                             ("end_ts", [str])])
        if present_keys_validation["status"] != api.API_STATUS_SUCCESS:
            logger.info("The present key validation failed! Returning error...")
            return jsonify(present_keys_validation), present_keys_validation["status_code"]
        logger.info("Keys are present! Getting data...")
        category_name = request_json["category_id"]
        monitor_name = request_json["monitor_id"]
        data_name = request_json["data_name"]
        start_timestamp = request_json["start_ts"]
        end_timestamp = request_json["end_ts"]
        get_data_api_response = api.get_data_api(
            category_name,
            monitor_name,
            data_name,
            start_timestamp,
            end_timestamp
        )
        logger.info(f"Get data API response: {get_data_api_response}. Returning...")
        return jsonify(get_data_api_response), api.get_status_code_from_api_response(get_data_api_response) #Return response
    elif request.method == "POST":
        logger.info("Request method is POST! Checking for required request parameters...")
        '''This method will add to the data that the monitor has reported. So, required keys here
        are the data name, and the data to add. NOTE: The data to add can be any type, but it must be JSON-serializable.
        Also, it must be an int, a float, or a bool to be plotted using Chart.js.'''

        present_keys_validation = api.validate_present_keys(request_json,
                                  [("category_id", [str]), ("monitor_id", [str]), ("data_name", [str]), ("value", None)])
        if present_keys_validation["status"] != api.API_STATUS_SUCCESS:
            logger.info("The present key validation failed! Returning error...")
            return jsonify(present_keys_validation), present_keys_validation["status_code"]
        logger.info("Keys are present! Adding data...")
        category_name = request_json["category_id"]
        monitor_name = request_json["monitor_id"]
        data_name = request_json["data_name"]
        value_to_add = request_json["value"]
        add_data_api_response = api.add_data_api(
            category_name,
            monitor_name,
            data_name,
            value_to_add
        )
        logger.info(f"Response from data addition: {add_data_api_response}. Returning response...")
        return jsonify(add_data_api_response), api.get_status_code_from_api_response(add_data_api_response)

@api_app.route("/api/incidents", methods=["GET", "POST", "PUT"])
def incidents_api():
    '''The incident API allows one to get, create, and update incidents.
    In really beautiful API methodology, a GET gets an incident, a POST creates an incident,
    and PUT updates an incident.'''
    logger.info("Got a request to the incidents API!")
    logger.info("Validating authorization...")
    #Validate authorization
    if request.method == "GET":
        accessed_api_endpoint = api.API_ENDPOINT_GET_INCIDENT
    elif request.method == "POST":
        accessed_api_endpoint = api.API_ENDPOINT_ADD_INCIDENT
    elif request.method == "PUT":
        accessed_api_endpoint = api.API_ENDPOINT_UPDATE_INCIDENT
    logger.debug(f"Accessed API endpoint: {accessed_api_endpoint}")
    authorization_validation_result = api.check_user_authentication_from_request(request,accessed_api_endpoint)
    if authorization_validation_result["status"] != api.API_STATUS_SUCCESS:
        logger.info("Authorization was not successful! Handling error...")
        return jsonify(authorization_validation_result), authorization_validation_result["status_code"]
    logger.info("Authorization is valid.")
    #We can assume that request.json != None and that JSON actually has been specified since it's required for an approved auth
    request_json = request.json
    del request_json["user_id"] #Remove the user ID from the request
    logger.info("Checking request method...")
    if request.method == "POST": #POST - CREATE incident data. Sexy!
        logger.info("The request method is POST! Creating new incident...")
        incident_api_response = api.create_incident_api(request_json)
        logger.info(f"Incident API response: {incident_api_response}. Returning...")
        return jsonify(incident_api_response), incident_api_response["status_code"] #Return the response
    elif request.method == "GET": #GET - GET incident data! UwU!
        logger.info("The request method is GET! Validating keys for incident ID...")
        #The incident ID must be specified
        key_validation_result = api.validate_present_keys(
            request_json,
            [("incident_id", [str])]
        )
        if key_validation_result["status"] != api.API_STATUS_SUCCESS:
            logger.info("Request is not valid, keys are not present! Returning error...")
            return jsonify(key_validation_result), key_validation_result["status_code"]
        logger.info("Keys are present, getting incident...")
        incident_id = request_json["incident_id"]
        get_incident_api_response = api.get_incident_api(incident_id)
        logger.debug(f"API response: {get_incident_api_response}")
        logger.info("API response gotten. Returning response...")
        return jsonify(get_incident_api_response), get_incident_api_response["status_code"]
    elif request.method == "PUT": #PUT - update existing incident
        logger.info("The request method is PUT! Updating existing incident...")
        logger.info("Validating keys...")
        #We want to provide the keys to update, or the user want to provide that. So, let's grab it!
        key_validation_result = api.validate_present_keys(
            request_json,
            [("incident_id", [str]), ("data_to_update", [dict])]
        )
        if key_validation_result["status"] != api.API_STATUS_SUCCESS:
            logger.info("Request is not valid, keys are not present! Returning error...")
            return jsonify(key_validation_result), key_validation_result["status_code"]
        logger.info("Keys are present, updating incident...")
        incident_id = request_json["incident_id"]
        data_to_update = request_json["data_to_update"]
        logger.info(f"Incident ID: {incident_id}, data to update: {data_to_update}. Updating...")
        update_incident_api_response = api.update_incident_api(incident_id,
                                data_to_update)
        logger.info(f"Update incident API response: {update_incident_api_response}. Returning...")
        return jsonify(update_incident_api_response), update_incident_api_response["status_code"] #Return the response
@api_app.route("/api/incidents/list", methods=["GET"])
def list_incidents_api():
    '''This API endpoint allows for listing incidents.'''
    logger.info("Got a request to the incident listing API!")
    logger.info("Validating authorization...")
    #Validate authorization
    authorization_validation_result = api.check_user_authentication_from_request(request, api.API_ENDPOINT_LIST_INCIDENTS)
    if authorization_validation_result["status"] != api.API_STATUS_SUCCESS:
        logger.info("Authorization was not successful! Handling error...")
        return jsonify(authorization_validation_result), authorization_validation_result["status_code"]
    logger.info("Authorization is valid.")
    list_incidents_api_response = api.list_incidents_api()
    logger.debug(f"Incidents API response: {list_incidents_api_response}")
    logger.info("Returning API response...")
    return jsonify(list_incidents_api_response), list_incidents_api_response["status_code"]

#Monitor-related APIs
@api_app.route("/api/monitor_status", methods=["GET"])
def monitor_status():
    '''The monitor_status API allows you to get the current status of a monitor.
    Perfect to ping from a script somewhere else to notify you in case the ping times out,
    or just to use for idk! Whatever you want it to, sweetheart <3'''
    logger.info("Got a request to the monitor status API!")
    logger.info("Validating authorization...")
    #Validate authorization
    authorization_validation_result = api.check_user_authentication_from_request(request, api.API_ENDPOINT_GET_MONITOR_STATUS)
    if authorization_validation_result["status"] != api.API_STATUS_SUCCESS:
        logger.info("Authorization was not successful! Handling error...")
        return jsonify(authorization_validation_result), authorization_validation_result["status_code"]
    logger.info("Authorization is valid.")
    request_json = request.json #We know this exists since it is valid for a successful authorization check
    #Validate present keys (we want the category id and the monitor id)
    logger.info("Validating present keys...")
    required_keys_check = api.validate_present_keys(request_json,
                                                    [("category_id", [str]),
                                                     ("monitor_id", [str])])
    if required_keys_check["status"] != api.API_STATUS_SUCCESS:
        logger.info("The present key validation failed! Returning error status...")
        return jsonify(required_keys_check), required_keys_check["status_code"]
    logger.info("Present key validation is successful. Getting response...")
    category_id = request_json["category_id"]
    monitor_id = request_json["monitor_id"]
    monitor_status_response = api.get_status_for_monitor(category_id, monitor_id)
    logger.info(f"Response from monitor status API: {monitor_status_response}. Returning response...")
    return jsonify(monitor_status_response), monitor_status_response["status_code"]

@api_app.route("/api/monitors", methods=["POST", "PUT", "DELETE"])
def monitors_api():
    '''The monitors API allows to create, update or delete monitors.
    TODO: Wishlist: add option to GET monitor config.'''
    logger.info("Got a request to the monitor API!")
    #Determinate the used endpoint used for permission control
    logger.info("Determining used endpoint...")
    if request.method == "POST":
        #POST - create a new monitor
        used_endpoint = api.API_ENDPOINT_CREATE_MONITOR
    elif request.method == "PUT":
        #PUT - update a monitor (the basic_config file or the ping)
        '''Whether the basic_config or the ping should be updated is decided
        by the parameter "update_config_type". If it isn't present or valid here, we can know it and already return an error.
        '''
        logger.debug("Method is PUT. Checking for keys...")
        if request.json == None or "update_config_type" not in request.json or request.json["update_config_type"] not in ["basic_config", "ping"]: #This key must be in the JSON
            logger.info("The update_config_type is invalid!")
            return jsonify(api.generate_api_error(
                "The parameter \"update_config_type\" is not present in the request or is invalid.",
                HTTPStatus.BAD_REQUEST
            )), HTTPStatus.BAD_REQUEST
        #Now we know the update config type!
        update_config_type = request.json["update_config_type"]
        if update_config_type == "basic_config":
            used_endpoint = api.API_ENDPOINT_UPDATE_MONITOR_CONFIG
        elif update_config_type == "ping":
            used_endpoint = api.API_ENDPOINT_UPDATE_MONITOR_PINGS
    elif request.method == "DELETE":
        #DELETE - delete a monitor
        used_endpoint = api.API_ENDPOINT_DELETE_MONITOR
    logger.info("Validating authorization...")
    #Validate authorization
    authorization_validation_result = api.check_user_authentication_from_request(request, used_endpoint)
    if authorization_validation_result["status"] != api.API_STATUS_SUCCESS:
        logger.info("Authorization was not successful! Handling error...")
        return jsonify(authorization_validation_result), authorization_validation_result["status_code"]
    logger.info("Authorization is valid.")
    request_json = request.json #We know this exists since it is valid for a successful authorization check
    #These keys in the JSON are required for all endpoints - so we can check them right here
    logger.debug("Checking for globally required monitor keys...")
    request_keys_check = api.validate_present_keys(
        request_json,
        [("monitor_category", [str]),
         ("monitor_id", [str])])
    if request_keys_check["status"] != api.API_STATUS_SUCCESS:
        logger.info("Globally required keys are missing! Returning error...")
        return jsonify(request_keys_check), request_keys_check["status"]
    logger.debug("Globally required keys are ok.")
    #Now, check the endpoint and apply applicable code
    logger.info("Executing endpoint specific code...")

    monitor_category = request_json["monitor_category"]
    monitor_id = request_json["monitor_id"]
    if used_endpoint == api.API_ENDPOINT_CREATE_MONITOR: #Post monitor (create monitor)
        logger.info("Executing monitor creation code...")
        '''Get keys from request:
        Required:
        - monitor_category (checked above)
        - monitor_id (checked above)
        - monitor_basic_config
        Optional:
        - monitor_pings_config'''
        logger.debug("Validating keys...")
        request_keys_check = api.validate_present_keys(
            request_json,
            [("monitor_basic_config", [dict])]
        )
        #Check response from key validation
        if request_keys_check["status"] != api.API_STATUS_SUCCESS:
            logger.info("The request contains invalid keys. Returning error...")
            return jsonify(request_keys_check), request_keys_check["status_code"] #The keys check return the error - so perfect!
        logger.debug("Keys seem ok. Getting values...")
        monitor_basic_config = request_json["monitor_basic_config"]
        logger.debug("Checking for pings config...")
        '''The pings config is optional. If not specified, it will be the default.
        (if specified, it will be validated later!)
        '''
        if "monitor_pings_config" in request_json:
            logger.debug("Pings config is specified. Using...")
            monitor_pings_config = request_json["monitor_pings_config"]
        else:
            logger.debug("Pings config is not specified. Using None...")
            monitor_pings_config = None
        monitor_creation_api_response = api.create_monitor_api(
            monitor_category,
            monitor_id,
            monitor_basic_config,
            monitor_pings_config
        )
        logger.debug(f"Response from API: {monitor_creation_api_response}. Returning...")
        return jsonify(monitor_creation_api_response), monitor_creation_api_response["status_code"] #Return the response.
    logger.debug("Checking for required key...")
    #The required key for this endpoint apart from the category and ID checked above is "config"
    if used_endpoint == api.API_ENDPOINT_UPDATE_MONITOR_CONFIG:
        logger.info("Updating monitor...")
        create_monitor_present_key_check = api.validate_present_keys(request_json,
                                                                     [("data_to_update", [dict])])
        #Check if the check was valid
        if create_monitor_present_key_check["status"] != api.API_STATUS_SUCCESS:
            logger.info("Keys are missing or invalid! Returning error...")
            return jsonify(create_monitor_present_key_check), create_monitor_present_key_check["status_code"]
        logger.info("Keys are valid. Executing API function...")
        data_to_update = request_json["data_to_update"]
        update_monitor_response = api.update_monitor_api(monitor_category, monitor_id, data_to_update)
        logger.info(f"Response from API: {update_monitor_response}. Returning...")
        return jsonify(update_monitor_response), update_monitor_response["status_code"]
    elif used_endpoint == api.API_ENDPOINT_UPDATE_MONITOR_PINGS:
        #The required key for this endpoint apart from the category and ID checked above is the data to update, "data_to_update"
        update_monitor_present_key_check = api.validate_present_keys(request_json,
                                                                     [("config", [dict])])
        #Check if the check was valid
        if update_monitor_present_key_check["status"] != api.API_STATUS_SUCCESS:
            logger.info("Keys are missing or invalid! Returning error...")
            return jsonify(update_monitor_present_key_check), update_monitor_present_key_check["status_code"]
        logger.info("Keys are valid. Executing API function...")
        config_value = request_json["config"]
        logger.info("Updating monitor pings...")
        update_monitor_ping_config_response = api.update_monitor_ping_config(monitor_category, monitor_id, config_value)
        logger.info(f"Response from API: {update_monitor_ping_config_response}. Returning...")
        return jsonify(update_monitor_ping_config_response), update_monitor_ping_config_response["status_code"]
    elif used_endpoint == api.API_ENDPOINT_DELETE_MONITOR:
        logger.info("Endpoint is delete monitor. Performing API action...")
        #We don't need to get any other keys here, since the monitor ID and category ID will already have been retrieved above.
        delete_monitor_response = api.delete_monitor_api(monitor_category, monitor_id)
        logger.info(f"Response from API: {delete_monitor_response}. Returning...")
        return jsonify(delete_monitor_response), delete_monitor_response["status_code"] #Return the response

@api_app.route("/api/categories", methods=["POST", "PUT", "DELETE"])
def categories_api():
    '''The categories API allows to create, update or delete the configuration of categories.'''
    logger.info("Got a request to the category API!")
    #Determinate the used endpoint
    if request.method == "POST":
        logger.info("Used method is POST.")
        used_endpoint = api.API_ENDPOINT_CREATE_CATEGORY
    elif request.method == "PUT":
        logger.info("Used method is PUT.")
        used_endpoint = api.API_ENDPOINT_UPDATE_CATEGORY_CONFIG
    elif request.method == "DELETE":
        logger.info("Used method is DELETE.")
        used_endpoint = api.API_ENDPOINT_DELETE_CATEGORY
    logger.info("Validating authorization...")
    #Validate authorization
    authorization_validation_result = api.check_user_authentication_from_request(request, used_endpoint)
    if authorization_validation_result["status"] != api.API_STATUS_SUCCESS:
        logger.info("Authorization was not successful! Handling error...")
        return jsonify(authorization_validation_result), authorization_validation_result["status_code"]
    logger.info("Authorization is valid.")
    request_json = request.json #We know this exists since it is valid for a successful authorization check
    #These keys in the JSON are required for all endpoints - so we can check them right here
    logger.debug("Checking for globally required category keys...")
    request_keys_check = api.validate_present_keys(request_json, [("category_id", [str])])
    if request_keys_check["status"] != api.API_STATUS_SUCCESS:
        logger.info("Globally required keys are missing! Returning error...")
        return jsonify(request_keys_check), request_keys_check["status"]
    logger.debug("Globally required keys are ok.")
    #Get the category ID
    category_id = request_json["category_id"]
    #Now, check the endpoint and apply applicable code
    logger.info("Executing endpoint specific code...")

    if used_endpoint == api.API_ENDPOINT_CREATE_CATEGORY: #If the endpoint is to create a category
        logger.debug("Executing category creation code...")
        #The creation of a category needs one value, the config
        create_or_update_category_key_validation = api.validate_present_keys(request_json, [("config", [dict])])
        if create_or_update_category_key_validation["status"] != api.API_STATUS_SUCCESS:
            logger.info("Required keys for category creation are missing! Returning error...")
            return jsonify(create_or_update_category_key_validation), create_or_update_category_key_validation["status"]
        config_value = request_json["config"] #Get the config
        category_creation_response = api.create_category_api(category_id, config_value)
        logger.info(f"Response from API: {category_creation_response}. Returning...")
        return jsonify(category_creation_response), category_creation_response["status_code"] #Return the response
    elif used_endpoint == api.API_ENDPOINT_UPDATE_CATEGORY_CONFIG: #If the endpoint is to update a category
        logger.debug("Executing category updating code...")
        #The updating of a category needs one value, the things to update
        logger.debug("Checking keys...")
        update_category_key_validation = api.validate_present_keys(request_json, [("data_to_update", [dict])])
        if update_category_key_validation["status"] != api.API_STATUS_SUCCESS:
            logger.info("Required keys for category creation are missing! Returning error...")
            return jsonify(update_category_key_validation), update_category_key_validation["status"]
        logger.debug("Keys are valid.")
        data_to_update = request_json["data_to_update"]
        category_creation_response = api.update_category_api(category_id, data_to_update) #The config value here is
        logger.info(f"Response from API: {category_creation_response}. Returning...")
        return jsonify(category_creation_response), category_creation_response["status_code"] #Return the response
    elif used_endpoint == api.API_ENDPOINT_DELETE_CATEGORY: #If the endpoint is to delete a category
        logger.debug("Executing category deletion code...")
        #(we only need to know the category ID for the deletion, and we know that)
        category_deletion_response = api.delete_category_api(category_id)
        logger.info(f"Response from category deletion API: {category_deletion_response}. Returning...")
        return jsonify(category_deletion_response), category_deletion_response["status_code"]

@api_app.route("/api/categories/list")
def list_categories_api():
    '''The category listing API returns a list of categories.'''
    logger.info("Got a request to the category listing API!")
    logger.info("Validating authorization...")
    #Validate authorization
    authorization_validation_result = api.check_user_authentication_from_request(request, api.API_ENDPOINT_LIST_CATEGORIES)
    if authorization_validation_result["status"] != api.API_STATUS_SUCCESS:
        logger.info("Authorization was not successful! Handling error...")
        return jsonify(authorization_validation_result), authorization_validation_result["status_code"]
    logger.info("Authorization is valid.")
    #...and that's it! We can now generate and return a response.
    logger.info("Retrieving response...")
    list_categories_api_response = api.list_categories_api()
    logger.info(f"Response from category listing API: {list_categories_api_response}. Returning...")
    return jsonify(list_categories_api_response), list_categories_api_response["status_code"]

#Configuration update APIs
@api_app.route("/api/personalization", methods=["GET", "PUT"])
def personalization_api():
    '''The personalization API allows you to make changes or get the personalization
    configuration on the server. Here's hi to automated seasonal logos, like favicons!
    Wholesome, innit?'''
    logger.info("Got a request to the personalization API!")
    #Check authorization
    logger.info("Validating authorization...")
    #Validate authorization
    authorization_validation_result = api.check_user_authentication_from_request(request, api.API_ENDPOINT_GET_PERSONALIZATION_CONFIG if request.method == "GET" else api.API_ENDPOINT_UPDATE_PERSONALIZATION_CONFIG)
    if authorization_validation_result["status"] != api.API_STATUS_SUCCESS:
        logger.info("Authorization was not successful! Handling error...")
        return jsonify(authorization_validation_result), authorization_validation_result["status_code"]
    logger.info("Authorization is valid.")
    request_json = request.json #We know this exists since it is valid for a successful authorization check
    #Determinate method and scope
    if request.method == "GET":
        logger.info("Request method is GET. Returning personalization config...")
        #Return personalization config
        get_personalization_api_response = api.get_personalization_api()
        return jsonify(get_personalization_api_response), get_personalization_api_response["status_code"]
    elif request.method == "PUT":
        logger.info("Request method is PUT. Validating required keys...")
        #Required keys, since we need to update some type of data... duh?
        required_keys_check = api.validate_present_keys(request_json,
                                                        [("data_to_update", [dict])])
        if required_keys_check["status"] != api.API_STATUS_SUCCESS:
            logger.info("The present key validation failed! Returning error status...")
            return jsonify(required_keys_check), required_keys_check["status_code"]
        logger.info("The present key validation seems ok. Returning API response...")
        data_to_update = request_json["data_to_update"]
        update_personalization_api_response = api.update_personalization_api(data_to_update)
        logger.info(f"Response from API: {update_personalization_api_response}. Returning...")
        return jsonify(update_personalization_api_response), update_personalization_api_response["status_code"]

@api_app.route("/api/monitors/list", methods=["GET"])
def list_monitors_api():
    '''The monitor listing API allows to list monitors in a certain category.'''
    logger.info("Got a request to the monitor listing API!")
    logger.info("Validating authorization...")
    #Validate authorization
    authorization_validation_result = api.check_user_authentication_from_request(request, api.API_ENDPOINT_GET_PERSONALIZATION_CONFIG if request.method == "GET" else api.API_ENDPOINT_UPDATE_PERSONALIZATION_CONFIG)
    if authorization_validation_result["status"] != api.API_STATUS_SUCCESS:
        logger.info("Authorization was not successful! Handling error...")
        return jsonify(authorization_validation_result), authorization_validation_result["status_code"]
    logger.info("Authorization is valid.")
    request_json = request.json #We know this exists since it is valid for a successful authorization check
    #There is one required key, "category_id" (so we know what category to list monitors in!
    logger.debug("Checking keys...")
    mandatory_key_check = api.validate_present_keys(request_json,
                                                    [("category_id", [str])])
    if mandatory_key_check["status"] != api.API_STATUS_SUCCESS:
        logger.info("The key check failed! Returning error...")
        return jsonify(mandatory_key_check), mandatory_key_check["status_code"]
    logger.debug("The check succeeded. Getting API response and returning...")
    category_id = request_json["category_id"]
    list_monitors_api_response = api.list_monitors_api(category_id)
    logger.info(f"Response from list monitors API: {list_monitors_api_response}. Returning...")
    return jsonify(list_monitors_api_response), list_monitors_api_response["status_code"]

@api_app.errorhandler(500)
def api_internal_server_error_handler(e):
    logger.critical(f"Handling an internal server error...\nException: {e}.")
    return jsonify(api.generate_api_error("The request could not be performed. An internal server error occurred.", 500)), 500 #Return 500
