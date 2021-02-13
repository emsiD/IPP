<?php
error_reporting(E_ERROR | E_PARSE);

function errxit($errstring, $errcode) {
    fprintf("STDOUT", "$errstring\n");
    exit($errcode);
}

#FOR HELP -> php7.4 test.php --help
if (($argc != 2) && (preg_match("/^(--|-)help$/", "$argv[1]"))) {
    echo("Unexpected arguments!\n");
    exit(10);
}

#VARIABLE INITIALIZATION
$path = system(pwd);
#$path = preg_replace("/\/test/", "", $path);
$pfile = "./parse.php";
$ifile = "./interpret.py";
$testdir = "$path"; #/home/emsid/Eclipse veci/test NAPRIKLAD
$jexamxml = "$path"+"/pub/courses/ipp/jexamxml/jexamxml.jar";
$parseonly = false;
$intonly = false;
$recursive = false;
$pflag = false;
$iflag = false;


#ARGUMENT CONTROL
foreach ($argv as $argument) {
    switch (true) {
        case preg_match("/^test.php$/", $argument):
            continue 2;
        case preg_match("/^(-|--)help$/", $argument):
            echo "Skript (test.php v jazyce PHP 7.4) bude sloužit pro automatické testování postupné aplikace
parse.php a interpret.py. Skript projde zadaný adresář s testy a využije je pro automatické
otestování správné funkčnosti obou předchozích programů včetně vygenerování přehledného souhrnu
v HTML 5 do standardního výstupu.\n";
            exit(0);
            break;
            
        case preg_match("/^(-|--)directory=.+$/", $argument):
            $path = preg_replace("/^(-|--)directory=/", "", $argument); // Check if the file exists, if not -> error 11;
            break;
            
        case preg_match("/^(-|--)parse-script=.+$/", $argument):
            $pfile = "$path" + preg_replace("/^(-|--)parse-script=/", "", $argument); // Check if the file exists, if not -> error 11;
            $pflag = true;
            if (!is_file($pfile)) errxit("The file $pfile does not exist!", 11);
            break;
            
        case preg_match("/^(-|--)int-script=.+$/", $argument):
            $ifile = "$path" + preg_replace("/^(-|--)int-script=/", "", $argument); // Check if the file exists, if not -> error 11;
            $iflag = true;
            if (!is_file($ifile)) errxit("The file $ifile does not exist!", 11);
            break;
            
        case preg_match("/^(-|--)jexamxml=.+$/", $argument):
            $jexamxml = preg_replace("/^(-|--)jexamxml=/", "", $argument); // Check if the file exists, if not -> error 11;
            break;
        case preg_match("/^(-|--)recursive$/", $argument): // Recursive search through folders;
            $recursive = true;
            ;
            break;
        case preg_match("/^(-|--)parse-only$/", $argument):
            $parseonly = true;
            ;
            break;
        case preg_match("/^(-|--)int-only$/", $argument):
            $intonly = true;
            ;
            break;
        default:
            continue 2;
            
    }
    ;
}
if (($parseonly && $intonly) || ($parseonly && $iflag) || ($intonly && $pflag)) {
    echo("Wrong argument combination!\n");
    exit(10);
}

#TEST DIRECTORY SEARCH

echo "$path\n"; // testovaci vypis
if (is_dir($path)) {
    $files = scandir($path);
    foreach ($files as $item) {
        if (preg_match("/^(.|..)$/", $item)) continue; //|| preg_match("$path", $item)
        if (is_file($item)) echo ("$item je subor\n");
        if (is_dir($item)) echo ("$item je zlozka\n");
    }
}
else {
    errxit("The directory $path does not exist!", 11);
}




echo ("<!DOCTYPE html>
<html lang=\"sk\">
<h3>Ahoj, toto je nedokonceny nefunkcny test.php pre frajerov, ktori si chcu otestovat svoje projekty do IPP!</h3>
<title>Page Title</title>
<meta charset=\"UTF-8\">
<div class=\"row\">
  <div class=\"column\">
    <p>Úspešnosť testov je ___%</p>
  </div>
</div>
 <table style=\"width:100%\" border=\"1\">
  <tr>
    <th>Testname</th>
    <th>RC comp.</th>
    <th>Output comp.</th>
  </tr>
  <tr>
    <td>Test1</td>
    <td>OK</td>
    <td>OK</td>
  </tr>
  <tr>
    <td>Test2</td>
    <td>OK</td>
    <td>NOK</td>
  </tr>
  <tr>
    <td>Test3</td>
    <td>NOK</td>
    <td>-</td>
  </tr>
</table>
");

exit(0);
?>