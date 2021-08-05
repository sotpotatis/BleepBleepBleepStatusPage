import datetime, pytz, internal_libraries.data as data, logging

def get_timezone():
    '''Function for getting the timezone that is configured by the user to be used by the script.

    The timezone is set under the configuration parameter time/timezone in server.json.'''
    logger.debug("Got a request to get the server timezone!")
    #Get the configuration
    server_configuration = data.get_configuration("server")
    logger.debug("Server configuration retrieved. Getting server timezone...")
    server_timezone = server_configuration["time"]["timezone"]
    logger.debug(f"Server timezone: {server_timezone}. Returning...")
    return server_timezone

get_now = lambda: datetime.datetime.now(tz=pytz.timezone(get_timezone())) #Quick function for getting current time

#Logging configuration
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def get_heaviest_status(status_list):
    '''Function for getting the heaviest (most severe/most impacting) status of a list of statuses.

    :param status_list: A list with names of the statuses.'''
    logger.info(f"Getting heaviest status of status list {status_list}...")
    heaviest_status = {"text": None, "severity": -1} #The variable where we store the "heaviest" status.
    for status in status_list:
        status_config = data.get_status(status)
        status_impact = status_config["severity"]
        if status_impact > heaviest_status["severity"]:
            logger.debug("New status with higher impact found!")
            heaviest_status["text"] = status
            heaviest_status["severity"] = status_impact
    logger.debug(f"Heaviest status calculation finished. Result: {heaviest_status}.")
    return heaviest_status["text"]

def pretty_format_list(list_to_format, convert_to_str=False):
    '''Function for pretty-formatting a list (returning it as a human-readable string). Should be used to more extent.

    :param list_to_format: The list to format.

    :param convert_to_str: If True, the list is marked as containing non-string arguments, and any of those are being
    converted to string before continuing.'''
    logger.debug(f"Pretty-formatting list {list_to_format}...")
    if convert_to_str:
        logger.debug("Non-string list elements should be converted to string. Doing so...")
        #Iterate through elements
        list_to_format = [str(elem) if type(elem) != str else elem for elem in list_to_format]
        logger.debug("List elements converted.")
    else:
        logger.debug("The list elements should not be converted to string.")
    return ",".join(list_to_format[:-1]) + ", and " + list_to_format[-1] #Return the pretty-formatted list

PRETTY_DATETIME_FORMAT = "%Y-%m-%d %H:%M" #The format as used in the function right below this. Use the beautiful strftime.org for a reference!
def pretty_format_datetime(datetime_object, include_timezone=False):
    '''Function for pretty formatting a datetime into a human-readable format that is yummy and sweet.

    :param datetime_object: The datetime format to format.

    :param include_timezone: Whether to include the user-configured timezone to ise or not.'''
    logger.debug(f"Pretty-formatting datetime: {datetime_object}...")
    formatted_dt = datetime_object.strftime(PRETTY_DATETIME_FORMAT)
    logger.debug(f"Formatted dt (without timezone): {formatted_dt}.")
    if include_timezone:
        logger.debug("Including timezone...")
        #To know this, we need to know what freakin' timezone we are using! Otherwise, your customers are going to be upset, lol!!!
        server_timezone = get_timezone()
        logger.debug(f"Timezone is: {server_timezone}. Adding...")
        formatted_dt += f" (timezone: {server_timezone})"
        logger.debug("Timezone added.")
    logger.debug(f"Final pretty-formatted datetime: {formatted_dt}. Returning...")
    return formatted_dt

def generate_text_page_data(text):
    '''The ui_frontend.py route exposes access to a "text page", which can be used for generic errors.
    This text page is usually accessed inline, so we need a quick way to pass the data that the text page wants
     in its Jinja template. And that way, is this function! How cool, right?
     It passes the user's configuration file and the text to render as data.

     :param text: The text to render on the page.'''
    logger.debug("Generating data to pass text to the rendering of text data...")
    personalization_config = data.get_configuration("personalization")
    #Since the function is meant to be used inline, but we want to support localization, we do some (a bit wonky) translation here
    website_language = personalization_config["language"]
    if website_language != "en":
        logger.debug("Language is not English, translating...")
        if website_language == "sv":
            logger.debug("Language is Swedish. Translating...")
            #Translate the strings by updating the text variable
            if text == "":
                text = ""
            elif text == "The end date is specified, but a start date is not. Please do so.":
                text = "Slutdatumet är specificerat, men ett startdatum är inte det. Vänligen gör det."
            elif text == "The end date entered in the request is invalid.":
                text = "Startdatumet angivet i din förfrågan är felaktigt."
            elif text == "The end date entered in the request is bigger than the start date.":
                text = "Slutdatumet angivet i din förfrågan är större än startdatumet."
            elif text == "Invalid status filter. Please use \"open\" or \"resolved\".":
                text = "Felaktigt statusfilter. Vänligen använd \"open\" eller \"resolved\"."
            elif text == "The requested page could not be found. Please check the link and try again.":
                text = "Den efterfrågade sidan kunde inte hittas. Var vänglig att kontrollera länken och testa igen."
            elif text == "An internal server error has occurred. We're sorry about the inconvenience.":
                text = "Ett internt serverfel har inträffat. Vi ber om ursäkt."
            else:
                logger.warning(f"The string {text} does not have a Swedish translation! It will not be translated.")
                #(since we don't update the text variable, the text will not be updated)
        else: #If the language is unsupported
            logger.warning(f"You have entered an unsupported language: {website_language}. The string returned on the message page will be in English!")
            #...and just use the English string (yeah I'm not a native English speaker and I think it sucks when webpages aren't fully translated but hey check that config!)
    text_page_data = {"personalization": personalization_config, "text": text} #Include the personalization file and the text to render
    logger.debug(f"Text page data: {text_page_data}")
    logger.debug("Returning render data...")
    return text_page_data
