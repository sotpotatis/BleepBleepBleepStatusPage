'''UI_frontend.py
Routes responsible for the UI and frontend bit.
This includes static routes, mainly.
'''
from flask import Blueprint, render_template, Response, request
import logging, internal_libraries.data as data, internal_libraries.api as api, internal_libraries.util as util
from http import HTTPStatus

#Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

uifr_app = Blueprint(__name__, "ui_frontend") #UIFR = UI Frontend. Nifty name, right? Nah, not my best variable name tbh

@uifr_app.route("/")
def index():
    '''The main index page. This is where the status page is publicly shown to your users.
    This is the main page, except for subpages that are related to incidents.
    The *** philosophy is to provide an *** amount of information in a way that feels intuitive and responsive.
    It is not intuitive for a status page to provide a *** number of redirects to view the current platform status.
    Not intuitive at all, bestie<3

    And hey, what does this index function do then? Well, it pulls the general configuration (app name, etc) and then
    pulls all categories and monitors. It magically combines them into one single dictionary (this is so *** good, JSON/dictionary lovers will *** love this)
    And this dictionary is passed on to the BUTTERY-SMOOTH, lovely, beautiful, soft markup called Jinja2. So *** much magic is done there, and it all renders as something pretty on the visitors end.
    Wow, I realized I can't write this long docstrings on all endpoints. But I hope you get it. If not, *** ask! Asking a *** number of questions is how you understand stuff.
    '''
    logger.info("Got a request to the status page!")
    render_data = {} #The cute render data that I mentioned earlier!
    '''Add personalization settings.
    This is things like the site appearence, so yeah, pretty essential.
    And yummy. Like ice cream!'''
    logger.info("Adding personalization settings...")
    render_data["personalization"] = data.get_configuration("personalization")
    logger.info("Personalization settings added.")
    '''Get the master dictionary. This has information about the current status of monitors. It also has information about
    all monitors and categoires. That's why it's like a foundation, a father!'''
    logger.info("Retrieveing master \"daddy\" dict...")
    master_dict = api.generate_daddy_dict()
    logger.info("Master dictionary retrieved. Adding...")
    render_data["categories_and_monitors"] = master_dict
    logger.info("Retrieving open incidents...")
    #Get open incidents
    open_incidents = api.get_incidents(status=api.INCIDENT_OPEN)["found_incidents"]
    logger.info("Open incidents retrieved. Adding, if any...")
    render_data["incidents"] = []
    for incident_id in open_incidents:
        logger.info(f"Adding incident data for {incident_id}...")
        incident_data = data.get_configuration(f"incidents/{incident_id}/data")
        #Add incident ID
        incident_data["id"] = incident_id
        render_data["incidents"].append(incident_data)
    #Now, get statuses, so we can convert a status like "up" to some readable stuff. You can personalize that, too.
    logger.info("Retrieving statuses...")
    render_data["statuses"] = data.get_statuses()["statuses"]
    logger.info("Statuses retrieved.")
    #Get the current platform status
    logger.info("Getting the current platform status...")
    render_data["current_platform_status"] = util.get_heaviest_status(master_dict["monitor_statuses"])
    #Get personalization settings
    logger.debug(f"Rendering data according to render data {render_data}...")
    return render_template("index.html",
                           data=render_data) #Render the index template and pass the beautiful render data to it!

@uifr_app.route("/incident/<string:incident_id>")
def incident_view(incident_id):
    '''Route for viewing in-depth information about an incident.'''
    logger.info(f"Got a request to view an incident with the ID {incident_id}...")
    logger.info("Getting incident data...")
    #Get data for the incident
    try:
        incident_data = data.get_configuration(f"incidents/{incident_id}/data")
        logger.info("Incident data retrieved.")
    except FileNotFoundError: #This is raised if the incident path doesn't exist, so most likely that the incident ID is invalid.
        #In that case, we return 404...
        logger.info("The incident ID provided is invalid. Returning 404...")
        return Response(status=HTTPStatus.NOT_FOUND)
    '''Things we also want to expose:
    - Parsing: incident ID --> text and color (statuses.json), since incidents only give us the type ID, but we want to render something pretty based on the status.
    - Heading configuration, so that we can provide a page header to the user.
    - Default color base value, so that we get the correct status colors.
    '''
    logger.info("Adding user data...")
    render_data = {"incident": incident_data}
    logger.info("Adding status config...")
    render_data["statuses"] = data.get_configuration("statuses")["statuses"] #Add statuses config
    logger.info("Status config added. Adding heading configuration and base color value...")
    #(the things we want are provided in the personalization.json file, so we can grab them both at the same time)
    personalization_settings = data.get_configuration("personalization")
    logger.info("Adding heading configuration...")
    render_data["personalization"] = personalization_settings
    logger.info("Personalization configuration added. Rendering incident data...")
    return render_template("incident.html", data=render_data)

