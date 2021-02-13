

Project implementation documentation for IPP 2019/2020
Name and surname: Matej Dubec
Login: xdubec00

## IPP  - parse.php (analyser)

### About 
Filter script in `PHP 7.4`,  named `parse.php` reads lines of code from `STDIN` . The script checks if written code is syntatically & lexically valid ( = syntax and lexical analysis ), then echoes its `XML` representation to `STDOUT`.

### Execution possibilities
If your intention is to perform analysis on a source file, the script takes no arguments and you need to redirect the desired file to `STDIN`.
   
    php7.4 parse.php < IPPcode20

For guidance / help, pass exactly 1 argument to the script.
    
    php7.4 parse.php --help

For extended statistics, pass following arguments to the script --stats=file --loc, --comments, --labels, --jumps.
    
    php7.4 parse.php --stats=subor --loc --jumps --comments -labels < IPPcode20

Arguments meaning: output file, number of instructions, comments, defined unique labels & jumps.
It is possible to use different order of passed arguments or to repeat those arguments.

### Implementation & code 
Read code is expected to be written in language named `IPPcode20`. 
When you run this script, it reads a line from `STDIN` in a loop ( 1 line equals 1 instruction & instruction operands). The analysis itself is done in a manner of iterating over an array of supported instructions,
comparing each known instruction with the first word that was read from line. Read line is sliced into array of substrings, using space character as a delimeter. First line makes sure that only actual words are gonna be analyzed.

    $line = preg_replace("/( |  )+/", " ", $line); 
    $lexemeArray = explode(" ", $line);

After we find a match between instruction in our instruction list `$IPPinstructs` and read instruction `$lexemeArray[0]` we then continue to analyze passed instruction arguments ( if there are such arguments ) with regular expressions, which denote syntactic and lexical correctness.
If the instruction was correctly written, the script then moves on to read the next line. 

If an error occured during analysis ( = instruction is not correctly written / unknown instruction was written / unexpected instruction arguments were passed or wrong format of passed arguments was used ), script prints error line to `STDERR`, and is terminated, returning with a code signalizing error encounter.

### Return values
Script returns `10` if `--help` is not the only argument passed to script or is incorrectly written as an argument.
Script returns `11` if it could not open desired file for writing. (STATP)
Script returns `21` if there is a missing or incorrectly written header (`.IPPcode19`).
Script returns `22` if unknown or incorrect operation code was found in source file.
Script returns `23` if other lexical or syntactical error was encountered.

