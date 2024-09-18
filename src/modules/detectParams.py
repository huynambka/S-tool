import requests

from .utils import Utils

utils = Utils()

payloads = {
    # payload: expected response
    "${7*7}": "49",
    "${7+7}": "14",
    "${7-7}": "0",
    "${[]}": "[]",
    "${[].size()}": "0",
    '${"a"}': "a",
    "${'zkz'.toString().replace('k','x')}": "zxz",
}


def detectParams(
    target: str, method: str, params: dict, cookies, isJsonBody: bool
) -> str:
    for key, value in params.items():
        poisonedParams = dict(params)
        for payload, expectedResponse in payloads.items():
            print(f"[+] Testing param [{key}] with payload: {payload}")
            for i in range(10):
                randomPrefix = utils.randomString(5)
                randomSubfix = utils.randomString(5)
                poisonedParams[key] = f"{randomPrefix}{payload}{randomSubfix}"
                if isJsonBody:
                    response = requests.post(
                        target, json=poisonedParams, cookies=cookies
                    )
                elif method == "POST":
                    response = requests.post(
                        target, data=poisonedParams, cookies=cookies
                    )
                else:
                    response = requests.get(
                        target, params=poisonedParams, cookies=cookies
                    )
                result = utils.getDataFromResponse(response, randomPrefix, randomSubfix)
                if result == expectedResponse:
                    print(
                        f"[*] Parameter {key} seem to be vulnerable to SSTI with payload: {payload}"
                    )
                    return key
    return ""


# detectParams('http://localhost:1337/addContact', 'POST', '{"firstName":"Huy","lastName":"Nam","description":"Nam","country":"Vietnam"}', '', True)
