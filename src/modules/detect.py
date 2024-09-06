import requests
import re
from modules.utils import read_lines_from_file
import json
import random
import string


class Payload:
    payload = ""
    expected = ""
    reversed_check = False
    
reflect_payload = []

def random_string(length=10):
    """
    Generate a random string of a specified length
    
    :param length: Length of the random string
    :return: Random string
    """

    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def random_integer(min=1, max=100):
    """
    Generate a random integer between a specified range
    
    :param min: Minimum value
    :param max: Maximum value
    :return: Random integer
    """
    return random.randint(min, max)

def generate_fuzzing_payloads():
    """
    Generate payloads for SSTI fuzzing.
    Three types of payloads are generated:
    - Java keywords
    - Special characters
    - Simple exploit payloads
    
    :return: List of payloads
    """
    # Java keywords
    java_keywords = read_lines_from_file("data/fuzzing/java_keywords.txt")
    for keyword in java_keywords:
        p = Payload()
        p.payload = keyword
        p.expected = keyword
        reflect_payload.append(p)
        

def reflect_test(url, params, method="GET"):
    """
    Fuzzing to detect parameters that vulnerable to SSTI
    
    :param url: URL of the target
    :param params: Parameters of the target as a dictionary
    :param method: HTTP method (GET or POST)
    :return: List of vulnerable parameters if SSTI is detected, otherwise False
    """
    print("[*] Fuzzing for SSTI vulnerability")
    payloads_for_detect = read_lines_from_file("data/fuzzing/payloads.txt")
    vulnerable_params = set()
    # Determine if params are in JSON format or query string format
    is_json = False
    try:
        # Try to load as JSON
        params = json.loads(params)
        is_json = True
    except json.JSONDecodeError:
        # If not JSON, assume query string format
        params = dict(item.split("=") for item in params.split("&"))
    # Loop through each parameter and test each payload
    for param in params:
        original_value = params[param]
        for payload in payloads_for_detect:
            print(f"[*] Testing parameter '{param}' with payload: {payload}")
            # Create a copy of the parameters to inject the payload
            test_params = params.copy()
            test_params[param] = payload
            
            try:
                # Send the request based on the method
                if method == "GET":
                    response = requests.get(url, params=test_params)
                elif method == "POST":
                    if is_json:
                        response = requests.post(url, json=test_params)
                    else:
                        response = requests.post(url, data=test_params)
                else:
                    print("[!] Invalid HTTP method")
                    return

                # Check if SSTI was executed
                if is_ssti_executed(response):
                    print(f"[+] SSTI vulnerability found in {url} with parameter '{param}' using payload: {payload}")
                    vulnerable_params.add(param)
        
            except Exception as e:
                print(f"[!] Error while testing {param} with payload {payload}: {e}")

    if vulnerable_params:
        print("[+] Vulnerable parameters:", vulnerable_params)
        return vulnerable_params
    else:
        print("[!] No SSTI vulnerability detected")
        return False


def is_ssti_executed(response):
    """
    Analyze the response to determine if SSTI was executed based on defined patterns.
    
    :param response: The HTTP response object
    :return: True if SSTI is detected, otherwise False
    """
    patterns = read_lines_from_file("data/fuzzing/patterns.txt")

    # Check response text against patterns
    for pattern in patterns:
        pattern = pattern.replace("\n", "").strip()
        # Escape the pattern to avoid regex errors
        escaped_pattern = re.escape(pattern) if pattern != "[]" else r'\[\]'
        
        # Perform case-insensitive search using the escaped pattern
        if re.search(escaped_pattern, response.text, re.IGNORECASE):
            return True
    return False
