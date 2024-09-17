import os
from os.path import exists
import random
import string
import requests
import json


class Utils:
    def arrayFromFile(self, filePath):
        """
        Read lines from a file

        :param filePath: Path to the file
        :return: List of lines
        """
        filePath = os.path.join(os.path.dirname(__file__), "..", filePath)
        if not os.path.exists(filePath):
            raise FileNotFoundError(f"The file {filePath} does not exist.")

        with open(filePath, "r", encoding="utf-8") as file:
            # Read lines, strip whitespace, and ignore empty lines
            lines = [line.strip() for line in file.readlines() if line.strip()]
        return lines

    def jsonFromFile(self, filePath) -> dict:
        filePath = os.path.join(os.path.dirname(__file__), "..", filePath)
        if not os.path.exists(filePath):
            raise FileNotFoundError(f"The file {filePath} does not exist.")
        with open(filePath, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                return data
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file {filePath}")
                return {}

    def randomString(self, length=10, filtered=[]):
        """
        Generate a random string and store it in the object

        :param length: Length of the string
        :return: Random string
        """
        allowedChar = "".join(c for c in string.ascii_letters if c not in filtered)
        randomStr = "".join(random.choice(allowedChar) for i in range(length))
        for word in filtered:
            if word in randomStr:
                return self.randomString(length, filtered)
        return randomStr

    def getDataFromResponse(self, response, randomPrefix, randomSubfix):
        """
        Get data from response

        :param response: Response object
        :return: Data from response
        """
        if randomPrefix in response.text and randomSubfix in response.text:
            data = response.text.split(randomPrefix)[1].split(randomSubfix)[0]
            if len(data) > 0:
                return data
        return ""

    def parseParams(self, params):
        """
        Parse parameters from string to list

        :param params: Parameters in string format
        :return: List of parameters
        """
        params = params.split("&")
        params = dict([tuple(param.split("=")) for param in params])
        return params

    def isJson(self, data):
        """
        Check if the data is JSON

        :param data: Data to check
        :return: True if the data is JSON, False otherwise
        """
        try:
            json.loads(data)
            return True
        except:
            return False

    def checkNoDigits(self, list):
        """
        Check if the list has no digits

        :param list: List to check
        :return: True if the list has no digits, False otherwise
        """
        return not any(char.isdigit() for char in list)

    def checkConnection(self, target):
        try:
            response = requests.get(target, timeout=5)
        except requests.ConnectionError:
            print(f"Failed to connect to {target}. Connection error.")
            return False
        except requests.Timeout:
            print(f"Failed to connect to {target}. Request timed out.")
            return False
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            return False
        return True


class RequestHandler:
    def __init__(
        self,
        target: str,
        method: str,
        vulnParam: str,
        params: dict,
        cookie: str,
        isJsonBody: bool,
    ):
        self.target = target
        self.method = method
        self.vulnParam = vulnParam
        self.params = params
        self.isJsonBody = isJsonBody
        self.cookie = cookie

    def sendPayload(self, payload):
        data = {}
        data.update(self.params)
        data.update({self.vulnParam: payload})
        if self.isJsonBody:
            headers = {"Content-Type": "application/json"}
            response = requests.post(f"{self.target}", json=data, headers=headers)
        elif self.method == "POST":
            response = requests.post(f"{self.target}", data=data)
        else:
            response = requests.get(f"{self.target}", params=data)

        return response
