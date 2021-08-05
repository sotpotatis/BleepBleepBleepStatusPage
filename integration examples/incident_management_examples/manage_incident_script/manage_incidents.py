'''Manage_incidents.py
The "manage incidents" script is a simple CLI script that allows you to create and update incidents
to keep your customers in the loop!
'''
#Imports
from colorama import Style, Back, Fore, init
from configparser import ConfigParser
import os, requests, datetime, pytz, logging
#Initialize colorama (color prints in terminal)
print("[INIT] Colorama, executing...")
init()
print("[INIT] Colorama complete.")

logging.basicConfig(level=logging.DEBUG) #Uncomment for requests logging
def print_error(message):
    '''Function that supports printing an error in a pretty way.'''
    print(f"{Fore.RED}[ERROR]{Fore.WHITE} {message}")

def exit_script():
    '''Function that allows exiting the script in a way that doesn't just make it
    disappear if you're running it using the default Python GUI console.'''
    input("Press enter to exit the script.")
    exit() #Exit the script.

def handle_request_response(request):
    '''A function to handle the response of a request made to the ***StatusPage server.
    If the request isn't successful, an error is printed out, and False is returned.
    If successful, True is returned.

    :param request: The request.'''
    print("[DEBUG] Checking request...")
    #Check for valid JSON
    try:
        request_json = request.json()
        if "status" not in request_json: #The status key must also be present in the response.
            raise KeyError("Status key missing.")
    except: #An error will be raised if the JSON is invalid
        print_error("[ERROR] Invalid JSON was returned from the server.")
        return False #False = Unsuccessful
    print("[DEBUG] JSON from server exists. Checking response...")
    #If the "status"-key != "success", there is something fishy with the request (fishy as in an error)
    if request_json["status"] != "success":
        print_error(f"[ERROR] An error occurred in the request to the server: {request_json['message']}.") #All requests have the "message" key to indicate what went wrong
    else:
        print(f"{Fore.LIGHTGREEN_EX}[SUCCESS]{Fore.WHITE} The request was successful.")
    return True
#Load preferences. This is an .INI file containing some information about your environment. It should be in the working dir.
working_dir_path = os.getcwd()
print(f"[DEBUG] Working directory path: {working_dir_path}.")
config_file_path = os.path.join(working_dir_path, "config.ini")
print(f"[DEBUG] Config file path: {config_file_path}")
#Check if config file exists
if not os.path.exists(config_file_path):
    print_error("The configuration file for this program does not exist! It must be in the same working directory and calle config.ini (case sensitive).")
    exit_script() #Exit the script since we can't continue.

print("Loading config file...")
config_parser = ConfigParser()
config_parser.read(config_file_path)
print("Config file loading. Loading config file parameters...")
#Load everything in the configuration file
server_settings = config_parser["server"]
authorization_settings = config_parser["authorization"]
print("[DEBUG] Basic dicts loaded.")
#Now, get individual keys that are in the configuration file
BASE_URL = server_settings["base_url"]
TIMEZONE = server_settings["is_in_timezone"]
user_id = authorization_settings["user_id"]
token = authorization_settings["token"]
AUTH_HEADERS = {
    "Authorization": f"Bearer {token}" #The authorization headers
}
print(f"""
{Fore.LIGHTCYAN_EX}INCIDENT MANAGEMENT SCRIPT
{Fore.WHITE}For BleepBleepBleepStatusPage
A {Fore.RED}***{Fore.WHITE} great way to provide status information to your customers!
""") #Intro

