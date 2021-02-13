# IPP
Princípy programovacích jazykov a OOP  
Projekt : Navrhni, implementuj a dokumentuj sadu skriptov pre interpretáciu neštruktúrovaného imperatívneho jazyka IPPcode20 (zjednodušený python). Rozdelené na 3 časti.  
1: skript parse.php  
- Skript typu filter (parse.php v jazyku PHP 7.4) načíta zo štandardného vstupu zdrojový kód v IPPcode20, skontroluje lexikálnu a syntaktickú správnosť kódu a vypíše na štandardný
výstup XML reprezentáciu programu. Získaných 7,7/7b  

2: skript interpret.py a test.php  
- Interpret (interpret.py v jazyku Python 3.8) načíta XML reprezentáciu programu a tento program s využitím vstupu podľa parametrov príkazového
riadku interpretuje a generuje výstup. Skript (test.php v jazyku PHP 7.4) bude slúžiť pre automatické testovanie postupnej aplikácie
parse.php a interpret.py. Implementácia testu bola veľmi chabá, dokopy získaných 9,6/13b
