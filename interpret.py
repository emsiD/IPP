# File:     interpret.py
# Author:   Matej Dubec (xdubec00)
# Date:     04.04.2020
# Desc:     Interpret jazyka ippcode20 v jazyku python
#
import sys
import xml.etree.ElementTree as ET
import re

#############################
"""        CLASSES        """
#############################

''' Class for all data, that concerns instructions, instruction order, labels '''
class instructionListClass():
    def __init__(self):
        self.instructions = {}          # key = position; value = {instruction}
        self.instructionsInFile = 0        
        self.instructionCounter = 1
        self.instructionsDone = 0
        self.labels = {}                # key = name; value = position
        self.callStack = []             # for CALL & RETURN instructions

    #Returns following instruction, if there is any
    def getNextInstruction(self):
        if (self.instructionCounter <= self.instructionsInFile):
            self.instructionsDone += 1 
            self.instructionCounter += 1 
            return self.instructions[self.instructionCounter-1]
        return None

    #Saves value to callstack
    def pushNextInstructionToCallStack(self):
        self.callStack.append(self.getInstrCounter()+1)

    #Pops value from callstack
    def popNextInstructionFromCallStack(self):
        if (len(self.callStack) > 0):   # callstack not empty
            self.instructionCounter = self.callStack.pop()
        else:
            sys.stderr.write("ERROR: Empty callstack!\n")
            sys.exit(56)

    #Rewrites value in instruction counter based on label position
    def jumpToLabel(self, argLabel):
        label = argLabel["text"]
        if (label in self.labels):      # label existence check
            self.instructionCounter = self.labels[label]
        else:
            sys.stderr.write("ERROR: Jumped to non-existing label!\n")
            sys.exit(52)

    #Returns code position
    def getInstrCounter(self):
        return self.instructionCounter -1

    #Returns done-instructions count
    def getInstrsDone(self):
        return self.instructionsDone - 1

''' Class for frame-content handling '''
class frameHandling():
    def __init__(self):
        # TEMPORARY FRAME (TF)
        self.defined = False
        self.tmpFrame = {}
        # GLOBAL FRAME (GF)
        self.globalFrame = {}
        # FRAME STACK
        self.frameStack = []

    #Initializes TF
    def initTmpFrame(self):
        self.defined = True
        self.tmpFrame = {}
        
    #Saves TF onto frame stack, undefines TF
    def pushTmpFrame(self):
        if (self.defined == True):
            self.frameStack.append(self.tmpFrame)
            self.defined = False
        else:
            sys.stderr.write("ERROR: Tried to push undefined TF to frame stack!\n")
            sys.exit(55)    

    #Pops frame from top of frame stack into TF
    def popFrameStack(self):
        if (len(self.frameStack) > 0): # framestack not empty
            self.tmpFrame = self.frameStack.pop()
            self.defined = True 
        else:
            sys.stderr.write("ERROR: Tried to pop frame from empty frame stack!\n")
            sys.exit(55)
            
    #Returns frame stack
    def getFrameStack(self):
        return self.frameStack

    #Returns requested frame / UNDEFINED
    def getFrame(self, frame):
        if (frame == "GF"):
            return self.globalFrame
        if (frame == "LF"):
            return self.frameStack[len(self.frameStack) - 1] if (len(self.frameStack) > 0) else "UNDEFINED"  # framestack not empty -> LF value      
        if frame == "TF": 
            return "UNDEFINED" if not (self.defined) else self.tmpFrame

    #Returns frame and name in tuple
    def getSplitVar(self, argVar):
        return argVar["text"].split("@", 1)

    #Returns tuple representing symbol as argument
    #TUPLE = (type, value, (bool) is in variable?)
    def getArgTuple(self, arg):
        if (arg["type"] in ["int", "bool", "string", "type", "label", "nil"]):
            return (arg["type"], arg["text"], False)
        else:# symb = var (is in variable = true)
            frame, name = self.getSplitVar(arg)
            frameToSearch = self.getFrame(frame)
            if (frameToSearch == "UNDEFINED"):
                sys.stderr.write("ERROR: Tried to read from undefined frame!\n")
                sys.exit(55)   
            if (name not in frameToSearch):
                sys.stderr.write("ERROR: Tried to read undefined variable!\n")
                sys.exit(54)    
            typeOfArg = frameToSearch[name]["type"]
            argValue = frameToSearch[name]["value"]
            return (typeOfArg, argValue, True) 

    #Rewrites value in passed variable 'argVar'
    def setVar(self, argVar, typeOfArg, argValue):
        frame, name = self.getSplitVar(argVar)
        frameToSearch = self.getFrame(frame)
        if (frameToSearch == "UNDEFINED"):
            sys.stderr.write("ERROR: Tried to write to variable in undefined frame!\n")
            sys.exit(55)
        if (name not in frameToSearch):
            sys.stderr.write("ERROR: Tried to write to undefined variable!\n")
            sys.exit(54)
        frameToSearch[name]["type"] = typeOfArg
        frameToSearch[name]["value"] = argValue

    # DEFVAR - instruction-handling method
    def defVar(self, arg):
        frame, name = self.getSplitVar(arg)
        frameToInsert = self.getFrame(frame)
        if (frameToInsert == "UNDEFINED"): # undefined frame
            sys.stderr.write("ERROR: Tried to define variable in undefined frame!\n")
            sys.exit(55)
        #frame exists
        if (name in frameToInsert): # variable already exists
            sys.stderr.write("ERROR: Tried to (re)define already defined variable!\n")
            sys.exit(52)
        frameToInsert[name] = {"value": None, "type": None}

