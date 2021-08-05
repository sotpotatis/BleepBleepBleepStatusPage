'''Client.py
A basic ***StatusPage client designed for reporting data to a specific monitor.
'''
from .exceptions import *
import requests, logging

#Logging
logger = logging.getLogger(__name__)

class Client:
    def __init__(self, server_url, server_port, token, username):
        '''A simple ***StatusPage client for reporting data for monitors.

        :param server_url: The server URL that your ***StatusPage uses INCLUDING the prefix (http:// or https://).

        :param server_port: The server port that your ***StatusPage uses.

        :param username: The username to authenticate with.

        :param token: The user token to authenticate with.'''
        self.token = token
        self.username = username
        self.server_url = server_url
        self.server_port = server_port
        self.full_server_url = f"{server_url}:{server_port}"
        self.request_auth_json = {"user_id": username}
        self.request_auth_headers = {"Authorization": f"Bearer {token}"}
        logger.debug(f"Client initialized with username {username} and token {token}.")

    def report_data(self, category_id, monitor_id, data_name, value):
        '''Function for reporting data for a specific monitor.

        :param category_id: The category ID that the monitor you want to report to has.

        :param monitor_id: The monitor ID that the monitor you want to report to has.

        :param data_name: The data name that you want to report.

        :param value: The value to report. Can be any time, but remember that if you want to plot it,
        it should be a number or a boolean like None.
        '''
        logger.debug("Reporting data...")
        report_data_request = requests.post(
            f"{self.full_server_url}/api/data",
            json={
                "user_id": self.username,
                "monitor_id": monitor_id,
                "category_id": category_id,
                "data_name": data_name,
                "value": value
            },
            headers=self.request_auth_headers
        )
        request_json = report_data_request.json()
        if request_json["status"] != "success":
            logger.debug("The request was unsuccessful.")
            raise APIError(f"The error {request_json['message']} occurred.")
        else:
            logger.debug("The data report was successful.")


