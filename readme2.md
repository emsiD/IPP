Documentation of project implementation for IPP 2019/2020
Name and surname: Matej Dubec
Login: xdubec00
## IPP  - interpret.py & test.php

### About assignment
Script in `python 3.8`,  named `interpret.py` loads `XML` representation of `IPPcode20` sourcecode from from stdin or file. Name of the sourcecode file can be passed as argument prior to script execution. The script checks whether XML the loaded sourcecode is lexically, syntactically and semantically correct. After proper analyzation, it executes loaded instructions in python language if the code is correctly written. 

### Program arguments
Script understands 3 possible arguments:
    `--help`, `--source=<filename.xml>` and `--input=<filename>`. 

The first one can not be passed along with other arguments. For the latter two possible arguments, at least one must be explicitly passed to script, the other one is loaded from `stdin`. (If both arguments are passed, the order doesn't matter) 
 
So the possibilities of argument passing are: 
   
    python3.6 interpret.py --source=<> | --input=<> | --source=<> --input=<>

For guidance / help :
    
    python3.6 interpret.py --help

### Implementation 
Script implementation contains 3 classes: `dataStack` for easier, more intuitive stack operations on list. `instructionListClass` for handling requests for next instructions, moving data to & from various stacks and moving across code using a pythonic dictionary for labels and their positions, and at last `frameHandling`, which, as its name suggests, handles operations concerning creation / deletion and usage of frames. After script execution, interpret parses passed arguments and responds to them accordingly.

Program consists of one `main()` function, which directs the flow of program. It can be divided into parts containing quite large loops, where argument validation, lexical, syntactic analysis and execution happens.

After checking, if arguments were passed correctly, we check if XML input is well-formed and doesn't have unexpected structure in `XMLCHECK` part of the script. 
If so, the first loop `INSTRCHECK`:
    checks if XML input is well-formed and doesn't have unexpected structure. 

Second loop `SYNTACTIC AND SEMANTIC CHECK`:
    consists of a number of conditions, sorted by expected number of arguments. Each iteration compares read instructions' operation code and number of its attributes to those known in `IPPcode20` language and reacts accordingly.

Third loop `INTERPRETATION` is the only one not being an iteration of XML input tree elements, mainly because of the need to jump across the code, thanks to the existence of labels. Each instruction is ordered, correctly formed, and compared to known instructions and then executed in python language. During interpretation, the script checks for possible runtime errors, if none were detected, it continues to interpret passed commands accordingly to project documentation.
 
### Return values
Intrpret returns:
`10` - if `--help` is not the only argument passed to `interpret.py` script or argument was incorrectly written
`31` - if XML input is not well-formed
`32` - if unexpected structure (of XML) or lexical / syntactic error of text elements & attributtes were encountered in XML input
`52` - if error was encountered during semantic check of IPPcode20 sourcecode (undefined label, redefinition of a variable)
`53` - runtime interpretation error (wrong operand types)
`54` - runtime interpretation error - access to non-existent variable
`55` - runtime interpretation error – non-existent frame (reading from empty framestack)
`56` - runtime interpretation error – missing value (in variable, datastack, or callstack)
`57` - runtime interpretation error – wrong operand value (zero division, wrong exit-code for instruction EXIT)
`58` - runtime interpretation error – unsupported string operation 
`0`  - if no error was encountered and everything ran correctly

### Script test.php
Should be used for automated testing. However, only argument check and folder searching, along with basic html output were implemented. If there will be enough time, I may implement more.