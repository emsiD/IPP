<?php
error_reporting(E_ERROR | E_PARSE); // Matej Dubec - xdubec00

#[INSTRNAME, ARGC, ARGTYPE]
$IPPinstructs = [
    ["MOVE", 2, "var", "symb"],
    ["CREATEFRAME",0],
    ["PUSHFRAME", 0],
    ["POPFRAME", 0],
    ["DEFVAR", 1, "var"],
    ["CALL", 1, "label"],
    ["RETURN", 0],

    ["PUSHS", 1, "symb"],
    ["POPS", 1, "var"],

    ["ADD", 3, "var", "symb", "symb"],
    ["SUB", 3, "var", "symb", "symb"],
    ["MUL", 3, "var", "symb", "symb"],
    ["IDIV", 3, "var", "symb", "symb"],
    ["LT", 3, "var", "symb", "symb"],
    ["GT", 3, "var", "symb", "symb"],
    ["EQ", 3, "var", "symb", "symb"],
    ["AND", 3, "var", "symb", "symb"],
    ["OR", 3, "var", "symb", "symb"],
    ["NOT", 2, "var", "symb"],
    ["INT2CHAR", 2, "var", "symb"],
    ["STRI2INT", 3, "var", "symb", "symb"],

    ["READ", 2, "var", "type"],
    ["WRITE", 1, "symb"],

    ["CONCAT", 3, "var", "symb", "symb"],
    ["STRLEN", 2, "var", "symb"],
    ["GETCHAR", 3, "var", "symb", "symb"],
    ["SETCHAR", 3, "var", "symb", "symb"],

    ["TYPE", 2, "var", "symb"],

    ["LABEL", 1, "label"],
    ["JUMP", 1, "label"],
    ["JUMPIFEQ", 3, "label", "symb", "symb"],
    ["JUMPIFNEQ", 3, "label", "symb", "symb"],
    ["EXIT", 1, "symb"],

    ["DPRINT", 1, "symb"],
    ["BREAK", 0]
];

#FLAGS (MAINLY FOR STATP)
$instructionCount = 0;
$commentaryCount = 0;
$jumpCount = 0;
$statsArgPassed = FALSE;
$statsArgIndex = 0;
$definedLabels = [];

#PRINTS XML REPRESENTATION OF INSTRUCTION
function printInstruction($num, $opCode) {
    $str ="\t<instruction order=\"$num\" opcode=\"$opCode\">\n";
    echo $str;
}

#PRINTS XML REPRESENTATION OF INSTR. OPERAND
function printArgument($num, $argType, $argVal) {
    $argVal = htmlspecialchars($argVal, ENT_XML1, 'UTF-8');
    $str = "\t\t<arg$num type=\"$argType\">$argVal</arg$num>\n";
    echo $str;
}

#SCRIPT BEGINNING:
#FOR HELP -> php7.4 parse.php --help
if (($argc == 2) && (preg_match("/^(--|-)help$/", "$argv[1]"))) { // Case sensitive

    print("Skript typu filter v jazyku PHP 7.4,\n");
    print("načíta zo štandardného vstupu zdrojový kód v IPPcode20,\n");
    print("skontroluje lexikálnu a syntaktickú správnosť kódu,\n");
    print("a vypíše na stdout XML reprezentáciu programu.\n");
    print("autor: Matej Dubec - xdubec00\n");
    print("Projekt do IPP, FIT VUT 2020\n");
    exit(0);

}

#CONTROL IF PASSED ARGUMENTS ARE CORRECTLY FORMATTED
elseif ($argc > 2) { // Only if some argument was actually passed
    $index = 0;
    foreach ($argv as $argument) {
        if (preg_match("/^(--|-)help$/", "$argument")) {
            fprintf(STDERR, "Wrong combination of script parameters!\n");
            exit(10);
        }
        if (preg_match("/^(--|-)stats=.*$/", "$argument")) {
            $statsArgPassed = TRUE;
            $statsArgIndex = $index;
        }
        $index++;
    }
}

#CONTROL FOR STATP EXTENSION
if ($argc == 2 && preg_match("/^(--|-)stats=.*$/", "$argv[1]")) {
    $statsArgPassed = TRUE;
    $statsArgIndex = 1;
}

foreach ($argv as $argument) { // Error handling
    if (preg_match("/^(--|-)(comments|labels|jumps|loc)$/", "$argument") && $statsArgPassed == FALSE) {
        fprintf(STDERR, "Script parameter --stats missing!\n");
        exit(10);
    }
    if (!preg_match("/^(--|-)(comments|labels|jumps|loc|help|stats=.*)$/", "$argument") && "$argument" != $argv[0]) {
        fprintf(STDERR, "Unexpected script parameter!\n");
        exit(10);
    }
}