while True: #This will run as long as the script hasn't stopped.
    '''The script allows for incident management.'''
    print("""Options:
          1. Create a new incident
          2. Edit an existing incident.
          3. Quit""") #Present with options
    option = input("Please pick an option by typing its number: ")
    VALID_OPTIONS = ["1", "2"]
    if option not in VALID_OPTIONS:
        print_error(f"The option you chose is invalid. Valid options: {','.join(VALID_OPTIONS)}")
    #If we get here, the option is valid
    if option == "1": #Option 1: Create incident
        print("Incident creation selected.")
        #Ask some options about the incident that we want to create
        input("You will now be asked some questions about the incident. Enter them below.\nPress enter to continue.")
        incident_data = {"text": {}, "affected": []}
        #First, the title
        incident_data["text"]["title"] = title = input("Enter a title for the incident: ")
        incident_data["text"]["description"] = description = input("Enter a description describing the incident: ")
        #And now, affected compontents.
        input("You will now be asked about affected components for the incident.\nPress enter to continue.")
        while True:
            VALID_AFFECTED_COMPONENTS_OPTIONS = ["1", "2", "3"]
            print("""Select type for the affected component:
                  1. An individual monitor.
                  2. A whole category.
                  3. Create incident.""")
            option_2 = input("Please select an option by typing its number: ")
            if option_2 not in VALID_AFFECTED_COMPONENTS_OPTIONS:
                print_error(f"The option you chose is invalid. Valid options: {','.join(VALID_AFFECTED_COMPONENTS_OPTIONS)}")
            #Parse option --> affected component type
            if option_2 == "1":
                affected_component_type = "monitor"
            if option_2 == "2":
                affected_component_type = "category"
            if option_2 == "3":
                break #Continue to sending the request
            affected_component_id = input("Please enter the ID of the affected component: ")
            affected_component_status = input("Please enter the ID of the status that this/these components have: ")
            #Append affected component information
            incident_data["affected"].append(
                {"type": affected_component_type,
                "id": affected_component_id,
                 "status": affected_component_status}
            )
        print("Generating and sending body...")
        #Generate the request
        request_body = incident_data
        request_body["user_id"] = user_id
        try: #Attempt a request from the server
            request = requests.post(
            f"{BASE_URL}/api/incidents",
            headers=AUTH_HEADERS,
            json=request_body
            )
            #Handle the response (including printing out any errors)
            request_valid = handle_request_response(request)
            if request_valid:
                print("The creation was successful.")
        except Exception as e:
            print_error(f"Request to server failed with exception: {e}.")
    elif option == "2": #Option 2: Edit an existing incident
        print("Editing an existing incident!")
        #First, get existing incidents from the server
        print("Getting existing incidents...")
        try: #Attempt a request from the server
            request = requests.get(
                f"{BASE_URL}/api/incidents/list",
                headers=AUTH_HEADERS,
                json={"user_id": user_id}
            )
        except Exception as e:
            print_error(f"Request to server failed with exception: {e}.")
            continue
        #Handle the response (including printing out any errors)
        request_valid = handle_request_response(request)
        if request_valid:
            print("The retrieval of incidents were successful.")
        else:
            continue #Errors would have been printed out at this point, so we can continue
        #Print out the IDs of existing incidents
        request_ids = request.json()["incident_ids"]
        while True: #(until valid)
            print("Incident IDs:\n%s"%('\n'.join(request_ids)))
            chosen_request_id = input("Select an incident ID to update by typing its name: ")
            if chosen_request_id not in request_ids:
                print_error("Invalid request ID! Note that they are case sensitive.")
            else: #If the request ID is valid.
                print("Valid request ID.")
                break #Continue the code
        #Now, get incident details
        print(f"Retrieving incident details for {chosen_request_id}...")
        try:
            request = requests.get(
                f"{BASE_URL}/api/incidents",
                headers=AUTH_HEADERS,
                json={"user_id": user_id, "incident_id": chosen_request_id}
            )
        except Exception as e:
            print_error(f"Request to server failed with exception: {e}.")
            continue
        #Handle the response (including printing out any errors)
        request_valid = handle_request_response(request)
        if request_valid:
            print("The retrieval of the incident was successful.")
        else:
            continue #Errors would have been printed out at this point, so we can continue
        #Pretty print the incident
        request_json = request.json()
        incident_data = request_json["data"]
        print(f"[DEBUG] Incident data: {incident_data}")
        print(
            f"""{incident_data['text']['title']}
            {incident_data['text']['description']}
            {len(incident_data['affected'])} affected components.
            Started at: {incident_data['timestamps']['created_at']}
            Solved at: {incident_data['timestamps']['solved_at']}"""
        )
        #The user might want to modify more than just one thing, so we give them the option to do so! Le magic!
        updated_incident = incident_data #This is a little bit of a hack of the "things_to_update" parameter, but it works
        del updated_incident["id"]
        while True: #(until user says "meow meow I'm satisfied for now!")
            print("""Select what to modify:
            1. Incident title
            2. Incident description
            3. Incident affected components
            4. Mark incident as solved/unsolved
            5. Exit and save""")
            #Ask what to modify
            VALID_INCIDENT_MODIFICATION_OPTIONS = ["1", "2", "3", "4", "5"]
            option_3 = input("Select what to modify by typing the number: ")
            if option_3 not in VALID_INCIDENT_MODIFICATION_OPTIONS:
                print_error("Invalid option entered, please try again.")
                continue #Restart and ask again
            if option_3 == "1": #Option 1 - edit title
                new_title = input("Select new title: ")
                if new_title == "":
                    print_error("Title can't be empty!")
                    continue
                updated_incident["text"]["title"] = new_title
            elif option_3 == "2": #Option 2 - edit description
                new_description = input("Select new description: ")
                if new_description == "":
                    print_error("Description can't be empty!")
                    continue
                updated_incident["text"]["description"] = new_description
            elif option_3 == "3": #Option 3 - Edit affected components
                #Pretty-print components
                i = 0
                for affected_component in updated_incident["affected"]:
                    print(f"{i+1}. [{affected_component['status']}] {affected_component['id']} (type: {affected_component['type']})")
                    i += 1
                print("""1. Add a new affected component
                2. Delete an affected component
                (the best way to edit an affected component is to delete it and then add it again)
                      """)
                option_4 = input("Please select an option by typing its name: ")
                VALID_AFFECTED_COMPONENTS_MODIFICATION_OPTIONS = ["1", "2"]
                if option_4 not in VALID_INCIDENT_MODIFICATION_OPTIONS:
                    print_error("Invalid option. Enter options by their name.")
                    continue
                if option_4 == "1": #1 - Add a new affected component
                    while True: #(while not valid)
                        VALID_AFFECTED_COMPONENTS_TYPES = ["category", "monitor"]
                        affected_component_type = input("Please select an affected component type: ")
                        if affected_component_type not in VALID_AFFECTED_COMPONENTS_TYPES:
                            print_error(f"Invalid affected component type (must be one of {','.join(VALID_AFFECTED_COMPONENTS_TYPES)}'")
                            continue
                        #Now, ask for affected ID
                        affected_component_id = input(f"What is the ID of the affected {affected_component_type}? ")
                        if affected_component_id == "": #If the response is not empty
                            print_error("The ID you enterred is empty.")
                            continue
                        #Now, ask for affected status
                        affected_component_status = input(f"What is the status ID for the {affected_component_type}? (e.g. down, up) ")
                        if affected_component_status == "": #If the response is not empty
                            print_error("The status you entered is empty.")
                            continue
                        print("Ok, thank you!")
                        affected_component_data = {"type": affected_component_type,
                                                   "id": affected_component_id,
                                                   "status": affected_component_status} #Data related to the affected component
                        #Check for duplicates
                        duplicate_found = False
                        for affected_component in updated_incident["affected"]: #Check previously affected components
                            if affected_component["type"] == affected_component_type and affected_component["id"] == affected_component_id:
                                print_error("You already have an entry for this affected component in the list.")
                                duplicate_found = True #Mark a duplicate as found
                        if duplicate_found:
                            continue #Continue
                        print("Adding component...")
                        updated_incident["affected"].append(affected_component_data)
                        print("Affected component added.")
                        break
                elif option_4 == "2": #2 - Remove an affected component
                    print("To remove an affected component, take note of its number that was printed above.")
                    number = input("Enter the number: ")
                    try:
                        number = int(number)
                    except:
                        print_error("The number you entered was invalid. Please try again.")
                        continue
                    #The number is valid - get the affected component
                    if number > len(updated_incident["affected"])+1 or number < 1:
                        print_error("The affected component number is invalid. Please try again.")
                        continue
                    print("Removing affected component...")
                    updated_incident["affected"].pop(number-1) #Pop number-1 from the list (-1 because the list number is added by one in the statement where we print the number, see above)
                    print("Affected component removed.")
            elif option_3 == "4": #4 - Mark incident as solved
                VALID_INCIDENT_SOLVED_STATUS_MODIFICATION_OPTIONS = ["unsolved", "resolved"]
                option_5 = input("Mark as unsolved or resolved? ").lower() #We don't have to be case sensitive here!
                if option_5 not in VALID_INCIDENT_SOLVED_STATUS_MODIFICATION_OPTIONS:
                    print_error("Invalid option!")
                if option_5 == "unsolved":
                    #Unsolved - remove timestamp for solving and set status to open
                    updated_incident["current_status"] = "open"
                    updated_incident["timestamps"]["solved_at"] = None
                    print("Incident marked as unsolved.")
                elif option_5 == "solved":
                    #Solved - remove timestamp for solving and set status to resolved
                    updated_incident["current_status"] = "resolved"
                    updated_incident["timestamps"]["solved_at"] = str(datetime.datetime.now(tz=pytz.timezone(TIMEZONE)))
                    print("Incident marked as solved.")
            elif option_3 == "5": #5 - Exit and update incident
                break
        #Now, send updated incident data
        print(f"[DEBUG] Updated incident data: {updated_incident}")
        print("Sending updated incident data...")
        request_body = {
            "incident_id": chosen_request_id,
            "data_to_update": updated_incident,
            "user_id": user_id
        }
        request = requests.put(
            f"{BASE_URL}/api/incidents",
            json=request_body,
            headers=AUTH_HEADERS
        )
        request_successful = handle_request_response(request)

    elif option == "3": #3 - Quit
        print("Quitting...")
        exit_script()