''' Class for stack-like methods on list '''
class dataStack():
    def __init__(self):
        self.stack = []

    def pushValue(self, type, value):
        self.stack.append((type, value))

    def popValue(self):
        if (len(self.stack) > 0):
            return self.stack.pop()
        else:
            sys.stderr.write("Nothing to pop!\n")
            sys.exit(56)

    def getStack(self): # for BREAK instruction
        return self.stack

###############################
"""        FUNCTIONS        """
###############################

#Sorts first 3 arguments - all wrong possibilities will be caught later in argCheck
def sortArgs(instruct):
    copy = instruct[:]
    try:
        for arg in copy:
            if (arg.tag == "arg1"):
                instruct[0] = arg
            if (arg.tag == "arg2"):
                instruct[1] = arg
            if (arg.tag == "arg3"):
                instruct[2] = arg
    except:
        pass

#Controls label type
def checkLabel(arg):
    if (arg.attrib['type'] != 'label'):
        sys.stderr.write("Invalid 'type'! (Not 'label')\n")
        print(arg.attrib)
        sys.exit(52)
    if (arg.text is None or not re.match('^(_|-|\$|&|%|\*|[a-zA-Z])(_|-|\$|&|%|\*|[a-zA-Z0-9])*$', arg.text)): # invalid text value
        sys.stderr.write("Invalid 'label' element value!\n")
        sys.exit(32)

#Controls variable type
def checkVar(arg):
    if (arg.attrib['type'] != 'var'):
        sys.stderr.write("Invalid 'type'! (Not 'type')\n")
        print(arg.attrib['type'])
        print(arg.text)
        sys.exit(52)
    if (arg.text is None or not re.match('^(GF|LF|TF)@(_|-|\$|&|%|\*|[a-zA-Z])(!|\?|;|_|-|\$|&|%|\*|[a-zA-Z0-9á-ž])*$', arg.text)): # invalid text value
        sys.stderr.write("Invalid 'var' element value!\n")
        sys.exit(32)

#Controls 'symbol' validity (constant / variable)         
def checkSymb(arg):
    if (arg.attrib['type'] in ['int', 'bool', 'string']):
        if (arg.attrib['type'] == 'int'):    # int
            if (arg.text is None or not re.match('^([+-]?[1-9][0-9]*|[+-]?[0-9])$', arg.text)):
                sys.stderr.write("Invalid 'int' element value!\n")
                sys.exit(32)
                
        elif (arg.attrib['type'] == 'bool'): # bool
            if (arg.text is None or not arg.text in ['true', 'false']):
                sys.stderr.write("Invalid 'bool' element value!\n")
                sys.exit(32)
                
        else: # string
            if (arg.text is None): # empty string
                arg.text = ''
            elif (not re.search('^(\\\\[0-9]{3}|[^\s\\\\#])*$', arg.text)):
                sys.stderr.write("Invalid 'string' element value!\n")
                sys.exit(32)
            else: # regex looks for escape sequences to transform (regex => int => char)
                arg.text = re.sub(r'\\([0-9]{3})', lambda x: chr(int(x.group(1))), arg.text)
                
    elif (arg.attrib['type'] == 'var'): # var
        checkVar(arg)
        
    elif (arg.attrib["type"] == "nil"): # nil
        if (arg.text != "nil"):
            sys.stderr.write("Invalid 'nil' element value!\n")
            sys.exit(32)
    else: # unexpected type
        sys.stderr.write("Invalid 'type'!\n")
        sys.exit(52)

#Controls 'type' validity
def checkType(arg):
    if (arg.attrib['type'] != 'type'):
        sys.stderr.write("Invalid 'type'!\n")
        sys.exit(52)
    if (arg.text is None or not re.match('^(int|bool|string)$', arg.text)):
        sys.stderr.write("Invalid 'type' element value!\n")
        sys.exit(32)

#Sorts instructions based on their xml attribute 'order'
def sortchildrenby(parent, attr):
    parent[:] = sorted(parent, key=lambda child: int(child.get(attr)))
    
#Returns argument count of instruction
def instrArgCount(instruction):
    return len(list(instruction))


##############################
"""        ARGCHECK        """
##############################
inputfile = None
linesRead = 0

