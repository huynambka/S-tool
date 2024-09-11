import requests
import json
from .utils import *

utils = Utils()

payloads = {
    # payload: expected response
    '${7*7}': '49',
    '${7+7}': '14',
    '${7-7}': '0',
    '${[]}':'[]',
    '${[].size()}':'0',
    '${"a"}': 'a'
}
def detectParams(target: str, method: str, params: dict, cookie: str, isJsonBody: bool):
    for key, value in params.items():
        poisonedParams = dict(params)
        for payload, expectedResponse in payloads.items():
            for i in range(1):
                randomPrefix = utils.randomString(5)
                randomSubfix = utils.randomString(5)
                poisonedParams[key] = f"{randomPrefix}{payload}{randomSubfix}"
                if isJsonBody:
                    response = requests.post(target, json=poisonedParams)
                elif method == 'POST':
                    response = requests.post(target, data=poisonedParams)
                else:
                    response = requests.get(target, params=poisonedParams)
                result = utils.getDataFromResponse(response, randomPrefix, randomSubfix)
                if result == expectedResponse:
                    print(f'Parameter {key} seem to be vulnerable to SSTI with payload: {payload}')
                    return key
        
# detectParams('http://localhost:1337/addContact', 'POST', '{"firstName":"Huy","lastName":"Nam","description":"Nam","country":"Vietnam"}', '', True)