#LOOPED READ FROM STDIN
if (STDIN) { // Reads lines from standard input, splits them according to spaces, analyzes read instructions / arguments
    $cnt = 0;
    while (($line = fgets(STDIN, 1024)) !== false) {

        $line = trim($line);
        $commentary = FALSE;

        if ($line == "\n" || $line == "" || ctype_space($line)) continue; // Empty read line is skipped

        #COMMENTARYCHECK
        if (($pos = strpos($line, "#")) !== FALSE ) { // If "#" present, either cuts the comment out from read line,
            if ($pos == 0) {                          // or skips the line (since it begins with a comment)
                $commentary = TRUE;
                $commentaryCount++;
                continue;
            }
            else $line = (preg_replace("/#(' '|.)*/", "", $line));
            $commentary = TRUE;
            $commentaryCount++;
        }

        #HEADER-PRESENCE CONTROL
        if ($cnt == 0) { // First non-comment, non-empty line has to be header
            if (!preg_match("/^.IPPcode20( )*$/i", $line)) {
                fprintf(STDERR, "Wrong or missing header in source file!\n");
                exit(21);
            }
            fwrite(STDOUT, "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<program language=\"IPPcode20\">\n");
        }

        else {
            #LEXICAL & SYNTACTIC ANALYSIS
            $line = preg_replace("/( |  )+/", " ", $line); // If more spaces than one -> replace them with exactly 1 space
            $lexemeArray = explode(" ", $line);            // Line split to words without white characters
            
            #LOOPED RECOGNIZATION OF PASSED INSTRUCTION
            foreach ($IPPinstructs as $instruction) {
                $instrFound = FALSE;
                $lexemeArray = array_map('trim', $lexemeArray);

                #INSTRUCTION ANALYSIS
                if (strcasecmp("$instruction[0]", "$lexemeArray[0]") == 0) { // Instruction recognized
                    $instructionCount++;

                    #IF NO ARGUMENTS NEEDED FOR INSTRUCTION
                    if ($instruction[1] === 0) {
			            if ($lexemeArray[1]) { // Argument passed when expecting none
				            fprintf(STDERR, "Unexpected argument (0 args expected)!\n");
                        	exit(23);
			            }
                        $instrFound = TRUE;
                        printInstruction($cnt, $instruction[0]);
                        fprintf(STDOUT, "\t</instruction>\n");
                        if (preg_match("/return/i", "$instruction[0]")) $jumpCount++;
                        break;
                    }
                    
                    #IF ARGUMENTS NEEDED FOR INSTRUCTION
                    if (((count($lexemeArray)-1) != $instruction[1]) and ($commentary == FALSE)) { // Wrong argument count of instruction
                        fprintf(STDERR, "Wrong number of arguments!\n");
                        exit(23);
                    }

                    $instrFound = TRUE;
                    printInstruction($cnt, $instruction[0]);

                    #INSTRUCTION OPERAND ANALYSIS
                    for ( $i = 0; $i < $instruction[1]; $i++) { // Checks if instructions / operands match correct reg.expressions

                        #OPERAND TYPE = SYMB -> expecting string / variable / constant
                        if (strcmp($instruction[$i+2], "symb") == 0) {

                            if (stristr($lexemeArray[$i+1], "@") == TRUE) {
                                $strippedOp = explode("@", $lexemeArray[$i+1]);

                                #VARIABLE AS OP. -> expecting LF/GF/TF@name
                                if ((count($strippedOp) == 2) && (preg_match("/^(LF|GF|TF)$/", $strippedOp[0]))) {
                                    if (preg_match("/^[a-zA-Z_\-\$&%\*!\?][a-zA-Z0-9_\-\$&%\*!\?]*$/", $strippedOp[1])) {
                                        printArgument($i+1, "var",$lexemeArray[$i+1]);
                                    }
                                    else {
                                        fprintf(STDERR, "Wrong operand format!\n");
                                        exit(23);
                                    }
                                }

                                #STRING AS OP. -> expecting \000 - \999 or string without white characters or "#"
                                elseif (preg_match("/^string$/", $strippedOp[0])) {
                                    if (preg_match("/^(\\\\[0-9][0-9][0-9]|[^#\\\\\s])*$/", $strippedOp[1])) {
                                        printArgument($i+1, $strippedOp[0],$strippedOp[1]);
                                    }
                                    else {
                                        echo "$strippedOp[1]";
                                        fprintf(STDERR, "Wrong operand format!\n");
                                        exit(23);
                                    }
                                }

                                #INT AS OP. -> expecting number (+|-)00..0420
                                elseif ((count($strippedOp) == 2) && (preg_match("/^int$/", $strippedOp[0]))) {
                                    if (preg_match("/^(\+|\-)?[0-9]+$/", $strippedOp[1])) {
                                        printArgument($i+1, $strippedOp[0],$strippedOp[1]);
                                    }
                                    else {
                                        fprintf(STDERR, "Wrong operand format!\n");
                                        exit(23);
                                    }
                                }

                                #BOOL AS OP. -> expecting bool@(true|false) only
                                elseif ((count($strippedOp) == 2) && (preg_match("/^bool$/", $strippedOp[0]))) {
                                    if (preg_match("/^(true|false)$/", $strippedOp[1])) {
                                        printArgument($i+1, $strippedOp[0],$strippedOp[1]);
                                    }
                                    else {
                                        fprintf(STDERR, "Wrong operand format!\n");
                                        exit(23);
                                    }
                                }

                                #NIL AS OP -> expecting-> expecting nil@nil only
                                elseif ((count($strippedOp) == 2) && (preg_match("/^nil$/", $strippedOp[0]))) {
                                    if (preg_match("/^nil$/", $strippedOp[1])) {
                                        printArgument($i+1, $strippedOp[0],$strippedOp[1]);
                                    }
                                    else {
                                        fprintf(STDERR, "Wrong operand format!\n");
                                        exit(23);
                                    }
                                }

                                #UNKNOWN OP.
                                else {
                                    fprintf(STDERR, "Unknown operand / Wrong format of operand!\n");
                                    exit(23);
                                }
                            }
                            else {
                                fprintf(STDERR, "Wrong operand format!\n");
                                exit(23);
                            }
                        }

                        #OPERAND TYPE = VAR -> expecting variable
                        elseif (strcmp($instruction[$i+2], "var") == 0) {
                            #komentar
                            if (stristr($lexemeArray[$i+1], "@") == TRUE) {
                                $strippedOp = explode("@", $lexemeArray[$i+1]);

                                #VARIABLE AS OP.
                                if ((count($strippedOp) == 2) && (preg_match("/^(LF|GF|TF)$/", $strippedOp[0]))
                                    && (preg_match("/^[a-zA-Z_\-\$&%\*!\?][a-zA-Z0-9_\-\$&%\*!\?]*$/", $strippedOp[1]))) {
                                    printArgument($i+1, "var", $lexemeArray[$i+1]);
                                }
                                else {
                                    fprintf(STDERR, "Wrong operand format!\n");
                                    exit(23);
                                }
                            }
                            else {
                                fprintf(STDERR, "Wrong operand format!\n");
                                exit(23);
                            }
                        }

                        #OPERAND TYPE = TYPE
                        elseif (strcmp($instruction[$i+2], "type") == 0) {
                            if ((preg_match("/^(int|bool|string)$/", $lexemeArray[$i+1]))) {
                                printArgument($i+1, $instruction[$i+2],$lexemeArray[$i+1]);
                            }
                            else {
                                fprintf(STDERR, "Wrong operand format!\n");
                                exit(23);
                            }
                        }

                        #OPERAND TYPE = LABEL
                        elseif (strcmp($instruction[$i+2], "label") == 0) {
                            if (preg_match("/^[a-zA-Z_\-\$&%\*!\?][a-zA-Z0-9_\-\$&%\*!\?]*$/", $lexemeArray[$i+1])) { // Same regex as for var ID
                            	printArgument($i+1, $instruction[$i+2],$lexemeArray[$i+1]);
                            	if (!in_array($lexemeArray[$i+1], $definedLabels)) $definedLabels[] = $lexemeArray[$i+1];
                            }
                            else {
                                fprintf(STDERR, "Wrong operand format!\n");
                                exit(23);
                            }
                        }

                        #OPERAND TYPE UNKNOWN
                        else {
                            fprintf(STDERR, "Unknown operand used!\n!\n");
                            exit(23);
                        }
                    }
                    fprintf(STDOUT, "\t</instruction>\n");
                    if (preg_match("/(call|jump|jumpifeq|jumpifneq)/i", "$instruction[0]")) { // Jumpcount for STATP extension
                        $jumpCount++;
                    }
                    break;
                }
            }
            #DIDNT FIND KNOWN INSTRUCTIONS
            if (($instrFound == FALSE) && (!preg_match("/^\s*$/", $line))) {
                fprintf(STDOUT, "Unknown or wrong op. code!\n");
                exit(22);
            }
        }
        $cnt++;
    }

    #IF EMPTY FILE PASSED
    if ($cnt == 0) {
        fwrite(STDERR, "Empty file!\n");
        exit(21);
    }
}
fwrite(STDOUT, "</program>\n");

#STATP EXTENSION OUTPUT LOGIC
if ($statsArgPassed) {
    $statsFileName = preg_replace("/(--|-)stats=/", "", $argv[$statsArgIndex]);
    $myFile = fopen("$statsFileName", "w") or die(12);

    foreach ($argv as $argument) {
        if (preg_match("/^(--|-)loc$/", $argument)) {
            fwrite($myFile, "$instructionCount\n");
        }
        if (preg_match("/^(--|-)jumps$/", $argument)) {
            fwrite($myFile, "$jumpCount\n");
        }
        if (preg_match("/^(--|-)labels$/", $argument)) {
            $labelCount = count($definedLabels);
            fwrite($myFile, "$labelCount\n");
        }
        if (preg_match("/^(--|-)comments$/", $argument)) {
            fwrite($myFile, "$commentaryCount\n");
        }
    }
    fclose($myFile);
}
exit(0);
?>