def main():
    global linesRead
    global inputfile
    argc = len(sys.argv[1:])
    # ARGUMENT: 0 arguments
    if (argc == 0):
        sys.stderr.write("No arguments! At least 1 must be passed.\n")
        sys.exit(10)
        
    # ARGUMENT: 1 argument    
    elif (argc == 1): # --source | --input | --help
        if ("--help" == sys.argv[1]):
            print('''Program loads XML representation of IPPcode20 sourcecode from input file and interprets this program with use of stdin and stdout.
Input XML representation is generated by script parse.php from sourcecode in IPPcode20 (language).\n''')
            sys.exit(0)
        if ("--source=" in sys.argv[1]):
            xmlfile = sys.argv[1].split("--source=")[1]
        elif ("--input=" in sys.argv[1]):
            with open(str(sys.argv[1].split("--input=")[1]), 'r') as file:
                inputfile = file.readlines()
            xmlfile = sys.stdin 
        else:
            sys.stderr.write("Unknown argument passed!\n")
            sys.exit(10)

    # ARGUMENT: 2 arguments 
    elif (argc == 2): # --source & --input
        arg1 = sys.argv[1]
        arg2 = sys.argv[2]
        if ("--source=" in arg1 and "--input=" in arg2):
            xmlfile = arg1.split("--source=")[1]
            with open(str(arg2.split("--input=")[1]), 'r') as file:
                inputfile = file.readlines()
        elif ("--input=" in arg1 and "--source=" in arg2):
            xmlfile = arg2.split("--source=")[1]
            with open(str(arg1.split("--input=")[1]), 'r') as file:
                inputfile = file.readlines()
        # ARGUMENT: unknown    
        else:
            sys.stderr.write("Unknown argument passed!\n")
            sys.exit(10) 

    # ARGUMENT: At least 3 arguments
    else:
        sys.stderr.write("Unexpected amount of arguments!\n")
        sys.exit(10)    

    ##############################
    """        XMLCHECK        """
    ##############################
    #sys.stderr.write("ERROR: Empty callstack!\n") debug;
    #XML loading and parsing
    try:
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        sortchildrenby(root, 'order')
    except FileNotFoundError: # file doesnt exist
        sys.stderr.write("Could not open input file!\n")
        sys.exit(11)
    except Exception as e: # incorrect XML structure (not well formed)
        sys.stderr.write("XML Not-well formed!\n")
        sys.exit(31)

    #Various xml-root validity controls
    # ROOT ELEMENT: program    
    if (root.tag != "program"):
        sys.stderr.write("XML not well-formed! Root element not 'program'!\n")
        sys.exit(31)
    # ROOT ELEMENT: povolene atributy su 'language'    
    if ("language" not in root.attrib):
        sys.stderr.write("Root attribute not 'language'!\n")
        sys.exit(32)
    # ROOT ELEMENT: atribut language obsahuje 'ippcode20'    
    if ((str(root.attrib["language"]).lower()) != "ippcode20"):
        sys.stderr.write("Invalid 'language' element value!\n")
        sys.exit(32)    

    ##############################
    """       INSTRCHECK       """
    ##############################

    instrOrderList = [] # list of loaded instructions from xml file

    #Validity controls concerned xml trees 
    for instruction in root:
        # INSTRUCTION: element name    
        if (instruction.tag != "instruction"):
            sys.stderr.write("XML Not well-formed! Incorrect element name for instruction!\n")
            sys.exit(31) 
        # INSTRUCTION: attribute opcode
        if ("opcode" not in instruction.attrib):
            sys.stderr.write("XML Not well-formed! Missing argument 'opcode' for instruction element!\n")
            sys.exit(31)    
        # INSTRUCTION: attribute order
        if ("order" not in instruction.attrib):
            sys.stderr.write("XML Not well-formed! Missing argument 'order' for instruction element!\n")
            sys.exit(31)
        # INSTRUCTION: value of 'order' attribute <= 0
        if (int(instruction.attrib["order"]) <= 0):
            sys.stderr.write("XML Not well-formed! Invalid 'order' value!\n")
            sys.exit(31)   
        instrOrderList.append(instruction.attrib["order"])
        
        ###########################################
        """     INSTRUCTION-ARGUMENTS CHECK     """
        ###########################################

        sortArgs(instruction)
        arg_order = 0

        #Validity controls concerning arguments of loaded instructions
        for argument in instruction:
            arg_order += 1
            # ARGUMENT: element attribute name
            if (argument.tag != 'arg'+str(arg_order)):
                sys.stderr.write("XML Not well-formed! Invalid element!\n")
                sys.exit(31)
            # ARGUMENT: attribute type
                if ('type' not in argument.attrib):
                    sys.stderr.write("XML Not well-formed! Missing 'type' as parameter!\n")
                    sys.exit(31)
            # ARGUMENT: attribute type valid values
                if (argument.attrib['type'] not in ['int', 'bool', 'string', 'label', 'type', 'var', 'nil']):
                    sys.stderr.write("Unxpected XML structure! Invalid 'type' value!\n")
                    sys.exit(32)
                
    #INSTRUCTION: Duplicit 'instruction order'
    if (len(instrOrderList) != len(set(instrOrderList))):  
        sys.stderr.write("XML Not well-formed! Duplicit value of 'order'!\n")
        sys.exit(31)
        

    ####################################
    """ SYNTACTIC AND SEMANTIC CHECK """
    ####################################

    instructionList = []
    #Basically parser.php in another language -> checks loaded instructions for semantic and syntactic errors
    #If 'instruction.attrib["opcode"]'s value considered in following if's => error (unknown / unexpected / invalid instruction)
    #I only commented few usual cases, since all other usual cases are resolved the same way
    for instruction in root:
        instructionDict = dict.fromkeys(["opcode", "argc", "arg1", "arg2", "arg3"]) # dictionary representing each loaded instructions
        instruction.attrib["opcode"] = str(instruction.attrib["opcode"]).upper() # opcode is not case sensitive
        
        #INSTRUCTIONS: ARGC = 0
        if (instruction.attrib["opcode"] in ['CREATEFRAME', 'PUSHFRAME', 'POPFRAME', 'BREAK', 'RETURN']): # none
            if (instrArgCount(instruction) == 0):       # argument-count check
                instructionDict["opcode"] = instruction.attrib["opcode"]
                instructionDict["argc"] = "0"
                del instructionDict["arg1"]             # deletion of unused argument keys in dictionary representing instruction
                del instructionDict["arg2"]             
                del instructionDict["arg3"]
                instructionList.append(instructionDict) # inserts instruction into instructionList (structure for loaded instructions)
            else:
                sys.stderr.write("XML Not well-formed! Wrong instruction argcount!\n")
                sys.exit(31)
                
        #INSTRUCTIONS: ARGC = 1
        elif (instruction.attrib["opcode"] in ['DEFVAR', 'POPS']): # <var>
            if (instrArgCount(instruction) == 1):       # argument-count check
                checkVar(instruction[0])                # lexical, syntactic check
                instructionDict["opcode"] = instruction.attrib["opcode"]
                instructionDict["argc"] = "1"
                del instructionDict["arg2"]             # deletion of unused argument keys in dictionary representing instruction
                del instructionDict["arg3"]             # value of 'arg1|2|3' key (in instruction) is another dictionary, where keys are 'type' and 'text'
                instructionDict["arg1"] = {"type": instruction[0].attrib["type"], "text": instruction[0].text}
                instructionList.append(instructionDict) # inserts instruction into instructionList (structure for loaded instructions)
            else:
                sys.stderr.write("XML Not well-formed! Wrong instruction argcount!\n")
                sys.exit(31)
                
        elif (instruction.attrib["opcode"] in ['PUSHS', 'WRITE', 'DPRINT', 'EXIT']): # <symb>
            if (instrArgCount(instruction) == 1):
                checkSymb(instruction[0])
                instructionDict["opcode"] = instruction.attrib["opcode"]
                instructionDict["argc"] = "1"
                del instructionDict["arg2"]
                del instructionDict["arg3"]
                instructionDict["arg1"] = {"type": instruction[0].attrib["type"], "text": instruction[0].text}
                instructionList.append(instructionDict)
            else:
                sys.stderr.write("XML Not well-formed! Wrong instruction argcount!\n")
                sys.exit(31)     

        elif (instruction.attrib["opcode"] in ['CALL', 'JUMP', 'LABEL']): # <label>
            if (instrArgCount(instruction) == 1):
                checkLabel(instruction[0])
                instructionDict["opcode"] = instruction.attrib["opcode"]
                instructionDict["argc"] = "1"
                del instructionDict["arg2"]
                del instructionDict["arg3"]
                instructionDict["arg1"] = {"type": instruction[0].attrib["type"], "text": instruction[0].text}
                instructionList.append(instructionDict)
            else:
                sys.stderr.write("XML Not well-formed! Wrong instruction argcount!\n")
                sys.exit(31)
                
        #INSTRUCTIONS: ARGC = 2
        elif (instruction.attrib["opcode"] in ['MOVE', 'NOT', 'INT2CHAR', 'TYPE', 'STRLEN']): # <var> <symb>
            if (instrArgCount(instruction) == 2): # argument-count check
                # lexical, syntactic check
                checkVar(instruction[0])
                checkSymb(instruction[1])
                instructionDict["opcode"] = instruction.attrib["opcode"]
                instructionDict["argc"] = "2"
                del instructionDict["arg3"]
                instructionDict["arg1"] = {"type": instruction[0].attrib["type"], "text": instruction[0].text}
                instructionDict["arg2"] = {"type": instruction[1].attrib["type"], "text": instruction[1].text}
                instructionList.append(instructionDict) # inserts instruction into instructionList (structure for loaded instructions)
            else:
                sys.stderr.write("XML Not well-formed! Wrong instruction argcount!\n")
                sys.exit(31)

        elif (instruction.attrib["opcode"] == 'READ'): # <var> <type>
            if (instrArgCount(instruction) == 2):
                checkVar(instruction[0])
                checkType(instruction[1])
                instructionDict["opcode"] = instruction.attrib["opcode"]
                instructionDict["argc"] = "2"
                del instructionDict["arg3"]
                instructionDict["arg1"] = {"type": instruction[0].attrib["type"], "text": instruction[0].text}
                instructionDict["arg2"] = {"type": instruction[1].attrib["type"], "text": instruction[1].text}
                instructionList.append(instructionDict)
            else:
                sys.stderr.write("XML Not well-formed! Wrong instruction argcount!\n")
                sys.exit(31)
                
        #INSTRUCTIONS: ARGC = 3            
        elif (instruction.attrib["opcode"] in ['ADD', 'SUB', 'MUL', 'IDIV', 'LT', 'GT', 'EQ', 'AND', 'OR', 'STRI2INT', 'CONCAT', 'GETCHAR', 'SETCHAR']): # <var> <symb1> <symb2>
            if (instrArgCount(instruction) == 3): # argument-count check
                # lexical, syntactic check
                checkVar(instruction[0])
                checkSymb(instruction[1])
                checkSymb(instruction[2])
                instructionDict["opcode"] = instruction.attrib["opcode"]
                instructionDict["argc"] = "3"           #deletion of unused argument keys in dictionary representing instruction
                instructionDict["arg1"] = {"type": instruction[0].attrib["type"], "text": instruction[0].text}
                instructionDict["arg2"] = {"type": instruction[1].attrib["type"], "text": instruction[1].text}
                instructionDict["arg3"] = {"type": instruction[2].attrib["type"], "text": instruction[2].text}
                instructionList.append(instructionDict) # inserts instruction into instructionList (structure for loaded instructions)
            else:
                sys.stderr.write("XML Not well-formed! Wrong instruction argcount!\n")
                sys.exit(31)      

        elif (instruction.attrib["opcode"] in ['JUMPIFEQ', 'JUMPIFNEQ']): # <label> <symb1> <symb2>
            if (instrArgCount(instruction) == 3):
                checkLabel(instruction[0])
                checkSymb(instruction[1])
                checkSymb(instruction[2])
                instructionDict["opcode"] = instruction.attrib["opcode"]
                instructionDict["argc"] = "3"
                instructionDict["arg1"] = {"type": instruction[0].attrib["type"], "text": instruction[0].text}
                instructionDict["arg2"] = {"type": instruction[1].attrib["type"], "text": instruction[1].text}
                instructionDict["arg3"] = {"type": instruction[2].attrib["type"], "text": instruction[2].text}
                instructionList.append(instructionDict)
            else:
                sys.stderr.write("XML Not well-formed! Wrong instruction argcount!\n")
                sys.exit(31)
                
        # UNKNOWN INSTRUCTION       
        else:
            sys.stderr.write("Invalid 'opcode' of element instruction!\n")
            sys.stderr.write(instruction.attrib["opcode"])
            sys.exit(32)   
    

    ###############################
    """     INTERPRETATION      """
    ###############################

    #Using while loop, that ends when no more instructions can be read,
    #compares read instruction attributes, arguments, values, types,
    #and then executes those instructions in python language; if outputting: (stdout > stderr)
    stack = dataStack()
    handleFrames = frameHandling()
    instrList = instructionListClass()
    instrPos = 1 
    instrList.instructionsInFile = len(instructionList)# loaded instruction count

    for instruction in instructionList:
        instrList.instructions[instrPos] = instruction # adding attributes to class
        if (instruction["opcode"] == "LABEL"):
            if (instruction["arg1"]["text"] in instrList.labels):
                sys.stderr.write("ERROR: Label already exists!\n")
                sys.exit(52)
            instrList.labels[instruction["arg1"]["text"]] = instrPos #adding (label) to instrList (class for instructions)
        instrPos += 1

    while (True):
        instruction = instrList.getNextInstruction() #load instruction
        if (instruction is None):
            return 
        instrOrder = instrList.getInstrCounter()
        executedInstrNum = instrList.getInstrsDone()  
            
        #BREAK
        if (instruction["opcode"] == "BREAK"):
            sys.stderr.write("Current line number: %d\n" % instrOrder)
            sys.stderr.write("Number of executed instructions: %d\n" % executedInstrNum)
            sys.stderr.write("Whole Data stack: ")
            sys.stderr.write(*stack.getStack())
            sys.stderr.write("\nWhole frame stack: ")
            sys.stderr.write(*handleFrames.getFrameStack())
            #LF
            if (handleFrames.getFrame("LF")):
                sys.stderr.write("Local frame: ")
                sys.stderr.write(handleFrames.getFrame("LF"))
            #TF    
            if (handleFrames.getFrame("TF")):
                sys.stderr.write("Temporary frame: ")
                sys.stderr.write(handleFrames.getFrame("TF"))
            #GF    
            if (handleFrames.getFrame("TF")):
                sys.stderr.write("Global frame: ")
                sys.stderr.write(handleFrames.getFrame("GF"))
                
        #PUSHS
        elif (instruction["opcode"] == "PUSHS"):
            argType, argValue, isInVar = handleFrames.getArgTuple(instruction["arg1"])
            if (argValue is None): #var not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            stack.pushValue(argType, argValue)
            
        #POPS
        elif (instruction["opcode"] == "POPS"):
            argType, argValue = stack.popValue()
            handleFrames.setVar(instruction["arg1"], argType, argValue)
        
        #CREATEFRAME
        elif (instruction["opcode"] == "CREATEFRAME"):
            handleFrames.initTmpFrame()
        
        #PUSHFRAME
        elif (instruction["opcode"] == "PUSHFRAME"):
            handleFrames.pushTmpFrame()
        
        #POPFRAME    
        elif (instruction["opcode"] == "POPFRAME"):
            handleFrames.popFrameStack()
        
        #DEFVAR
        elif (instruction["opcode"] == "DEFVAR"):
            handleFrames.defVar(instruction["arg1"])
        
        #WRITE | DPRINT | EXIT
        elif (instruction["opcode"] in ["WRITE", "DPRINT", "EXIT"]):
            argType, argValue, isInVar = handleFrames.getArgTuple(instruction["arg1"])
            if (argValue is None): #var not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (instruction["opcode"] == "EXIT"):
                if (argType != "int"):
                    sys.stderr.write("ERROR: Invalid instruction operand type!\n")
                    sys.exit(53)
                elif (not 0 <= int(argValue) <= 49):
                    sys.stderr.write("ERROR: Invalid 'symbol' value!\n")
                    sys.exit(57)
                else:
                    sys.exit(int(argValue))  
            elif (instruction["opcode"] == "WRITE"):  #WRITE
                if (argType == "nil"):
                    pass
                elif (argValue == '\n'):
                    pass 
                else: 
                    print(argValue, end="") 
            else:  #DPRINT
                sys.stderr.write(argValue)
                
        #MOVE
        elif (instruction["opcode"] == "MOVE"):
            argType, argValue, isInVar = handleFrames.getArgTuple(instruction["arg2"])
            if (argValue is None): #var not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            handleFrames.setVar(instruction["arg1"], argType, argValue)
        
        #ADD | SUB | MUL | IDIV
        elif (instruction["opcode"] in ["ADD", "SUB", "MUL", "IDIV"]):
            argType1, argValue1, isInVar1 = handleFrames.getArgTuple(instruction["arg2"])
            argType2, argValue2, isInVar2 = handleFrames.getArgTuple(instruction["arg3"])
            if (argValue1 is None or argValue2 is None): #var(s) not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType1 == argType2 == "int"):
                # ADD
                if (instruction["opcode"] == "ADD"):
                    handleFrames.setVar(instruction["arg1"], "int", str(int(argValue1) + int(argValue2)))
                # SUB    
                elif (instruction["opcode"] == "SUB"):
                    handleFrames.setVar(instruction["arg1"], "int", str(int(argValue1) - int(argValue2)))
                # MUL    
                elif (instruction["opcode"] == "MUL"):
                    handleFrames.setVar(instruction["arg1"], "int", str(int(argValue1) * int(argValue2)))
                #IDIV    
                else:
                    if int(argValue2) == 0:
                        sys.stderr.write("ERROR: Division by zero!\n")
                        sys.exit(57)
                    else:
                        handleFrames.setVar(instruction["arg1"], "int", str(int(argValue1) // int(argValue2)))
            else:
                sys.stderr.write("ERROR: Invalid instruction operand type!\n")
                sys.exit(53)

        #TYPE    
        elif (instruction["opcode"] == "TYPE"):
            argType, argValue, isInVar = handleFrames.getArgTuple(instruction["arg2"])
            if (argType is None):                                       # uninitialized --> empty string
                argType = ''
            handleFrames.setVar(instruction["arg1"], "string", argType) # writing type of arg2 into arg1
        
        #CONCAT
        elif (instruction["opcode"] == "CONCAT"):
            argType1, argValue1, isInVar1 = handleFrames.getArgTuple(instruction["arg2"])
            argType2, argValue2, isInVar2 = handleFrames.getArgTuple(instruction["arg3"])
            if (argValue1 is None or argValue2 is None): #var(s) not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType1 == argType2 == "string"):
                handleFrames.setVar(instruction["arg1"], "string", argValue1 + argValue2)
            else: # invalid operand types
                sys.stderr.write("ERROR: Invalid instruction operand type!\n")
                sys.exit(53)
                
        #AND | OR
        elif (instruction["opcode"] in ["AND", "OR"]):
            argType1, argValue1, isInVar1 = handleFrames.getArgTuple(instruction["arg2"])
            argType2, argValue2, isInVar2 = handleFrames.getArgTuple(instruction["arg3"])
            if (argValue1 is None or argValue2 is None): #var(s) not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType1 == argType2 == "bool"):
                if (instruction["opcode"] == "AND"):
                    handleFrames.setVar(instruction["arg1"], "bool", "true" if (argValue1 == "true" == argValue2) else "false")     
                else:    
                    handleFrames.setVar(instruction["arg1"], "bool", "true" if ("true" in [argValue1,argValue2]) else "false")
            else:
                sys.stderr.write("ERROR: Invalid instruction operand type!\n")
                sys.exit(53)

        #NOT
        elif (instruction["opcode"] == "NOT"):
            argType, argValue, isInVar = handleFrames.getArgTuple(instruction["arg2"])
            if (argValue is None): #var not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType == "bool"):
                handleFrames.setVar(instruction["arg1"], "bool", "true" if (argValue == "false") else "false")
            else:
                sys.stderr.write("ERROR: Invalid instruction operand type!\n")
                sys.exit(53)
                
        #LABEL
        elif (instruction["opcode"] == "LABEL"): # labels are loaded prior to interpretation
            continue 
        
        #JUMP
        elif (instruction["opcode"] == "JUMP"):
            instrList.jumpToLabel(instruction["arg1"])
        
        #JUMPIFEQ |JUMPIFNEQ
        elif (instruction["opcode"] in ["JUMPIFEQ", "JUMPIFNEQ"]):
            argType1, argValue1, isInVar1 = handleFrames.getArgTuple(instruction["arg2"])
            argType2, argValue2, isInVar2 = handleFrames.getArgTuple(instruction["arg3"])
            if (argValue1 is None or argValue2 is None): #var(s) not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType1 == argType2 or argType1 == "nil" or argType2 == "nil"): # equal types or one is nil
                if (instruction["opcode"] == "JUMPIFEQ" and argValue1 == argValue2):
                    instrList.jumpToLabel(instruction["arg1"])
                elif (instruction["opcode"] == "JUMPIFNEQ" and argValue1 != argValue2):
                    instrList.jumpToLabel(instruction["arg1"])
                else:
                    if (instruction["arg1"]["text"] not in instrList.labels):  # label existence check
                        sys.stderr.write("ERROR: Unknown label used!\n")
                        sys.exit(52)
                    pass  
            else: # not-equal types
                sys.stderr.write("ERROR: Instruction has different argument types!\n")
                sys.exit(53)
            
        #CALL
        elif (instruction["opcode"] == "CALL"):
            instrList.pushNextInstructionToCallStack()
            instrList.jumpToLabel(instruction["arg1"])
        
        #RETURN
        elif (instruction["opcode"] == "RETURN"):
            instrList.popNextInstructionFromCallStack()
        
        #LT | GT | EQ
        elif (instruction["opcode"] in ["LT", "GT", "EQ"]):
            argType1, argValue1, isInVar1 = handleFrames.getArgTuple(instruction["arg2"])
            argType2, argValue2, isInVar2 = handleFrames.getArgTuple(instruction["arg3"])
            if (argValue1 is None or argValue2 is None): #var(s) not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType1 == argType2):
                if (instruction["opcode"] == "EQ"):  # equal
                    handleFrames.setVar(instruction["arg1"], "bool", "true" if (argValue1 == argValue2) else "false")
                elif (instruction["opcode"] == "LT"): # lower
                    if (argType1 == "int"):
                        handleFrames.setVar(instruction["arg1"], "bool", "true" if (int(argValue1) < int(argValue2)) else "false")
                    elif (argType1 == "bool"):
                        handleFrames.setVar(instruction["arg1"], "bool", "true" if (argValue1 == "false" and  argValue2 == "true") else "false")
                    elif (argType1 == "nil"):
                        sys.stderr.write("ERROR: Type 'nil' can only be compared with instruction EQ!\n")
                        sys.exit(53)
                    else:
                        handleFrames.setVar(instruction["arg1"], "bool", "true" if (argValue1 < argValue2) else "false")
                else: # greater
                    if (argType1 == "int"):
                        handleFrames.setVar(instruction["arg1"], "bool", "true" if (int(argValue1) > int(argValue2)) else "false")
                    elif (argType1 == "bool"):
                        handleFrames.setVar(instruction["arg1"], "bool", "true" if (argValue1 == "true" and  argValue2 == "false") else "false")
                    elif (argType1 == "nil"):
                        sys.stderr.write("ERROR: Type 'nil' can only be compared with instruction EQ!\n")
                        sys.exit(53)    
                    else:
                        handleFrames.setVar(instruction["arg1"], "bool", "true" if (argValue1 > argValue2) else "false")
            elif ((argType1 == "nil" or argType2 == "nil") and instruction["opcode"] == "EQ"):         
                handleFrames.setVar(instruction["arg1"], "bool", "true" if (argValue1 == argValue2) else "false")   
            else:
                sys.stderr.write("ERROR: Instruction has different argument types!\n")
                sys.exit(53)

        #STRLEN
        elif (instruction["opcode"] == "STRLEN"):    
            argType, argValue, isInVar = handleFrames.getArgTuple(instruction["arg2"])
            if (argValue is None): #var not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType == "string"): # type check
                handleFrames.setVar(instruction["arg1"], "int", len(argValue))
            else:
                sys.stderr.write("ERROR: in STRLEN -- operand type not string!\n")
                sys.exit(53)  
        
        #GETCHAR
        elif (instruction["opcode"] == "GETCHAR"):
            argType1, argValue1, isInVar1 = handleFrames.getArgTuple(instruction["arg2"])
            argType2, argValue2, isInVar2 = handleFrames.getArgTuple(instruction["arg3"])
            if (argValue1 is None or argValue2 is None): #var(s) not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType1 == "string" and argType2 == "int"):   # type check (if correct)
                index = int(argValue2)
                if (0 <= index <= len(argValue1)-1): # correct index, writing char to arg1
                    handleFrames.setVar(instruction["arg1"], "string", argValue1[index])
                else:                                          # index out of bounds (for string)
                    sys.stderr.write("ERROR: in GETCHAR -- index out of bounds!\n")
                    sys.exit(58)
            else:
                sys.stderr.write("ERROR: in GETCHAR -- invalid operand type!\n")
                sys.exit(53)
        
        #SETCHAR
        elif (instruction["opcode"] == "SETCHAR"):
            argType1, argValue1, isInVar1 = handleFrames.getArgTuple(instruction["arg1"])
            argType2, argValue2, isInVar2 = handleFrames.getArgTuple(instruction["arg2"])
            argType3, argValue3, isInVar3 = handleFrames.getArgTuple(instruction["arg3"])
            if (argValue1 is None or argValue2 is None or argValue3 is None): #var(s) not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType1 == "string" and argType2 == "int" and argType3 == "string"): # type check (if correct)
                index = int(argValue2)
                if (not(0 <= index <= len(argValue1)-1)):
                    sys.stderr.write("ERROR: in SETCHAR -- index out of bounds!\n")
                    sys.exit(58)
                if (argValue3 == ""): # empty string as arg3
                    sys.stderr.write("ERROR: in SETCHAR -- empty string!\n")
                    sys.exit(58)
                argValue1 = list(argValue1)
                argValue1[index] = argValue3[0]
                argValue1 = "".join(argValue1)
                handleFrames.setVar(instruction["arg1"], "string", argValue1)

            else:  
                sys.stderr.write("ERROR: in SETCHAR -- invalid operand type!\n")
                sys.exit(53)    
            
        #INT2CHAR
        elif (instruction["opcode"] == "INT2CHAR"):
            argType, argValue, isInVar = handleFrames.getArgTuple(instruction["arg2"])
            if (argValue is None): #var not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType == "int"): # type check
                try:
                    char = chr(int(argValue))
                except ValueError:
                    sys.stderr.write("ERROR: in INT2CHAR -- invalid ordinal value of char!\n")
                    sys.exit(58)
                handleFrames.setVar(instruction["arg1"], "string", char)
            else:
                sys.stderr.write("ERROR: in INT2CHAR -- invalid operand type!\n")
                sys.exit(53)    
        
        #STRI2INT
        elif (instruction["opcode"] == "STRI2INT"):
            argType1, argValue1, isInVar1 = handleFrames.getArgTuple(instruction["arg2"])
            argType2, argValue2, isInVar2 = handleFrames.getArgTuple(instruction["arg3"])
            if (argValue1 is None or argValue2 is None): #var(s) not initialized
                sys.stderr.write("ERROR: Tried to read uninitialized variable!\n")
                sys.exit(56)
            if (argType1 == "string" and argType2 == "int"): # type check (if correct)
                index = int(argValue2)
                if (index >= 0 and index <= len(argValue1)-1): # correct index
                    ordVal = ord(argValue1[index])
                    handleFrames.setVar(instruction["arg1"], "int", ordVal)
                else: # index out of bounds (for arg2)
                    sys.stderr.write("ERROR: in STRI2INT -- index out of bounds!\n")
                    sys.exit(58)
            else:
                sys.stderr.write("ERROR: in STRI2INT -- invalid operand type!\n")
                sys.exit(53)
        
        #READ
        elif (instruction["opcode"] == "READ"):
            argType, argValue, isInVar = handleFrames.getArgTuple(instruction["arg2"])
            exceptionRaised = False
            if (not inputfile):
                try:
                    userInput = input()
                except Exception:   # exception occured during input
                    exceptionRaised = True
            else:
                try:
                    userInput = inputfile[linesRead]
                    userInput = userInput.rstrip()
                except:
                    exceptionRaised = True   
                linesRead += 1    
                            
            if (exceptionRaised == False):
                if (argValue == "int"): # int
                    try:
                        userInput = int(userInput)
                    except Exception:
                        exceptionRaised = True      
                elif (argValue == "bool"): # bool
                    try:
                        userInput = "true" if (userInput.lower() == "true") else "false" 
                    except Exception:
                        userInput = "false"
                else: # string    
                    try:
                        userInput = str(userInput)
                    except Exception:
                        exceptionRaised = True        

            if (exceptionRaised == True):
                handleFrames.setVar(instruction["arg1"], "nil", "nil")
            else:
                handleFrames.setVar(instruction["arg1"], argValue, userInput)

if __name__ == '__main__':
    main()