@uifr_app.route("/incidents")
def incidents_view():
    '''The incidents frontend endpoint allows to list incidents.
    The option to list incident between an end date and a start date exists.
    The option to filter incidents by their status ("open" or "resolved") also exists.'''
    logger.info("Got a request to list incidents!")
    #Check for start and end date
    logger.info("Checking for start date and end date parameters...")
    start_date = request.args["start_date"] if "start_date" in request.args else None
    end_date = request.args["end_date"] if "end_date" in request.args else None
    logger.info(f"Start date: {start_date}. End date: {end_date}")
    '''If end date exists, a start date should exist, since that is logical.
    However, the default end date is the current time, so start date can be specified without
    end date having to be specified. But not the other way around! And it makes sense when you
    think about it.'''
    #Perform the check mentioned above
    logger.debug("Performing end date/start date relationship check completed...")
    if end_date != None and start_date == None:
        logger.info("End date is specified, but start date isn't! Returning error...")
        return render_template("text_page.html", data=util.generate_text_page_data("The end date is specified, but a start date is not. Please do so."))
    logger.debug("End date/start date relationship check complete.")
    #Perform a date validity check
    logger.info("Performing date validity check...")
    parsed_start_date = parsed_end_date = None #Set parsed start and end dates to None, since they will not be set unless the user has specified a start or end date
    if end_date != None:
        logger.debug("End date is specified, parsing...")
        parsed_end_date = api.check_date(end_date)
        if parsed_end_date == api.INVALID_DATE_RESPONSE:
            logger.info("The parsed end date is invalid! Returning error...")
            return render_template("text_page.html", data=util.generate_text_page_data("The end date entered in the request is invalid."))
    else:
        logger.debug("End date is not specified.")
    if start_date != None:
        logger.debug("Start date is specified, parsing...")
        parsed_start_date = api.check_date(start_date)
        if parsed_start_date == api.INVALID_DATE_RESPONSE:
            logger.info("The parsed start date is invalid! Returning error...")
            return render_template("text_page.html", data=util.generate_text_page_data("The start date entered in the request is invalid."))
    else:
        logger.debug("Start date is not specified.")
    #End date shouldn't be bigger than start date, duh!
    if parsed_start_date != None and parsed_end_date != None and parsed_end_date > parsed_start_date:
        logger.info("End date is bigger than start date! Returning error...")
        return render_template("text_page.html", data=util.generate_text_page_data("The end date entered in the request is bigger than the start date."))
    #Check for "status" argument
    logger.info("Checking for status argument...")
    status = request.args["status"] if "status" in request.args else None
    if status not in ["open", "resolved", None]: #The valid incident statuses
        logger.info("Specified status filter is invalid! Returning error...")
        return render_template("text_page.html", data=util.generate_text_page_data("Invalid status filter. Please use \"open\" or \"resolved\"."))
    logger.info("Arguments are looking fresh and ok! Getting incidents...")
    incidents = api.get_incidents(status=status, start_date=parsed_start_date, end_date=parsed_end_date)
    found_incidents = incidents["found_incidents"]
    logger.info("Incident retrieved.")
    logger.debug(f"Retrieved incidents: {incidents}.")
    #Check if any incidents were found. This is for debugging since this is handled by the Jinja2 template.
    if len(incidents) == 0:
        logger.info("No incidents were found for active selection.")
    else:
        logger.info("Incidents for the active selection were found.")
    #Iterate through all incidents and get their data. (the found incident API responds with the IDs of the incidents)
    logger.info("Iterating through found incidents and getting their data...")
    i = 0 #Iteration counter for the loop below
    for found_incident_id in found_incidents:
        logger.info(f"Adding data for incident {found_incident_id}...")
        #Get the incident data itself
        logger.debug("Getting incident data...")
        incident_data = data.get_incident_data(found_incident_id)
        logger.debug("Incident data retrieved. Adding...")
        #Replace the incident ID in the list of found incidents with the incident data
        found_incidents[i] = incident_data
        logger.info("Data added.")
        i += 1
    logger.info("Returning response...")
    #We want to expose user personalization data to the file so we can render a nice header/heading and support localization!
    personalization = data.get_configuration("personalization")
    return render_template("incidents.html", data={"incidents": found_incidents, "personalization": personalization})

#And, a 500 error handler and 404 handler!
@uifr_app.errorhandler(404)
def page_not_found_error_handler():
    logger.info("Handling 404 error...")
    return render_template("text_page.html", data=util.generate_text_page_data("The requested page could not be found. Please check the link and try again.")), 404

@uifr_app.errorhandler(500)
def internal_server_error_error_handler(e):
    logger.critical(f"Handling internal server error...\nException: {e}.", exc_info=True)
    return render_template("text_page.html", data=util.generate_text_page_data("An internal server error has occurred. We're sorry about the inconvenience.")), 500
