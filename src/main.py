import modules.detect as detect
import argparse
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSTI Scanner")
    parser.add_argument("--url", help="URL of the target")
    parser.add_argument("--params", help="Parameters of the target")
    parser.add_argument("--method", help="HTTP method (GET or POST)", default="GET")

    args = parser.parse_args()
    target_url = args.url
    method = args.method.upper()
    
    detect.reflect_test(target_url, args.params, method)
