import requests
import json
import string
from utils import RequestHandler, Utils

reqHandler = RequestHandler('http://localhost:1337/addContact', 'POST', 'country', '{}', '', True)
utils = Utils()
waf = []
singleChar = [letter for letter in string.ascii_letters] + [number for number in string.digits] + [symbol for symbol in string.punctuation]
keywords = [
    'java',
    'Class',
    'Object',
    'java.lang.reflect',
    'Method',
    'Field',
    'Constructor',
    'invoke',
    'newInstance',
    'getDeclaredMethod',
    'getDeclaredField',
    'getDeclaredConstructor',
    'setAccessible',
    'Runtime',
    'exec',
    'ProcessBuilder',
    'start',
    'java.io.File',
    'java.io.FileInputStream',
    'java.io.FileOutputStream',
    'java.io.FileReader',
    'java.io.FileWriter',
    'java.nio.file.Files',
    'java.nio.file.Paths',
    'ObjectInputStream',
    'ObjectOutputStream',
    'Serializable',
    'java.lang.management',
    'ManagementFactory',
    'getRuntimeMXBean',
    'getInputArguments',
    'ClassLoader',
    'URLClassLoader',
    'defineClass',
    'loadClass',
    'SecurityManager',
    'getSecurityManager',
    'setSecurityManager',
    'checkPermission',
    'javax.script',
    'ScriptEngine',
    'ScriptEngineManager',
    'eval',
    'nashorn',
    'System.getProperty',
    'System.setProperty',
    'System.getenv',
    'System.exit',
    'forName',
    'toURL',
    'toURI',
    'toString',
    'hashCode',
    'equals',
    'compareTo',
    'getClass',
    'bytecode',
    'class',
    'instanceof',
    'native',
    'import',
    'if',
    'cmd',
    'eval',
    'true',
    'false',
    'char',
    'Char',
    'for',
    'while',
    'goto',
    'bash'
]
javaKeywords = [
    
]
def isFiltered(word, response, randomPrefix, randomSubfix):
    """
    Check if the response is filtered by the WAF
    """
    if response.status_code == 403 or "blocked" in response.text.lower() or "forbidden" in response.text.lower():
        return True
    if word not in response.text and randomPrefix in response.text and randomSubfix in response.text:
        return True
    return False
def checkSingleChar():
    """
    Check what characters are filter by the WAF
    """
    for char in singleChar:
        randomPrefix = utils.randomString(length = 10, filtered = [char] + waf)
        randomSubfix = utils.randomString(length = 10, filtered = [char] + waf)
        payload = f"{randomPrefix}{char}{randomSubfix}"
        response = reqHandler.sendPayload(payload)
        if isFiltered(char, response, randomPrefix, randomSubfix):
            if char in string.ascii_letters:
                print(payload)
            waf.append(char)
            utils.randomString(length = 10, filtered=waf)
def checkKeyword():
    """
    Check what Java keywords are filter by the WAF
    """
    for keyword in keywords:
        randomPrefix = utils.randomString(length = 10, filtered=waf)
        randomSubfix = utils.randomString(length = 10, filtered=waf)
        payload = f"{randomPrefix}{keyword}{randomSubfix}"
        response = reqHandler.sendPayload(payload)
        if isFiltered(keyword, response, randomPrefix, randomSubfix):
            waf.append(keyword)
            utils.randomString(length = 10, filtered=waf)
def genWAF():
    """
    Generate WAF filter
    """
    checkSingleChar()
    checkKeyword()
    return waf