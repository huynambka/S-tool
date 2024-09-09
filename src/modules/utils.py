import os
import random
import string
import requests
import json

class Utils:
    def __init__(self, target: str, method: str, targetParam: str, extraParams: str, cookie: str, isJsonBody: bool):
        self.target = target
        self.method = method
        self.targetParam = targetParam
        self.extraParams = extraParams
        self.isJsonBody = isJsonBody
        self.cookie = cookie  
        self.randomString()
    
    def sendPayload(self, payload):
        payload = self.addRandomStringToPayload(payload)
        data = {
            self.targetParam: payload,
        }
        data.update(json.loads(self.extraParams))
        if self.isJsonBody:
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(f'{self.target}', json=data, headers=headers)
        elif self.method == 'POST':
            response = requests.post(f'{self.target}', data=data)
        else:
            response = requests.get(f'{self.target}', params=data)
        
        return response
    
    def read_lines_from_file(file_path):
        """
        Read lines from a file
        
        :param file_path: Path to the file
        :return: List of lines
        """
        file_path = os.path.join(os.path.dirname(__file__), '..', file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            # Read lines, strip whitespace, and ignore empty lines
            lines = [line.strip() for line in file.readlines() if line.strip()]
        return lines

    def randomString(self, length = 10 ):
        """
        Generate a random string
        
        :param length: Length of the string
        :return: Random string
        """
        randomStr = ''.join(random.choice(string.ascii_letters) for _ in range(length))
        self.randomStr = randomStr

    def addRandomStringToPayload(self, payload):
        """
        Add random string to payload for detecting where the payload is reflected
        """
        randomStringText = self.randomStr
        payload = f"{randomStringText}{payload}{randomStringText}"
        return payload

    def getDataFromResponse(self, response):
        """
        Get data from response
        
        :param response: Response object
        :return: Data from response
        """
        if self.randomStr in response.text:
            return response.text.split(self.randomStr)[1]