import argparse
import json
from modules.utils import *
from modules.genWAF import *
from modules.detectParams import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSTI Scanner")
    parser.add_argument("--url", help="URL of the target")
    parser.add_argument("--params", help="Parameters of the target")
    parser.add_argument("--method", help="HTTP method (GET or POST)", default="GET")
    parser.add_argument("--cookie", help="Cookie for the request")
    
    utils = Utils()
    args = parser.parse_args()
    params = args.params
    urlTarget = args.url
    method = args.method
    cookie = args.cookie
    isJsonBody = False
    if utils.isJson(params):
        isJsonBody = True
        params = json.loads(params)
    else:
        params = utils.parseParams(params)
    targetParam = detectParams(urlTarget, method, params, cookie, isJsonBody)
    if targetParam:
        isContinue = input("Do you want to continue? (y/n): ").lower()
        if isContinue.lower() != 'y':
            exit()
    requestHandler = RequestHandler(urlTarget, method, targetParam, params, cookie, isJsonBody)
    genwaf = genWAF(requestHandler)
    waf = genwaf.generateWAF()
    print(waf)