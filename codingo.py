import sys, json, os, re, random, math, difflib, unicodedata, wave, struct, threading
from datetime import date
from PySide6.QtCore import Qt, Signal, QTimer, QPointF, QRectF, QPropertyAnimation, QEasingCurve, QAbstractAnimation, QPoint, QObject, QEvent, QUrl
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QRadialGradient, QPainterPath, QPolygonF
from PySide6.QtWidgets import *
try:
    from PySide6.QtMultimedia import QSoundEffect
except Exception:
    QSoundEffect = None

SAVE = os.path.join(os.path.expanduser("~"), ".codingo.json")
MONO = "'JetBrains Mono','Cascadia Code',Consolas,Menlo,monospace"

LANGS = {
    "Python": ("🐍", "#3b82f6", [
        ("Basics", "🌱", [
            ("What does this print?", "print(2 + 3 * 2)", ["10", "8", "12", "7"], 1),
            ("Pick a valid assignment", "", ["int x = 5", "x = 5", "var x = 5", "x := 5"], 1),
            ("What is the type?", "type(3.14)", ["int", "str", "float", "bool"], 2),
            ("Keyword that defines a function?", "", ["func", "def", "fn", "lambda"], 1)]),
        ("Loops", "🔁", [
            ("What does this print?", "for i in range(3):\n    print(i)", ["1 2 3", "0 1 2", "0 1 2 3", "1 2"], 1),
            ("Complete the loop", "while x ___ 5:\n    x += 1", ["<", "=>", "=", "in"], 0),
            ("Result?", "len([1, 2, 3])", ["2", "3", "4", "error"], 1),
            ("Which creates [0, 1, 2]?", "", ["list(range(3))", "range(3)", "[0..2]", "list(3)"], 0)]),
        ("Collections", "📦", [
            ("What does this print?", "d = {'a': 1}\nprint(d['a'])", ["a", "1", "error", "None"], 1),
            ("Add an item", "xs = []\nxs.___(5)", ["add", "push", "append", "put"], 2),
            ("Result?", "'abc'[1]", ["a", "b", "c", "error"], 1),
            ("Result?", "[1, 2, 3, 4][1:3]", ["[1, 2]", "[2, 3]", "[2, 3, 4]", "[1, 2, 3]"], 1)])]),
    "C": ("⚙️", "#a855f7", [
        ("Basics", "🌱", [
            ("Program entry point?", "", ["start()", "main()", "run()", "init()"], 1),
            ("Print to console", "", ['print("hi");', 'console.log("hi");', 'printf("hi");', 'echo "hi";'], 2),
            ("Declare an integer", "", ["int x = 5;", "x = 5", "let x = 5;", "integer x = 5;"], 0),
            ("Header for printf", "#include <___>", ["stdio.h", "print.h", "io.h", "math.h"], 0)]),
        ("Pointers", "🎯", [
            ("What does the address-of operator give?", "", ["value", "address", "size", "type"], 1),
            ("Declare an int pointer", "", ["int p*;", "int *p;", "ptr int p;", "int @p;"], 1),
            ("What does this print?", 'int x = 5;\nint *p = &x;\nprintf("%d", *p);', ["address", "5", "0", "error"], 1),
            ("Release malloc memory", "", ["delete p;", "free(p);", "release(p);", "drop(p);"], 1)]),
        ("Arrays", "🧱", [
            ("Array of 3 ints", "", ["int a[3];", "int[3] a;", "array a(3);", "int a = [3];"], 0),
            ("Index of first element", "", ["1", "0", "-1", "depends"], 1),
            ("String terminator", "", ["\\n", "\\0", "EOF", "NULL"], 1),
            ("sizeof(int) is typically", "", ["1", "2", "4", "16"], 2)])]),
    "JavaScript": ("⚡", "#f59e0b", [
        ("Basics", "🌱", [
            ("Block-scoped constant keyword", "", ["var", "const", "static", "final"], 1),
            ("What does this print?", "console.log(typeof 'hi')", ["string", "String", "text", "char"], 0),
            ("Strict equality operator", "", ["=", "==", "===", "=>"], 2),
            ("What does this print?", "console.log('5' + 3)", ["8", "53", "error", "NaN"], 1)]),
        ("Functions", "🧩", [
            ("Arrow function", "", ["x -> x * 2", "x => x * 2", "fn x: x * 2", "(x) -> x"], 1),
            ("What does this print?", "const f = (a, b) => a + b;\nconsole.log(f(2, 3));", ["23", "5", "undefined", "NaN"], 1),
            ("Transform every item into a new array", "", ["forEach", "map", "push", "splice"], 1),
            ("Result?", "[1, 2, 3].filter(n => n > 1)", ["[1]", "[2, 3]", "[1, 2, 3]", "[3]"], 1)]),
        ("Async & Co.", "🚀", [
            ("Keyword to wait for a Promise", "", ["await", "pause", "wait", "hold"], 0),
            ("Parse a JSON string", "", ["JSON.parse", "JSON.decode", "parse.json", "JSON.load"], 0),
            ("Result?", "[1, 2, 3].length", ["2", "3", "4", "undefined"], 1),
            ("Which value is falsy?", "", ["'0'", "[]", "0", "{}"], 2)])]),
}

NEW = {
    "Python": [
        ("Functions", "⚙️", [
            ("What does this print?", "def f(a, b=2):\n    return a * b\nprint(f(3))", ["6", "3", "5", "error"], 0),
            ("Type the keyword that sends a value back", "", None, ["return"]),
            ("Type the missing keyword", "___ add(a, b):\n    return a + b", None, ["def"]),
            ("Which creates an anonymous function?", "", ["lambda x: x", "def x:", "fn x", "x => x"], 0),
            ("Type the function that counts items", "___([1, 2, 3])  # 3", None, ["len"])]),
        ("Strings & Logic", "🧠", [
            ("Result?", "'hi' * 3", ["hihihi", "hi3", "error", "hi hi hi"], 0),
            ("Type the method that makes text uppercase", "'abc'.___()", None, ["upper"]),
            ("Result?", "not (True and False)", ["True", "False", "None", "error"], 0),
            ("Type the operator for integer division", "7 ___ 2  # 3", None, ["//"]),
            ("Which keyword checks membership?", "", ["in", "has", "contains", "inside"], 0)])],
    "C": [
        ("Functions", "🧪", [
            ("Type the return type of a function that returns nothing", "___ hello(void)", None, ["void"]),
            ("What does this print?", 'int sq(int n){ return n*n; }\nprintf("%d", sq(4));', ["8", "16", "4", "error"], 1),
            ("Type the missing keyword", "___ (int i = 0; i < 3; i++)", None, ["for"]),
            ("Which format specifier prints an int?", "", ["%d", "%s", "%f", "%c"], 0),
            ("Type the character that ends a statement", "", None, [";"])]),
        ("Structs & Memory", "🏗️", [
            ("Type the keyword that defines a structure", "___ Point { int x; int y; };", None, ["struct"]),
            ("Access a member through pointer p", "", ["p->x", "p.x", "p::x", "*p.x"], 0),
            ("Type the function that allocates memory", "int *p = ___(sizeof(int));", None, ["malloc"]),
            ("Result?", "sizeof(char)", ["1", "2", "4", "8"], 0),
            ("NULL means", "", ["pointer to nothing", "zero string", "empty array", "false"], 0)])],
    "JavaScript": [
        ("Arrays & Objects", "🗂️", [
            ("Type the method that adds to the end of an array", "arr.___(4)", None, ["push"]),
            ("What does this print?", "const o = {a: 1, b: 2};\nconsole.log(o.b);", ["1", "2", "undefined", "b"], 1),
            ("Type the property that gives array size", "[1, 2, 3].___", None, ["length"]),
            ("Result?", "[3, 1, 2].sort()[0]", ["1", "3", "2", "undefined"], 0),
            ("Which is spread syntax?", "", ["...arr", "..arr", "*arr", "&arr"], 0)]),
        ("Control & Strings", "🎛️", [
            ("Type the keyword that declares a changeable variable", "___ x = 1;", None, ["let"]),
            ("Result?", "`1+1=${1 + 1}`", ["1+1=2", "1+1=${1+1}", "error", "2"], 0),
            ("Type the keyword that exits a loop early", "", None, ["break"]),
            ("Result?", "Boolean('')", ["true", "false", "null", "undefined"], 1),
            ("Which prints to the console?", "", ["console.log", "print", "echo", "System.out"], 0)])],
}
TYPED = {
    "Python": [
        ("Type the function that prints", "___('hi')", None, ["print"]),
        ("Type the keyword to loop over items", "___ x in [1, 2]:", None, ["for"]),
        ("Type the method that returns dict keys", "d.___()", None, ["keys"])],
    "C": [
        ("Type the function that prints formatted text", '___("hi");', None, ["printf"]),
        ("Type the symbol that dereferences p", "___p", None, ["*"]),
        ("Declare a 5-int array named a", "int ___;", None, ["a[5]"])],
    "JavaScript": [
        ("Type the keyword for a constant", "___ pi = 3.14;", None, ["const"]),
        ("Type the keyword that returns a value", "", None, ["return"]),
        ("Type the keyword that marks an async function", "___ function f() {}", None, ["async"])],
}
for _n in LANGS:
    for _i, _q in enumerate(TYPED[_n]):
        LANGS[_n][2][_i][2].append(_q)
    LANGS[_n][2].extend(NEW[_n])

TRUNK = [("l", 13), ("l", 14), ("l", 15), ("l", 0), ("l", 5), ("l", 9), ("l", 6), ("p", 0), ("l", 7), ("l", 1), ("l", 10), ("p", 1),
         ("l", 2), ("l", 12), ("l", 3), ("l", 11), ("l", 4), ("l", 8), ("p", 2)]
TOTAL = len(TRUNK) + 4
BR = {
    "Python": [("Data", "📊", [("l", 16), ("l", 17)]), ("Automation", "🤖", [("l", 18), ("l", 19)])],
    "C": [("Systems", "🖥️", [("l", 16), ("l", 17)]), ("Embedded", "🔌", [("l", 18), ("l", 19)])],
    "JavaScript": [("Web", "🌐", [("l", 16), ("l", 17)]), ("Backend", "🗄️", [("l", 18), ("l", 19)])],
}


def nodes(lang, st):
    f, f2 = st["field"].get(lang), st["field2"].get(lang)
    return (TRUNKS[lang] + [("f", 0)] + (BR[lang][f][2] if f is not None else []) + [("b", 0)] + EXTN.get(lang, [])
            + [("f", 1)] + (BR2[lang][f2][2] if f2 is not None else []) + POST.get(lang, []))


PROJ = [
    ("Hello Calculator", "🛠️", "<b>Print Hello, Codingo!</b> on the first line. On the second line <b>print the result of (7 + 3) * 2</b>. Let the program calculate it and use brackets."),
    ("FizzBuzz", "🛠️", "<b>Print the numbers 1 to 15, one per line.</b> Print <b>Fizz</b> for multiples of 3, <b>Buzz</b> for multiples of 5 and <b>FizzBuzz</b> for both. Use a loop, if/else and the remainder operator.<br>Expected start: 1, 2, Fizz, 4, Buzz, Fizz ..."),
    ("Fibonacci", "🏆", "<b>Print the first 10 Fibonacci numbers, one per line.</b> Each number is the sum of the two before it, starting with 0 and 1. Use a loop and two variables.<br>Expected start: 0, 1, 1, 2, 3, 5 ..."),
]
STARTER = {
    "Python": ["print()\n", "for i in range(1, 16):\n    pass\n", "a, b = 0, 1\nfor _ in range(10):\n    pass\n"],
    "C": ["#include <stdio.h>\n\nint main(void) {\n    return 0;\n}\n",
          "#include <stdio.h>\n\nint main(void) {\n    for (int i = 1; i <= 15; i++) {\n    }\n    return 0;\n}\n",
          "#include <stdio.h>\n\nint main(void) {\n    int a = 0, b = 1;\n    for (int i = 0; i < 10; i++) {\n    }\n    return 0;\n}\n"],
    "JavaScript": ["console.log();\n", "for (let i = 1; i <= 15; i++) {\n}\n", "let a = 0, b = 1;\nfor (let i = 0; i < 10; i++) {\n}\n"],
}
PRINT = {"Python": r"\bprint\s*\(", "C": r"\bprintf\s*\(", "JavaScript": r"console\s*\.\s*log\s*\("}
CHECKS = [
    [("prints something", "PRINT"), ("contains the text Hello, Codingo!", r"Hello, Codingo!"),
     ("calculates (7 + 3) * 2 with brackets", r"\(\s*7\s*\+\s*3\s*\)\s*\*\s*2|2\s*\*\s*\(\s*7\s*\+\s*3\s*\)")],
    [("prints something", "PRINT"), ("uses a for or while loop", r"\b(for|foreach|while|each|times|upto|loop|repeat)\b"), ("uses if", r"\b(if|cond|case|when|match|unless)\b"),
     ("tests multiples of 3 with %", r"%\s*3\b|\b(rem|mod)\(\s*\w+\s*,\s*3\s*\)"), ("tests multiples of 5 with %", r"%\s*5\b|\b(rem|mod)\(\s*\w+\s*,\s*5\s*\)"),
     ("contains Fizz and Buzz", r"Fizz[\s\S]*Buzz|Buzz[\s\S]*Fizz"), ("handles FizzBuzz", r"FizzBuzz|%\s*15\b"),
     ("loops up to 15", r"\b(15|16)\b")],
    [("prints something", "PRINT"), ("uses a for or while loop", r"\b(for|foreach|while|each|times|upto|loop|repeat)\b"), ("starts with 0 and 1", r"\b0\b[\s\S]*\b1\b"),
     ("adds two values (a + b)", r"\b\w+\s*\+\s*\w+\b"), ("runs 10 times", r"\b10\b")],
]
TEACH = {
    "Python": [
        ("Python runs your program from top to bottom, one line at a time. A <b>variable</b> is a name for a value, created by assigning with <b>=</b>. Common types are <b>int</b> (whole numbers), <b>float</b> (decimals), <b>str</b> (text) and <b>bool</b> (True/False). Maths follows the normal order, so multiplication happens before addition.",
         "x = 5\nprice = 3.14\nname = 'Ada'\nprint(x + 1)"),
        ("A <b>for</b> loop repeats code once per item. <b>range(3)</b> produces 0, 1, 2 - counting starts at zero and stops BEFORE the end number. A <b>while</b> loop runs as long as its condition is true, so something inside must change or it never ends. Python uses indentation (4 spaces) to mark what belongs inside the loop.",
         "for i in range(3):\n    print(i)\n\nx = 0\nwhile x < 3:\n    x += 1"),
        ("A <b>list</b> keeps items in order and you reach them by index starting at 0. Add to the end with <b>append</b> and slice with <b>[start:stop]</b> (stop is excluded). A <b>dict</b> stores key/value pairs and you look values up by key. Strings behave like lists of characters, so indexing works on them too.",
         "xs = [1, 2, 3]\nxs.append(4)\nprint(xs[1:3])\nd = {'a': 1}\nprint(d['a'])"),
        ("A <b>function</b> packages code so you can reuse it. Define it with <b>def</b>, list parameters in brackets, and send a result back with <b>return</b>. Parameters can have default values. <b>lambda</b> makes tiny one-line functions without a name.",
         "def f(a, b=2):\n    return a * b\n\nprint(f(3))\nsq = lambda x: x * x"),
        ("Strings can be repeated with <b>*</b> and transformed with methods like <b>upper()</b>. Booleans combine with <b>and</b>, <b>or</b> and <b>not</b>. <b>//</b> is integer division (drops the remainder) and <b>%</b> gives the remainder. <b>in</b> checks whether something is inside a string or list.",
         "print('hi' * 3)\nprint('abc'.upper())\nprint(7 // 2, 7 % 2)\nprint('a' in 'cat')")],
    "C": [
        ("C is compiled: you write source code and a compiler turns it into a program. Execution starts in <b>main</b>. Every variable needs a <b>type</b> (int, float, char) and every statement ends with a semicolon. <b>printf</b> prints text and comes from the header <b>stdio.h</b>, which you include at the top.",
         '#include <stdio.h>\n\nint main(void) {\n    int x = 5;\n    printf("%d", x);\n    return 0;\n}'),
        ("A <b>pointer</b> stores the memory address of another variable. <b>&amp;x</b> gives the address of x, and <b>*p</b> follows a pointer to read the value stored there. <b>malloc</b> reserves memory on the heap and you must give it back with <b>free</b>, otherwise you leak memory.",
         'int x = 5;\nint *p = &x;\nprintf("%d", *p);\n\nint *h = malloc(sizeof(int));\nfree(h);'),
        ("An <b>array</b> is a fixed-size row of values of the same type, stored side by side. Indexes start at 0 and C does NOT check bounds, so reading past the end is a bug. A string is just a char array ending with the special character <b>\\0</b>. <b>sizeof</b> tells you how many bytes a type needs - an int is usually 4.",
         'int a[3] = {10, 20, 30};\nprintf("%d", a[0]);\nchar s[] = "hi";\nprintf("%zu", sizeof(int));'),
        ("A <b>function</b> has a return type, a name, parameters and a body. Use <b>void</b> when nothing is returned. A <b>for</b> loop has three parts: start, condition, step. <b>printf</b> needs format specifiers: <b>%d</b> for int, <b>%s</b> for strings, <b>%f</b> for decimals and <b>%c</b> for a char.",
         'int sq(int n) {\n    return n * n;\n}\n\nfor (int i = 0; i < 3; i++) {\n    printf("%d\\n", sq(i));\n}'),
        ("A <b>struct</b> groups related values into one type. Use <b>.</b> to reach a member, or <b>-&gt;</b> when you have a pointer to the struct. <b>NULL</b> is the special pointer value meaning 'points to nothing', so check for it before using a pointer.",
         'struct Point { int x; int y; };\n\nstruct Point p = {1, 2};\nstruct Point *q = &p;\nprintf("%d", q->x);')],
    "JavaScript": [
        ("JavaScript runs in browsers and in Node.js. Declare variables with <b>let</b> (can change) or <b>const</b> (cannot be reassigned) and avoid the old <b>var</b>. Use <b>===</b> to compare because <b>==</b> converts types first. Adding a string and a number glues them together as text.",
         "const name = 'Ada';\nlet n = 1;\nconsole.log(typeof name);\nconsole.log('5' + 3);"),
        ("An <b>arrow function</b> is written as parameters, then =&gt;, then the result. Arrays have helper methods that take functions: <b>map</b> transforms every item, <b>filter</b> keeps the items that pass a test, <b>forEach</b> just runs code for each one. map and filter return a NEW array.",
         "const f = (a, b) => a + b;\nconsole.log(f(2, 3));\nconsole.log([1, 2, 3].map(n => n * 2));"),
        ("Some work takes time (network, files). A <b>Promise</b> is a future result and <b>await</b> pauses an <b>async</b> function until it is ready. <b>JSON.parse</b> turns a JSON string into an object. Falsy values are false, 0, empty string, null, undefined and NaN - everything else is truthy, even '0' and [].",
         "async function load() {\n    const r = await Promise.resolve(42);\n    console.log(r);\n}\nconsole.log(JSON.parse('{\"a\": 1}').a);"),
        ("Arrays hold ordered values and have <b>push</b>, <b>length</b>, <b>sort</b> and more. Objects store named properties, read with a dot. The <b>spread</b> operator <b>...</b> copies items out of an array or object. Careful: sort() compares as text unless you pass a function.",
         "const arr = [3, 1, 2];\narr.push(4);\nconst o = {a: 1, b: 2};\nconsole.log(o.b, arr.length);\nconst copy = [...arr];"),
        ("<b>break</b> leaves a loop early and <b>continue</b> skips to the next round. Template literals use backticks and <b>${}</b> to put values inside text. Convert values with <b>Boolean()</b>, <b>Number()</b> and <b>String()</b>. <b>console.log</b> prints to the console.",
         "for (let i = 0; i < 5; i++) {\n    if (i === 3) break;\n    console.log(`i is ${i}`);\n}")],
}


NEW2 = {
    "Python": [
        ("Data Types", "🔢", [
            ("What type is True?", "type(True)", ["int", "bool", "str", "float"], 1),
            ("What does this print?", "print(int('7') + 1)", ["71", "8", "error", "'8'"], 1),
            ("Type the function that converts text to a whole number", "___('42')", None, ["int"]),
            ("What does this print?", "print('7' + '1')", ["8", "71", "error", "7 1"], 1),
            ("Type the value that means 'no value'", "x = ___", None, ["None"])]),
        ("Operators", "➗", [
            ("Result?", "2 ** 3", ["6", "8", "9", "5"], 1),
            ("Result?", "7 / 2", ["3", "3.5", "4", "3.0"], 1),
            ("Type the operator that gives the remainder", "7 ___ 2  # 1", None, ["%"]),
            ("What does this print?", "x = 4\nx += 3\nprint(x)", ["4", "7", "12", "error"], 1),
            ("Which means 'not equal'?", "", ["!=", "<>", "=!", "=/="], 0)]),
        ("Conditions", "🔀", [
            ("What does this print?", "x = 7\nif x % 2 == 0:\n    print('even')\nelse:\n    print('odd')", ["even", "odd", "7", "nothing"], 1),
            ("Type the keyword for 'otherwise if'", "", None, ["elif"]),
            ("Which line is a correct if statement?", "", ["if x > 1:", "if x > 1;", "if (x > 1) {", "if x > 1 then"], 0),
            ("What does this print?", "x = 3\nif x > 1 or x > 5:\n    print('A')\nelif x > 2:\n    print('B')", ["A", "B", "AB", "nothing"], 0),
            ("Type the keyword that handles all remaining cases", "", None, ["else"])])],
    "C": [
        ("Data Types", "🔢", [
            ("What does this print?", 'printf("%d", 7 / 2);', ["3", "3.5", "4", "error"], 0),
            ("Type the type for decimals with more precision than float", "___ d = 3.14;", None, ["double"]),
            ("Which type holds one character?", "", ["char", "string", "str", "text"], 0),
            ("Result?", "(double)7 / 2", ["3", "3.5", "4", "3.0"], 1),
            ("Type the specifier that prints a decimal number", 'printf("___", 2.5);', None, ["%f"])]),
        ("Operators", "➗", [
            ("Result?", "7 % 3", ["1", "2", "0", "3"], 0),
            ("What does this print?", 'int x = 5;\nx++;\nprintf("%d", x);', ["5", "6", "7", "error"], 1),
            ("Type the operator meaning 'and'", "if (a ___ b)", None, ["&&"]),
            ("Which operator compares two values?", "", ["==", "=", "=>", ":="], 0),
            ("What is the value of 5 > 3 in C?", "", ["1", "0", "true", "error"], 0)]),
        ("Conditions", "🔀", [
            ("What does this print?", 'int x = 0;\nif (x) printf("yes");\nelse printf("no");', ["yes", "no", "0", "error"], 1),
            ("Type the keyword that handles all remaining cases", "", None, ["else"]),
            ("Which is valid C?", "", ["if (x > 1) {", "if x > 1:", "if x > 1 then", "if [x > 1] {"], 0),
            ("Type the keyword that ends a switch case", "case 1: ...; ___;", None, ["break"]),
            ("Type the keyword that chooses between many values", "___ (n) { case 1: break; }", None, ["switch"])])],
    "JavaScript": [
        ("Data Types", "🔢", [
            ("What does this print?", "console.log(typeof 7.5)", ["number", "float", "double", "decimal"], 0),
            ("Type the operator that gives the type of a value", "___ x", None, ["typeof"]),
            ("Result?", "Number('7') + 1", ["71", "8", "NaN", "'8'"], 1),
            ("Result?", "'3' * 2", ["6", "32", "NaN", "error"], 0),
            ("Which value means 'declared but not assigned'?", "", ["undefined", "null", "NaN", "empty"], 0)]),
        ("Operators", "➗", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 1),
            ("Result?", "2 ** 3", ["6", "8", "9", "23"], 1),
            ("Type the strict not-equal operator", "a ___ b", None, ["!=="]),
            ("Result?", "1 === '1'", ["true", "false", "NaN", "error"], 1),
            ("Type the operator meaning 'and'", "if (a ___ b)", None, ["&&"])]),
        ("Conditions", "🔀", [
            ("What does this print?", "console.log(5 > 3 ? 'yes' : 'no')", ["yes", "no", "true", "error"], 0),
            ("Type the keyword that handles all remaining cases", "", None, ["else"]),
            ("Which is valid?", "", ["if (x > 1) {", "if x > 1:", "if x > 1 then", "if [x > 1] {"], 0),
            ("What does this print?", "if ('0') console.log('A'); else console.log('B');", ["A", "B", "nothing", "error"], 0),
            ("Type the operator for a one-line if/else", "n > 5 ___ 'big' : 'small'", None, ["?"])])],
}
TEACH2 = {
    "Python": [
        ("Every value has a <b>type</b>. <b>int</b> is a whole number, <b>float</b> has a decimal point, <b>str</b> is text in quotes, <b>bool</b> is True or False, and <b>None</b> means 'no value'. Use <b>type(x)</b> to inspect a value and <b>int()</b>, <b>float()</b>, <b>str()</b> to convert. Converting text to a number is needed before doing maths on it, because '7' + '1' glues text together.",
         "print(type(7))\nprint(type(7.0))\nprint(type('7'))\nprint(int('7') + 1)\nprint(str(7) + '1')"),
        ("Arithmetic: <b>+ - * /</b>, plus <b>**</b> for powers, <b>//</b> for integer division and <b>%</b> for the remainder. <b>/</b> always gives a float. Comparisons (<b>==</b>, <b>!=</b>, <b>&gt;</b>, <b>&gt;=</b>) give True or False. <b>+=</b> is shorthand: x += 2 means x = x + 2.",
         "print(2 ** 3)\nprint(7 / 2)\nprint(7 % 2)\nx = 1\nx += 2\nprint(x == 3)"),
        ("<b>if</b> runs a block only when its condition is true. Add <b>elif</b> for more cases and <b>else</b> for everything left. Every such line ends with a colon and the block under it is indented. Combine tests with <b>and</b>, <b>or</b>, <b>not</b>. Only the FIRST matching branch runs.",
         "x = 7\nif x % 2 == 0:\n    print('even')\nelif x > 5:\n    print('big odd')\nelse:\n    print('small odd')")],
    "C": [
        ("C has several number types: <b>char</b> (1 byte, a character), <b>int</b> (whole numbers), <b>long</b> (bigger whole numbers), <b>float</b> and <b>double</b> (decimals; double is more precise). There is no built-in string type - text is a <b>char</b> array. An int divided by an int gives an int, so 7 / 2 is 3. Use a <b>cast</b> like (double)7 / 2 to get 3.5.",
         "int a = 7;\ndouble d = 7.5;\nchar c = 'A';\nprintf(\"%d %f %c\", a, d, c);\nprintf(\"%d\", 7 / 2);"),
        ("C has <b>+ - * / %</b> (% is the remainder, ints only), plus <b>++</b> and <b>--</b> to add or subtract one. Comparisons give 1 for true and 0 for false - basic C has no boolean. Logic uses <b>&amp;&amp;</b> (and), <b>||</b> (or) and <b>!</b> (not). Beware: <b>=</b> assigns, <b>==</b> compares.",
         "int x = 5;\nx++;\nprintf(\"%d\", x % 4);\nprintf(\"%d\", x > 3 && x < 10);"),
        ("<b>if (condition) { }</b> runs the block when the condition is non-zero. Add <b>else if</b> and <b>else</b>. The condition must be in brackets and blocks use curly braces. <b>switch</b> chooses between many exact values; put <b>break</b> at the end of each case or execution falls through.",
         "int x = 7;\nif (x % 2 == 0) {\n    printf(\"even\");\n} else if (x > 5) {\n    printf(\"big odd\");\n} else {\n    printf(\"small odd\");\n}")],
    "JavaScript": [
        ("Primitive types: <b>number</b> (ints and decimals alike), <b>string</b>, <b>boolean</b>, <b>undefined</b> (declared but no value), <b>null</b> (intentionally empty), <b>bigint</b> and <b>symbol</b>. Arrays and objects are <b>object</b> types. Use <b>typeof</b> to check. Convert with <b>Number()</b>, <b>String()</b> and <b>parseInt()</b>.",
         "console.log(typeof 7);\nconsole.log(typeof '7');\nconsole.log(typeof null);\nconsole.log(Number('7') + 1);\nconsole.log(0.1 + 0.2);"),
        ("Arithmetic: <b>+ - * / % **</b> (<b>/</b> never truncates: 7 / 2 is 3.5). <b>++</b> and <b>--</b> add or subtract one. Compare with <b>===</b> and <b>!==</b> (strict, no type conversion). Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>, and <b>??</b> which picks the right side only when the left is null or undefined.",
         "console.log(7 / 2);\nconsole.log(7 % 2);\nconsole.log(2 ** 3);\nconsole.log(1 === '1');\nconsole.log(null ?? 'default');"),
        ("<b>if (condition) { }</b> runs when the condition is truthy. Chain with <b>else if</b> and <b>else</b>. The <b>ternary</b> <b>cond ? a : b</b> is a one-line if/else that returns a value. <b>switch</b> compares with === and needs <b>break</b>.",
         "const n = 7;\nif (n % 2 === 0) {\n    console.log('even');\n} else {\n    console.log('odd');\n}\nconsole.log(n > 5 ? 'big' : 'small');")],
}
for _n in LANGS:
    LANGS[_n][2].extend(NEW2[_n])
    TEACH[_n].extend(TEACH2[_n])


FACTS = [
    "The first computer 'bug' was a real moth found in a Harvard computer in 1947.",
    "Python is named after Monty Python, not the snake.",
    "C was created in the early 1970s by Dennis Ritchie.",
    "JavaScript was written in just 10 days in 1995.",
    "The first programmer was Ada Lovelace in the 1840s.",
    "Your phone is far more powerful than the computers that flew Apollo 11.",
]
TIPS = [
    "💡 Byte: read error messages from the bottom up.",
    "💡 Byte: type the code yourself, don't copy it.",
    "💡 Byte: small steps beat big leaps.",
    "💡 Byte: every bug is a teacher in disguise.",
    "💡 Byte: stuck? Print the value and look at it.",
    "💡 Byte: sleep on a bug, it often fixes itself.",
]
PRAISE = ["Nice!", "Boom!", "Smooth!", "Big brain!", "Hacker mode!", "Clean!", "Flawless!"]
OOPS = ["Almost!", "Bugs happen!", "Debug time!", "Not quite!", "Next time!"]
TITLES = ["Rookie", "Script Kiddie", "Coder", "Hacker", "Wizard", "Legend"]
BUG_TEXT = "Debugging is detective work. Read the error message from the BOTTOM up, find the line number, then check the usual suspects: typos, missing colons or semicolons, wrong types and off-by-one indexes. Printing values shows what the program REALLY does."
BUGS = {
    "Python": (("Bug Hunt", "🐛", [
        ("Why does this crash?", "x = 5\nprint(x + '1')", ["int + str", "x undefined", "missing colon", "bad indent"], 0),
        ("Find the bug", "if x == 5\n    print('five')", ["missing colon", "wrong operator", "bad quote", "nothing"], 0),
        ("What is wrong?", "for i in range(3):\nprint(i)", ["no indent", "range wrong", "missing colon", "i undefined"], 0),
        ("Find the bug", "name = 'Ada\nprint(name)", ["unclosed quote", "bad name", "missing colon", "nothing"], 0),
        ("Type the operator that fixes it", "if x ___ 5:   # compare, not assign", None, ["=="])]),
        "print(type(x))\nprint(x)"),
    "C": (("Bug Hunt", "🐛", [
        ("Find the bug", 'printf("hi")', ["missing semicolon", "wrong function", "missing include", "nothing"], 0),
        ("Why does this misbehave?", 'int a[3] = {1, 2, 3};\nprintf("%d", a[3]);', ["index out of bounds", "bad type", "missing &", "nothing"], 0),
        ("What is wrong?", "if (x = 5) {\n}", ["= assigns, use ==", "missing else", "bad brackets", "nothing"], 0),
        ("Memory bug?", "int *p = malloc(4);\np = NULL;", ["leak: never freed", "double free", "wrong type", "nothing"], 0),
        ("Type the missing header", '#include <___>\nint main(void) { printf("x"); }', None, ["stdio.h"])]),
        'printf("%d\\n", x);'),
    "JavaScript": (("Bug Hunt", "🐛", [
        ("Why does this throw?", "const x = 1;\nx = 2;", ["const cannot be reassigned", "x undefined", "missing let", "nothing"], 0),
        ("What is wrong?", "if (x = 5) {\n}", ["= assigns, use ===", "missing else", "bad brackets", "nothing"], 0),
        ("Why NaN?", "console.log('a' * 2)", ["text times number", "missing quote", "bad log", "nothing"], 0),
        ("Why undefined?", "function f() {\n    5;\n}\nconsole.log(f());", ["no return", "bad name", "missing call", "nothing"], 0),
        ("Type the keyword that declares a function", "___ f() { return 1; }", None, ["function"])]),
        "console.log(x);"),
}
for _n in LANGS:
    LANGS[_n][2].append(BUGS[_n][0])
    TEACH[_n].append((BUG_TEXT, BUGS[_n][1]))


MORE = {
    "Python": [
        ("Output & Input", "🖨️", [
            ("What does this print?", "print('a', 'b', sep='-')", ["a b", "a-b", "ab", "a,b"], 1),
            ("Type the letter that starts an f-string", "print(___'Hi {name}')", None, ["f"]),
            ("What does this print?", "x = 3\nprint(f'x is {x + 1}')", ["x is 3", "x is 4", "x is {x + 1}", "error"], 1),
            ("Type the function that reads user text", "name = ___('Name? ')", None, ["input"])],
         "<b>print()</b> shows values. Give it several values and it puts a space between them; <b>sep</b> and <b>end</b> change that. <b>f-strings</b> insert values into text: put <b>f</b> before the quote and variables inside <b>{}</b>. <b>input()</b> reads what the user types, always as text.",
         "name = 'Ada'\nage = 30\nprint('Hi', name)\nprint(f'{name} is {age}')\nprint('a', 'b', sep='-')\nprint('end', end='!')"),
        ("Loop Tricks", "🌀", [
            ("What does this print?", "for n in [1, 2, 3, 4]:\n    if n == 3:\n        break\n    print(n)", ["1 2", "1 2 3", "1 2 4", "3"], 0),
            ("Type the keyword that skips to the next round", "", None, ["continue"]),
            ("How many times does print run?", "for i in range(2):\n    for j in range(3):\n        print(i, j)", ["5", "6", "2", "3"], 1),
            ("What does this print?", "print(list(range(0, 10, 4)))", ["[0, 4, 8]", "[0, 4, 8, 10]", "[4, 8]", "[0, 10]"], 0)],
         "<b>break</b> leaves the loop immediately, <b>continue</b> skips to the next round. Loops can be <b>nested</b>: the inner loop runs completely for every round of the outer one. <b>range(start, stop, step)</b> can count in jumps, even backwards.",
         "for i in range(10, 0, -3):\n    print(i)\n\nfor n in [1, 2, 3, 4]:\n    if n == 3:\n        break\n    print(n)"),
        ("Scope", "🔭", [
            ("Why does print(result) fail?", "def add(n):\n    result = n + 1\n    return result\nadd(1)\nprint(result)", ["result is local", "add not defined", "missing return", "n is global"], 0),
            ("Type the keyword needed to change a global inside a function", "def f():\n    ___ count\n    count += 1", None, ["global"]),
            ("What does this print?", "x = 1\ndef f():\n    x = 2\nf()\nprint(x)", ["1", "2", "error", "None"], 0),
            ("Where is a function parameter visible?", "", ["only inside the function", "everywhere", "only in loops", "only at the top"], 0)],
         "A <b>local</b> variable exists only inside the function that created it. A <b>global</b> variable lives outside and can be read anywhere, but to CHANGE it inside a function you need the <b>global</b> keyword. Parameters are local too. Prefer passing values in and returning results.",
         "total = 0\n\ndef add(n):\n    result = total + n\n    return result\n\nprint(add(5))\nprint(total)"),
        ("Strings Deep Dive", "🔤", [
            ("Result?", "'Hello'[-1]", ["H", "o", "l", "error"], 1),
            ("What does this print?", "print('a,b,c'.split(','))", ["['a', 'b', 'c']", "a b c", "['a,b,c']", "('a','b','c')"], 0),
            ("Type the method that removes surrounding spaces", "'  hi  '.___()", None, ["strip"]),
            ("What does this print?", "s = 'cat'\ns.upper()\nprint(s)", ["CAT", "cat", "error", "None"], 1)],
         "Strings are sequences: <b>len()</b> counts characters, indexing starts at 0 and negative indexes count from the end. Useful methods: <b>upper</b>, <b>lower</b>, <b>strip</b>, <b>split</b>, <b>join</b>, <b>replace</b>, <b>find</b>. Strings are <b>immutable</b>: methods return a NEW string instead of changing the old one.",
         "s = '  Hello World  '\nprint(s.strip())\nprint(s.strip().split())\nprint('-'.join(['a', 'b']))\nprint('Hello'[-1])")],
    "C": [
        ("Output & Input", "🖨️", [
            ("What does this print?", 'printf("%.2f", 3.14159);', ["3.14", "3.1", "3.14159", "3"], 0),
            ("Type the escape sequence for a new line", 'printf("Hi___");', None, ["\\n"]),
            ("Which placeholder prints a string?", "", ["%s", "%d", "%c", "%f"], 0),
            ("What goes before x to pass its address to scanf?", 'scanf("%d", ___x);', None, ["&"])],
         "<b>printf</b> prints formatted text: placeholders like <b>%d</b>, <b>%f</b>, <b>%c</b>, <b>%s</b> are replaced by the extra arguments in order. <b>\\n</b> starts a new line and <b>%.2f</b> prints two decimals. <b>scanf</b> reads input and needs the ADDRESS of the variable, so you write <b>&amp;x</b>.",
         "int age = 30;\nfloat pi = 3.14159;\nprintf(\"Age: %d\\n\", age);\nprintf(\"%.2f\\n\", pi);\nscanf(\"%d\", &age);"),
        ("Loop Tricks", "🌀", [
            ("What does this print?", 'for (int i = 0; i < 3; i++) {\n    if (i == 1) continue;\n    printf("%d", i);\n}', ["02", "012", "01", "12"], 0),
            ("Which loop always runs at least once?", "", ["do { } while", "for", "while", "foreach"], 0),
            ("How many times does the body run?", "for (int i = 1; i <= 4; i++) { }", ["3", "4", "5", "1"], 1),
            ("Type the keyword that leaves a loop", "", None, ["break"])],
         "<b>break</b> exits a loop, <b>continue</b> jumps to the next round. <b>do { } while</b> always runs at least once. Loops can be nested: the inner one runs completely for every round of the outer one. Watch for off-by-one errors: <b>i &lt; 3</b> runs 0, 1, 2.",
         "for (int i = 0; i < 3; i++) {\n    if (i == 1) continue;\n    printf(\"%d\", i);\n}\n\nint n = 0;\ndo {\n    n++;\n} while (n < 3);"),
        ("Scope", "🔭", [
            ("What does this print?", 'void inc(int n) { n++; }\nint x = 1;\ninc(x);\nprintf("%d", x);', ["1", "2", "0", "error"], 0),
            ("What must you pass to let a function change x?", "", ["&x", "x", "*x", "x++"], 0),
            ("Type the keyword that keeps a local variable between calls", "___ int count = 0;", None, ["static"]),
            ("Where does a variable declared inside { } exist?", "", ["only inside the braces", "whole file", "whole program", "nowhere"], 0)],
         "A variable declared inside <b>{ }</b> exists only there (local). Variables outside every function are <b>global</b>. A function receives COPIES of its arguments (pass by value), so changing a parameter does not change the caller's variable - unless you pass a <b>pointer</b>. <b>static</b> inside a function keeps its value between calls.",
         "void inc(int n) { n++; }\nvoid incp(int *n) { (*n)++; }\n\nint x = 1;\ninc(x);\nprintf(\"%d\", x);\nincp(&x);\nprintf(\"%d\", x);"),
        ("Strings Deep Dive", "🔤", [
            ("What does strlen return for the string cat?", "", ["3", "4", "2", "0"], 0),
            ("Type the function that compares two strings", "if (___(a, b) == 0)", None, ["strcmp"]),
            ("Why is a == b wrong for comparing strings?", "", ["it compares addresses", "it compares length", "it is a syntax error", "it is slower"], 0),
            ("Which header declares strlen?", "", ["string.h", "stdio.h", "stdlib.h", "math.h"], 0)],
         "A C string is a <b>char</b> array ending in <b>\\0</b>. Include <b>string.h</b> for helpers: <b>strlen</b> (length), <b>strcpy</b> (copy), <b>strcmp</b> (compare, returns 0 when equal) and <b>strcat</b> (append). Never compare strings with <b>==</b>, that compares addresses. Make sure the destination array is big enough!",
         "#include <string.h>\n\nchar s[10] = \"cat\";\nprintf(\"%zu\", strlen(s));\nprintf(\"%d\", strcmp(s, \"cat\"));")],
    "JavaScript": [
        ("Output & Input", "🖨️", [
            ("What does this print?", "console.log('a', 'b')", ["a b", "ab", "a,b", "['a','b']"], 0),
            ("What does this print?", "const n = 2;\nconsole.log(`n is ${n * 2}`)", ["n is 4", "n is 2", "n is ${n * 2}", "error"], 0),
            ("Type the method that prints an error message", "console.___('oops')", None, ["error"]),
            ("Which turns an object into text?", "", ["JSON.stringify", "JSON.parse", "toObject", "String.object"], 0)],
         "<b>console.log()</b> prints any number of values separated by spaces. <b>Template literals</b> (backticks) embed values with <b>${}</b>. <b>console.error</b> prints errors and <b>JSON.stringify</b> turns objects into readable text. In a browser, <b>prompt()</b> asks the user for text and <b>alert()</b> shows a popup.",
         "const name = 'Ada';\nconsole.log('Hi', name);\nconsole.log(`${name} is ${20 + 10}`);\nconsole.log(JSON.stringify({a: 1}));"),
        ("Loop Tricks", "🌀", [
            ("What does this print?", "for (const n of [1, 2, 3]) {\n    if (n === 2) continue;\n    console.log(n);\n}", ["1 3", "1 2 3", "2", "1"], 0),
            ("Type the keyword that loops over array values", "for (const n ___ [1, 2]) {}", None, ["of"]),
            ("What does for...in give for an object?", "", ["its keys", "its values", "its length", "nothing"], 0),
            ("Type the keyword that leaves a loop", "", None, ["break"])],
         "<b>for...of</b> loops over the VALUES of an array, <b>for...in</b> over the KEYS of an object. <b>break</b> and <b>continue</b> work like in other languages. <b>forEach</b>, <b>map</b> and <b>filter</b> are loops in disguise. Use <b>while</b> when you don't know in advance how many rounds you need.",
         "for (const n of [1, 2, 3]) {\n    if (n === 2) continue;\n    console.log(n);\n}\nfor (const k in {a: 1, b: 2}) {\n    console.log(k);\n}"),
        ("Scope", "🔭", [
            ("What does this print?", "function counter() {\n    let n = 0;\n    return () => ++n;\n}\nconst c = counter();\nc();\nconsole.log(c());", ["2", "1", "0", "undefined"], 0),
            ("Where does a let variable exist?", "", ["inside its { } block", "whole file", "whole program", "only in functions"], 0),
            ("Type the keyword to avoid because it is function-scoped", "___ x = 1;", None, ["var"]),
            ("What is a closure?", "", ["a function that remembers outer variables", "a closed file", "a loop type", "an error"], 0)],
         "<b>let</b> and <b>const</b> are block-scoped: they only exist inside the nearest { }. <b>var</b> is function-scoped, which causes surprises, so avoid it. Inner functions can read variables of outer functions - this is a <b>closure</b>. Variables declared outside everything are global.",
         "function counter() {\n    let n = 0;\n    return () => ++n;\n}\nconst c = counter();\nconsole.log(c());\nconsole.log(c());"),
        ("Strings Deep Dive", "🔤", [
            ("Result?", "'Hello'.at(-1)", ["H", "o", "l", "undefined"], 1),
            ("Type the method that removes surrounding spaces", "'  hi  '.___()", None, ["trim"]),
            ("What does this print?", "console.log('a,b,c'.split(','))", ["['a', 'b', 'c']", "a b c", "['a,b,c']", "3"], 0),
            ("What does this print?", "const s = 'cat';\ns.toUpperCase();\nconsole.log(s);", ["CAT", "cat", "error", "undefined"], 1)],
         "Strings have <b>length</b> and methods like <b>toUpperCase</b>, <b>trim</b>, <b>split</b>, <b>includes</b>, <b>slice</b>, <b>replace</b> and <b>indexOf</b>. Strings are immutable: methods return NEW strings. Arrays have <b>join</b> to glue pieces back together and <b>at(-1)</b> reads from the end.",
         "const s = '  Hello World  ';\nconsole.log(s.trim());\nconsole.log('a,b,c'.split(','));\nconsole.log(['a', 'b'].join('-'));\nconsole.log('Hello'.at(-1));")],
}
for _n in LANGS:
    for _t, _e, _qs, _tx, _cd in MORE[_n]:
        LANGS[_n][2].append((_t, _e, _qs))
        TEACH[_n].append((_tx, _cd))


SHARED = ("How Computers Think", "🧠", [
    ("What does a CPU do?", "", ["Runs instructions", "Stores photos", "Draws the screen", "Connects to Wi-Fi"], 0),
    ("Computers fundamentally work with...", "", ["Binary (0s and 1s)", "English", "Emoji", "Colors"], 0),
    ("What is an algorithm?", "", ["A step-by-step recipe to solve a problem", "A kind of computer", "A language", "A bug"], 0),
    ("Type the name for a mistake in code", "", None, ["bug"])],
    "A computer follows instructions one by one, extremely fast. Everything inside it - numbers, text, pictures - is stored as <b>binary</b>: just 0s and 1s. A <b>program</b> is a list of instructions and an <b>algorithm</b> is the step-by-step plan behind it. Programming languages let you write those instructions in a form humans can read.",
    "Algorithm for tea:\n1. Boil water\n2. Add tea bag\n3. Wait 3 minutes\n4. Pour and enjoy")
ADD = {
    "Python": [
        ("Hello, World!", "👋", [
            ("What does this print?", "print('Hello')", ["Hello", "'Hello'", "print", "Error"], 0),
            ("Type the function that shows text", "___('Hi')", None, ["print"]),
            ("Which line is valid Python?", "", ["print('Hi')", "Print('Hi')", "echo 'Hi'", "console.log('Hi')"], 0)],
         "Tradition says your first program prints <b>Hello, World!</b>. In Python that is one line: <b>print()</b> with text in quotes. Python runs the file top to bottom and is case-sensitive: print works, Print does not.",
         "print('Hello, World!')"),
        ("Comments & Style", "🎨", [
            ("Which starts a comment?", "", ["#", "//", "/*", "--"], 0),
            ("What does this print?", "# print('A')\nprint('B')", ["A", "B", "AB", "nothing"], 1),
            ("Type the symbol that starts a Python comment", "___ this is ignored", None, ["#"])],
         "<b>Comments</b> are notes for humans; the computer ignores them. In Python a comment starts with <b>#</b>. Good style means clear names (<b>total_price</b>, not <b>x</b>), 4-space indentation and short lines. Code is read far more often than it is written.",
         "# add two numbers\nprice = 5\ntax = 2\ntotal_price = price + tax"),
        ("Number Crunching", "📊", [
            ("Result?", "sum([1, 2, 3])", ["6", "5", "123", "error"], 0),
            ("What does this print?", "print([x * 2 for x in [1, 2, 3]])", ["[2, 4, 6]", "[1, 2, 3]", "[1, 4, 9]", "6"], 0),
            ("Type the function that returns the biggest item", "___([3, 9, 2])", None, ["max"])],
         "Python shines at data. <b>sum()</b>, <b>min()</b>, <b>max()</b> and <b>sorted()</b> work on lists. A <b>list comprehension</b> builds a new list in one line: <b>[x * 2 for x in nums]</b>, optionally filtered with <b>if</b>. Average = sum / len.",
         "nums = [4, 1, 3]\nprint(sum(nums) / len(nums))\nprint(sorted(nums))\nprint([x * 2 for x in nums])"),
        ("Counting with Dicts", "🗂️", [
            ("What does this print?", "d = {'a': 1}\nprint(d.get('b', 0))", ["0", "None", "error", "1"], 0),
            ("Result?", "len({'x': 1, 'y': 2})", ["2", "1", "3", "error"], 0),
            ("Type the method that loops over key/value pairs", "for k, v in d.___():", None, ["items"])],
         "A <b>dict</b> maps keys to values, which is perfect for counting. <b>d.get(key, 0)</b> reads with a default, <b>d.items()</b> loops over pairs and <b>len(d)</b> counts keys. To count words: <b>counts[w] = counts.get(w, 0) + 1</b>.",
         "counts = {}\nfor w in ['a', 'b', 'a']:\n    counts[w] = counts.get(w, 0) + 1\nprint(counts)"),
        ("Files & Text", "📄", [
            ("Which mode erases the file and writes?", "", ["'w'", "'r'", "'a'", "'x'"], 0),
            ("Type the keyword that closes the file automatically", "___ open('a.txt') as f:", None, ["with"]),
            ("Which mode adds to the end?", "", ["'a'", "'w'", "'r'", "'e'"], 0)],
         "Scripts often read and write files. <b>with open(name) as f:</b> opens a file and closes it automatically. <b>f.read()</b> gets all the text, <b>f.write()</b> saves text. Modes: <b>'r'</b> read, <b>'w'</b> write (replaces!), <b>'a'</b> append.",
         "with open('notes.txt', 'w') as f:\n    f.write('hello')\nwith open('notes.txt') as f:\n    print(f.read())"),
        ("Modules", "🧰", [
            ("Type the keyword that loads a module", "___ random", None, ["import"]),
            ("Result?", "import math\nmath.sqrt(16)", ["4.0", "4", "16", "error"], 0),
            ("Which module gives random numbers?", "", ["random", "math", "os", "sys"], 0)],
         "A <b>module</b> is a file of ready-made tools. <b>import</b> loads it: <b>random</b> for dice, <b>os</b> for the file system, <b>datetime</b> for dates, <b>math</b> for maths. Use <b>from math import sqrt</b> to import just one thing.",
         "import random\nimport math\nprint(math.sqrt(16))\nprint(random.randint(1, 6))")],
    "C": [
        ("Hello, World!", "👋", [
            ("Which line starts every C program?", "", ["int main(void)", "start()", "program main", "def main()"], 0),
            ("Type the header that provides printf", "#include <___>", None, ["stdio.h"]),
            ("What ends each statement?", "", [";", ".", ":", "!"], 0)],
         "A C program needs a <b>main</b> function, the place where execution starts. <b>#include &lt;stdio.h&gt;</b> gives you <b>printf</b>. Each statement ends with <b>;</b> and a compiler turns your source into a runnable program.",
         '#include <stdio.h>\n\nint main(void) {\n    printf("Hello, World!\\n");\n    return 0;\n}'),
        ("Comments & Style", "🎨", [
            ("Which starts a single-line comment in C?", "", ["//", "#", "--", "%"], 0),
            ("What does this print?", '/* printf("A"); */\nprintf("B");', ["A", "B", "AB", "nothing"], 1),
            ("Type the characters that start a line comment", "___ note", None, ["//"])],
         "<b>//</b> comments out the rest of a line and <b>/* ... */</b> comments out a block. Use clear names, consistent braces and indentation. Comment WHY, not what the code obviously does.",
         '// total with tax\nint total = price + tax;\n/* old code\nprintf("x");\n*/'),
        ("Dynamic Memory", "🧱", [
            ("What does malloc return on failure?", "", ["NULL", "0 bytes", "-1", "an error code"], 0),
            ("Type the function that releases heap memory", "___(p);", None, ["free"]),
            ("What is a memory leak?", "", ["memory that is never freed", "freeing twice", "a wrong type", "a stack overflow"], 0)],
         "<b>malloc(n)</b> reserves n bytes on the heap and returns a pointer (or NULL on failure). Use <b>sizeof</b>: <b>malloc(5 * sizeof(int))</b> makes room for 5 ints. <b>free</b> gives memory back. Forgetting it is a <b>leak</b>; using memory after free is a <b>dangling pointer</b> bug.",
         "int *a = malloc(3 * sizeof(int));\nif (a == NULL) return 1;\na[0] = 7;\nfree(a);\na = NULL;"),
        ("Files in C", "📁", [
            ("Which function opens a file?", "", ["fopen", "open_file", "fread", "fstart"], 0),
            ("Type the function that closes a file", "___(f);", None, ["fclose"]),
            ("What does fopen return if it fails?", "", ["NULL", "0 bytes", "-1 file", "EOF"], 0)],
         "<b>fopen</b> opens a file and returns a <b>FILE *</b>. Modes: <b>\"r\"</b> read, <b>\"w\"</b> write, <b>\"a\"</b> append. Write with <b>fprintf</b>, read with <b>fgets</b>, and always <b>fclose</b>. If fopen returns NULL the file could not be opened.",
         'FILE *f = fopen("a.txt", "w");\nif (f) {\n    fprintf(f, "hi");\n    fclose(f);\n}'),
        ("Bits & Bytes", "🔢", [
            ("Result?", "1 << 3", ["8", "3", "6", "4"], 0),
            ("Result?", "5 & 3", ["1", "7", "6", "2"], 0),
            ("Type the operator for bitwise OR", "a ___ b", None, ["|"])],
         "Hardware talks in bits. <b>&amp;</b> (AND), <b>|</b> (OR), <b>^</b> (XOR) and <b>~</b> (NOT) work on every bit; <b>&lt;&lt;</b> and <b>&gt;&gt;</b> shift bits. Set bit n with <b>x |= (1 &lt;&lt; n)</b>, clear it with <b>x &amp;= ~(1 &lt;&lt; n)</b>.",
         'unsigned char x = 0;\nx |= (1 << 3);\nx &= ~(1 << 3);\nprintf("%d", 1 << 4);'),
        ("Hex & Fixed Types", "🔌", [
            ("What is 0xFF in decimal?", "", ["255", "256", "15", "16"], 0),
            ("How many bits is uint8_t?", "", ["8", "16", "32", "1"], 0),
            ("Type the keyword for values that hardware can change", "___ int reg;", None, ["volatile"])],
         "Hex is shorthand for binary: one hex digit is 4 bits, so <b>0xFF</b> is 255. Embedded code uses fixed-size types from <b>stdint.h</b>: <b>uint8_t</b> (0-255), <b>uint16_t</b>, <b>int32_t</b>. <b>volatile</b> tells the compiler a value can change by itself, like a hardware register.",
         '#include <stdint.h>\n\nuint8_t r = 0xFF;\nvolatile uint8_t status = 0;\nprintf("%d", r);')],
    "JavaScript": [
        ("Hello, World!", "👋", [
            ("What does this print?", "console.log('Hello')", ["Hello", "'Hello'", "console", "Error"], 0),
            ("Type the object whose log method prints", "___.log('Hi')", None, ["console"]),
            ("Which is valid JavaScript?", "", ["console.log('Hi')", "print('Hi')", "echo 'Hi'", "System.out('Hi')"], 0)],
         "In JavaScript, <b>console.log()</b> prints to the console: in a browser press F12, in Node.js it appears in the terminal. Strings go in quotes (single or double). Semicolons at the end of a line are optional but common.",
         "console.log('Hello, World!');"),
        ("Comments & Style", "🎨", [
            ("Which starts a single-line comment in JavaScript?", "", ["//", "#", "--", "%"], 0),
            ("What does this print?", "// console.log('A');\nconsole.log('B');", ["A", "B", "AB", "nothing"], 1),
            ("Type the characters that start a line comment", "___ note", None, ["//"])],
         "<b>//</b> comments out the rest of a line and <b>/* ... */</b> comments out a block. JavaScript style uses <b>camelCase</b> names like <b>totalPrice</b>. Comment WHY, not what the code obviously does.",
         "// total with tax\nconst totalPrice = price + tax;"),
        ("The DOM", "🌐", [
            ("Type the method that finds an element by CSS selector", "document.___('#title')", None, ["querySelector"]),
            ("Which property changes an element's text?", "", ["textContent", "textBox", "innerLabel", "content()"], 0),
            ("What does DOM stand for?", "", ["Document Object Model", "Data Output Mode", "Digital Object Map", "Document Order Method"], 0)],
         "In a browser, JavaScript controls the page through the <b>DOM</b>, a tree of elements. <b>document.querySelector('#id')</b> finds an element; set <b>.textContent</b> to change its text and <b>.style.color</b> to restyle it. <b>createElement</b> and <b>append</b> add new elements.",
         "const h = document.querySelector('h1');\nh.textContent = 'Hi!';\nh.style.color = 'red';\nconst p = document.createElement('p');\ndocument.body.append(p);"),
        ("Events", "🖱️", [
            ("Type the method that attaches an event handler", "btn.___('click', fn)", None, ["addEventListener"]),
            ("Which event fires when a user clicks?", "", ["click", "press", "tap", "hit"], 0),
            ("What is event.target?", "", ["the element that triggered it", "the page URL", "the mouse speed", "the event name"], 0)],
         "<b>Events</b> let code react to the user. <b>element.addEventListener('click', fn)</b> runs fn on every click. Common events: <b>click</b>, <b>input</b>, <b>keydown</b>, <b>submit</b>. The function receives an <b>event</b> object, and <b>event.target</b> is the element involved.",
         "const btn = document.querySelector('button');\nbtn.addEventListener('click', () => {\n    console.log('clicked');\n});"),
        ("Node.js & Modules", "🗄️", [
            ("What does Node.js do?", "", ["Runs JavaScript outside the browser", "Styles web pages", "Stores databases only", "Compiles C"], 0),
            ("Which tool installs packages?", "", ["npm", "nodepkg", "getjs", "fs"], 0),
            ("Type the keyword that loads a module", "___ fs from 'fs';", None, ["import"])],
         "<b>Node.js</b> runs JavaScript outside the browser. Code is split into <b>modules</b>: <b>export</b> something from one file and <b>import</b> it in another. <b>npm</b> installs packages and <b>package.json</b> lists them. Node can read files with the built-in <b>fs</b> module.",
         "import fs from 'fs';\nconst text = fs.readFileSync('a.txt', 'utf8');\nconsole.log(text);"),
        ("Async & Fetch", "📡", [
            ("What does status 404 mean?", "", ["Not found", "OK", "Server error", "Redirect"], 0),
            ("Type the function that requests data from a URL", "___('/api')", None, ["fetch"]),
            ("What does response.json() do?", "", ["parses the body into an object", "sends JSON", "closes the connection", "validates HTML"], 0)],
         "<b>fetch(url)</b> asks a server for data and returns a Promise. Use <b>await</b> to wait, then <b>response.json()</b> to turn the body into an object. Wrap it in <b>try/catch</b> because networks fail. The server replies with a <b>status code</b>: 200 means OK, 404 means not found.",
         "async function load() {\n    const r = await fetch('/api/users');\n    const data = await r.json();\n    console.log(data);\n}")],
}
for _n in LANGS:
    for _t, _e, _qs, _tx, _cd in [SHARED] + ADD[_n]:
        LANGS[_n][2].append((_t, _e, _qs))
        TEACH[_n].append((_tx, _cd))


T2 = [("l", 0), ("l", 1), ("l", 2), ("l", 3), ("p", 0), ("l", 4), ("p", 1), ("l", 5), ("l", 6), ("p", 2)]
TRUNKS = {"Python": TRUNK, "C": TRUNK, "JavaScript": TRUNK, "Java": T2, "C++": T2, "Rust": T2}
UN2 = [(0, "Unit 1", "Foundations"), (5, "Unit 2", "Logic & Loops"), (7, "Unit 3", "Functions & Objects"), ("f", "Crossroads", "Choose Your Field"), ("e", "Boss", "Boss 1")]
UN = {n: UN2 for n in ("Java", "C++", "Rust")}
BR.update({
    "Java": [("Backend", "🗄️", [("l", 7)]), ("Android", "📱", [("l", 8)])],
    "C++": [("Games", "🎮", [("l", 7)]), ("Systems", "🖥️", [("l", 8)])],
    "Rust": [("Systems", "⚙️", [("l", 7)]), ("Web", "🕸️", [("l", 8)])],
})


def total(lang):
    return len(TRUNKS[lang]) + 2 + len(BR[lang][0][2]) + len(EXTN.get(lang, [])) + 1 + len(BR2[lang][0][2]) + len(POST.get(lang, []))


def _body(b1, b2):
    return b1, b2


STARTER.update({
    "Java": ["public class Main {\n    public static void main(String[] args) {\n    }\n}\n",
             "public class Main {\n    public static void main(String[] args) {\n        for (int i = 1; i <= 15; i++) {\n        }\n    }\n}\n",
             "public class Main {\n    public static void main(String[] args) {\n        int a = 0, b = 1;\n        for (int i = 0; i < 10; i++) {\n        }\n    }\n}\n"],
    "C++": ["#include <iostream>\n\nint main() {\n    return 0;\n}\n",
            "#include <iostream>\n\nint main() {\n    for (int i = 1; i <= 15; i++) {\n    }\n    return 0;\n}\n",
            "#include <iostream>\n\nint main() {\n    int a = 0, b = 1;\n    for (int i = 0; i < 10; i++) {\n    }\n    return 0;\n}\n"],
    "Rust": ["fn main() {\n}\n", "fn main() {\n    for i in 1..=15 {\n    }\n}\n", "fn main() {\n    let (mut a, mut b) = (0, 1);\n    for _ in 0..10 {\n    }\n}\n"],
})
PRINT.update({"Java": r"System\s*\.\s*out\s*\.\s*print(ln)?\s*\(", "C++": r"\bcout\s*<<|\bprintf\s*\(", "Rust": r"\bprintln!\s*\(|\bprint!\s*\("})
NEWL = {
    "Java": ("☕", "#ef4444", [
        ("Hello, World!", "👋", [
            ("Which method is the program entry point?", "", ["public static void main", "start()", "run()", "init()"], 0),
            ("What does this print?", 'System.out.println("Hi");', ["Hi", '"Hi"', "println", "error"], 0),
            ("Type the keyword that starts a class", "public ___ Main {", None, ["class"])],
         "Every Java program lives inside a <b>class</b> and starts in <b>main</b>. <b>System.out.println()</b> prints a line. Java compiles to bytecode that runs on the <b>JVM</b>, and statements end with <b>;</b>.",
         'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}'),
        ("Variables & Types", "📦", [
            ("Which type holds whole numbers?", "", ["int", "String", "boolean", "double"], 0),
            ("Which declares a text variable?", "", ['String s = "hi";', 'string s = "hi";', 'text s = "hi";', 's = "hi";'], 0),
            ("Type the keyword for the true/false type", "___ ok = true;", None, ["boolean"])],
         "Java is <b>statically typed</b>: every variable has a type. Primitives: <b>int</b>, <b>long</b>, <b>double</b>, <b>boolean</b>, <b>char</b>. <b>String</b> is a class for text in double quotes. Use <b>final</b> for constants.",
         'int age = 20;\ndouble price = 9.99;\nboolean ok = true;\nString name = "Ada";\nfinal int MAX = 10;'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 0),
            ("Type the operator for logical and", "if (a ___ b)", None, ["&&"]),
            ("How do you compare Strings correctly?", "", ["a.equals(b)", "a == b", "a = b", "a.same(b)"], 0)],
         "Operators: <b>+ - * / %</b>; integer division drops the fraction. <b>if / else if / else</b> choose branches; combine tests with <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>. Compare Strings with <b>.equals()</b>, never <b>==</b>.",
         'int x = 7;\nif (x % 2 == 0) {\n    System.out.println("even");\n} else {\n    System.out.println("odd");\n}'),
        ("Loops", "🔁", [
            ("How many times does this run?", "for (int i = 0; i < 3; i++) { }", ["3", "2", "4", "0"], 0),
            ("Type the keyword that leaves a loop", "", None, ["break"]),
            ("Which loop visits every element?", "", ["for (int x : list)", "foreach x in list", "for x of list", "loop list"], 0)],
         "<b>for</b> has three parts: start, condition, step. <b>while</b> repeats while a condition is true. The <b>for-each</b> loop <b>for (int x : arr)</b> visits every element. <b>break</b> exits and <b>continue</b> skips to the next round.",
         'for (int i = 0; i < 3; i++) {\n    System.out.println(i);\n}\nint[] a = {1, 2, 3};\nfor (int x : a) {\n    System.out.println(x);\n}'),
        ("Methods", "⚙️", [
            ("Which return type means nothing is returned?", "", ["void", "null", "none", "empty"], 0),
            ("What does this print?", "static int sq(int n) { return n * n; }\nSystem.out.println(sq(3));", ["9", "6", "3", "error"], 0),
            ("Type the keyword that sends a value back", "", None, ["return"])],
         "A <b>method</b> has a return type, a name, parameters and a body. Use <b>void</b> when nothing is returned. <b>static</b> methods belong to the class itself. Methods with the same name but different parameters are <b>overloaded</b>.",
         "static int add(int a, int b) {\n    return a + b;\n}\n\nSystem.out.println(add(2, 3));"),
        ("Classes & Objects", "🐶", [
            ("Which keyword creates an object?", "", ["new", "make", "create", "object"], 0),
            ("Type the keyword that hides a field from outside", "___ int age;", None, ["private"]),
            ("What is a constructor?", "", ["Code that runs when an object is created", "A loop", "A static field", "An error type"], 0)],
         "A <b>class</b> is a blueprint and <b>new</b> builds an object from it. <b>Fields</b> hold data, <b>methods</b> hold behavior. A <b>constructor</b> has the class name and sets things up. Mark fields <b>private</b> and expose them through methods (encapsulation).",
         'class Dog {\n    private String name;\n    Dog(String name) { this.name = name; }\n    void bark() { System.out.println(name + " woofs"); }\n}\nnew Dog("Rex").bark();'),
        ("Exceptions & Files", "🛡️", [
            ("Which block catches an error?", "", ["catch", "except", "rescue", "handle"], 0),
            ("Type the keyword for the block that always runs", "try { } catch (Exception e) { } ___ { }", None, ["finally"]),
            ("Which exception means a missing file?", "", ["FileNotFoundException", "NullError", "FileGone", "IOMissing"], 0)],
         "Errors are <b>exceptions</b>. Wrap risky code in <b>try</b>, handle problems in <b>catch</b> and put cleanup in <b>finally</b>. <b>throw new ...</b> raises your own. File methods throw <b>IOException</b>, so handle it or declare <b>throws</b>.",
         'try {\n    int x = 10 / 0;\n} catch (ArithmeticException e) {\n    System.out.println("oops");\n} finally {\n    System.out.println("done");\n}'),
        ("Android Basics", "📱", [
            ("What is an Activity?", "", ["One screen of an app", "A database", "A loop", "A file type"], 0),
            ("Which language does modern Android favor besides Java?", "", ["Kotlin", "Swift", "Rust", "Ruby"], 0),
            ("Type the file extension of the manifest", "AndroidManifest.___", None, ["xml"])],
         "Android apps are built from <b>Activities</b> (screens). Layouts are written in <b>XML</b> or Compose and <b>findViewById</b> connects code to views. <b>AndroidManifest.xml</b> lists screens and permissions. Taps arrive as <b>listeners</b> like <b>setOnClickListener</b>.",
         'Button b = findViewById(R.id.btn);\nb.setOnClickListener(v -> {\n    b.setText("Clicked");\n});')]),
    "C++": ("➕", "#0ea5e9", [
        ("Hello, World!", "👋", [
            ("Which prints to the console?", "", ['std::cout << "Hi";', 'print("Hi");', 'console.log("Hi");', 'echo "Hi";'], 0),
            ("Type the header that provides cout", "#include <___>", None, ["iostream"]),
            ("What is the entry point?", "", ["int main()", "start()", "run()", "void begin()"], 0)],
         "C++ is C plus classes, templates and a big standard library. <b>#include &lt;iostream&gt;</b> gives <b>std::cout</b>, which prints with the <b>&lt;&lt;</b> operator. Execution starts in <b>main</b>. <b>std::endl</b> ends a line.",
         '#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}'),
        ("Variables & Types", "📦", [
            ("Which type holds text?", "", ["std::string", "text", "str", "String"], 0),
            ("What does auto do?", "", ["Lets the compiler deduce the type", "Makes a variable constant", "Creates a loop", "Frees memory"], 0),
            ("Type the keyword for a constant", "___ int MAX = 10;", None, ["const"])],
         "C++ is statically typed: <b>int</b>, <b>double</b>, <b>bool</b>, <b>char</b> and <b>std::string</b>. <b>auto</b> lets the compiler deduce the type. <b>const</b> forbids changes. Initialise with braces, <b>int x{5};</b>, to catch lossy conversions.",
         'int age = 20;\ndouble price = 9.99;\nbool ok = true;\nstd::string name = "Ada";\nauto n = 5;\nconst int MAX = 10;'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 0),
            ("Type the operator for logical or", "if (a ___ b)", None, ["||"]),
            ("Which compares equality?", "", ["==", "=", "=>", "eq"], 0)],
         "Arithmetic works like C: <b>+ - * / %</b>, and integer division truncates. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>. <b>if / else if / else</b> branch the flow and <b>switch</b> picks between constants. <b>x ? a : b</b> is a compact choice.",
         'int x = 7;\nif (x % 2 == 0) {\n    std::cout << "even";\n} else {\n    std::cout << "odd";\n}'),
        ("Loops", "🔁", [
            ("Which loop visits every element of a vector?", "", ["for (auto x : v)", "foreach x in v", "for x of v", "loop v"], 0),
            ("Type the keyword that skips to the next round", "", None, ["continue"]),
            ("How many times does this run?", "for (int i = 1; i <= 4; i++) { }", ["4", "3", "5", "1"], 0)],
         "<b>for</b>, <b>while</b> and <b>do-while</b> work like in C. Modern C++ adds the <b>range-based for</b>: <b>for (auto x : v)</b> visits every element of a container. <b>break</b> exits and <b>continue</b> skips to the next round.",
         'std::vector<int> v = {1, 2, 3};\nfor (auto x : v) {\n    std::cout << x << " ";\n}'),
        ("Functions", "⚙️", [
            ("Which return type means nothing?", "", ["void", "null", "none", "empty"], 0),
            ("What does this print?", "int sq(int n) { return n * n; }\nstd::cout << sq(3);", ["9", "6", "3", "error"], 0),
            ("Type the symbol that passes by reference", "void inc(int___ n)", None, ["&"])],
         "A function has a return type, name, parameters and body. Arguments are copied unless you take a <b>reference</b>: <b>void inc(int&amp; n)</b> changes the caller's variable. Declare a function before use with a <b>prototype</b>. <b>const T&amp;</b> avoids copying big objects.",
         "int add(int a, int b) {\n    return a + b;\n}\n\nvoid inc(int& n) {\n    n++;\n}"),
        ("Classes & RAII", "🐶", [
            ("Which keyword hides members from outside?", "", ["private", "hidden", "secret", "closed"], 0),
            ("What runs when an object dies?", "", ["The destructor", "The constructor", "main", "nothing"], 0),
            ("Type the smart pointer for single ownership", "std::___<int> p;", None, ["unique_ptr"])],
         "A <b>class</b> bundles data and functions. The <b>constructor</b> sets an object up and the <b>destructor</b> (<b>~Name</b>) cleans up when it goes out of scope. This is <b>RAII</b>. Prefer smart pointers like <b>std::unique_ptr</b> over raw <b>new/delete</b>.",
         'class Dog {\n    std::string name;\npublic:\n    Dog(std::string n) : name(n) {}\n    void bark() { std::cout << name << " woofs"; }\n};'),
        ("Game Loops & Vectors", "🎮", [
            ("Which container grows dynamically?", "", ["std::vector", "int[]", "std::array", "char*"], 0),
            ("Type the method that adds to the end of a vector", "v.___(5);", None, ["push_back"]),
            ("What does a game loop do each frame?", "", ["Update then draw", "Only draw", "Only exit", "Compile"], 0)],
         "A game runs a <b>loop</b>: read input, <b>update</b> the world, <b>draw</b>, repeat about 60 times a second. <b>std::vector</b> stores things like enemies: <b>push_back</b> adds, <b>size()</b> counts, <b>erase</b> removes. Engines like Unreal are written in C++.",
         "bool running = true;\nwhile (running) {\n    update();\n    draw();\n}"),
        ("Smart Pointers & Templates", "🧩", [
            ("Which smart pointer shares ownership?", "", ["std::shared_ptr", "std::unique_ptr", "std::raw_ptr", "std::ptr"], 0),
            ("Type the keyword that starts a generic function", "___ <typename T>", None, ["template"]),
            ("Which creates a unique_ptr safely?", "", ["std::make_unique<int>(5)", "new unique_ptr(5)", "unique(5)", "make(5)"], 0)],
         "<b>unique_ptr</b> owns an object alone; <b>shared_ptr</b> counts owners and frees when the last one goes. Create them with <b>std::make_unique</b> or <b>make_shared</b>. <b>Templates</b> write one function for many types: <b>template &lt;typename T&gt;</b>.",
         "template <typename T>\nT biggest(T a, T b) {\n    return a > b ? a : b;\n}\nauto p = std::make_unique<int>(5);")]),
    "Rust": ("🦀", "#b45309", [
        ("Hello, World!", "👋", [
            ("Which prints a line in Rust?", "", ['println!("Hi");', 'print("Hi")', 'console.log("Hi")', 'echo "Hi"'], 0),
            ("Type the keyword that defines a function", "___ main() {}", None, ["fn"]),
            ("What does the ! in println! mean?", "", ["It is a macro", "It negates", "It is an error", "It is a pointer"], 0)],
         "Rust compiles to fast native code with memory safety and no garbage collector. Programs start in <b>fn main()</b>. <b>println!</b> is a <b>macro</b> (note the <b>!</b>) that prints a line. <b>cargo new</b> creates a project and <b>cargo run</b> builds and runs it.",
         'fn main() {\n    println!("Hello, World!");\n}'),
        ("Variables & Types", "📦", [
            ("Are Rust variables mutable by default?", "", ["No, immutable", "Yes", "Only ints", "Only strings"], 0),
            ("Type the keyword that lets a variable change", "let ___ x = 5;", None, ["mut"]),
            ("Which is a 32-bit signed integer?", "", ["i32", "u32", "f32", "int"], 0)],
         "<b>let</b> binds a value, and variables are <b>immutable</b> by default; add <b>mut</b> to allow changes. Types: <b>i32</b>/<b>u32</b> (signed/unsigned ints), <b>f64</b>, <b>bool</b>, <b>char</b>, <b>&amp;str</b> and <b>String</b>. Rust infers types, but you can write them: <b>let x: i32 = 5;</b>.",
         'let x = 5;\nlet mut y = 10;\ny += x;\nlet pi: f64 = 3.14;\nlet name = String::from("Ada");'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 0),
            ("Type the keyword for a branch", "___ x > 5 { }", None, ["if"]),
            ("Does an if condition need brackets in Rust?", "", ["No", "Yes", "Only for else", "Only in loops"], 0)],
         "Arithmetic is <b>+ - * / %</b>; integer division truncates and both sides must be the SAME type. <b>if</b> conditions need no brackets but must be <b>bool</b>. <b>if</b> is an expression: <b>let s = if x &gt; 5 { 1 } else { 2 };</b>. <b>match</b> checks many patterns exhaustively.",
         'let x = 7;\nif x % 2 == 0 {\n    println!("even");\n} else {\n    println!("odd");\n}'),
        ("Loops", "🔁", [
            ("Which is an infinite loop?", "", ["loop { }", "for { }", "while { }", "repeat { }"], 0),
            ("What does 1..4 cover?", "", ["1, 2, 3", "1, 2, 3, 4", "2, 3, 4", "1 to 5"], 0),
            ("Type the keyword that leaves a loop", "", None, ["break"])],
         "<b>for i in 1..4</b> loops over a range that stops BEFORE 4; <b>1..=4</b> includes 4. <b>while</b> checks a condition and <b>loop</b> runs forever until <b>break</b>. <b>for x in &amp;v</b> visits every item of a vector.",
         'for i in 1..4 {\n    println!("{}", i);\n}\nlet v = vec![1, 2, 3];\nfor x in &v {\n    println!("{}", x);\n}'),
        ("Functions", "⚙️", [
            ("What does this function return?", "fn add(a: i32, b: i32) -> i32 {\n    a + b\n}", ["a + b", "nothing", "an error", "a"], 0),
            ("Type the symbol that introduces the return type", "fn f() ___ i32 { 5 }", None, ["->"]),
            ("Why is there no semicolon after a + b?", "", ["It is the returned expression", "It is a typo", "Rust forbids semicolons", "It ends the loop"], 0)],
         "Functions use <b>fn</b>, typed parameters and a return type after <b>-&gt;</b>. The last expression WITHOUT a semicolon is returned; adding <b>;</b> turns it into a statement that returns nothing. <b>return</b> exists for early exits.",
         'fn add(a: i32, b: i32) -> i32 {\n    a + b\n}\n\nprintln!("{}", add(2, 3));'),
        ("Ownership", "👑", [
            ("How many owners can a value have?", "", ["Exactly one", "Unlimited", "Two", "None"], 0),
            ("After let b = a; (a is a String), what is true?", "", ["a is moved and unusable", "both are usable", "a is deleted twice", "it fails at runtime"], 0),
            ("Type the method that makes a deep copy", "let b = a.___();", None, ["clone"])],
         "Rust's big idea is <b>ownership</b>: every value has ONE owner, and when the owner goes out of scope the value is freed. Assigning a String to another variable <b>moves</b> it, so the old name becomes invalid. Use <b>.clone()</b> for a real copy. This prevents memory bugs at compile time.",
         'let a = String::from("hi");\nlet b = a;\nlet c = b.clone();\nprintln!("{} {}", b, c);'),
        ("Borrowing", "🤝", [
            ("What does &x create?", "", ["A reference (borrow)", "A copy", "A pointer to free", "A macro"], 0),
            ("How many mutable borrows may exist at once?", "", ["One", "Two", "Unlimited", "Zero"], 0),
            ("Type the keyword for a mutable reference", "fn f(v: &___ Vec<i32>)", None, ["mut"])],
         "A <b>reference</b> <b>&amp;x</b> lets you use a value WITHOUT taking ownership (a borrow). The rule: any number of shared <b>&amp;</b> borrows OR exactly one <b>&amp;mut</b> borrow at a time. The compiler checks this, which prevents data races.",
         'fn len(s: &String) -> usize {\n    s.len()\n}\nlet s = String::from("hi");\nprintln!("{}", len(&s));'),
        ("Cargo & Crates", "📦", [
            ("What is Cargo?", "", ["Rust's build tool and package manager", "A compiler flag", "A Rust editor", "A web server"], 0),
            ("Type the file extension of the dependency list", "Cargo.___", None, ["toml"]),
            ("What is a crate?", "", ["A package of Rust code", "A variable type", "A loop", "A macro"], 0)],
         "<b>Cargo</b> builds, tests and manages dependencies. <b>Cargo.toml</b> lists <b>crates</b> (packages from crates.io). Rust powers fast web servers and compiles to <b>WebAssembly</b> to run in the browser. Handle failures with <b>Result</b> and the <b>?</b> operator.",
         '[dependencies]\nserde = "1.0"\n\nfn main() {\n    println!("cargo run");\n}')]),
}
for _n, (_ic, _c, _ls) in NEWL.items():
    LANGS[_n] = (_ic, _c, [SHARED[:3]] + [l[:3] for l in _ls])
    TEACH[_n] = [SHARED[3:]] + [l[3:] for l in _ls]


NEW3 = ("C#", "Go", "TypeScript")
TRUNKS.update({n: T2 for n in NEW3})
UN.update({n: UN2 for n in NEW3})
BR.update({
    "C#": [("Games", "🎮", [("l", 7)]), ("Web", "🌐", [("l", 8)])],
    "Go": [("Backend", "🗄️", [("l", 7)]), ("Concurrency", "⚡", [("l", 8)])],
    "TypeScript": [("Frontend", "🎨", [("l", 7)]), ("Backend", "🗄️", [("l", 8)])],
})
STARTER.update({
    "C#": ["using System;\n\nclass Program {\n    static void Main() {\n    }\n}\n",
           "using System;\n\nclass Program {\n    static void Main() {\n        for (int i = 1; i <= 15; i++) {\n        }\n    }\n}\n",
           "using System;\n\nclass Program {\n    static void Main() {\n        int a = 0, b = 1;\n        for (int i = 0; i < 10; i++) {\n        }\n    }\n}\n"],
    "Go": ['package main\n\nimport "fmt"\n\nfunc main() {\n}\n',
           'package main\n\nimport "fmt"\n\nfunc main() {\n    for i := 1; i <= 15; i++ {\n    }\n}\n',
           'package main\n\nimport "fmt"\n\nfunc main() {\n    a, b := 0, 1\n    for i := 0; i < 10; i++ {\n    }\n}\n'],
    "TypeScript": ["console.log();\n", "for (let i = 1; i <= 15; i++) {\n}\n", "let a = 0, b = 1;\nfor (let i = 0; i < 10; i++) {\n}\n"],
})
PRINT.update({"C#": r"\bConsole\s*\.\s*Write(Line)?\s*\(", "Go": r"\bfmt\s*\.\s*Print(ln|f)?\s*\(", "TypeScript": r"console\s*\.\s*log\s*\("})
NEWL2 = {
    "C#": ("🎯", "#7c3aed", [
        ("Hello, World!", "👋", [
            ("Which prints a line?", "", ['Console.WriteLine("Hi");', 'print("Hi");', 'System.out.println("Hi");', 'echo "Hi";'], 0),
            ("Type the method name every program starts in", "static void ___() {}", None, ["Main"]),
            ("What do C# statements end with?", "", [";", ".", ":", "!"], 0)],
         "C# runs on .NET. Programs start in <b>Main</b> inside a class. <b>Console.WriteLine()</b> prints a line and statements end with <b>;</b>. <b>using System;</b> imports the Console class.",
         'using System;\n\nclass Program {\n    static void Main() {\n        Console.WriteLine("Hello, World!");\n    }\n}'),
        ("Variables & Types", "📦", [
            ("Which type holds text?", "", ["string", "text", "str", "String8"], 0),
            ("What does var do?", "", ["Infers the type", "Makes it constant", "Declares a loop", "Frees memory"], 0),
            ("Type the keyword for a constant", "___ int Max = 10;", None, ["const"])],
         "C# is statically typed: <b>int</b>, <b>double</b>, <b>bool</b>, <b>char</b>, <b>string</b>. <b>var</b> lets the compiler infer the type and <b>const</b> fixes a value. A <b>$</b> string interpolates values: <b>$\"{x}\"</b>.",
         'int age = 20;\ndouble price = 9.99;\nbool ok = true;\nstring name = "Ada";\nvar n = 5;\nConsole.WriteLine($"{name} is {age}");'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 0),
            ("Type the operator for logical and", "if (a ___ b)", None, ["&&"]),
            ("Which keyword picks between many constants?", "", ["switch", "select", "pick", "choose"], 0)],
         "Operators: <b>+ - * / %</b>; integer division truncates. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>. <b>if / else</b> and <b>switch</b> branch the flow; <b>cond ? a : b</b> is a one-line choice.",
         'int x = 7;\nif (x % 2 == 0) {\n    Console.WriteLine("even");\n} else {\n    Console.WriteLine("odd");\n}'),
        ("Loops", "🔁", [
            ("Which loop visits every item?", "", ["foreach (var x in list)", "for x of list", "each x in list", "loop list"], 0),
            ("Type the keyword that skips a round", "", None, ["continue"]),
            ("How many times does this run?", "for (int i = 0; i < 3; i++) { }", ["3", "2", "4", "0"], 0)],
         "<b>for</b>, <b>while</b> and <b>do-while</b> work like in Java. <b>foreach (var x in items)</b> visits every element of a collection. <b>break</b> exits and <b>continue</b> skips to the next round.",
         'foreach (var x in new[] {1, 2, 3}) {\n    Console.WriteLine(x);\n}\nfor (int i = 0; i < 3; i++) {\n    Console.WriteLine(i);\n}'),
        ("Methods", "⚙️", [
            ("Which return type means nothing?", "", ["void", "null", "none", "empty"], 0),
            ("What does this print?", "static int Sq(int n) => n * n;\nConsole.WriteLine(Sq(3));", ["9", "6", "3", "error"], 0),
            ("Type the symbol for expression-bodied methods", "static int Sq(int n) ___ n * n;", None, ["=>"])],
         "A method has a return type, name, parameters and body. <b>void</b> returns nothing. One-liners can use <b>=&gt;</b>. Parameters can have default values, and <b>static</b> methods belong to the class.",
         "static int Add(int a, int b) {\n    return a + b;\n}\n\nConsole.WriteLine(Add(2, 3));"),
        ("Classes & Properties", "🐶", [
            ("Which keyword creates an object?", "", ["new", "make", "create", "object"], 0),
            ("Type the keyword for a field visible only inside the class", "___ int age;", None, ["private"]),
            ("What is a property?", "", ["A field with get/set accessors", "A loop", "A comment", "A namespace"], 0)],
         "A <b>class</b> is a blueprint and <b>new</b> creates an object. <b>Properties</b> wrap fields with <b>get</b> and <b>set</b>: <b>public int Age { get; set; }</b>. A <b>constructor</b> has the class name and <b>private</b> hides members.",
         'class Dog {\n    public string Name { get; set; }\n    public Dog(string name) { Name = name; }\n    public void Bark() => Console.WriteLine(Name + " woofs");\n}\nnew Dog("Rex").Bark();'),
        ("Unity Basics", "🎮", [
            ("Which method runs once at start in Unity?", "", ["Start()", "Main()", "Init()", "Begin()"], 0),
            ("Type the method that runs every frame", "void ___() { }", None, ["Update"]),
            ("What is a GameObject?", "", ["An object in a Unity scene", "A C# keyword", "A texture", "A sound"], 0)],
         "Unity scripts are C# classes that inherit from <b>MonoBehaviour</b>. <b>Start()</b> runs once and <b>Update()</b> runs every frame. Scripts attach to <b>GameObjects</b>, read input with <b>Input.GetKey</b> and move things with <b>transform.Translate</b>.",
         "public class Player : MonoBehaviour {\n    void Update() {\n        transform.Translate(Vector3.right * Time.deltaTime);\n    }\n}"),
        ("ASP.NET Basics", "🌐", [
            ("What does ASP.NET build?", "", ["Web apps and APIs", "Mobile games", "Operating systems", "Spreadsheets"], 0),
            ("Type the HTTP verb used to read data", "[Http___]", None, ["Get"]),
            ("Which status code means OK?", "", ["200", "404", "500", "301"], 0)],
         "<b>ASP.NET Core</b> builds web apps and APIs in C#. A <b>controller</b> class has action methods that answer HTTP requests, marked with attributes like <b>[HttpGet]</b>. They return data that becomes JSON. <b>200</b> means OK and <b>404</b> means not found.",
         '[HttpGet("hello")]\npublic string Hello() {\n    return "Hello from C#";\n}')]),
    "Go": ("🐹", "#14b8a6", [
        ("Hello, World!", "👋", [
            ("Which prints a line?", "", ['fmt.Println("Hi")', 'print("Hi")', 'console.log("Hi")', 'echo "Hi"'], 0),
            ("Type the keyword that defines a function", "___ main() {}", None, ["func"]),
            ("What does package main mean?", "", ["This file builds a runnable program", "It imports main", "It is a comment", "It is a class"], 0)],
         "Go is a simple, fast, compiled language from Google. Every file starts with a <b>package</b>; runnable programs use <b>package main</b> and a <b>func main()</b>. <b>fmt.Println</b> prints a line. No semicolons needed.",
         'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}'),
        ("Variables & Types", "📦", [
            ("What does := do?", "", ["Declares and infers a variable", "Compares values", "Starts a loop", "Imports a package"], 0),
            ("Type the keyword for a long-form declaration", "___ x int = 5", None, ["var"]),
            ("What is the zero value of an int?", "", ["0", "nil", "-1", "undefined"], 0)],
         "Declare with <b>var x int = 5</b> or the short form <b>x := 5</b> inside functions. Types: <b>int</b>, <b>float64</b>, <b>string</b>, <b>bool</b>. Unused variables are a compile error! Every type has a <b>zero value</b> (0, empty string, false).",
         'var age int = 20\nname := "Ada"\nprice := 9.99\nok := true\nfmt.Println(name, age, price, ok)'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 0),
            ("Do Go if conditions need brackets?", "", ["No", "Yes", "Only with else", "Only in loops"], 0),
            ("Type the keyword for the other branch", "if x > 1 { } ___ { }", None, ["else"])],
         "Operators: <b>+ - * / %</b>; integer division truncates and types must match. <b>if</b> needs no brackets but braces are required. <b>if v := f(); v &gt; 1 { }</b> can declare a variable first. <b>switch</b> doesn't fall through by default.",
         'x := 7\nif x%2 == 0 {\n    fmt.Println("even")\n} else {\n    fmt.Println("odd")\n}'),
        ("Loops", "🔁", [
            ("Which is Go's only loop keyword?", "", ["for", "while", "loop", "repeat"], 0),
            ("What does for { } do?", "", ["Loops forever", "Does nothing", "Loops once", "Fails to compile"], 0),
            ("Type the keyword that leaves a loop", "", None, ["break"])],
         "Go has ONE loop keyword: <b>for</b>. <b>for i := 0; i &lt; 3; i++ { }</b> is the classic form, <b>for cond { }</b> acts like while and <b>for { }</b> runs forever. <b>for i, v := range items</b> walks slices.",
         "for i := 0; i < 3; i++ {\n    fmt.Println(i)\n}\nfor i, v := range []int{5, 6} {\n    fmt.Println(i, v)\n}"),
        ("Functions", "⚙️", [
            ("What does this function return?", "func add(a, b int) int {\n    return a + b\n}", ["a + b", "nothing", "an error", "a"], 0),
            ("Can Go functions return several values?", "", ["Yes", "No", "Only two ints", "Only with classes"], 0),
            ("Type the keyword that sends a value back", "", None, ["return"])],
         "Functions use <b>func</b>, typed parameters and a result type after them. They can return <b>multiple values</b>, often a result and an <b>error</b>. Check errors with <b>if err != nil</b>. <b>defer</b> runs a call when the function ends.",
         'func div(a, b int) (int, error) {\n    if b == 0 {\n        return 0, errors.New("zero")\n    }\n    return a / b, nil\n}'),
        ("Structs & Methods", "🏗️", [
            ("Which declares a struct?", "", ["type Name struct", "class Name", "struct Name()", "new Name"], 0),
            ("Type the operator that reads a field", "p___X", None, ["."]),
            ("How does Go attach methods to types?", "", ["Functions with a receiver", "Inheritance", "Prototypes", "Macros"], 0)],
         "Go has no classes. A <b>struct</b> groups fields and <b>methods</b> are functions with a <b>receiver</b>: <b>func (p Point) Sum() int</b>. <b>interface</b> types describe behavior, and any type with the right methods fits automatically.",
         "type Point struct {\n    X, Y int\n}\n\nfunc (p Point) Sum() int {\n    return p.X + p.Y\n}"),
        ("HTTP Servers", "🗄️", [
            ("Which package serves HTTP?", "", ["net/http", "fmt", "os", "math"], 0),
            ("Type the function that starts a server", 'http.___(":8080", nil)', None, ["ListenAndServe"]),
            ("What does a handler receive?", "", ["ResponseWriter and Request", "Only a string", "A file", "Nothing"], 0)],
         "Go's standard library includes a web server. <b>http.HandleFunc</b> registers a handler that receives a <b>ResponseWriter</b> and a <b>Request</b>, and <b>http.ListenAndServe</b> starts listening. Each request runs in its own goroutine.",
         'http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {\n    fmt.Fprintln(w, "Hello")\n})\nhttp.ListenAndServe(":8080", nil)'),
        ("Goroutines & Channels", "⚡", [
            ("Which keyword starts a goroutine?", "", ["go", "async", "thread", "spawn"], 0),
            ("Type the keyword for a channel type", "ch := make(___ int)", None, ["chan"]),
            ("What do channels do?", "", ["Pass values between goroutines", "Open files", "Print text", "Compile code"], 0)],
         "A <b>goroutine</b> is a lightweight thread: put <b>go</b> before a call. Goroutines talk through <b>channels</b>: <b>ch &lt;- v</b> sends and <b>v := &lt;-ch</b> receives. A <b>sync.WaitGroup</b> waits for workers to finish.",
         "ch := make(chan int)\ngo func() {\n    ch <- 42\n}()\nfmt.Println(<-ch)")]),
    "TypeScript": ("🔷", "#1d4ed8", [
        ("Hello, World!", "👋", [
            ("What is TypeScript?", "", ["JavaScript with types", "A new browser", "A database", "A CSS tool"], 0),
            ("Type the command that compiles .ts files", "___ app.ts", None, ["tsc"]),
            ("What does this print?", "console.log('Hi')", ["Hi", "'Hi'", "console", "Error"], 0)],
         "<b>TypeScript</b> is JavaScript plus a <b>type system</b>. The compiler <b>tsc</b> checks types and outputs plain JavaScript. All JavaScript is valid TypeScript, so <b>console.log()</b> works exactly the same.",
         "console.log('Hello, World!');"),
        ("Types", "📦", [
            ("Which annotation is valid?", "", ["let n: number = 5", "let n = number 5", "number n = 5", "let 5: n"], 0),
            ("Type the type for text", "let s: ___ = 'hi';", None, ["string"]),
            ("Which type switches type checking off?", "", ["any", "void", "never", "unknown"], 0)],
         "Annotate types after a colon: <b>number</b>, <b>string</b>, <b>boolean</b>, <b>string[]</b>. TypeScript infers types, so annotations are often optional. <b>any</b> switches checking off (avoid it), <b>unknown</b> is the safe version, and <b>|</b> makes unions like <b>string | number</b>.",
         "let n: number = 5;\nlet name: string = 'Ada';\nlet ids: number[] = [1, 2];\nlet v: string | number = 'x';"),
        ("Operators & Conditions", "🔀", [
            ("Result?", "'5' + 1", ["51", "6", "error", "NaN"], 0),
            ("Which operator is strict equality?", "", ["===", "==", "=", "=>"], 0),
            ("Type the keyword for the other branch", "if (x) { } ___ { }", None, ["else"])],
         "Conditions and operators work like JavaScript: <b>+ - * / %</b>, <b>===</b> for strict equality, <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>, <b>if / else</b> and the <b>? :</b> ternary. TypeScript also refuses nonsense like <b>5 - 'a'</b> at compile time.",
         "const n = 7;\nif (n % 2 === 0) {\n    console.log('even');\n} else {\n    console.log('odd');\n}"),
        ("Loops", "🔁", [
            ("Which loop visits array values?", "", ["for (const x of arr)", "for (const x in arr)", "foreach x in arr", "for x : arr"], 0),
            ("Type the keyword that leaves a loop", "", None, ["break"]),
            ("What does for...in give for an object?", "", ["its keys", "its values", "its length", "nothing"], 0)],
         "<b>for...of</b> loops over the VALUES of an array and <b>for...in</b> over the KEYS of an object. <b>break</b> exits a loop and <b>continue</b> skips to the next round. TypeScript infers the type of the loop variable for you.",
         "for (const x of [1, 2, 3]) {\n    console.log(x);\n}"),
        ("Functions", "⚙️", [
            ("What does this function return?", "function add(a: number, b: number): number {\n    return a + b;\n}", ["a number", "a string", "nothing", "any"], 0),
            ("Type the symbol that starts the return type", "function f()___ number { return 1; }", None, [":"]),
            ("What does void mean?", "", ["The function returns nothing", "The function is private", "It never ends", "It returns null"], 0)],
         "Functions annotate parameters and the return type: <b>(a: number): number</b>. <b>void</b> means nothing is returned. Parameters can be optional (<b>b?: number</b>) or have defaults. Arrow functions work too: <b>(x: number) =&gt; x * 2</b>.",
         "function add(a: number, b: number): number {\n    return a + b;\n}\nconst dbl = (x: number) => x * 2;"),
        ("Interfaces", "🧩", [
            ("Which keyword describes an object's shape?", "", ["interface", "shape", "struct", "blueprint"], 0),
            ("Type the symbol that makes a property optional", "name___: string", None, ["?"]),
            ("When are types checked?", "", ["At compile time", "Only at runtime", "Never", "While running tests"], 0)],
         "An <b>interface</b> describes the shape of an object: <b>interface User { name: string; age?: number }</b>. <b>?</b> marks optional properties. Types exist only at COMPILE time and disappear in the JavaScript output. <b>type</b> aliases work similarly.",
         'interface User {\n    name: string;\n    age?: number;\n}\nconst u: User = { name: "Ada" };'),
        ("React Components", "🎨", [
            ("What is a React component?", "", ["A function that returns UI", "A database table", "A CSS file", "A compiler"], 0),
            ("Type the file extension for TypeScript with JSX", "App.___", None, ["tsx"]),
            ("Which hook stores state?", "", ["useState", "useStore", "useData", "setState"], 0)],
         "<b>React</b> builds interfaces from <b>components</b>: functions that return JSX markup. <b>.tsx</b> files allow TypeScript plus JSX. Type <b>props</b> with an interface. <b>useState</b> stores data that re-renders the component when it changes.",
         "interface Props { name: string }\n\nfunction Hello({ name }: Props) {\n    const [n, setN] = useState(0);\n    return <h1>Hi {name} {n}</h1>;\n}"),
        ("Node & Express", "🗄️", [
            ("What is Express?", "", ["A Node.js web framework", "A database", "A browser", "A CSS tool"], 0),
            ("Type the method that handles GET requests", "app.___('/', handler)", None, ["get"]),
            ("Which package manager installs Express?", "", ["npm", "pip", "cargo", "gem"], 0)],
         "<b>Node.js</b> runs compiled TypeScript on servers. <b>Express</b> is a tiny web framework: <b>app.get(path, handler)</b> answers GET requests and <b>res.json(data)</b> replies with JSON. Install packages with <b>npm</b> and add <b>@types/...</b> for type definitions.",
         "app.get('/hello', (req, res) => {\n    res.json({ msg: 'hi' });\n});\napp.listen(3000);")]),
}
for _n, (_ic, _c, _ls) in NEWL2.items():
    LANGS[_n] = (_ic, _c, [SHARED[:3]] + [l[:3] for l in _ls])
    TEACH[_n] = [SHARED[3:]] + [l[3:] for l in _ls]


NEW4 = {
    "Kotlin": ("🟣", "#7f52ff", [
        ("Hello, World!", "👋", [
            ("Which function is the entry point?", "", ["fun main()", "def main()", "void main()", "start()"], 0),
            ("Type the function that prints a line", '___("Hi")', None, ["println"]),
            ("Do Kotlin statements need semicolons?", "", ["No", "Yes", "Only in loops", "Only in classes"], 0)],
         "Kotlin runs on the JVM and is the preferred language for Android. Programs start in <b>fun main()</b>. <b>println()</b> prints a line and semicolons are optional.",
         'fun main() {\n    println("Hello, World!")\n}'),
        ("Variables & Types", "📦", [
            ("Which keyword makes a read-only variable?", "", ["val", "var", "let", "final"], 0),
            ("Type the keyword for a changeable variable", "___ x = 5", None, ["var"]),
            ("What type does val n = 5 get?", "", ["Int", "Fails", "String", "Float"], 0)],
         "<b>val</b> is read-only and <b>var</b> can change. Types are inferred: <b>val n = 5</b> is an Int. Types: <b>Int</b>, <b>Double</b>, <b>Boolean</b>, <b>String</b>. Strings embed values with <b>$name</b>.",
         'val name = "Ada"\nvar age = 20\nage += 1\nprintln("$name is $age")'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 0),
            ("Type the keyword for the other branch", "if (x > 1) { } ___ { }", None, ["else"]),
            ("Which is Kotlin's switch-like keyword?", "", ["when", "switch", "match", "select"], 0)],
         "Operators: <b>+ - * / %</b>; Int division truncates. <b>if</b> is an expression: <b>val s = if (x &gt; 5) 1 else 2</b>. <b>when</b> replaces switch. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>.",
         'val x = 7\nval s = if (x % 2 == 0) "even" else "odd"\nprintln(s)'),
        ("Loops", "🔁", [
            ("What does 1..3 contain?", "", ["1, 2, 3", "1, 2", "2, 3", "0, 1, 2"], 0),
            ("Type the keyword for looping over items", "for (x ___ list)", None, ["in"]),
            ("Which loop checks a condition first?", "", ["while", "do", "loop", "repeat"], 0)],
         "<b>for (i in 1..3)</b> loops over a range including 3; <b>until</b> excludes the end. <b>for (x in list)</b> visits items. <b>while</b> repeats on a condition and <b>break</b> / <b>continue</b> work as usual.",
         "for (i in 1..3) {\n    println(i)\n}\nfor (x in listOf(5, 6)) println(x)"),
        ("Functions", "⚙️", [
            ("What does this return?", "fun add(a: Int, b: Int): Int = a + b", ["a + b", "nothing", "a", "an error"], 0),
            ("Type the keyword that declares a function", "___ greet() {}", None, ["fun"]),
            ("Where does the return type go?", "", ["After the parameters", "Before fun", "Inside the body", "Nowhere"], 0)],
         "Functions use <b>fun</b>, typed parameters and a return type after <b>:</b>. One-liners use <b>=</b>. Parameters can have default values and be named when calling.",
         "fun add(a: Int, b: Int): Int {\n    return a + b\n}\nfun twice(x: Int) = x * 2"),
        ("Classes & Null Safety", "🐶", [
            ("Which type can hold null?", "", ["String?", "String", "Int", "val"], 0),
            ("Type the keyword that defines a class", "___ Dog(val name: String)", None, ["class"]),
            ("What does ?. do?", "", ["Safe call (skips null)", "Compares", "Casts", "Declares"], 0)],
         "A <b>class</b> can declare properties in its constructor: <b>class Dog(val name: String)</b>. Kotlin is <b>null-safe</b>: <b>String</b> can't be null, <b>String?</b> can. Use <b>?.</b> to call safely and <b>?:</b> for a default.",
         'class Dog(val name: String) {\n    fun bark() = println("$name woofs")\n}\nval s: String? = null\nprintln(s?.length ?: 0)'),
        ("Jetpack Compose", "📱", [
            ("What is Jetpack Compose?", "", ["Android's modern UI toolkit", "A database", "A compiler", "A game engine"], 0),
            ("Type the annotation that marks a Compose function", "@___\nfun Hello() {}", None, ["Composable"]),
            ("What is an Activity?", "", ["One screen of an app", "A database", "A loop", "A file"], 0)],
         "Android UIs are built with <b>Jetpack Compose</b>: functions marked <b>@Composable</b> describe the screen. State lives in <b>remember { mutableStateOf(..) }</b> and the UI redraws when it changes. An <b>Activity</b> hosts your screens.",
         '@Composable\nfun Counter() {\n    var n by remember { mutableStateOf(0) }\n    Button(onClick = { n++ }) { Text("Count $n") }\n}'),
        ("Coroutines & Ktor", "🗄️", [
            ("Which framework is popular for Kotlin servers?", "", ["Ktor", "Django", "Rails", "Laravel"], 0),
            ("Type the keyword that lets a function pause", "___ fun load()", None, ["suspend"]),
            ("What are coroutines for?", "", ["Lightweight async work", "Styling", "Compiling", "Printing"], 0)],
         "<b>Coroutines</b> are Kotlin's lightweight async tools: <b>suspend</b> functions can pause without blocking a thread and <b>launch</b> starts one. <b>Ktor</b> is a Kotlin web framework where you declare routes.",
         'suspend fun load(): String {\n    delay(1000)\n    return "done"\n}\nGlobalScope.launch { println(load()) }')]),
    "Swift": ("🍎", "#fb7185", [
        ("Hello, World!", "👋", [
            ("Which prints a line?", "", ['print("Hi")', 'println("Hi")', 'echo "Hi"', 'console.log("Hi")'], 0),
            ("Type the function that prints", '___("Hi")', None, ["print"]),
            ("Do Swift statements need semicolons?", "", ["No", "Yes", "Only in classes", "Always"], 0)],
         "Swift is Apple's language for iPhone, iPad and Mac apps. Top-level code runs from the top and <b>print()</b> shows output. Semicolons are optional. Swift is statically typed and very safe.",
         'print("Hello, World!")'),
        ("Variables & Types", "📦", [
            ("Which keyword makes a constant?", "", ["let", "var", "const", "final"], 0),
            ("Type the keyword for a changeable variable", "___ x = 5", None, ["var"]),
            ("What type is 3.14 by default?", "", ["Double", "Int", "String", "Float32"], 0)],
         "<b>let</b> declares a constant and <b>var</b> a variable. Swift infers types: <b>Int</b>, <b>Double</b>, <b>Bool</b>, <b>String</b>. Insert values into text with a backslash and brackets: string interpolation.",
         'let name = "Ada"\nvar age = 20\nage += 1\nprint("\\(name) is \\(age)")'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 0),
            ("Type the keyword for the other branch", "if x > 1 { } ___ { }", None, ["else"]),
            ("Do Swift if conditions need brackets?", "", ["No", "Yes", "Only with else", "Only in loops"], 0)],
         "Int division truncates: <b>7 / 2</b> is 3. <b>if</b> conditions need no brackets but braces are required. <b>switch</b> must cover every case and doesn't fall through. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>.",
         'let x = 7\nif x % 2 == 0 {\n    print("even")\n} else {\n    print("odd")\n}'),
        ("Loops", "🔁", [
            ("What does 1...3 contain?", "", ["1, 2, 3", "1, 2", "2, 3", "0, 1, 2"], 0),
            ("Type the keyword for looping over items", "for x ___ list {}", None, ["in"]),
            ("What does 1..<3 contain?", "", ["1, 2", "1, 2, 3", "2, 3", "1"], 0)],
         "<b>for i in 1...3</b> includes 3; <b>1..&lt;3</b> stops before 3. <b>for x in array</b> visits items and <b>while</b> repeats on a condition. <b>break</b> and <b>continue</b> work as usual.",
         "for i in 1...3 {\n    print(i)\n}\nfor x in [5, 6] {\n    print(x)\n}"),
        ("Functions", "⚙️", [
            ("What does this return?", "func add(a: Int, b: Int) -> Int {\n    return a + b\n}", ["a + b", "nothing", "a", "an error"], 0),
            ("Type the symbol before the return type", "func f() ___ Int { 5 }", None, ["->"]),
            ("Which keyword declares a function?", "", ["func", "fun", "def", "fn"], 0)],
         "Functions use <b>func</b>, labeled parameters and a return type after <b>-&gt;</b>. Callers write the labels: <b>add(a: 1, b: 2)</b>. Use <b>_</b> to drop a label.",
         "func add(a: Int, b: Int) -> Int {\n    return a + b\n}\nprint(add(a: 2, b: 3))"),
        ("Structs & Optionals", "🧩", [
            ("What is an Optional?", "", ["A value that may be nil", "A loop", "A class", "A comment"], 0),
            ("Type the keyword that defines a struct", "___ Point { var x = 0 }", None, ["struct"]),
            ("What does ! do after an optional?", "", ["Force-unwraps it", "Negates it", "Compares it", "Deletes it"], 0)],
         "A <b>struct</b> groups values and is copied when passed around. An <b>Optional</b> (<b>Int?</b>) may hold a value or <b>nil</b>. Unwrap safely with <b>if let</b>; <b>!</b> force-unwraps and crashes if nil.",
         "struct Point {\n    var x = 0\n    var y = 0\n}\nvar n: Int? = nil\nif let v = n { print(v) }"),
        ("SwiftUI", "📱", [
            ("What is SwiftUI?", "", ["Apple's modern UI framework", "A database", "A compiler", "A game engine"], 0),
            ("Type the protocol every SwiftUI screen adopts", "struct V: ___ { }", None, ["View"]),
            ("Which property wrapper holds changing data?", "", ["@State", "@Static", "@Const", "@Data"], 0)],
         "<b>SwiftUI</b> builds screens by declaring views: <b>Text</b>, <b>Button</b>, <b>VStack</b>. A screen is a struct that adopts <b>View</b> and returns its <b>body</b>. <b>@State</b> stores data that makes the view redraw when it changes.",
         'struct Counter: View {\n    @State var n = 0\n    var body: some View {\n        Button("Count \\(n)") { n += 1 }\n    }\n}'),
        ("Protocols & Extensions", "🧰", [
            ("What is a protocol?", "", ["A list of required methods", "A loop", "A comment", "A network"], 0),
            ("Type the keyword that defines a protocol", "___ Drawable { }", None, ["protocol"]),
            ("What does extension do?", "", ["Adds methods to an existing type", "Deletes a type", "Makes a loop", "Imports a file"], 0)],
         "A <b>protocol</b> lists methods a type must provide, like an interface. Any struct or class can <b>conform</b> to it. An <b>extension</b> adds new methods to an existing type, and <b>generics</b> let one function work for many types.",
         "protocol Drawable {\n    func draw()\n}\nextension Int {\n    func double() -> Int { self * 2 }\n}")]),
    "Ruby": ("🛤️", "#be123c", [
        ("Hello, World!", "👋", [
            ("Which prints a line?", "", ['puts "Hi"', 'print("Hi");', 'console.log("Hi")', 'echo "Hi"'], 0),
            ("Type the method that prints a line", "___ 'Hi'", None, ["puts"]),
            ("Do Ruby statements need semicolons?", "", ["No", "Yes", "Always", "Only in loops"], 0)],
         "Ruby is a friendly language built for programmer happiness and it powers Rails. <b>puts</b> prints a line. Everything is an object, semicolons aren't needed and brackets are often optional.",
         'puts "Hello, World!"'),
        ("Variables & Types", "📦", [
            ("How do you make a variable?", "", ["x = 5", "let x = 5", "var x = 5", "int x = 5"], 0),
            ("Type the method that converts to a string", "5.___", None, ["to_s"]),
            ("How do you embed a value in a string?", "", ['"Hi #{name}"', '"Hi ${name}"', '"Hi %name"', '"Hi (name)"'], 0)],
         "No keyword needed: <b>x = 5</b>. Types: Integer, Float, String, true/false and <b>nil</b>. Double-quoted strings interpolate with <b>#{...}</b>. Symbols like <b>:name</b> are lightweight labels.",
         'name = "Ada"\nage = 20\nputs "#{name} is #{age}"'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 0),
            ("Type the keyword that closes an if block", "if x > 1\n  puts 1\n___", None, ["end"]),
            ("Which keyword means otherwise-if?", "", ["elsif", "elif", "else if", "elseif"], 0)],
         "Integer division truncates: <b>7 / 2</b> is 3. <b>if / elsif / else</b> blocks close with <b>end</b>. Modifiers read like English: <b>puts x if x &gt; 1</b>. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>.",
         'x = 7\nif x % 2 == 0\n  puts "even"\nelse\n  puts "odd"\nend'),
        ("Loops", "🔁", [
            ("Which method repeats 3 times?", "", ["3.times", "3.loop", "repeat 3", "for 3"], 0),
            ("Type the method that visits each item", "[1, 2].___ { |x| puts x }", None, ["each"]),
            ("What does 1..3 contain?", "", ["1, 2, 3", "1, 2", "2, 3", "0, 1, 2"], 0)],
         "Ruby loops with blocks: <b>3.times { }</b>, <b>[1, 2].each { |x| ... }</b> and ranges <b>1..3</b> (includes 3). <b>while</b> works too, and <b>break</b> / <b>next</b> exit or skip.",
         '3.times { puts "hi" }\n[5, 6].each do |x|\n  puts x\nend\n(1..3).each { |i| puts i }'),
        ("Methods", "⚙️", [
            ("Which keyword defines a method?", "", ["def", "fn", "func", "function"], 0),
            ("What does this return?", "def add(a, b)\n  a + b\nend", ["a + b", "nothing", "nil", "an error"], 0),
            ("Type the keyword that ends a method", "def f\n  1\n___", None, ["end"])],
         "Methods start with <b>def</b> and end with <b>end</b>. The last expression is returned automatically. Parameters can have defaults, and brackets are optional when calling.",
         "def add(a, b = 1)\n  a + b\nend\nputs add(2, 3)"),
        ("Classes", "🐶", [
            ("Which keyword defines a class?", "", ["class", "struct", "def class", "object"], 0),
            ("Type the method name used as the constructor", "def ___(name)", None, ["initialize"]),
            ("What does @name hold?", "", ["An instance variable", "A global", "A constant", "A symbol"], 0)],
         "A <b>class</b> bundles data and methods. <b>initialize</b> is the constructor and variables starting with <b>@</b> belong to one object. <b>attr_reader</b> creates getters. Create objects with <b>.new</b>.",
         'class Dog\n  attr_reader :name\n  def initialize(name)\n    @name = name\n  end\n  def bark = puts("#{@name} woofs")\nend\nDog.new("Rex").bark'),
        ("Rails Basics", "🌐", [
            ("What is Rails?", "", ["A web framework for Ruby", "A database", "A compiler", "A game engine"], 0),
            ("Type the command that creates a new Rails app", "rails ___ blog", None, ["new"]),
            ("Which pattern does Rails follow?", "", ["MVC", "MVP", "CLI", "ETL"], 0)],
         "<b>Rails</b> builds websites with the <b>MVC</b> pattern: <b>Models</b> hold data, <b>Views</b> show pages and <b>Controllers</b> handle requests. Conventions mean less setup. <b>rails new</b> creates an app and <b>rails server</b> runs it.",
         "class PostsController < ApplicationController\n  def index\n    @posts = Post.all\n  end\nend"),
        ("Scripting", "🧰", [
            ("Which class reads a file?", "", ["File", "Disk", "Reader", "IO.get"], 0),
            ("Type the method that splits text", "'a,b'.___(',')", None, ["split"]),
            ("What is a gem?", "", ["A packaged Ruby library", "A bug", "A loop", "A variable"], 0)],
         "Ruby is great for scripts. <b>File.read(name)</b> loads text, <b>split</b> cuts a string into an array and <b>map</b> / <b>select</b> transform lists. A <b>gem</b> is a packaged library installed with <b>gem install</b>.",
         'text = File.read("a.txt")\nwords = text.split\nputs words.map(&:upcase).first(3)')]),
}
for _n, (_ic, _c, _ls) in NEW4.items():
    LANGS[_n] = (_ic, _c, [SHARED[:3]] + [l[:3] for l in _ls])
    TEACH[_n] = [SHARED[3:]] + [l[3:] for l in _ls]
    TRUNKS[_n] = T2
BR.update({"Kotlin": [("Android", "📱", [("l", 7)]), ("Backend", "🗄️", [("l", 8)])],
           "Swift": [("iOS", "📱", [("l", 7)]), ("Craft", "🧰", [("l", 8)])],
           "Ruby": [("Web", "🌐", [("l", 7)]), ("Scripting", "🧰", [("l", 8)])]})
STARTER.update({
    "Kotlin": ["fun main() {\n}\n", "fun main() {\n    for (i in 1..15) {\n    }\n}\n", "fun main() {\n    var a = 0\n    var b = 1\n    for (i in 1..10) {\n    }\n}\n"],
    "Swift": ["print()\n", "for i in 1...15 {\n}\n", "var a = 0\nvar b = 1\nfor _ in 1...10 {\n}\n"],
    "Ruby": ["puts\n", "(1..15).each do |i|\nend\n", "a, b = 0, 1\n10.times do\nend\n"],
})
PRINT.update({"Kotlin": r"\bprintln?\s*\(", "Swift": r"\bprint\s*\(", "Ruby": r"\b(puts|print|p)\b[ (]"})

SH = [
    ("Big-O & Speed", "⏱️", [
        ("Which grows slowest as data grows?", "", ["O(1)", "O(n)", "O(n²)", "O(2ⁿ)"], 0),
        ("Searching an unsorted list item by item is...", "", ["O(n)", "O(1)", "O(log n)", "O(n²)"], 0),
        ("Binary search needs the data to be...", "", ["Sorted", "Unique", "Small", "Text"], 0),
        ("Type the letter used in Big-O notation", "___(n)", None, ["O"])],
     "<b>Big-O</b> describes how a program's work grows as the input grows. <b>O(1)</b> is constant, <b>O(log n)</b> halves the problem each step (binary search), <b>O(n)</b> touches every item once and <b>O(n²)</b> compares every pair (nested loops). Faster growth means slower programs on big data.",
     "O(1)      get item by index\nO(log n)  binary search\nO(n)      loop through a list\nO(n²)     nested loops"),
    ("Data Structures", "🏗️", [
        ("Which structure is last-in, first-out?", "", ["Stack", "Queue", "Array", "Tree"], 0),
        ("Which is first-in, first-out?", "", ["Queue", "Stack", "Set", "Map"], 0),
        ("Which gives fast lookup by key?", "", ["Hash map", "Stack", "Queue", "Linked list"], 0),
        ("Type the structure of nodes connected by links", "linked ___", None, ["list"])],
     "<b>Stacks</b> are last-in-first-out (the undo button). <b>Queues</b> are first-in-first-out (a waiting line). <b>Hash maps</b> look up values by key almost instantly. <b>Trees</b> organize data in branches and <b>linked lists</b> chain nodes together.",
     "stack:  push, pop (top only)\nqueue:  enqueue, dequeue\nmap:    key -> value\ntree:   root -> children"),
    ("Git & Teamwork", "🌿", [
        ("Which command saves a snapshot?", "", ["git commit", "git push", "git clone", "git init"], 0),
        ("Type the command that sends commits to a server", "git ___", None, ["push"]),
        ("What is a branch?", "", ["A separate line of work", "A bug", "A server", "A file type"], 0),
        ("Which command downloads a repository?", "", ["git clone", "git commit", "git add", "git merge"], 0)],
     "<b>Git</b> tracks changes to your code. <b>git add</b> stages files, <b>git commit</b> saves a snapshot, <b>git push</b> uploads it and <b>git clone</b> downloads a repository. A <b>branch</b> lets you try ideas safely and <b>merge</b> brings them back together.",
     'git init\ngit add .\ngit commit -m "first"\ngit branch feature\ngit push'),
    ("Clean Code", "✨", [
        ("Which variable name is best?", "", ["total_price", "x", "tp", "thing"], 0),
        ("What does DRY stand for?", "", ["Don't Repeat Yourself", "Do Run Yearly", "Data Rarely Yields", "Debug Right Yesterday"], 0),
        ("A function should ideally do...", "", ["One thing", "Everything", "Nothing", "Ten things"], 0),
        ("Type the practice of testing small pieces of code", "unit ___", None, ["tests", "test"])],
     "<b>Clean code</b> is easy to read. Use clear names, keep functions small and focused, and follow <b>DRY</b>: Don't Repeat Yourself. Write comments for WHY, not what. <b>Unit tests</b> check small pieces automatically so changes don't break things.",
     "bad:   def f(x): ...\ngood:  def total_price(items): ..."),
]
UN.update({n: UN2 for n in NEW4})
OLDUN = [(0, "Unit 1", "Foundations"), (8, "Unit 2", "Logic & Loops"), (12, "Unit 3", "Data & Functions"), (16, "Unit 4", "Mastery"),
         ("f", "Crossroads", "Choose Your Field"), ("e", "Boss", "Boss 1")]
for _n in list(LANGS):
    _b = len(LANGS[_n][2])
    for _t, _e, _qs, _tx, _cd in SH:
        LANGS[_n] = (LANGS[_n][0], LANGS[_n][1], LANGS[_n][2] + [(_t, _e, _qs)])
        TEACH[_n].append((_tx, _cd))
    _old = len(TRUNKS[_n])
    TRUNKS[_n] = TRUNKS[_n] + [("l", _b + i) for i in range(len(SH))]
    UN[_n] = list(UN.get(_n, OLDUN)) + [(_old, "Bonus", "CS Concepts")]


LP = r"\b(for|foreach|while|each|times|upto|loop|repeat)\b"
DEFRX = r"\b(def|fn|func|function|fun)\s+\w+|=>|\bfunction\s*\(|\b(int|void|double|float|long|string|String|bool|boolean|char|auto)\s+\w+\s*\([^)]*\)\s*(\{|=>)"
REV = r"reverse|reversed|\[::-1\]|\brev\b|strrev|\.chars\(\)|\.length|len\(|\.count|size|\.split"
XPJ = [
    ("Hello, You", "👋", "Store a name in a variable and print a greeting that says <b>Hello</b> and uses that variable.", "easy", 20, 40,
     [("prints something", "PRINT"), ("stores a name in a variable", r"(=|<-)\s*[\"'][^\"']+[\"']"), ("says Hello", r"Hello")]),
    ("Times Table", "✖️", "Print the <b>7 times table</b> from 7 × 1 to 7 × 10, one line each, using a loop.", "easy", 20, 40,
     [("prints something", "PRINT"), ("uses a loop", LP), ("multiplies", r"\*"), ("uses the number 7", r"\b7\b"), ("goes up to 10", r"\b(10|11)\b")]),
    ("Even or Odd", "🔢", "For each number from 1 to 10 print whether it is <b>even</b> or <b>odd</b>.", "easy", 25, 45,
     [("prints something", "PRINT"), ("uses a loop", LP), ("uses the remainder %2", r"%\s*2\b|\b(rem|mod)\(\s*\w+\s*,\s*2\s*\)"), ("uses if", r"\b(if|cond|case|when|match|unless)\b"), ("prints even and odd", r"even[\s\S]*odd|odd[\s\S]*even")]),
    ("Sum 1 to 100", "➕", "Add all the numbers from 1 to 100 with a loop and print the total. It should be 5050.", "medium", 35, 60,
     [("prints something", "PRINT"), ("uses a loop", LP), ("adds up a total", r"\+=|\bsum\b|\btotal\b|=\s*\w+\s*\+"), ("counts to 100", r"\b(100|101)\b")]),
    ("Reverse a Word", "🔄", "Reverse the word <b>codingo</b> and print the result.", "medium", 35, 60,
     [("prints something", "PRINT"), ("uses the word codingo", r"codingo"), ("reverses it somehow", REV)]),
    ("Prime Hunter", "🔍", "Print all prime numbers up to 30. A prime is only divisible by 1 and itself, so test with a loop inside a loop.", "medium", 45, 80,
     [("prints something", "PRINT"), ("uses two loops", LP + r"[\s\S]*" + LP), ("uses the remainder %", r"%|\b(rem|mod)\("), ("uses if", r"\b(if|cond|case|when|match|unless)\b"), ("goes up to 30", r"\b(30|31)\b")]),
    ("Temperature Table", "🌡️", "Print Celsius from 0 to 100 in steps of 10 with the Fahrenheit value (F = C × 9 / 5 + 32).", "medium", 40, 70,
     [("prints something", "PRINT"), ("uses a loop", LP), ("converts with 9/5", r"9\s*/\s*5|1\.8|\*\s*9"), ("adds 32", r"\+\s*32")]),
    ("Factorial", "❗", "Write a <b>function</b> that returns n! (1 × 2 × ... × n) and print factorial(5). It should be 120.", "hard", 60, 100,
     [("prints something", "PRINT"), ("defines a function", "FUNC"), ("multiplies", r"\*"), ("loops or recurses", LP + r"|\w+\s*\(\s*\w+\s*-\s*1\s*\)"), ("tests with 5", r"\b5\b")]),
    ("Palindrome Checker", "🪞", "Write a <b>function</b> that checks if a word reads the same backwards. Test it on <b>level</b> and <b>coding</b>.", "hard", 65, 110,
     [("prints something", "PRINT"), ("defines a function", "FUNC"), ("tests level", r"level"), ("tests coding", r"coding"), ("compares two values", r"==|equals|eql"), ("reverses text", REV)]),
    ("Bank Account", "🏦", "Create a <b>class or struct</b> for a bank account with a <b>balance</b>, <b>deposit</b> and <b>withdraw</b>. Make one, deposit, withdraw and print the balance.", "hard", 80, 140,
     [("prints something", "PRINT"), ("defines a class/struct/type", r"class|struct|\btype\b|setmetatable|R6|defmodule|\bobject\b"), ("has a balance", r"balance"), ("has deposit", r"deposit"), ("has withdraw", r"withdraw")]),
]
TIER = {"easy": ("🟢 Easy", "#58cc02"), "medium": ("🟡 Medium", "#f59e0b"), "hard": ("🔴 Hard", "#ef4444")}


def skeleton(lang, todo):
    ln = ("# " if lang in ("Python", "Ruby", "R", "Julia", "Elixir") else "-- " if lang == "Lua" else "// ") + todo
    w = {"C": "#include <stdio.h>\n\nint main(void) {\n    %s\n    return 0;\n}\n",
         "C++": "#include <iostream>\n#include <string>\n\nint main() {\n    %s\n    return 0;\n}\n",
         "Java": "public class Main {\n    public static void main(String[] args) {\n        %s\n    }\n}\n",
         "C#": "using System;\n\nclass Program {\n    static void Main() {\n        %s\n    }\n}\n",
         "Rust": "fn main() {\n    %s\n}\n", "Go": 'package main\n\nimport "fmt"\n\nfunc main() {\n    %s\n}\n', "Kotlin": "fun main() {\n    %s\n}\n"}
    return ({**w, "PHP": "<?php\n%s\n", "Dart": "void main() {\n    %s\n}\n", "Scala": "object Main extends App {\n    %s\n}\n"}).get(lang, "%s\n") % ln


NEW5 = {
    "PHP": ("🐘", "#8892bf", [
        ("Hello, World!", "👋", [
            ("Which tag starts PHP code?", "", ["<?php", "<php>", "<%", "{php}"], 0),
            ("Type the keyword that prints text", '___ "Hi";', None, ["echo"]),
            ("What ends each PHP statement?", "", [";", ".", ":", "!"], 0)],
         "PHP runs on web servers and powers WordPress. Code lives after the <b>&lt;?php</b> tag. <b>echo</b> prints text and every statement ends with <b>;</b>.",
         '<?php\necho "Hello, World!";'),
        ("Variables & Types", "📦", [
            ("Which symbol starts every PHP variable?", "", ["$", "@", "#", "&"], 0),
            ("Type the operator that joins strings", "'a' ___ 'b'", None, ["."]),
            ("Which is valid?", "", ["$age = 20;", "age = 20;", "var age = 20;", "int age = 20;"], 0)],
         "Variables start with <b>$</b>: <b>$age = 20;</b>. Types are dynamic: int, float, string, bool, array. Join strings with <b>.</b> and insert variables inside double quotes.",
         '$name = "Ada";\n$age = 20;\necho "$name is $age";\necho "Hi " . $name;'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3.5", "3", "4", "error"], 0),
            ("Type the keyword for otherwise-if", "if ($a) { } ___ ($b) { }", None, ["elseif"]),
            ("Which operator compares value AND type?", "", ["===", "==", "=", "=>"], 0)],
         "Arithmetic: <b>+ - * / %</b> (<b>/</b> gives 3.5). <b>if / elseif / else</b> branch. <b>===</b> compares value and type; <b>==</b> converts types first. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>.",
         '$x = 7;\nif ($x % 2 == 0) {\n    echo "even";\n} else {\n    echo "odd";\n}'),
        ("Loops", "🔁", [
            ("Which loop walks through an array?", "", ["foreach", "each", "loop", "iterate"], 0),
            ("Type the keyword that leaves a loop", "", None, ["break"]),
            ("How many times does this run?", "for ($i = 0; $i < 3; $i++) { }", ["3", "2", "4", "0"], 0)],
         "<b>for</b>, <b>while</b> and <b>do-while</b> work like in C. <b>foreach ($items as $x)</b> visits every element of an array. <b>break</b> exits and <b>continue</b> skips to the next round.",
         "for ($i = 1; $i <= 3; $i++) {\n    echo $i;\n}\nforeach ([5, 6] as $x) {\n    echo $x;\n}"),
        ("Functions", "⚙️", [
            ("Which keyword declares a function?", "", ["function", "fun", "def", "func"], 0),
            ("What does this print?", "function add($a, $b) { return $a + $b; }\necho add(2, 3);", ["5", "23", "error", "nothing"], 0),
            ("Type the keyword that sends a value back", "", None, ["return"])],
         "Functions use <b>function</b>, parameters with <b>$</b> and <b>return</b>. Parameters can have defaults and types: <b>function f(int $n): int</b>. Variables inside a function are local.",
         "function add(int $a, int $b): int {\n    return $a + $b;\n}\necho add(2, 3);"),
        ("Classes & Objects", "🐶", [
            ("Which keyword creates an object?", "", ["new", "make", "create", "object"], 0),
            ("Type the symbol that reads a property", "$this___name", None, ["->"]),
            ("Which method is the constructor?", "", ["__construct", "init", "new", "constructor"], 0)],
         "A <b>class</b> bundles data and methods. <b>__construct</b> runs when you create an object with <b>new</b>. Read members with <b>-&gt;</b>: <b>$this-&gt;name</b>. <b>public</b> / <b>private</b> control access.",
         'class Dog {\n    public function __construct(private string $name) {}\n    public function bark() { echo $this->name . " woofs"; }\n}\n(new Dog("Rex"))->bark();'),
        ("Web & Laravel", "🌐", [
            ("What is Laravel?", "", ["A PHP web framework", "A database", "A browser", "A CSS tool"], 0),
            ("Which superglobal holds submitted form data?", "", ["$_POST", "$_FORM", "$_DATA", "$_SEND"], 0),
            ("What does MVC separate?", "", ["Data, views and logic", "Files and folders", "Users and admins", "Tests and code"], 0)],
         "PHP builds websites. <b>$_GET</b> and <b>$_POST</b> hold data sent by users, so always validate and escape it. <b>Laravel</b> is the popular framework using <b>MVC</b>: models, views, controllers. <b>WordPress</b> is also written in PHP.",
         '<?php\n$name = htmlspecialchars($_POST["name"] ?? "guest");\necho "Hello $name";'),
        ("PDO & Databases", "🗄️", [
            ("Which PHP class talks to databases?", "", ["PDO", "DBX", "SQLPHP", "Data"], 0),
            ("Type the SQL keyword that reads rows", "___ * FROM users", None, ["SELECT"]),
            ("Why use prepared statements?", "", ["They prevent SQL injection", "They are shorter", "They hide errors", "They are required"], 0)],
         "<b>PDO</b> connects PHP to databases like MySQL. <b>Prepared statements</b> send the query and the data separately, which prevents <b>SQL injection</b>. <b>SELECT</b> reads rows and <b>INSERT</b> adds them.",
         '$st = $pdo->prepare("SELECT * FROM users WHERE id = ?");\n$st->execute([5]);\n$row = $st->fetch();')]),
    "Dart": ("🎯", "#22d3ee", [
        ("Hello, World!", "👋", [
            ("Which function is the entry point?", "", ["void main()", "start()", "def main()", "fun run()"], 0),
            ("Type the function that prints", "___('Hi');", None, ["print"]),
            ("What ends each statement?", "", [";", ".", ":", "!"], 0)],
         "Dart is Google's language, used with <b>Flutter</b> to build mobile apps. Programs start in <b>main()</b>. <b>print()</b> shows output and statements end with <b>;</b>.",
         "void main() {\n  print('Hello, World!');\n}"),
        ("Variables & Types", "📦", [
            ("Which keyword infers the type?", "", ["var", "dyn", "let", "auto"], 0),
            ("Type the keyword for a compile-time constant", "___ pi = 3.14;", None, ["const"]),
            ("Which type holds text?", "", ["String", "Text", "string", "Str"], 0)],
         "<b>var</b> infers a type, or write it: <b>int</b>, <b>double</b>, <b>String</b>, <b>bool</b>. <b>final</b> sets a value once and <b>const</b> is fixed at compile time. Insert values with <b>$name</b>. Dart is null-safe: <b>String?</b> may be null.",
         "var name = 'Ada';\nint age = 20;\nfinal pi = 3.14;\nprint('$name is $age');"),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3.5", "3", "4", "error"], 0),
            ("Which operator does integer division?", "", ["~/", "//", "div", "%%"], 0),
            ("Type the keyword for the other branch", "if (x) { } ___ { }", None, ["else"])],
         "<b>/</b> always gives a double (7 / 2 is 3.5); <b>~/</b> gives the whole part. <b>%</b> is the remainder. <b>if / else</b> branch and <b>? :</b> is the ternary. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>.",
         "var x = 7;\nif (x % 2 == 0) {\n  print('even');\n} else {\n  print('odd');\n}\nprint(7 ~/ 2);"),
        ("Loops", "🔁", [
            ("Which loop visits every item?", "", ["for (var x in list)", "foreach x in list", "for x of list", "each list"], 0),
            ("Type the keyword that skips a round", "", None, ["continue"]),
            ("What does list.forEach do?", "", ["Runs a function for each item", "Sorts the list", "Deletes items", "Counts items"], 0)],
         "<b>for</b> and <b>while</b> work like in C. <b>for (var x in list)</b> visits every item and <b>list.forEach((x) =&gt; ...)</b> runs a function per item. <b>break</b> exits and <b>continue</b> skips.",
         "for (var i = 1; i <= 3; i++) {\n  print(i);\n}\nfor (var x in [5, 6]) {\n  print(x);\n}"),
        ("Functions", "⚙️", [
            ("What does this print?", "int add(int a, int b) => a + b;\nprint(add(2, 3));", ["5", "23", "error", "nothing"], 0),
            ("Type the symbol for one-line functions", "int sq(int n) ___ n * n;", None, ["=>"]),
            ("Where does the return type go?", "", ["Before the name", "After the name", "After the body", "Nowhere"], 0)],
         "Functions put the return type first: <b>int add(int a, int b)</b>. One-liners use <b>=&gt;</b>. Named parameters in braces are common in Flutter. Functions are values and can be passed around.",
         "int add(int a, int b) {\n  return a + b;\n}\nint twice(int x) => x * 2;"),
        ("Classes", "🐶", [
            ("Which keyword defines a class?", "", ["class", "struct", "object", "type"], 0),
            ("What does a leading underscore make a member?", "", ["Private to the library", "Public", "Static", "Constant"], 0),
            ("Type the keyword that inherits", "class B ___ A {}", None, ["extends"])],
         "A <b>class</b> bundles fields and methods. The constructor shortcut sets fields: <b>Dog(this.name);</b>. A leading <b>_</b> makes a member private. <b>extends</b> inherits from another class.",
         "class Dog {\n  final String name;\n  Dog(this.name);\n  void bark() => print('$name woofs');\n}\nDog('Rex').bark();"),
        ("Flutter Widgets", "📱", [
            ("What is Flutter?", "", ["A UI toolkit using Dart", "A database", "A compiler", "A game"], 0),
            ("Everything in Flutter is a...", "", ["Widget", "Table", "Object file", "Script"], 0),
            ("Type the class used for UI that changes", "class C extends ___ {}", None, ["StatefulWidget"])],
         "<b>Flutter</b> builds apps for phone, web and desktop from one Dart codebase. Everything is a <b>widget</b>: <b>Text</b>, <b>Column</b>, <b>Scaffold</b>. A <b>StatefulWidget</b> holds data that changes and <b>setState</b> redraws it.",
         "Column(\n  children: [\n    Text('Hello'),\n    ElevatedButton(onPressed: () {}, child: Text('Tap')),\n  ],\n)"),
        ("Async & Futures", "⚡", [
            ("What does await do?", "", ["Waits for a Future", "Starts a loop", "Defines a class", "Prints text"], 0),
            ("Type the keyword that marks an async function", "void f() ___ {}", None, ["async"]),
            ("Which type is a value that arrives later?", "", ["Future", "Timer", "Later", "Stream only"], 0)],
         "A <b>Future</b> is a value that arrives later (a download, a file read). Mark a function <b>async</b> and use <b>await</b> to wait. A <b>Stream</b> delivers many values over time. Wrap risky awaits in <b>try / catch</b>.",
         "Future<String> load() async {\n  await Future.delayed(Duration(seconds: 1));\n  return 'done';\n}")]),
    "Lua": ("🌙", "#6366f1", [
        ("Hello, World!", "👋", [
            ("Which prints a line?", "", ['print("Hi")', 'echo "Hi"', 'console.log("Hi")', 'puts "Hi"'], 0),
            ("Type the function that prints", '___("Hi")', None, ["print"]),
            ("Do Lua statements need semicolons?", "", ["No", "Yes", "Always", "Only in loops"], 0)],
         "Lua is a tiny, fast language used in games (Roblox, LÖVE) and embedded systems. <b>print()</b> shows output. Semicolons are optional and comments start with <b>--</b>.",
         'print("Hello, World!")'),
        ("Variables & Types", "📦", [
            ("Which keyword makes a local variable?", "", ["local", "let", "var", "my"], 0),
            ("Type the operator that joins strings", "'a' ___ 'b'", None, [".."]),
            ("What does an unset variable hold?", "", ["nil", "0", "empty string", "false"], 0)],
         "Variables are global unless declared <b>local</b>. Types: number, string, boolean, <b>nil</b> (no value), table and function. Join strings with <b>..</b>. Use <b>#</b> to get a length.",
         'local name = "Ada"\nlocal age = 20\nprint(name .. " is " .. age)\nprint(#name)'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3.5", "3", "4", "error"], 0),
            ("Type the keyword that closes an if block", "if x > 1 then\n  print(1)\n___", None, ["end"]),
            ("Which means not equal?", "", ["~=", "!=", "<>", "=/="], 0)],
         "<b>/</b> gives 3.5 and <b>//</b> gives the whole part. <b>if ... then ... elseif ... else ... end</b> branches. Not equal is <b>~=</b>. Logic uses the words <b>and</b>, <b>or</b>, <b>not</b>.",
         'local x = 7\nif x % 2 == 0 then\n  print("even")\nelse\n  print("odd")\nend'),
        ("Loops", "🔁", [
            ("What does for i = 1, 3 do loop over?", "", ["1, 2, 3", "1, 2", "0, 1, 2", "3 only"], 0),
            ("Type the keyword that ends a loop block", "for i = 1, 3 do\n  print(i)\n___", None, ["end"]),
            ("Which loop always runs at least once?", "", ["repeat ... until", "while", "for", "loop"], 0)],
         "<b>for i = 1, 3 do</b> counts from 1 to 3 inclusive. <b>for k, v in pairs(t)</b> walks a table. <b>while</b> checks first and <b>repeat ... until</b> runs at least once. <b>break</b> exits.",
         "for i = 1, 3 do\n  print(i)\nend\nfor _, x in ipairs({5, 6}) do\n  print(x)\nend"),
        ("Functions", "⚙️", [
            ("Which keyword defines a function?", "", ["function", "fun", "def", "func"], 0),
            ("What does this print?", "local function add(a, b)\n  return a + b\nend\nprint(add(2, 3))", ["5", "23", "nil", "error"], 0),
            ("Type the keyword that sends a value back", "", None, ["return"])],
         "Functions use <b>function ... end</b> and <b>return</b>. They are values, so you can store and pass them. A function can return several values at once: <b>return a, b</b>. Declare helpers with <b>local function</b>.",
         "local function add(a, b)\n  return a + b\nend\nlocal sq = function(x) return x * x end"),
        ("Tables", "🧩", [
            ("What is Lua's one data structure?", "", ["Table", "Array", "Class", "List"], 0),
            ("What index does the first array item have?", "", ["1", "0", "-1", "it depends"], 0),
            ("Type the function that attaches a metatable", "___(obj, mt)", None, ["setmetatable"])],
         "The <b>table</b> is Lua's only data structure: it works as array, dictionary and object. Arrays start at <b>1</b>! <b>#t</b> is the length and <b>table.insert</b> appends. <b>setmetatable</b> adds class-like behavior.",
         'local t = {10, 20, 30}\ntable.insert(t, 40)\nprint(#t, t[1])\nlocal p = {name = "Ada", age = 20}\nprint(p.name)'),
        ("Game Dev with LÖVE", "🎮", [
            ("What is LÖVE?", "", ["A 2D game framework using Lua", "A database", "A browser", "An editor"], 0),
            ("Type the LÖVE function that draws every frame", "function love.___()", None, ["draw"]),
            ("Which LÖVE function updates game logic?", "", ["love.update", "love.tick", "love.step", "love.run"], 0)],
         "<b>LÖVE</b> is a 2D game framework scripted in Lua. You define <b>love.load</b> (setup), <b>love.update(dt)</b> (logic every frame) and <b>love.draw</b> (rendering). <b>dt</b> is the time since the last frame, so movement stays smooth. Roblox uses a Lua dialect too.",
         "x = 0\nfunction love.update(dt)\n  x = x + 60 * dt\nend\nfunction love.draw()\n  love.graphics.rectangle('fill', x, 100, 40, 40)\nend"),
        ("Metatables & Modules", "🔧", [
            ("What does require do?", "", ["Loads a module", "Defines a class", "Starts a loop", "Prints text"], 0),
            ("Type the metatable key used for missing fields", "_____", None, ["index"]),
            ("What are metatables used for?", "", ["Custom table behavior", "Printing", "Loops", "Comments"], 0)],
         "A <b>module</b> is a file that returns a table; load it with <b>require</b>. <b>Metatables</b> customize tables: <b>__index</b> looks up missing fields (inheritance) and <b>__add</b> overloads +. This is how Lua builds classes.",
         "local Dog = {}\nDog.__index = Dog\nfunction Dog.new(n)\n  return setmetatable({name = n}, Dog)\nend\nfunction Dog:bark() print(self.name) end")]),
    "R": ("📊", "#2979ff", [
        ("Hello, World!", "👋", [
            ("Which prints a value?", "", ['print("Hi")', 'echo "Hi"', 'console.log("Hi")', 'puts "Hi"'], 0),
            ("Type the function that prints plain text", "___('Hi')", None, ["cat"]),
            ("What is R mainly used for?", "", ["Statistics and data analysis", "Mobile apps", "Games", "Operating systems"], 0)],
         "R is built for <b>statistics and data analysis</b>. <b>print()</b> shows a value and <b>cat()</b> prints plain text. Comments start with <b>#</b>. You can run R line by line in RStudio.",
         'print("Hello, World!")\ncat("Hi", "there\\n")'),
        ("Variables & Vectors", "📦", [
            ("Which operator assigns a value in R?", "", ["<-", "=>", ":=", "->>"], 0),
            ("Type the function that builds a vector", "x <- ___(1, 2, 3)", None, ["c"]),
            ("What does length(c(4, 5, 6)) give?", "", ["3", "6", "15", "1"], 0)],
         "Assign with <b>&lt;-</b> (or =). R's basic unit is the <b>vector</b>: <b>c(1, 2, 3)</b>. Types: numeric, character, logical (<b>TRUE</b> / <b>FALSE</b>) and <b>NA</b> for missing. Operations work on whole vectors at once.",
         'x <- c(4, 5, 6)\nname <- "Ada"\nprint(length(x))\nprint(x * 2)'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 %/% 2", ["3", "3.5", "4", "1"], 0),
            ("Type the operator for the remainder", "7 ___ 2", None, ["%%"]),
            ("Which is R's logical and for single values?", "", ["&&", "and", "&&&", "AND"], 0)],
         "<b>/</b> divides (3.5), <b>%/%</b> is integer division and <b>%%</b> the remainder. <b>if / else if / else</b> branch. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>. <b>ifelse()</b> works on whole vectors.",
         'x <- 7\nif (x %% 2 == 0) {\n  print("even")\n} else {\n  print("odd")\n}'),
        ("Loops", "🔁", [
            ("What does 1:3 produce?", "", ["1 2 3", "1 2", "0 1 2", "3"], 0),
            ("Type the keyword for looping over items", "for (x ___ c(1, 2))", None, ["in"]),
            ("What is often better than a loop in R?", "", ["Vectorised operations", "More loops", "Goto", "Recursion only"], 0)],
         "<b>for (i in 1:3)</b> loops over a sequence; <b>1:3</b> means 1, 2, 3. <b>while</b> repeats on a condition. In R you often skip loops: <b>sapply</b> and vectorised maths like <b>x * 2</b> are shorter and faster.",
         "for (i in 1:3) {\n  print(i)\n}\nx <- c(5, 6)\nprint(sapply(x, function(v) v * 2))"),
        ("Functions", "⚙️", [
            ("Which keyword creates a function?", "", ["function", "def", "fun", "func"], 0),
            ("What does this print?", "add <- function(a, b) {\n  a + b\n}\nprint(add(2, 3))", ["5", "23", "NULL", "error"], 0),
            ("Type the function that stops with an error", "___('bad input')", None, ["stop"])],
         "Create functions with <b>function(...)</b> and store them in a name: <b>add &lt;- function(a, b) { a + b }</b>. The last value is returned (or use <b>return()</b>). Arguments can have defaults. <b>stop()</b> raises an error.",
         "add <- function(a, b = 1) {\n  a + b\n}\nprint(add(2, 3))"),
        ("Lists & Data Frames", "🧩", [
            ("What is a data frame?", "", ["A table of rows and columns", "A loop", "A function", "A comment"], 0),
            ("Type the function that creates a data frame", "d <- ___(x = 1:3)", None, ["data.frame"]),
            ("Which symbol selects a column?", "", ["$", "@", "#", "&"], 0)],
         "A <b>list</b> holds mixed items. A <b>data.frame</b> is a table: each column is a vector. Select a column with <b>$</b> (<b>df$age</b>) or rows with <b>df[1, ]</b>. <b>head(df)</b> shows the first rows and <b>summary(df)</b> gives statistics.",
         'df <- data.frame(name = c("A", "B"), age = c(20, 30))\nprint(df$age)\nprint(mean(df$age))'),
        ("Data Analysis", "📊", [
            ("Which function gives the average?", "", ["mean", "avg", "average", "mid"], 0),
            ("Type the function that reads a CSV file", "___('data.csv')", None, ["read.csv"]),
            ("Which package is popular for data manipulation?", "", ["dplyr", "numpy", "pandas", "jquery"], 0)],
         "Real analysis starts with data: <b>read.csv()</b> loads a file into a data frame. Summaries: <b>mean</b>, <b>median</b>, <b>sd</b>. The <b>tidyverse</b> packages like <b>dplyr</b> filter, group and summarise data with readable pipelines using <b>%&gt;%</b>.",
         'df <- read.csv("data.csv")\nprint(mean(df$score))\nlibrary(dplyr)\ndf %>% filter(score > 50)'),
        ("Plots & Charts", "📈", [
            ("Which function draws a basic plot?", "", ["plot", "draw", "chart", "graph"], 0),
            ("Type the function that draws a histogram", "___(x)", None, ["hist"]),
            ("Which package makes polished charts?", "", ["ggplot2", "dplyr", "stringr", "shiny"], 0)],
         "<b>plot(x, y)</b> draws a scatter or line plot, <b>hist(x)</b> shows a distribution and <b>boxplot</b> compares groups. The <b>ggplot2</b> package builds beautiful layered charts. Good charts have titles, axis labels and a clear message.",
         'x <- c(1, 2, 3, 4)\ny <- c(2, 4, 5, 9)\nplot(x, y, main = "Growth")\nhist(y)')]),
}
for _n, (_ic, _c, _ls) in NEW5.items():
    LANGS[_n] = (_ic, _c, [SHARED[:3]] + [l[:3] for l in _ls])
    TEACH[_n] = [SHARED[3:]] + [l[3:] for l in _ls]
    TRUNKS[_n] = T2
    UN[_n] = UN2
BR.update({"PHP": [("Web", "🌐", [("l", 7)]), ("Database", "🗄️", [("l", 8)])], "Dart": [("Flutter", "📱", [("l", 7)]), ("Async", "⚡", [("l", 8)])],
           "Lua": [("Games", "🎮", [("l", 7)]), ("Metatables", "🔧", [("l", 8)])], "R": [("Data", "📊", [("l", 7)]), ("Plots", "📈", [("l", 8)])]})
STARTER.update({
    "PHP": ["<?php\n", "<?php\nfor ($i = 1; $i <= 15; $i++) {\n}\n", "<?php\n$a = 0;\n$b = 1;\nfor ($i = 0; $i < 10; $i++) {\n}\n"],
    "Dart": ["void main() {\n}\n", "void main() {\n  for (var i = 1; i <= 15; i++) {\n  }\n}\n", "void main() {\n  var a = 0, b = 1;\n  for (var i = 0; i < 10; i++) {\n  }\n}\n"],
    "Lua": ["print()\n", "for i = 1, 15 do\nend\n", "local a, b = 0, 1\nfor i = 1, 10 do\nend\n"],
    "R": ["print()\n", "for (i in 1:15) {\n}\n", "a <- 0\nb <- 1\nfor (i in 1:10) {\n}\n"],
})
PRINT.update({"PHP": r"\b(echo|print|printf|print_r|var_dump)\b", "Dart": r"\bprint\s*\(", "Lua": r"\bprint\s*\(", "R": r"\b(print|cat|message)\s*\("})
for _n in NEW5:
    _b = len(LANGS[_n][2])
    for _t, _e, _qs, _tx, _cd in SH:
        LANGS[_n] = (LANGS[_n][0], LANGS[_n][1], LANGS[_n][2] + [(_t, _e, _qs)])
        TEACH[_n].append((_tx, _cd))
    _old = len(TRUNKS[_n])
    TRUNKS[_n] = TRUNKS[_n] + [("l", _b + i) for i in range(len(SH))]
    UN[_n] = list(UN[_n]) + [(_old, "Bonus", "CS Concepts")]


TIPS.append("💡 Byte: tap a locked unit banner marked ⏩ to take a test and jump ahead!")


NEW6 = {
    "Julia": ("🔬", "#9558b2", [
        ("Hello, World!", "👋", [
            ("Which prints a line?", "", ['println("Hi")', 'echo "Hi"', 'console.log("Hi")', 'puts "Hi"'], 0),
            ("Type the function that prints a line", '___("Hi")', None, ["println"]),
            ("What is Julia known for?", "", ["Fast scientific computing", "Web styling", "Mobile games", "Databases"], 0)],
         "Julia is a fast language for science, data and maths. <b>println()</b> prints a line and no semicolons are needed. Comments start with <b>#</b>. It reads like Python but runs near C speed.",
         'println("Hello, World!")'),
        ("Variables & Types", "📦", [
            ("Does Julia need type declarations?", "", ["No, types are inferred", "Yes, always", "Only for strings", "Only for numbers"], 0),
            ("Type the keyword that makes a constant", "___ TAU2 = 6.28", None, ["const"]),
            ("How do you insert a value into a string?", "", ['"Hi $name"', '"Hi {name}"', '"Hi #{name}"', '"Hi %name"'], 0)],
         "Variables need no keyword: <b>x = 5</b>. Types: Int, Float64, String, Bool. Insert values with <b>$name</b> inside strings. <b>const</b> makes a global fixed. Names can even use Unicode like <b>π</b>.",
         'name = "Ada"\nage = 20\nprintln("$name is $age")'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3.5", "3", "4", "error"], 0),
            ("Type the function for integer division", "___(7, 2)", None, ["div"]),
            ("Type the keyword that closes an if block", "if x > 1\n  println(1)\n___", None, ["end"])],
         "<b>/</b> always gives a float (3.5); <b>div(7, 2)</b> gives 3 and <b>%</b> the remainder. <b>if / elseif / else</b> blocks close with <b>end</b>. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>.",
         'x = 7\nif x % 2 == 0\n    println("even")\nelse\n    println("odd")\nend'),
        ("Loops", "🔁", [
            ("What does 1:3 contain?", "", ["1, 2, 3", "1, 2", "0, 1, 2", "3"], 0),
            ("Type the keyword for looping over items", "for x ___ [1, 2]", None, ["in"]),
            ("What closes a for loop?", "", ["end", "}", "next", "done"], 0)],
         "<b>for i in 1:3</b> loops over a range including 3. <b>while</b> repeats on a condition, <b>break</b> exits and <b>continue</b> skips. Blocks close with <b>end</b>. Array comprehensions: <b>[x^2 for x in 1:3]</b>.",
         "for i in 1:3\n    println(i)\nend\nprintln([x^2 for x in 1:3])"),
        ("Functions", "⚙️", [
            ("What does this return?", "function add(a, b)\n    a + b\nend", ["a + b", "nothing", "a", "an error"], 0),
            ("Type the symbol of the one-line function style", "sq(x) ___ x^2", None, ["="]),
            ("Which keyword defines a function?", "", ["function", "def", "fn", "fun"], 0)],
         "Functions use <b>function ... end</b> and return the last value. One-liners look like maths: <b>sq(x) = x^2</b>. Julia picks the fastest method for the argument types (multiple dispatch).",
         "function add(a, b)\n    a + b\nend\nsq(x) = x^2\nprintln(add(2, 3))"),
        ("Structs & Arrays", "🧩", [
            ("Which keyword defines a custom type?", "", ["struct", "class", "type", "object"], 0),
            ("What index does the first array item have?", "", ["1", "0", "-1", "it depends"], 0),
            ("Type the function that adds to an array", "___!(a, 4)", None, ["push"])],
         "A <b>struct</b> groups fields into a new type. Arrays start at <b>1</b> and grow with <b>push!</b>. Functions ending in <b>!</b> change their argument. Maths works on whole arrays with the <b>.</b> broadcast: <b>a .* 2</b>.",
         "struct Point\n    x::Float64\n    y::Float64\nend\na = [1, 2, 3]\npush!(a, 4)\nprintln(a .* 2)"),
        ("Data with Julia", "📊", [
            ("Which package handles tables?", "", ["DataFrames", "NumPy", "Pandas", "Tidy"], 0),
            ("Type the keyword that loads a package", "___ DataFrames", None, ["using"]),
            ("Which function gives the average?", "", ["mean", "avg", "average", "mid"], 0)],
         "Julia loves data work. <b>using DataFrames</b> loads a table package and <b>using Statistics</b> adds <b>mean</b>, <b>median</b> and <b>std</b>. <b>Plots</b> draws charts. Install packages with <b>Pkg.add</b>.",
         'using Statistics\nx = [1, 2, 3, 4]\nprintln(mean(x), " ", std(x))'),
        ("Speed & Dispatch", "⚡", [
            ("Why is Julia fast?", "", ["It compiles to machine code just in time", "It skips checks", "It is interpreted", "It uses a GPU"], 0),
            ("Type the macro that measures running time", "@___ sum(1:10^6)", None, ["time"]),
            ("What is multiple dispatch?", "", ["Choosing a method by argument types", "Running in parallel", "Copying code", "Printing twice"], 0)],
         "Julia is <b>just-in-time compiled</b>: the first call compiles and later calls are very fast. Write type-stable code and use <b>@time</b> to measure. <b>Multiple dispatch</b> picks the method by ALL argument types.",
         "f(x::Int) = x * 2\nf(x::String) = x * 2\n@time println(f(21))")]),
    "Scala": ("🔺", "#f43f5e", [
        ("Hello, World!", "👋", [
            ("Which prints a line?", "", ['println("Hi")', 'print("Hi");', 'echo "Hi"', 'console.log("Hi")'], 0),
            ("Type the keyword for a singleton program entry", "___ Main extends App", None, ["object"]),
            ("On which platform does Scala run?", "", ["The JVM", "The .NET CLR", "The browser only", "Android only"], 0)],
         "Scala blends object-oriented and functional programming and runs on the JVM. <b>println()</b> prints a line. A program is an <b>object</b> extending <b>App</b>; Scala 3 also allows <b>@main</b>. Semicolons are optional.",
         'object Main extends App {\n  println("Hello, World!")\n}'),
        ("Variables & Types", "📦", [
            ("Which keyword makes an unchangeable value?", "", ["val", "var", "let", "const"], 0),
            ("Type the keyword for a changeable variable", "___ x = 5", None, ["var"]),
            ("What type does val n = 5 get?", "", ["Int", "Double", "String", "Any"], 0)],
         "<b>val</b> is immutable and <b>var</b> is changeable; prefer <b>val</b>. Types are inferred but can be written: <b>val n: Int = 5</b>. Types: Int, Double, Boolean, String. A leading <b>s</b> before a string interpolates <b>$name</b>.",
         'val name = "Ada"\nvar age = 20\nage += 1\nprintln(s"$name is $age")'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "7 / 2", ["3", "3.5", "4", "error"], 0),
            ("Type the keyword for the other branch", "if (x > 1) 1 ___ 2", None, ["else"]),
            ("Which Scala keyword replaces switch?", "", ["match", "switch", "select", "choose"], 0)],
         "Int division truncates. <b>if / else</b> is an expression: <b>val s = if (x &gt; 5) 1 else 2</b>. <b>match</b> with <b>case</b> patterns replaces switch and is very powerful. Logic: <b>&amp;&amp;</b>, <b>||</b>, <b>!</b>.",
         'val x = 7\nval s = if (x % 2 == 0) "even" else "odd"\nprintln(s)'),
        ("Loops", "🔁", [
            ("What does 1 to 3 contain?", "", ["1, 2, 3", "1, 2", "0, 1, 2", "3"], 0),
            ("Type the collection method that runs code for each item", "list.___(println)", None, ["foreach"]),
            ("What does 1 until 3 contain?", "", ["1, 2", "1, 2, 3", "2, 3", "1"], 0)],
         "<b>for (i &lt;- 1 to 3)</b> includes 3; <b>until</b> excludes the end. Collections have <b>foreach</b>, <b>map</b> and <b>filter</b>, which Scala developers use instead of most loops. <b>while</b> exists too.",
         "for (i <- 1 to 3) {\n  println(i)\n}\nList(5, 6).foreach(println)"),
        ("Functions", "⚙️", [
            ("Which keyword defines a function?", "", ["def", "fun", "func", "function"], 0),
            ("What does this return?", "def add(a: Int, b: Int): Int = a + b", ["a + b", "nothing", "a", "an error"], 0),
            ("Type the symbol between parameters and body", "def f(x: Int) ___ x * 2", None, ["="])],
         "Functions use <b>def</b>, typed parameters, a return type after <b>:</b> and <b>=</b> before the body. The last expression is returned. Anonymous functions look like <b>x =&gt; x * 2</b>.",
         "def add(a: Int, b: Int): Int = a + b\nval twice = (x: Int) => x * 2\nprintln(add(2, 3))"),
        ("Case Classes & Traits", "🏗️", [
            ("What do case classes give you for free?", "", ["equals, copy and toString", "Faster loops", "Network access", "Nothing"], 0),
            ("Type the keyword for a data class", "___ class Point(x: Int, y: Int)", None, ["case"]),
            ("What is a trait?", "", ["Like an interface that can hold code", "A loop", "A comment", "A package"], 0)],
         "A <b>class</b> bundles data and methods. A <b>case class</b> is a data holder with free <b>equals</b>, <b>copy</b> and <b>toString</b>. A <b>trait</b> is like an interface that can also carry code. Pattern matching works on case classes.",
         "case class Point(x: Int, y: Int)\nval p = Point(1, 2)\nprintln(p.copy(x = 5))"),
        ("Functional Style", "🧩", [
            ("What does map do?", "", ["Transforms every item", "Deletes items", "Sorts items", "Counts items"], 0),
            ("Type the method that keeps items passing a test", "list.___(_ > 1)", None, ["filter"]),
            ("What is an Option?", "", ["A value that may be missing", "A loop", "A class", "A comment"], 0)],
         "Functional style transforms collections: <b>map</b> changes every item, <b>filter</b> keeps some and <b>reduce</b> combines them. <b>Option</b> is <b>Some(value)</b> or <b>None</b>, which avoids null crashes. Immutable data makes code safer.",
         "val xs = List(1, 2, 3, 4)\nprintln(xs.filter(_ % 2 == 0).map(_ * 10))\nprintln(Option(5).getOrElse(0))"),
        ("Big Data & Spark", "📊", [
            ("What is Apache Spark written in?", "", ["Scala", "Ruby", "PHP", "Lua"], 0),
            ("Type the short name of Spark's core abstraction (resilient distributed dataset)", "___", None, ["RDD"]),
            ("Why is Scala popular for big data?", "", ["Concise and runs on the JVM", "It has no types", "It is interpreted", "It is tiny"], 0)],
         "<b>Apache Spark</b>, the big-data engine, is written in Scala. You process huge datasets with the same <b>map</b> / <b>filter</b> / <b>reduce</b> style spread across many machines. A <b>DataFrame</b> is a distributed table.",
         'val lines = spark.read.textFile("log.txt")\nval errors = lines.filter(_.contains("ERROR"))\nprintln(errors.count())')]),
    "Elixir": ("💧", "#9333ea", [
        ("Hello, World!", "👋", [
            ("Which prints a line?", "", ['IO.puts("Hi")', 'print("Hi")', 'echo "Hi"', 'println!("Hi")'], 0),
            ("Type the module that prints", '___.puts("Hi")', None, ["IO"]),
            ("What is Elixir built on?", "", ["The Erlang VM", "The JVM", "The .NET CLR", "LLVM"], 0)],
         "Elixir is a functional language on the Erlang VM, built for reliable, concurrent systems. <b>IO.puts</b> prints a line. Everything is an expression and data is <b>immutable</b>. Scripts run with <b>elixir file.exs</b>.",
         'IO.puts("Hello, World!")'),
        ("Variables & Types", "📦", [
            ("Can you change a value in place?", "", ["No, data is immutable", "Yes", "Only numbers", "Only lists"], 0),
            ("Type the symbol that binds a name", "x ___ 5", None, ["="]),
            ("What does :ok represent?", "", ["An atom", "A string", "A function", "A list"], 0)],
         "<b>x = 5</b> binds a name; <b>=</b> is really pattern matching. Data is immutable: you create new values. <b>Atoms</b> like <b>:ok</b> are constants named by themselves. Types: integer, float, string, boolean, list, tuple, map.",
         'name = "Ada"\nage = 20\nIO.puts("#{name} is #{age}")\nIO.inspect({:ok, age})'),
        ("Operators & Conditions", "🔀", [
            ("Result?", "div(7, 2)", ["3", "3.5", "4", "error"], 0),
            ("Type the function for the remainder", "___(7, 2)", None, ["rem"]),
            ("Which construct checks many conditions?", "", ["cond", "switch", "select", "when only"], 0)],
         "<b>/</b> always returns a float; <b>div(7, 2)</b> gives 3 and <b>rem(7, 2)</b> the remainder. <b>if / else</b> use <b>do ... end</b>. <b>case</b> pattern-matches a value and <b>cond</b> checks several conditions. Logic: <b>and</b>, <b>or</b>, <b>not</b>.",
         'x = 7\nif rem(x, 2) == 0 do\n  IO.puts("even")\nelse\n  IO.puts("odd")\nend'),
        ("Loops", "🔁", [
            ("How do you repeat in Elixir?", "", ["Enum functions and recursion", "while loops", "goto", "do-while"], 0),
            ("Type the module with each and map", "___.each(1..3, &IO.puts/1)", None, ["Enum"]),
            ("What does 1..3 contain?", "", ["1, 2, 3", "1, 2", "0, 1, 2", "3"], 0)],
         "Elixir has no while loop. You use <b>Enum.each</b>, <b>Enum.map</b> and <b>for</b> comprehensions over collections, or recursion. <b>1..3</b> is a range including 3. The pipe <b>|&gt;</b> chains steps.",
         "Enum.each(1..3, fn i -> IO.puts(i) end)\nfor x <- [5, 6], do: IO.puts(x)"),
        ("Functions", "⚙️", [
            ("Which keyword defines a named function?", "", ["def", "fn", "func", "function"], 0),
            ("What does this return?", "def add(a, b) do\n  a + b\nend", ["a + b", "nothing", "nil", "an error"], 0),
            ("Type the keyword for an anonymous function", "___ x -> x * 2 end", None, ["fn"])],
         "Named functions live in modules: <b>def add(a, b) do ... end</b>. Anonymous ones use <b>fn x -&gt; x * 2 end</b>. The last expression is returned. Functions can have several clauses chosen by <b>pattern matching</b> on the arguments.",
         "defmodule Math do\n  def add(a, b), do: a + b\nend\nIO.puts(Math.add(2, 3))"),
        ("Modules & Maps", "🧩", [
            ("Which keyword defines a module?", "", ["defmodule", "module", "class", "namespace"], 0),
            ("Type the operator that chains function calls", "list ___ Enum.sum()", None, ["|>"]),
            ("Which type holds key-value pairs?", "", ["Map", "Tuple", "Atom", "Range"], 0)],
         "Code is organized in <b>modules</b> made with <b>defmodule</b>. Lists, tuples and <b>maps</b> hold data. The pipe <b>|&gt;</b> passes the result of one call into the next, which keeps transformations readable. <b>structs</b> are maps with a fixed shape.",
         'user = %{name: "Ada", age: 20}\nIO.puts(user.name)\n[1, 2, 3] |> Enum.map(&(&1 * 2)) |> IO.inspect()'),
        ("Phoenix Web", "🌐", [
            ("What is Phoenix?", "", ["Elixir's web framework", "A database", "A compiler", "A game engine"], 0),
            ("Type the command word that creates a Phoenix app", "mix phx.___ blog", None, ["new"]),
            ("What is LiveView for?", "", ["Real-time UI without writing JavaScript", "Styling", "Databases", "Testing"], 0)],
         "<b>Phoenix</b> is Elixir's web framework, known for speed and real-time features. <b>mix</b> is the build tool (<b>mix phx.new</b>). <b>LiveView</b> updates the page in real time over a websocket without writing JavaScript.",
         'def index(conn, _params) do\n  render(conn, "index.html")\nend'),
        ("Processes & OTP", "⚡", [
            ("What are Elixir processes?", "", ["Very lightweight isolated units", "Operating system threads", "Files", "Classes"], 0),
            ("Type the function that starts a process", "___(fn -> 1 end)", None, ["spawn"]),
            ("How do processes talk?", "", ["By sending messages", "By sharing variables", "By files only", "They cannot"], 0)],
         "Elixir runs millions of tiny isolated <b>processes</b>. <b>spawn</b> starts one and processes talk by <b>send</b> and <b>receive</b>; nothing is shared. A <b>supervisor</b> restarts crashed processes (let it crash), which makes systems very reliable.",
         'pid = spawn(fn ->\n  receive do\n    msg -> IO.puts(msg)\n  end\nend)\nsend(pid, "hi")')]),
}
for _n, (_ic, _c, _ls) in NEW6.items():
    LANGS[_n] = (_ic, _c, [SHARED[:3]] + [l[:3] for l in _ls])
    TEACH[_n] = [SHARED[3:]] + [l[3:] for l in _ls]
    TRUNKS[_n] = T2
    UN[_n] = UN2
BR.update({"Julia": [("Data", "📊", [("l", 7)]), ("Speed", "⚡", [("l", 8)])], "Scala": [("Functional", "🧩", [("l", 7)]), ("Big Data", "📊", [("l", 8)])],
           "Elixir": [("Web", "🌐", [("l", 7)]), ("Concurrency", "⚡", [("l", 8)])]})
STARTER.update({
    "Julia": ["println()\n", "for i in 1:15\nend\n", "a, b = 0, 1\nfor i in 1:10\nend\n"],
    "Scala": ["object Main extends App {\n}\n", "object Main extends App {\n  for (i <- 1 to 15) {\n  }\n}\n", "object Main extends App {\n  var a = 0\n  var b = 1\n  for (i <- 1 to 10) {\n  }\n}\n"],
    "Elixir": ["IO.puts()\n", "Enum.each(1..15, fn i ->\nend)\n", "a = 0\nb = 1\nEnum.each(1..10, fn i ->\nend)\n"],
})
PRINT.update({"Julia": r"\bprintln?\s*\(", "Scala": r"\bprintln?\s*\(", "Elixir": r"\bIO\.(puts|inspect)\b"})
for _n in NEW6:
    _b = len(LANGS[_n][2])
    for _t, _e, _qs, _tx, _cd in SH:
        LANGS[_n] = (LANGS[_n][0], LANGS[_n][1], LANGS[_n][2] + [(_t, _e, _qs)])
        TEACH[_n].append((_tx, _cd))
    _old = len(TRUNKS[_n])
    TRUNKS[_n] = TRUNKS[_n] + [("l", _b + i) for i in range(len(SH))]
    UN[_n] = list(UN[_n]) + [(_old, "Bonus", "CS Concepts")]


INP = r"\b(input|raw_input|scanf|fgets|gets|getline|readLine|readline|readln|ReadLine|Scanner|prompt|io\.read|IO\.gets|stdin|STDIN|read_line)\b|\bcin\s*>>|\bread\("
COND = r"\b(if|cond|case|when|match|unless|switch)\b"
MAINL = ("C", "C++", "Java", "C#", "Rust", "Go", "Kotlin", "Dart")
BIGP = [
    ("Number Guessing Game", "🎲", "A complete game over 5 milestones: the computer picks a secret number and you guess until you win.", [
        ("Pick a secret number", "Create a variable with a secret number and print a welcome message that mentions the game.",
         [("prints something", "PRINT"), ("stores a secret number", r"(=|:=|<-)\s*\d+"), ("welcomes the player", r"welcome|guess|game")]),
        ("Read a guess", "Ask the player for a number and read it from the keyboard.",
         [("reads input", "INPUT"), ("asks a question", r"\?|enter|guess|number")]),
        ("Compare", "Tell the player if the guess is too <b>high</b>, too <b>low</b> or <b>correct</b>.",
         [("uses a condition", COND), ("says too high", r"high"), ("says too low", r"low"), ("says correct", r"correct|right|win|congrat")]),
        ("Keep playing", "Wrap the guessing in a loop that repeats until the guess is right.",
         [("uses a loop", LP), ("can stop the loop", r"break|return|exit|until|while|!=|<>")]),
        ("Random & attempts", "Make the secret number random and count the attempts. Show the count when the player wins.",
         [("random number", r"rand|random|rnd"), ("counts attempts", r"\+\+|\+=|\+\s*1|count|attempt|tries")])]),
    ("Todo List Manager", "📝", "A task manager with a menu. Add, show and remove tasks, built step by step.", [
        ("Store tasks", "Create a list/array with a few starting tasks and print a title.",
         [("prints something", "PRINT"), ("has a list of tasks", r"\[|\bvec\b|vector|ArrayList|\blist\b|\barray\b|\bmake\(|\bnew\b|listOf|mutableListOf"), ("has task words", r"task|todo|item")]),
        ("Show tasks", "Loop through the tasks and print each one with its number.",
         [("uses a loop", LP), ("numbers the tasks", r"\+\s*1|enumerate|\bindex\b|with_index|withIndex|\bi\b|\bn\b")]),
        ("Add tasks", "Write a <b>function</b> that adds a new task to the list.",
         [("defines a function", "FUNC"), ("adds to the list", r"add|append|push|insert|<<|\+=|concat")]),
        ("Remove tasks", "Write a <b>function</b> that removes a task.",
         [("defines a function", "FUNC"), ("removes from the list", r"remove|delete|pop|splice|erase|drop|filter|reject")]),
        ("Menu", "Build a menu loop: read a choice from the player and add, show or remove tasks. Include a way to quit.",
         [("reads input", "INPUT"), ("uses a loop", LP), ("uses a condition", COND), ("has quit", r"quit|exit|stop|break")])]),
    ("Text Adventure", "🏰", "Explore rooms, pick up items and escape! A small adventure game in 5 milestones.", [
        ("Rooms", "Describe at least two rooms (a map, dictionary, struct or list) and print the first room's description.",
         [("prints something", "PRINT"), ("has rooms", r"room|location|place"), ("stores data", r"\{|\[|struct|class|dict|map|Hash")]),
        ("Player position", "Keep track of which room the player is in with a variable.",
         [("tracks position", r"current|player|position|here|location|where")]),
        ("Commands", "Read a command from the player and react to words like <b>go</b>, <b>north</b> or <b>look</b>.",
         [("reads input", "INPUT"), ("uses a condition", COND), ("knows commands", r"go|north|south|east|west|look")]),
        ("Inventory", "Add an inventory so the player can pick up and carry items.",
         [("has an inventory", r"inventory|items|bag|backpack"), ("adds items", r"append|push|add|insert|<<|\+=")]),
        ("Win condition", "Run the game in a loop and show a win (or game over) message when the goal is reached.",
         [("uses a loop", LP), ("has a win message", r"win|won|victory|escape|treasure|congrat|game over")])]),
]


def bigcheck(lang, ms, code):
    c = strip_comments(lang, code)
    res = [("syntax looks valid (brackets, colons, semicolons)", syntax_ok(lang, c))]
    for n, (title, desc, chk) in enumerate(ms):
        for label, rx in chk:
            if rx == "FUNC":
                ok = len(re.findall(DEFRX, c)) >= (2 if lang in MAINL else 1)
            else:
                ok = re.search(PRINT[lang] if rx == "PRINT" else INP if rx == "INPUT" else rx, c, re.I) is not None
            res.append((label if n == len(ms) - 1 else "↩ " + label, ok))
    return res


EXTL = {
    "Python": [
        ("Comprehensions & Generators", "🧬", [
            ("What does this print?", "print([x * x for x in range(4)])", ["[0, 1, 4, 9]", "[1, 4, 9, 16]", "[0, 1, 2, 3]", "error"], 0),
            ("Type the keyword that yields values one by one", "def gen():\n    ___ 1", None, ["yield"]),
            ("What is a generator good for?", "", ["Producing values lazily to save memory", "Sorting lists", "Drawing windows", "Opening files"], 0)],
         "A <b>list comprehension</b> builds a list in one line, with an optional <b>if</b>: <b>[x for x in nums if x &gt; 2]</b>. A <b>generator</b> uses <b>yield</b> to produce values one at a time, so huge sequences never sit in memory.",
         "squares = [x * x for x in range(5) if x % 2 == 0]\n\ndef count(n):\n    for i in range(n):\n        yield i\n\nprint(squares, list(count(3)))"),
        ("Decorators & Context Managers", "🎀", [
            ("Which symbol applies a decorator?", "", ["@", "#", "$", "&"], 0),
            ("Type the statement that auto-closes resources", "___ open('a.txt') as f:", None, ["with"]),
            ("What does a decorator do?", "", ["Wraps a function to add behavior", "Deletes a function", "Imports a module", "Declares a class"], 0)],
         "A <b>decorator</b> wraps a function to add behavior without changing its code: put <b>@name</b> above <b>def</b>. A <b>context manager</b> (<b>with</b>) guarantees cleanup, like closing a file even after errors.",
         "def shout(f):\n    def wrap(*a):\n        return f(*a).upper()\n    return wrap\n\n@shout\ndef hi():\n    return 'hi'\n\nprint(hi())")],
    "C": [
        ("Linked Lists", "🔗", [
            ("What does a node usually store?", "", ["Data and a pointer to the next node", "Only data", "Only a pointer", "A file"], 0),
            ("Type the symbol that follows a pointer to a field", "node___next", None, ["->"]),
            ("What marks the end of a linked list?", "", ["A NULL next pointer", "A zero value", "A comment", "A semicolon"], 0)],
         "A <b>linked list</b> chains <b>struct</b> nodes: each holds data and a pointer to the next. Create nodes with <b>malloc</b>, walk with <b>-&gt;next</b> until <b>NULL</b>, and <b>free</b> every node when done.",
         "struct Node {\n    int val;\n    struct Node *next;\n};\n\nstruct Node *n = malloc(sizeof(struct Node));\nn->val = 7;\nn->next = NULL;"),
        ("Preprocessor & Headers", "📂", [
            ("Which directive includes a header?", "", ["#include", "#import", "#use", "#load"], 0),
            ("Type the directive that defines a constant", "#___ MAX 100", None, ["define"]),
            ("Why use include guards?", "", ["To stop a header being included twice", "To speed up loops", "To hide variables", "To free memory"], 0)],
         "The <b>preprocessor</b> runs before compilation: <b>#include</b> pastes headers and <b>#define</b> creates constants and macros. Split programs into <b>.h</b> headers (declarations) and <b>.c</b> files. <b>Include guards</b> stop a header being pasted twice.",
         "#ifndef MATH_H\n#define MATH_H\n#define MAX 100\nint add(int a, int b);\n#endif")],
    "JavaScript": [
        ("Promises & Async/Await", "⏳", [
            ("What does await do?", "", ["Pauses an async function until a Promise settles", "Starts a loop", "Defines a class", "Imports a file"], 0),
            ("Type the keyword that marks an async function", "___ function load() {}", None, ["async"]),
            ("Which method runs several Promises together?", "", ["Promise.all", "Promise.each", "Promise.many", "Promise.run"], 0)],
         "A <b>Promise</b> is a value that arrives later. <b>async</b> functions return Promises and <b>await</b> pauses inside them. Use <b>try / catch</b> for errors and <b>Promise.all([...])</b> to run tasks in parallel.",
         "async function load() {\n  try {\n    const [a, b] = await Promise.all([fetch('/a'), fetch('/b')]);\n    console.log(a.status, b.status);\n  } catch (e) {\n    console.log('failed');\n  }\n}"),
        ("ES6 Classes & Modules", "📦", [
            ("Which keyword creates a class?", "", ["class", "struct", "object", "type"], 0),
            ("Type the keyword that shares a value with other files", "___ const x = 1;", None, ["export"]),
            ("What does extends do?", "", ["Inherits from another class", "Imports a module", "Declares a variable", "Starts a loop"], 0)],
         "<b>class</b> bundles data and methods with a <b>constructor</b>; <b>extends</b> inherits and <b>super()</b> calls the parent. <b>export</b> shares values from a file and <b>import</b> brings them into another, so big programs stay organized.",
         "class Dog extends Animal {\n  constructor(name) {\n    super(name);\n  }\n  bark() { console.log(this.name + ' woofs'); }\n}\nexport default Dog;")],
    "Java": [
        ("Collections & Generics", "🧺", [
            ("Which collection keeps order and allows duplicates?", "", ["ArrayList", "HashSet", "TreeSet", "HashMap"], 0),
            ("Type the interface for unique items", "___<String> s = new HashSet<>();", None, ["Set"]),
            ("Which interface stores key-value pairs?", "", ["Map", "List", "Set", "Queue"], 0)],
         "The <b>Collections</b> framework gives ready-made structures: <b>List</b> (ordered, duplicates), <b>Set</b> (unique items) and <b>Map</b> (key to value). <b>Generics</b> like <b>List&lt;String&gt;</b> make the compiler check the item type.",
         'List<String> names = new ArrayList<>();\nnames.add("Ada");\nMap<String, Integer> ages = new HashMap<>();\nages.put("Ada", 20);'),
        ("Streams & Lambdas", "🌊", [
            ("What does a lambda look like?", "", ["(x) -> x * 2", "fn x: x * 2", "x => { }", "lambda x"], 0),
            ("Type the stream method that transforms each item", "list.stream().___(x -> x * 2)", None, ["map"]),
            ("What does filter do in a stream?", "", ["Keeps items that pass a test", "Sorts items", "Counts items", "Deletes the list"], 0)],
         "A <b>lambda</b> is a short anonymous function: <b>(x) -&gt; x * 2</b>. <b>Streams</b> process collections in a pipeline: <b>filter</b> keeps items, <b>map</b> transforms them and <b>collect</b> gathers the result.",
         "List<Integer> out = nums.stream()\n    .filter(n -> n > 1)\n    .map(n -> n * 10)\n    .collect(Collectors.toList());")],
    "C++": [
        ("STL Containers & Algorithms", "🧰", [
            ("Which container is a dynamic array?", "", ["std::vector", "std::map", "std::set", "std::pair"], 0),
            ("Type the algorithm that sorts", "std::___(v.begin(), v.end());", None, ["sort"]),
            ("Which container stores sorted key-value pairs?", "", ["std::map", "std::vector", "std::stack", "std::array"], 0)],
         "The <b>STL</b> offers containers (<b>vector</b>, <b>map</b>, <b>set</b>) and algorithms (<b>sort</b>, <b>find</b>, <b>count</b>) that work on iterator ranges <b>begin()..end()</b>. Prefer them over hand-written loops.",
         'std::vector<int> v = {3, 1, 2};\nstd::sort(v.begin(), v.end());\nstd::map<std::string, int> ages;\nages["Ada"] = 20;'),
        ("Lambdas & Move Semantics", "🚚", [
            ("What does [](int x) { return x * 2; } create?", "", ["An anonymous function", "A class", "A pointer", "A header"], 0),
            ("Type the function that enables moving a value", "std::___(a)", None, ["move"]),
            ("Why move instead of copy?", "", ["It avoids an expensive copy", "It makes code shorter only", "It frees the stack", "It prints less"], 0)],
         "A <b>lambda</b> <b>[](int x) { ... }</b> is an inline function you can pass to algorithms. <b>Move semantics</b> (<b>std::move</b>) transfers a resource like a big vector's buffer instead of copying it.",
         "auto twice = [](int x) { return x * 2; };\nstd::vector<int> a = {1, 2, 3};\nstd::vector<int> b = std::move(a);")],
    "Rust": [
        ("Traits & Generics", "🧬", [
            ("What does a trait describe?", "", ["Shared behavior types can implement", "A loop", "A file", "A macro"], 0),
            ("Type the keyword that implements a trait for a type", "___ Speak for Dog {}", None, ["impl"]),
            ("What does fn largest<T>(a: T) mean?", "", ["A generic function over type T", "A function named T", "A macro", "A loop"], 0)],
         "A <b>trait</b> defines shared behavior, like an interface. Types opt in with <b>impl Speak for Dog</b>. <b>Generics</b> (<b>&lt;T&gt;</b>) write code once for many types, optionally limited by trait bounds like <b>T: Speak</b>.",
         'trait Speak {\n    fn speak(&self) -> String;\n}\nstruct Dog;\nimpl Speak for Dog {\n    fn speak(&self) -> String { "woof".to_string() }\n}'),
        ("Result & the ? Operator", "🛟", [
            ("What does Result<T, E> hold?", "", ["Either Ok(T) or Err(E)", "Only T", "A loop", "A file"], 0),
            ("Type the operator that returns early on an error", "let n = parse()___;", None, ["?"]),
            ("What does unwrap() do on an Err?", "", ["Panics (crashes)", "Returns 0", "Ignores it", "Retries"], 0)],
         "Rust has no exceptions. Functions return <b>Result&lt;T, E&gt;</b>: <b>Ok(value)</b> or <b>Err(error)</b>. The <b>?</b> operator returns the error early so you can chain fallible steps. <b>unwrap()</b> crashes on Err.",
         "fn read(n: &str) -> Result<i32, std::num::ParseIntError> {\n    let v = n.parse::<i32>()?;\n    Ok(v * 2)\n}")],
    "C#": [
        ("LINQ & Collections", "🔎", [
            ("What does LINQ let you do?", "", ["Query collections with readable methods", "Draw graphics", "Open files only", "Compile faster"], 0),
            ("Type the LINQ method that keeps matching items", "list.___(x => x > 1)", None, ["Where"]),
            ("Which collection is a resizable array?", "", ["List<T>", "int[]", "Tuple", "Delegate"], 0)],
         "<b>List&lt;T&gt;</b> is the everyday resizable collection and <b>Dictionary&lt;K,V&gt;</b> maps keys to values. <b>LINQ</b> queries them with chainable methods: <b>Where</b> filters, <b>Select</b> transforms, <b>OrderBy</b> sorts.",
         "var xs = new List<int> {1, 2, 3, 4};\nvar big = xs.Where(x => x > 1)\n            .Select(x => x * 10)\n            .ToList();"),
        ("Async/Await & Tasks", "⏳", [
            ("What does await do?", "", ["Waits for a Task without blocking the thread", "Starts a thread", "Locks a file", "Ends the program"], 0),
            ("Type the keyword that marks an async method", "public ___ Task Run()", None, ["async"]),
            ("What does an async method return?", "", ["Task", "int only", "void always", "Thread"], 0)],
         "<b>async</b> methods return a <b>Task</b> and use <b>await</b> to wait for slow work (web requests, files) without freezing the app. <b>Task.WhenAll</b> awaits many tasks together.",
         'async Task<string> LoadAsync() {\n    var http = new HttpClient();\n    return await http.GetStringAsync("https://example.com");\n}')],
    "Go": [
        ("Interfaces & Errors", "🧩", [
            ("How does a Go type satisfy an interface?", "", ["By having the required methods", "By declaring implements", "By inheriting", "By importing"], 0),
            ("Type the keyword that defines an interface", "type Speaker ___ { Speak() string }", None, ["interface"]),
            ("What does a function usually return to signal failure?", "", ["An error value", "An exception", "A panic only", "Nothing"], 0)],
         "An <b>interface</b> is a set of method signatures; any type with those methods satisfies it automatically. Errors are plain values: functions return <b>(result, error)</b> and callers check <b>if err != nil</b>.",
         "type Speaker interface {\n    Speak() string\n}\nfunc say(s Speaker) { fmt.Println(s.Speak()) }"),
        ("Testing & Modules", "✅", [
            ("Which suffix do Go test files use?", "", ["_test.go", "Test.go", "test_.go", ".test"], 0),
            ("Type the parameter type used in tests", "func TestAdd(t *testing.___)", None, ["T"]),
            ("Which command runs tests?", "", ["go test", "go run", "go build", "go fmt"], 0)],
         "Go ships with testing built in: put tests in <b>file_test.go</b>, name them <b>TestXxx(t *testing.T)</b> and run <b>go test</b>. A <b>module</b> (<b>go.mod</b>) tracks dependencies, created with <b>go mod init</b>.",
         'func TestAdd(t *testing.T) {\n    if add(2, 3) != 5 {\n        t.Error("expected 5")\n    }\n}')],
    "TypeScript": [
        ("Generics & Utility Types", "🧬", [
            ("What does function id<T>(x: T): T show?", "", ["A generic function", "A class", "A loop", "An error"], 0),
            ("Type the utility type that makes all properties optional", "___<User>", None, ["Partial"]),
            ("What does Readonly<T> do?", "", ["Prevents changing properties", "Deletes properties", "Adds methods", "Makes them strings"], 0)],
         "<b>Generics</b> (<b>&lt;T&gt;</b>) let one function or type work with many types while staying type-safe. <b>Utility types</b> reshape types: <b>Partial&lt;T&gt;</b> (all optional), <b>Readonly&lt;T&gt;</b>, <b>Pick</b> and <b>Omit</b>.",
         "function first<T>(xs: T[]): T {\n  return xs[0];\n}\ntype Draft = Partial<User>;"),
        ("Unions & Narrowing", "🔀", [
            ("What does string | number mean?", "", ["Either a string or a number", "Both at once", "A tuple", "An error"], 0),
            ("Type the operator that checks a primitive type at runtime", "___ x === 'string'", None, ["typeof"]),
            ("What is narrowing?", "", ["Refining a union type with checks", "Shrinking files", "Removing types", "Compiling faster"], 0)],
         "A <b>union</b> <b>string | number</b> allows several types. <b>Narrowing</b> checks refine it: <b>typeof x === 'string'</b> tells the compiler x is a string inside that branch. <b>Discriminated unions</b> add a <b>kind</b> field so a switch is checked for completeness.",
         "function show(x: string | number) {\n  if (typeof x === 'string') return x.toUpperCase();\n  return x.toFixed(1);\n}")],
    "Kotlin": [
        ("Collections & Lambdas", "🧺", [
            ("Which function transforms each item?", "", ["map", "each", "change", "alter"], 0),
            ("Type the function that keeps matching items", "list.___ { it > 1 }", None, ["filter"]),
            ("What is it in a lambda?", "", ["The implicit single parameter", "A keyword for loops", "A class", "A type"], 0)],
         "Kotlin collections have <b>listOf</b> (read-only) and <b>mutableListOf</b>. Lambdas use braces and the implicit <b>it</b>: <b>list.map { it * 2 }</b>. <b>filter</b>, <b>map</b>, <b>sortedBy</b> and <b>groupBy</b> replace most loops.",
         "val xs = listOf(1, 2, 3, 4)\nprintln(xs.filter { it % 2 == 0 }.map { it * 10 })"),
        ("Data & Sealed Classes", "🔒", [
            ("What does a data class give you?", "", ["equals, copy and toString", "Faster loops", "Threads", "Nothing"], 0),
            ("Type the keyword for a restricted class hierarchy", "___ class State", None, ["sealed"]),
            ("What does when do with a sealed class?", "", ["Checks every case exhaustively", "Loops", "Prints", "Imports"], 0)],
         "A <b>data class</b> holds data and auto-generates <b>equals</b>, <b>copy</b> and <b>toString</b>. A <b>sealed class</b> has a fixed set of subclasses, so a <b>when</b> must cover every case, which makes states like Loading, Success and Error safe.",
         'sealed class State\nobject Loading : State()\ndata class Done(val v: Int) : State()\n\nfun show(s: State) = when (s) {\n    is Loading -> "..."\n    is Done -> s.v.toString()\n}')],
    "Swift": [
        ("Closures & Collections", "🧺", [
            ("What is a closure?", "", ["A self-contained block of code", "A loop", "A class", "A file"], 0),
            ("Type the method that transforms every item", "[1, 2].___ { $0 * 2 }", None, ["map"]),
            ("What is $0?", "", ["The first closure argument", "A constant", "A string", "An error"], 0)],
         "A <b>closure</b> <b>{ x in x * 2 }</b> is a block of code you can pass around. <b>$0</b> is shorthand for the first argument. Arrays and dictionaries have <b>map</b>, <b>filter</b> and <b>reduce</b> that take closures.",
         "let xs = [1, 2, 3, 4]\nlet big = xs.filter { $0 > 1 }.map { $0 * 10 }\nprint(big)"),
        ("Errors & Codable", "🧯", [
            ("Which statements handle a throwing call?", "", ["do / try / catch", "if / else", "switch", "guard only"], 0),
            ("Type the keyword that marks a call that can throw", "let d = ___ load()", None, ["try"]),
            ("What does Codable do?", "", ["Converts types to and from JSON", "Compiles code", "Draws views", "Connects Wi-Fi"], 0)],
         "Functions that can fail are marked <b>throws</b>; call them with <b>try</b> inside <b>do { } catch { }</b>. A type that adopts <b>Codable</b> converts to and from JSON automatically with <b>JSONEncoder</b> and <b>JSONDecoder</b>.",
         'struct User: Codable { var name: String }\ndo {\n    let u = try JSONDecoder().decode(User.self, from: data)\n    print(u.name)\n} catch {\n    print("bad json")\n}')],
    "Ruby": [
        ("Blocks, Procs & Lambdas", "🧱", [
            ("What does yield do in a method?", "", ["Runs the block passed to the method", "Ends the program", "Defines a class", "Prints"], 0),
            ("Type the method that transforms every item", "[1, 2].___ { |x| x * 2 }", None, ["map"]),
            ("What is a block?", "", ["A chunk of code passed to a method", "A variable", "A class", "A comment"], 0)],
         "A <b>block</b> (<b>do ... end</b> or <b>{ }</b>) is code you hand to a method, which can run it with <b>yield</b>. <b>Procs</b> and <b>lambdas</b> are blocks saved in variables. Ruby's <b>map</b>, <b>select</b> and <b>each</b> are all built on blocks.",
         "def twice\n  yield\n  yield\nend\ntwice { puts 'hi' }\ndbl = ->(x) { x * 2 }\nputs dbl.call(4)"),
        ("Modules & Mixins", "🧩", [
            ("What does include do?", "", ["Mixes a module's methods into a class", "Imports a file", "Starts a loop", "Prints"], 0),
            ("Type the keyword that defines a module", "___ Walkable", None, ["module"]),
            ("Why use modules?", "", ["Share behavior between unrelated classes", "Make loops faster", "Hide variables only", "Compile code"], 0)],
         "A <b>module</b> groups methods and constants. <b>include</b> mixes its methods into a class, letting unrelated classes share behavior without inheritance (a <b>mixin</b>). Modules also act as <b>namespaces</b>, like <b>Math::PI</b>.",
         "module Walkable\n  def walk = puts('walking')\nend\nclass Dog\n  include Walkable\nend\nDog.new.walk")],
    "PHP": [
        ("Arrays & Sorting", "🗂️", [
            ("Which array has named keys?", "", ["Associative array", "Indexed array only", "Numeric list", "Tuple"], 0),
            ("Type the function that sorts an array", "___($a);", None, ["sort"]),
            ("Which function counts items?", "", ["count", "size", "len", "total"], 0)],
         "PHP <b>arrays</b> are both lists and dictionaries: <b>[1, 2]</b> or <b>['name' =&gt; 'Ada']</b>. Handy functions: <b>count</b>, <b>sort</b>, <b>array_map</b>, <b>array_filter</b> and <b>in_array</b>. <b>foreach ($a as $k =&gt; $v)</b> walks keys and values.",
         "$ages = ['Ada' => 20, 'Bob' => 30];\nforeach ($ages as $name => $age) {\n    echo \"$name is $age\";\n}\nsort($nums);"),
        ("Composer & Namespaces", "📦", [
            ("What is Composer?", "", ["PHP's dependency manager", "A code editor", "A database", "A framework"], 0),
            ("Type the keyword that declares a namespace", "___ App\\Models;", None, ["namespace"]),
            ("Which file lists Composer dependencies?", "", ["composer.json", "package.json", "config.php", "deps.txt"], 0)],
         "<b>Composer</b> installs libraries listed in <b>composer.json</b> and generates an autoloader. <b>namespace</b> avoids name clashes and <b>use</b> imports a class, following the <b>PSR-4</b> folder convention. This is how Laravel projects are organized.",
         "namespace App\\Models;\nuse Carbon\\Carbon;\nclass Post {\n    public function age() { return Carbon::now(); }\n}")],
    "Dart": [
        ("Collections & Generics", "🧺", [
            ("Which collection stores unique items?", "", ["Set", "List", "Map", "Queue"], 0),
            ("Type the generic list type for ints", "___<int> xs = [1, 2];", None, ["List"]),
            ("What does map(...) on a list return?", "", ["An iterable of transformed items", "A Map", "Nothing", "A string"], 0)],
         "Dart has <b>List</b>, <b>Set</b> and <b>Map</b>, all generic: <b>List&lt;int&gt;</b>. Chain <b>where</b>, <b>map</b> and <b>toList()</b> to filter and transform. Collection <b>if</b> and <b>for</b> let you build lists inline.",
         "var xs = [1, 2, 3, 4];\nvar big = xs.where((x) => x > 1).map((x) => x * 10).toList();\nprint(big);"),
        ("Null Safety Deep Dive", "🛡️", [
            ("What does String? allow?", "", ["A null value", "Only text", "Only numbers", "Nothing"], 0),
            ("Type the operator that gives a default for null", "name ___ 'guest'", None, ["??"]),
            ("What does ! do after a nullable value?", "", ["Asserts it is not null", "Negates it", "Compares it", "Deletes it"], 0)],
         "Dart separates <b>String</b> (never null) from <b>String?</b> (maybe null). <b>?.</b> calls safely, <b>??</b> gives a default and <b>!</b> asserts non-null (crashes if wrong). <b>late</b> delays initialization.",
         "String? name;\nprint(name?.length ?? 0);\nprint(name ?? 'guest');")],
    "Lua": [
        ("Closures & Coroutines", "🔁", [
            ("What does a closure remember?", "", ["Variables from its outer function", "Nothing", "Only globals", "The file name"], 0),
            ("Type the function that creates a coroutine", "local co = coroutine.___(fn)", None, ["create"]),
            ("What does coroutine.yield do?", "", ["Pauses the coroutine", "Ends the program", "Prints", "Loops"], 0)],
         "A <b>closure</b> keeps the local variables of the function that created it. A <b>coroutine</b> is a function that can pause with <b>coroutine.yield</b> and continue with <b>coroutine.resume</b>, great for game logic and generators.",
         "function counter()\n  local n = 0\n  return function() n = n + 1; return n end\nend\nlocal c = counter()\nprint(c(), c())"),
        ("String Patterns & Files", "🧵", [
            ("Which function finds a pattern in a string?", "", ["string.find", "string.search", "string.look", "string.seek"], 0),
            ("Type the function that opens a file", "local f = io.___('a.txt')", None, ["open"]),
            ("What does string.gsub do?", "", ["Replaces matches", "Counts characters", "Sorts text", "Reads files"], 0)],
         "Lua strings have a built-in <b>pattern</b> language (lighter than regex): <b>string.find</b>, <b>match</b>, <b>gmatch</b> and <b>gsub</b>. Files use <b>io.open</b>, then <b>f:read</b> and <b>f:close</b>.",
         "local s = 'hello world'\nprint(s:gsub('world', 'Lua'))\nlocal f = io.open('a.txt', 'r')\nprint(f:read('*a'))\nf:close()")],
    "R": [
        ("apply Family & Functional Tools", "🧰", [
            ("What does sapply do?", "", ["Applies a function to each item", "Sorts data", "Reads files", "Draws plots"], 0),
            ("Type the function that keeps items passing a test", "___(function(x) x > 1, v)", None, ["Filter"]),
            ("Why prefer sapply over a loop?", "", ["Shorter and often faster", "Needed for plots", "It is the only way", "It saves disk space"], 0)],
         "R favors functional tools over loops: <b>sapply(x, f)</b> applies a function to each item, <b>lapply</b> returns a list, <b>Filter</b>, <b>Map</b> and <b>Reduce</b> work on vectors. Anonymous functions look like <b>function(x) x * 2</b>.",
         "v <- c(1, 2, 3, 4)\nprint(sapply(v, function(x) x * 10))\nprint(Filter(function(x) x > 1, v))"),
        ("Tidyverse Pipelines", "🚰", [
            ("What does the pipe %>% do?", "", ["Passes the left result into the next function", "Prints", "Compares", "Loops"], 0),
            ("Type the dplyr verb that keeps rows", "df %>% ___(score > 50)", None, ["filter"]),
            ("Which verb adds or changes columns?", "", ["mutate", "select", "arrange", "count"], 0)],
         "The <b>tidyverse</b> reads like a recipe using the pipe <b>%&gt;%</b>: <b>filter</b> keeps rows, <b>select</b> picks columns, <b>mutate</b> adds columns, <b>group_by</b> + <b>summarise</b> aggregate and <b>arrange</b> sorts.",
         "df %>%\n  filter(score > 50) %>%\n  mutate(pct = score / 100) %>%\n  arrange(desc(pct))")],
    "Julia": [
        ("Multiple Dispatch", "🎯", [
            ("What picks the method in Julia?", "", ["The types of all arguments", "Only the first argument", "The file name", "Random choice"], 0),
            ("Type the integer type used to annotate an argument", "f(x::___) = x", None, ["Int"]),
            ("Which keyword defines an abstract type?", "", ["abstract type", "interface", "trait", "class"], 0)],
         "Julia chooses which method to run from the types of ALL arguments: <b>area(s::Circle)</b> vs <b>area(s::Square)</b>. Add methods to your own or existing functions, and use <b>abstract type</b> to group related types.",
         "abstract type Shape end\nstruct Circle <: Shape\n    r::Float64\nend\narea(c::Circle) = 3.14 * c.r^2"),
        ("Broadcasting & Comprehensions", "📡", [
            ("What does the dot in f.(x) do?", "", ["Applies f to every element", "Prints", "Imports", "Compares"], 0),
            ("Type the keyword in a comprehension", "[x^2 ___ x in 1:3]", None, ["for"]),
            ("What does a .+ b do?", "", ["Adds element by element", "Joins strings", "Concatenates arrays", "Errors"], 0)],
         "The <b>.</b> broadcasts an operation over every element: <b>x .* 2</b>, <b>sqrt.(v)</b>. <b>Comprehensions</b> build arrays: <b>[x^2 for x in 1:3 if x &gt; 1]</b>. Both are fast and replace explicit loops for array maths.",
         "v = [1, 2, 3]\nprintln(v .* 2)\nprintln(sqrt.(v))\nprintln([x^2 for x in 1:5 if isodd(x)])")],
    "Scala": [
        ("Pattern Matching & Sealed Traits", "🧩", [
            ("Which keyword does pattern matching?", "", ["match", "switch", "when", "select"], 0),
            ("Type the keyword that restricts subtypes to one file", "___ trait Shape", None, ["sealed"]),
            ("Why seal a trait?", "", ["The compiler checks all cases are matched", "It runs faster", "It hides it", "It makes it private"], 0)],
         "<b>match</b> compares a value against <b>case</b> patterns, deconstructing case classes. A <b>sealed trait</b> has a fixed set of subtypes, so the compiler warns if a match misses one.",
         "sealed trait Shape\ncase class Circle(r: Double) extends Shape\ncase class Square(s: Double) extends Shape\n\ndef area(x: Shape) = x match {\n  case Circle(r) => 3.14 * r * r\n  case Square(s) => s * s\n}"),
        ("Futures & For-Comprehensions", "⏳", [
            ("What is a Future?", "", ["A value computed asynchronously", "A loop", "A trait", "A package"], 0),
            ("Type the keyword that chains Futures readably", "___ { a <- f1; b <- f2 } yield a + b", None, ["for"]),
            ("What does Await.result do?", "", ["Blocks until the Future completes", "Starts it", "Cancels it", "Prints"], 0)],
         "A <b>Future</b> runs work asynchronously and completes later. <b>map</b> and <b>flatMap</b> transform results, and a <b>for-comprehension</b> chains several Futures readably. <b>Await.result</b> blocks, so use it rarely, mostly in tests.",
         "val f = Future { 21 * 2 }\nval g = for {\n  a <- f\n  b <- Future(a + 1)\n} yield b")],
    "Elixir": [
        ("Pattern Matching & Recursion", "🧩", [
            ("What does {:ok, v} = result do?", "", ["Matches the shape and binds v", "Compares strings", "Loops", "Prints"], 0),
            ("What makes recursion stop?", "", ["A base case clause", "A break", "A semicolon", "A while"], 0),
            ("Type the operator used to match values", "{a, b} ___ {1, 2}", None, ["="])],
         "In Elixir <b>=</b> is pattern matching: <b>{:ok, v} = result</b> checks the shape and binds <b>v</b>. Functions can have several clauses matched on arguments, which is how recursion works: a clause for the <b>base case</b> and one for the rest.",
         "defmodule M do\n  def sum([]), do: 0\n  def sum([h | t]), do: h + sum(t)\nend\nIO.puts(M.sum([1, 2, 3]))"),
        ("GenServer & Supervision", "🛡️", [
            ("What does a GenServer hold?", "", ["State and handles messages", "Only a function", "A file", "A template"], 0),
            ("Type the word for the tree that restarts crashed children", "___ tree", None, ["supervision"]),
            ("What does 'let it crash' mean?", "", ["Let supervisors restart failing processes", "Ignore errors", "Use try everywhere", "Stop the VM"], 0)],
         "A <b>GenServer</b> is a process that keeps <b>state</b> and answers messages through <b>handle_call</b> and <b>handle_cast</b>. A <b>Supervisor</b> watches processes and restarts them if they crash, so failures stay small and the system keeps running.",
         "defmodule Counter do\n  use GenServer\n  def init(n), do: {:ok, n}\n  def handle_call(:inc, _from, n), do: {:reply, n + 1, n + 1}\nend")],
}
EXTN = {}
for _n, _ls in EXTL.items():
    _b = len(LANGS[_n][2])
    for _t, _e, _qs, _tx, _cd in _ls:
        LANGS[_n] = (LANGS[_n][0], LANGS[_n][1], LANGS[_n][2] + [(_t, _e, _qs)])
        TEACH[_n].append((_tx, _cd))
    EXTN[_n] = [("l", _b), ("l", _b + 1), ("b", 1)]
    UN[_n] = list(UN[_n]) + [("x", "Part 2", "Language Focus")]


SH2 = [
    ("Recursion", "🔄", [
        ("What does a recursive function do?", "", ["Calls itself on a smaller problem", "Loops forever", "Calls main", "Deletes itself"], 0),
        ("What stops a recursion?", "", ["A base case", "A semicolon", "A comment", "An import"], 0),
        ("If f(n) = n * f(n-1) and f(1) = 1, what is f(3)?", "", ["6", "3", "9", "1"], 0),
        ("Type the name of the case that ends the recursion", "___ case", None, ["base"])],
     "<b>Recursion</b> solves a problem by calling the same function on a smaller piece. Every recursive function needs a <b>base case</b> that stops it and a <b>recursive case</b> that moves toward it. Without a base case you get a stack overflow.",
     "factorial(n):\n  if n <= 1: return 1          (base case)\n  return n * factorial(n - 1)  (recursive case)"),
    ("Sorting & Searching", "📊", [
        ("About how many steps does binary search need for 1000 sorted items?", "", ["10", "1000", "500", "100"], 0),
        ("Which sort repeatedly swaps neighbours?", "", ["Bubble sort", "Merge sort", "Quick sort", "Heap sort"], 0),
        ("Merge sort has time complexity...", "", ["O(n log n)", "O(n)", "O(n²)", "O(1)"], 0),
        ("Type the search that halves a sorted list each step", "___ search", None, ["binary"])],
     "<b>Bubble sort</b> swaps neighbours (simple but O(n²)). <b>Merge sort</b> splits, sorts and merges for O(n log n). <b>Binary search</b> checks the middle of a sorted list and discards half each step, so a million items need only about 20 checks. Built-in sort functions are almost always the right choice.",
     "binary_search(list, x):\n  lo, hi = 0, len(list) - 1\n  while lo <= hi:\n    mid = (lo + hi) / 2\n    if list[mid] == x: return mid\n    if list[mid] < x: lo = mid + 1\n    else: hi = mid - 1"),
    ("APIs & JSON", "📡", [
        ("What does JSON look like?", "", ['{"name": "Ada"}', "<name>Ada</name>", "name=Ada;", "name -> Ada"], 0),
        ("Which HTTP method reads data?", "", ["GET", "POST", "DELETE", "PUT"], 0),
        ("Which status code means not found?", "", ["404", "200", "500", "301"], 0),
        ("Type the text format of key/value pairs used by most APIs", "___", None, ["JSON"])],
     "An <b>API</b> lets programs talk over HTTP. Common methods: <b>GET</b> (read), <b>POST</b> (create), <b>PUT</b> (update) and <b>DELETE</b>. Data usually travels as <b>JSON</b>, text made of key: value pairs and lists. Status codes: <b>200</b> OK, <b>404</b> not found, <b>500</b> server error.",
     'GET /users/5\n-> 200 OK\n{"id": 5, "name": "Ada"}'),
    ("Databases & SQL", "🗃️", [
        ("Which SQL command reads rows?", "", ["SELECT", "INSERT", "DELETE", "UPDATE"], 0),
        ("What is a primary key?", "", ["A unique id for each row", "A password", "A column name", "A table type"], 0),
        ("Which clause filters rows?", "", ["WHERE", "FROM", "ORDER", "GROUP"], 0),
        ("Type the SQL command that adds a row", "___ INTO users VALUES (1)", None, ["INSERT"])],
     "A <b>database</b> stores data in <b>tables</b> of rows and columns. <b>SQL</b> queries them: <b>SELECT</b> reads, <b>INSERT</b> adds, <b>UPDATE</b> changes and <b>DELETE</b> removes. <b>WHERE</b> filters rows, <b>JOIN</b> combines tables and a <b>primary key</b> uniquely identifies each row.",
     "SELECT name, age\nFROM users\nWHERE age > 18\nORDER BY name;"),
    ("Testing & Debugging", "🧪", [
        ("What is a unit test?", "", ["A small automatic check of one piece of code", "A user survey", "A type of loop", "A compiler flag"], 0),
        ("Which is a good first debugging step?", "", ["Reproduce the bug reliably", "Rewrite everything", "Ignore it", "Delete the file"], 0),
        ("What does a failing test tell you?", "", ["Behavior differs from what you expected", "The computer is broken", "Nothing", "The test is always wrong"], 0),
        ("Type the word for stepping through code to find a bug", "___ the code", None, ["debug"])],
     "<b>Unit tests</b> are small automatic checks: give an input, assert the expected output. Write them for edge cases (empty, zero, huge values). To <b>debug</b>: reproduce the bug, find where reality and expectation split (print values or use a debugger), fix it and keep a test so it never returns.",
     "test add:\n  assert add(2, 3) == 5\n  assert add(-1, 1) == 0\n  assert add(0, 0) == 0"),
    ("Design Patterns", "🧱", [
        ("What is a design pattern?", "", ["A reusable solution to a common problem", "A color theme", "A language feature", "A file format"], 0),
        ("Which pattern ensures only one instance of a class?", "", ["Singleton", "Observer", "Factory", "Adapter"], 0),
        ("Which pattern notifies many listeners when something changes?", "", ["Observer", "Singleton", "Builder", "Proxy"], 0),
        ("Type the pattern that creates objects without exposing the exact class", "___ pattern", None, ["factory"])],
     "<b>Design patterns</b> are proven solutions to common design problems. <b>Singleton</b> keeps one instance, <b>Factory</b> creates objects for you, <b>Observer</b> notifies listeners when something changes (events) and <b>Strategy</b> swaps algorithms at runtime. Use them when they fit, not everywhere.",
     "Observer:\n  button.on('click', handler1)\n  button.on('click', handler2)\n  -> both run when it is clicked"),
]
BR2, POST = {}, {}
for _n in list(LANGS):
    _b = len(LANGS[_n][2])
    for _t, _e, _qs, _tx, _cd in SH2:
        LANGS[_n] = (LANGS[_n][0], LANGS[_n][1], LANGS[_n][2] + [(_t, _e, _qs)])
        TEACH[_n].append((_tx, _cd))
    EXTN[_n] = [x for x in EXTN[_n] if x[0] == "l"]
    BR2[_n] = [("Algorithms", "🧮", [("l", _b), ("l", _b + 1)]), ("Web & Data", "🌐", [("l", _b + 2), ("l", _b + 3)])]
    POST[_n] = [("l", _b + 4), ("l", _b + 5), ("b", 1)]
    UN[_n] = list(UN[_n]) + [("f2", "Crossroads", "Specialization"), ("z", "Part 3", "Pro Skills")]


SPEC = {
    "Python": [
        ("Machine Learning", "🤖", "Machine Learning with scikit-learn", "🤖", [
            ("What does a model learn from?", "", ["Training data", "Comments", "Compiler flags", "Screenshots"], 0),
            ("Type the method that trains a scikit-learn model", "model.___(X, y)", None, ["fit"]),
            ("Why split data into train and test sets?", "", ["To check the model on unseen data", "To make training faster", "To save disk space", "To remove bugs"], 0)],
         "<b>Machine learning</b> finds patterns in data instead of using hand-written rules. With <b>scikit-learn</b>: split the data (<b>train_test_split</b>), create a model, <b>fit</b> it on training data and <b>predict</b> on unseen data. Always judge it on the TEST set to avoid <b>overfitting</b>.",
         "from sklearn.linear_model import LinearRegression\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)\nprint(model.predict(X_test))"),
        ("FastAPI Web", "🕸️", "FastAPI & Web APIs", "🕸️", [
            ("What does FastAPI build?", "", ["Web APIs", "Desktop games", "Spreadsheets", "Compilers"], 0),
            ("Type the decorator that routes GET requests", "@app.___('/')", None, ["get"]),
            ("Which format does an endpoint usually return?", "", ["JSON", "PNG", "EXE", "ZIP"], 0)],
         "<b>FastAPI</b> builds web APIs in a few lines: a decorator like <b>@app.get('/items')</b> maps a URL to a function and the return value becomes <b>JSON</b>. Type hints validate inputs automatically and docs are generated for free. Run it with <b>uvicorn</b>.",
         "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/hello/{name}')\ndef hello(name: str):\n    return {'msg': f'Hi {name}'}")],
    "C": [
        ("Kernel Dev", "🐧", "Kernel Modules & OS Basics", "🐧", [
            ("What is the kernel?", "", ["The core of the OS that manages hardware", "A text editor", "A compiler", "A shell"], 0),
            ("Type the system call that creates a new process on Unix", "___()", None, ["fork"]),
            ("What is a kernel module?", "", ["Code loaded into the running kernel", "A user program", "A library header", "A script"], 0)],
         "The <b>kernel</b> is the core of the operating system: it manages memory, processes and hardware. User programs talk to it with <b>system calls</b> like <b>fork</b>, <b>read</b> and <b>write</b>. A <b>kernel module</b> (<b>module_init</b>, <b>module_exit</b>) adds code to a running Linux kernel without rebooting; bugs there can crash the whole machine.",
         '#include <linux/module.h>\n\nstatic int __init hi(void) {\n    printk(KERN_INFO "hello kernel\\n");\n    return 0;\n}\nmodule_init(hi);'),
        ("Networking", "🌐", "Sockets & Networking", "🌐", [
            ("Which call creates a socket?", "", ["socket()", "open()", "fork()", "malloc()"], 0),
            ("Type the call that waits for a client to connect", "___(fd, 0, 0)", None, ["accept"]),
            ("What does TCP guarantee?", "", ["Ordered, reliable delivery", "The fastest speed", "Encryption", "Nothing"], 0)],
         "<b>Sockets</b> let programs talk over a network. A server calls <b>socket</b>, <b>bind</b>, <b>listen</b> and <b>accept</b>; a client calls <b>socket</b> and <b>connect</b>. <b>TCP</b> gives ordered reliable streams, <b>UDP</b> is faster but may lose packets. Always check return values.",
         "int fd = socket(AF_INET, SOCK_STREAM, 0);\nbind(fd, (struct sockaddr *)&addr, sizeof(addr));\nlisten(fd, 5);\nint client = accept(fd, NULL, NULL);")],
    "JavaScript": [
        ("React", "⚛️", "React & Component UIs", "⚛️", [
            ("What is a component?", "", ["A function that returns UI", "A database", "A loop", "A style file"], 0),
            ("Type the hook that stores state", "const [n, setN] = ___(0)", None, ["useState"]),
            ("What does React do when state changes?", "", ["Re-renders the component", "Reloads the browser", "Deletes the page", "Nothing"], 0)],
         "<b>React</b> builds UIs from <b>components</b>: functions that return JSX. <b>Props</b> pass data in, <b>useState</b> keeps changing data and <b>useEffect</b> runs side effects like fetching. When state changes React re-renders only what changed.",
         "function Counter() {\n  const [n, setN] = useState(0);\n  return <button onClick={() => setN(n + 1)}>{n}</button>;\n}"),
        ("Browser Games", "🎮", "Canvas & Game Loops", "🎮", [
            ("Which function schedules the next animation frame?", "", ["requestAnimationFrame", "setTimeout only", "nextFrame", "draw"], 0),
            ("Type the canvas method that draws a filled rectangle", "ctx.___(10, 10, 50, 50)", None, ["fillRect"]),
            ("What does a game loop do each frame?", "", ["Update then draw", "Only draw", "Only update", "Close the page"], 0)],
         "Browser games use the <b>canvas</b> element: get a <b>2d</b> context and draw with <b>fillRect</b>, <b>drawImage</b> and more. A <b>game loop</b> with <b>requestAnimationFrame</b> updates positions and redraws about 60 times a second.",
         "function loop() {\n  x += 2;\n  ctx.clearRect(0, 0, 400, 300);\n  ctx.fillRect(x, 100, 40, 40);\n  requestAnimationFrame(loop);\n}\nloop();")],
    "Java": [
        ("Desktop GUI", "🖥️", "GUI with JavaFX & Swing", "🖥️", [
            ("What does a GUI event listener do?", "", ["Reacts to user actions like clicks", "Draws pictures", "Compiles code", "Stores files"], 0),
            ("Type the JavaFX class for a clickable control", 'new ___("Click")', None, ["Button"]),
            ("What are layouts for?", "", ["Arranging controls in a window", "Loading files", "Sorting lists", "Network calls"], 0)],
         "Desktop apps use a GUI toolkit: <b>JavaFX</b> (modern) or <b>Swing</b>. A window (<b>Stage</b>) holds a scene of controls like <b>Button</b> and <b>Label</b>, arranged by <b>layouts</b> (VBox, HBox). User actions trigger <b>event handlers</b>: <b>button.setOnAction(e -&gt; ...)</b>.",
         'Button b = new Button("Click");\nb.setOnAction(e -> System.out.println("hi"));\nVBox root = new VBox(b);\nstage.setScene(new Scene(root, 300, 200));'),
        ("Spring Boot", "🏢", "Spring Boot Services", "🏢", [
            ("What is Spring Boot?", "", ["A framework for Java web services", "A GUI toolkit", "A database", "A compiler"], 0),
            ("Type the annotation that marks a REST controller", "@___\nclass Api {}", None, ["RestController"]),
            ("What does @GetMapping do?", "", ["Maps GET requests to a method", "Reads a file", "Prints text", "Starts a thread"], 0)],
         "<b>Spring Boot</b> builds production web services quickly. Mark a class <b>@RestController</b>, map URLs with <b>@GetMapping</b> and <b>@PostMapping</b>, and return objects that become JSON. <b>Dependency injection</b> hands your classes the objects they need.",
         '@RestController\nclass Api {\n    @GetMapping("/hello")\n    String hello() { return "Hello"; }\n}')],
    "C++": [
        ("Game Engines", "🎮", "Game Engines & Graphics", "🎮", [
            ("What does a game loop repeat?", "", ["Input, update, render", "Compile, link, run", "Read, write, close", "Open, save, quit"], 0),
            ("Type the cross-platform graphics API ending in GL", "Open___", None, ["GL"]),
            ("Why do engines use C++?", "", ["Speed and control over memory", "It has no bugs", "It is interpreted", "It is tiny"], 0)],
         "Game engines like <b>Unreal</b> are written in C++ for speed and memory control. The core is a <b>game loop</b>: process input, <b>update</b> the world with delta time, <b>render</b> with a graphics API (<b>OpenGL</b>, <b>Vulkan</b>, <b>DirectX</b>). Entities are often organized with an <b>ECS</b>.",
         "while (running) {\n    float dt = clock.restart();\n    handleInput();\n    update(dt);\n    render();\n}"),
        ("Performance", "⚡", "Concurrency & Performance", "⚡", [
            ("What does std::thread do?", "", ["Runs a function in parallel", "Sorts a list", "Opens a file", "Prints"], 0),
            ("Type the class that protects shared data from races", "std::___ m;", None, ["mutex"]),
            ("What is a data race?", "", ["Two threads touching the same data unsafely", "A fast loop", "A slow disk", "A syntax error"], 0)],
         "Modern C++ has <b>std::thread</b>, <b>std::mutex</b> and <b>std::atomic</b> for parallel code. A <b>data race</b> (two threads changing shared data without protection) causes unpredictable bugs, so lock with <b>std::lock_guard</b>. Measure before optimizing: profilers beat guessing.",
         "std::mutex m;\nint total = 0;\nvoid add() {\n    std::lock_guard<std::mutex> g(m);\n    total++;\n}\nstd::thread t(add);\nt.join();")],
    "Rust": [
        ("Embedded", "🔩", "Embedded & no_std Rust", "🔩", [
            ("What does no_std mean?", "", ["Code without the standard library for tiny devices", "Code with no tests", "Code without variables", "Code without loops"], 0),
            ("Type the attribute that disables the standard library", "#![___]", None, ["no_std"]),
            ("What does unsafe allow?", "", ["Hardware access you must verify yourself", "Faster compile times", "Ignoring all types", "Removing the compiler"], 0)],
         "<b>Embedded Rust</b> runs on microcontrollers with no operating system: <b>#![no_std]</b> drops the standard library and <b>#![no_main]</b> replaces main. Hardware registers are accessed through safe wrappers, with small <b>unsafe</b> blocks only where needed. Memory safety without a garbage collector fits perfectly.",
         "#![no_std]\n#![no_main]\n\n#[entry]\nfn main() -> ! {\n    loop {}\n}"),
        ("WebAssembly", "🕸️", "WebAssembly with Rust", "🕸️", [
            ("What is WebAssembly?", "", ["A fast binary format that runs in browsers", "A JavaScript framework", "A database", "A CSS tool"], 0),
            ("Type the tool name that builds Rust for the web", "wasm-___", None, ["pack"]),
            ("Why compile Rust to Wasm?", "", ["Near-native speed in the browser", "To avoid HTML", "To skip types", "To use less RAM only"], 0)],
         "<b>WebAssembly</b> (Wasm) is a compact binary format that runs in browsers at near-native speed. Rust compiles to it with <b>wasm-pack</b> and <b>wasm-bindgen</b> exposes functions to JavaScript. Great for image processing, games and heavy maths on the web.",
         "use wasm_bindgen::prelude::*;\n\n#[wasm_bindgen]\npub fn add(a: i32, b: i32) -> i32 {\n    a + b\n}")],
    "C#": [
        ("Desktop Apps", "🖥️", "Desktop Apps with WPF & MAUI", "🖥️", [
            ("What does XAML describe?", "", ["The UI layout in XML", "Database tables", "Network packets", "Build scripts"], 0),
            ("Type the three-letter pattern that separates View, ViewModel and Model", "___", None, ["MVVM"]),
            ("What does .NET MAUI build?", "", ["Cross-platform apps", "Only websites", "Only games", "Only drivers"], 0)],
         "<b>WPF</b> (Windows) and <b>.NET MAUI</b> (cross-platform) build desktop and mobile apps. The UI is written in <b>XAML</b> (XML), logic lives in C#, and <b>data binding</b> connects them. The <b>MVVM</b> pattern separates View, ViewModel and Model so the UI stays testable.",
         '<Button Content="Click" Click="OnClick" />\n\nprivate void OnClick(object s, EventArgs e) {\n    label.Text = "Hi!";\n}'),
        ("Cloud", "☁️", "Cloud & Microservices", "☁️", [
            ("What is a microservice?", "", ["A small independent service doing one job", "A tiny variable", "A short loop", "A UI widget"], 0),
            ("Type the tool that packages apps into containers", "___", None, ["Docker"]),
            ("Which method defines a route in a Minimal API?", "", ["app.MapGet", "app.Route()", "@Get", "get()"], 0)],
         "Cloud apps split into <b>microservices</b>: small services that each do one job and talk over HTTP or queues. <b>Docker</b> packages each service into a container and an orchestrator like <b>Kubernetes</b> runs many copies. ASP.NET Core <b>Minimal APIs</b> define routes in a few lines.",
         'var app = WebApplication.Create();\napp.MapGet("/health", () => "ok");\napp.Run();')],
    "Go": [
        ("Cloud Tools", "☁️", "Cloud & Container Tools", "☁️", [
            ("Which famous tools are written in Go?", "", ["Docker and Kubernetes", "Photoshop and Word", "Chrome and Firefox", "Excel and Access"], 0),
            ("Type the keyword that runs a function concurrently", "___ worker()", None, ["go"]),
            ("Why is Go popular for cloud tools?", "", ["Fast, simple, single binary output", "It has no types", "It needs a VM", "It is interpreted"], 0)],
         "Go dominates cloud infrastructure: <b>Docker</b> and <b>Kubernetes</b> are written in it. It compiles to a <b>single static binary</b> that is easy to ship, and <b>goroutines</b> handle thousands of connections. A tiny <b>net/http</b> server is production-ready.",
         'func main() {\n    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {\n        w.Write([]byte("ok"))\n    })\n    http.ListenAndServe(":8080", nil)\n}'),
        ("CLI Tools", "🛠️", "CLI Tools & Worker Pools", "🛠️", [
            ("Which package parses command-line flags?", "", ["flag", "cli_args", "os.exec", "cmdline"], 0),
            ("Type the sync type that waits for goroutines", "sync.___", None, ["WaitGroup"]),
            ("What does a channel do?", "", ["Passes values between goroutines", "Reads files", "Prints", "Compiles"], 0)],
         "Go is great for <b>CLI tools</b>: the <b>flag</b> package parses options and <b>os.Args</b> gives raw arguments. Combine goroutines with <b>sync.WaitGroup</b> to wait for workers, and <b>channels</b> to send them jobs and collect results (the worker-pool pattern).",
         'name := flag.String("name", "world", "who")\nflag.Parse()\nfmt.Println("hello", *name)')],
    "TypeScript": [
        ("Next.js", "🧱", "Full-Stack with Next.js", "🧱", [
            ("What is Next.js?", "", ["A React framework with server rendering", "A database", "A CSS library", "A compiler"], 0),
            ("Type the name of the folder-based router folder", "___/page.tsx", None, ["app"]),
            ("Why render pages on the server?", "", ["Faster first load and better SEO", "Smaller servers", "No JavaScript ever", "It is required"], 0)],
         "<b>Next.js</b> is a React framework that renders pages on the <b>server</b> for fast first load and good SEO, with file-based routing (the <b>app/</b> folder) and API routes. With TypeScript, props and API responses are typed end to end.",
         "export default async function Page() {\n  const res = await fetch('https://api.example.com/items');\n  const items: Item[] = await res.json();\n  return <ul>{items.map(i => <li key={i.id}>{i.name}</li>)}</ul>;\n}"),
        ("Type Wizardry", "🧠", "Advanced Type Programming", "🧠", [
            ("What does a conditional type look like?", "", ["T extends U ? X : Y", "if T then X", "T == U ? X : Y", "switch T"], 0),
            ("Type the keyword that captures a type inside a condition", "T extends (___ R)[] ? R : never", None, ["infer"]),
            ("What is a mapped type?", "", ["A type built by transforming each property", "A map data structure", "A function", "A module"], 0)],
         "TypeScript's type system is a language of its own: <b>conditional types</b> (<b>T extends U ? X : Y</b>), <b>mapped types</b> (<b>{ [K in keyof T]: ... }</b>) and <b>infer</b> to capture types let you build helpers like <b>Partial</b> yourself. Use them to make libraries hard to misuse.",
         "type ElementOf<T> = T extends (infer E)[] ? E : never;\ntype Flags<T> = { [K in keyof T]: boolean };")],
    "Kotlin": [
        ("Multiplatform", "📲", "Kotlin Multiplatform", "📲", [
            ("What does Kotlin Multiplatform share?", "", ["Business logic across platforms", "Only UI", "Only tests", "Nothing"], 0),
            ("Type the keyword for platform-specific declarations", "___ fun platform(): String", None, ["expect"]),
            ("Which platforms can KMP target?", "", ["Android, iOS, desktop and web", "Only Android", "Only iOS", "Only servers"], 0)],
         "<b>Kotlin Multiplatform</b> shares business logic between Android, iOS, desktop and web while keeping native UIs. Common code uses <b>expect</b> declarations that each platform fulfills with <b>actual</b> implementations.",
         'expect fun platform(): String\n\nactual fun platform() = "Android"'),
        ("Android Arch", "🏛️", "MVVM, Room & Coroutines", "🏛️", [
            ("What does a ViewModel do?", "", ["Holds UI state that survives rotation", "Draws pixels", "Compiles code", "Stores the APK"], 0),
            ("Type the Android library for local databases", "___", None, ["Room"]),
            ("What are coroutines used for in Android?", "", ["Async work without blocking the UI", "Styling", "Layouts", "Fonts"], 0)],
         "Modern Android apps use <b>MVVM</b>: a <b>ViewModel</b> holds UI state, the UI observes it with <b>StateFlow</b> and a <b>Repository</b> fetches data. <b>Room</b> is the local database library and <b>coroutines</b> keep slow work off the main thread.",
         '@Dao\ninterface TodoDao {\n    @Query("SELECT * FROM todo")\n    fun all(): Flow<List<Todo>>\n}')],
    "Swift": [
        ("SwiftData", "💾", "SwiftData & Persistence", "💾", [
            ("What does SwiftData do?", "", ["Saves model objects on the device", "Draws UI", "Compiles code", "Plays sounds"], 0),
            ("Type the macro that marks a persistent model class", "@___ class Task {}", None, ["Model"]),
            ("Where does the data live?", "", ["On the device", "Only in memory", "In the cloud only", "In the compiler"], 0)],
         "<b>SwiftData</b> stores your app's objects on the device: mark a class with <b>@Model</b> and read them in SwiftUI with <b>@Query</b>. Changes save automatically and can sync through iCloud.",
         "@Model class Task {\n    var title: String\n    init(title: String) { self.title = title }\n}\n@Query var tasks: [Task]"),
        ("Concurrency", "⚡", "Swift Concurrency & Actors", "⚡", [
            ("What does await do?", "", ["Waits for an async result", "Starts a loop", "Defines a class", "Prints"], 0),
            ("Type the keyword that marks an async function", "func load() ___ -> Int", None, ["async"]),
            ("What is an actor?", "", ["A type that protects its own state from data races", "A UI widget", "A protocol", "A loop"], 0)],
         "<b>async/await</b> makes asynchronous code read top to bottom. <b>Task</b> starts concurrent work and <b>actors</b> protect mutable state: only one task touches it at a time, so data races are prevented by the compiler.",
         "actor Counter {\n    var n = 0\n    func inc() { n += 1 }\n}\nTask { await counter.inc() }")],
    "Ruby": [
        ("Rails Testing", "✅", "Rails APIs & RSpec Testing", "✅", [
            ("What is RSpec?", "", ["A testing framework for Ruby", "A web server", "A database", "A gem manager"], 0),
            ("Type the RSpec keyword that groups examples", "___ 'Math' do", None, ["describe"]),
            ("What does expect(x).to eq(5) do?", "", ["Checks that x equals 5", "Sets x to 5", "Prints 5", "Loops 5 times"], 0)],
         "<b>Rails</b> can power JSON APIs, and <b>RSpec</b> tests them in readable English: <b>describe</b> groups, <b>it</b> defines an example and <b>expect(x).to eq(y)</b> asserts. Test-driven development writes the failing test first, then the code.",
         "describe 'Math' do\n  it 'adds' do\n    expect(2 + 3).to eq(5)\n  end\nend"),
        ("Metaprogramming", "🪄", "Metaprogramming", "🪄", [
            ("What is metaprogramming?", "", ["Code that writes or changes code", "Writing comments", "Compiling twice", "Using macros in C"], 0),
            ("Type the method that defines a method at runtime", "___(:hello) { puts 'hi' }", None, ["define_method"]),
            ("What does method_missing do?", "", ["Handles calls to undefined methods", "Deletes methods", "Prints methods", "Lists files"], 0)],
         "Ruby lets code inspect and change itself at runtime: <b>define_method</b> creates methods, <b>send</b> calls a method by name and <b>method_missing</b> catches undefined calls. This powers Rails' DSLs, but use it sparingly: magic is hard to debug.",
         "class Dog\n  [:bark, :sit].each do |m|\n    define_method(m) { puts m }\n  end\nend\nDog.new.bark")],
    "PHP": [
        ("WordPress", "🧩", "WordPress Plugins", "🧩", [
            ("What is a WordPress hook?", "", ["A place where plugins run code", "A fishing tool", "A database table", "A theme color"], 0),
            ("Type the function that attaches code to a hook", "___('init', 'my_fn')", None, ["add_action"]),
            ("Which two kinds of hooks exist?", "", ["Actions and filters", "Loops and ifs", "Posts and pages", "Themes and skins"], 0)],
         "<b>WordPress</b> runs a third of the web and is written in PHP. Plugins extend it through <b>hooks</b>: <b>add_action</b> runs your code at an event and <b>add_filter</b> changes data on the way through. Always escape output (<b>esc_html</b>) and validate input.",
         "add_action('wp_footer', function () {\n    echo esc_html('Thanks for visiting');\n});"),
        ("Laravel APIs", "🚀", "Laravel APIs & Eloquent", "🚀", [
            ("What is Eloquent?", "", ["Laravel's ORM for databases", "A template engine", "A router", "A cache"], 0),
            ("Type the method that finds a model by id", "User::___(5)", None, ["find"]),
            ("What do migrations do?", "", ["Version-control the database schema", "Move servers", "Copy images", "Compile PHP"], 0)],
         "<b>Laravel</b> makes APIs elegant: routes in <b>routes/api.php</b>, controllers for logic and <b>Eloquent</b> models that map to database tables (<b>User::find(5)</b>). <b>Migrations</b> version your schema and <b>resources</b> shape the JSON output.",
         "Route::get('/users/{id}', function ($id) {\n    return User::findOrFail($id);\n});")],
    "Dart": [
        ("State Mgmt", "🧠", "Flutter State Management", "🧠", [
            ("Why use state management?", "", ["Share and update data across widgets", "Draw pixels", "Compile faster", "Store assets"], 0),
            ("Type the method that rebuilds a StatefulWidget", "___(() { n++; })", None, ["setState"]),
            ("Which is a popular state package?", "", ["Provider", "Docker", "Express", "Rails"], 0)],
         "When many widgets need the same data, simple <b>setState</b> isn't enough. Packages like <b>Provider</b>, <b>Riverpod</b> and <b>Bloc</b> hold state outside the widgets and rebuild only what listens. Keep UI dumb and logic testable.",
         "class Counter extends ChangeNotifier {\n  int n = 0;\n  void inc() { n++; notifyListeners(); }\n}"),
        ("Animations", "🎨", "Animations & Design", "🎨", [
            ("What controls an animation over time?", "", ["AnimationController", "Scaffold", "Navigator", "Future"], 0),
            ("Type the prefix of widgets that animate property changes", "___Container", None, ["Animated"]),
            ("What does Hero do?", "", ["Animates a shared widget between screens", "Draws a cape", "Loads images", "Sorts lists"], 0)],
         "Flutter animations are smooth by default: <b>AnimatedContainer</b> and other <b>implicit</b> animations change properties over time automatically. <b>AnimationController</b> gives full control, and <b>Hero</b> flies a shared widget between two screens.",
         "AnimatedContainer(\n  duration: Duration(milliseconds: 300),\n  width: big ? 200 : 100,\n  color: Colors.blue,\n)")],
    "Lua": [
        ("Roblox", "🧱", "Roblox & Luau Scripting", "🧱", [
            ("What language does Roblox use?", "", ["Luau, a Lua variant", "Python", "Java", "C"], 0),
            ("Type the method that gets a Roblox service", "game:___('Players')", None, ["GetService"]),
            ("What does a Script in Roblox control?", "", ["Game behavior", "Textures only", "Sound files", "Fonts"], 0)],
         "<b>Roblox</b> games are scripted in <b>Luau</b>, a fast Lua variant. Scripts get services with <b>game:GetService</b>, react to <b>events</b> like <b>Touched</b> and change Parts in the 3D world. <b>RemoteEvents</b> send messages between server and clients.",
         "local part = workspace.Part\npart.Touched:Connect(function(hit)\n    print(hit.Name .. ' touched me')\nend)"),
        ("Neovim", "📝", "Neovim Plugins & Config", "📝", [
            ("What language configures modern Neovim?", "", ["Lua", "Java", "C#", "Ruby"], 0),
            ("Type the vim table used for Neovim API calls", "vim.___.nvim_command", None, ["api"]),
            ("What is a plugin manager for?", "", ["Installing and updating plugins", "Compiling code", "Playing games", "Syncing clocks"], 0)],
         "<b>Neovim</b> uses Lua for configuration and plugins. The <b>vim.api</b> and <b>vim.keymap.set</b> functions create commands and shortcuts, and a plugin manager like <b>lazy.nvim</b> installs plugins. You can script your whole editor.",
         "vim.keymap.set('n', '<leader>w', ':w<CR>')\nvim.opt.number = true\nvim.api.nvim_create_user_command('Hi', function() print('hi') end, {})")],
    "R": [
        ("ML in R", "🤖", "Machine Learning in R", "🤖", [
            ("What is overfitting?", "", ["A model that memorizes training data", "A model that is too small", "A slow model", "A model with no data"], 0),
            ("Type the function that fits a linear model", "___(y ~ x, data = df)", None, ["lm"]),
            ("What does predict() do?", "", ["Estimates outcomes for new data", "Draws a plot", "Reads files", "Sorts"], 0)],
         "R fits models with formulas: <b>lm(y ~ x, data = df)</b> is a linear model and <b>glm</b> handles classification. <b>predict(model, newdata)</b> makes predictions. Evaluate on held-out data to detect <b>overfitting</b>; packages like <b>caret</b> and <b>tidymodels</b> streamline this.",
         "model <- lm(price ~ size, data = houses)\nsummary(model)\npredict(model, data.frame(size = 100))"),
        ("Shiny", "📊", "Shiny Dashboards", "📊", [
            ("What is Shiny?", "", ["A framework for interactive web apps in R", "A plotting theme", "A database", "A compiler"], 0),
            ("Type the end of the Shiny function that builds the page layout", "fluid___", None, ["Page"]),
            ("What makes a Shiny app interactive?", "", ["Reactive inputs and outputs", "Loops", "Packages", "Comments"], 0)],
         "<b>Shiny</b> turns R analysis into interactive web apps. The <b>ui</b> defines inputs (<b>sliderInput</b>) and outputs (<b>plotOutput</b>); the <b>server</b> function reacts to inputs and renders results. <b>Reactivity</b> re-runs only what depends on a changed input.",
         "ui <- fluidPage(sliderInput('n', 'N', 1, 100, 50), plotOutput('p'))\nserver <- function(input, output) {\n  output$p <- renderPlot(hist(rnorm(input$n)))\n}")],
    "Julia": [
        ("SciML", "🧪", "Differential Equations & SciML", "🧪", [
            ("What do differential equations model?", "", ["Change over time", "Colors", "File sizes", "Text"], 0),
            ("Type the neural network package name (hint: it flows)", "___.jl", None, ["Flux"]),
            ("What does Flux.jl do?", "", ["Builds neural networks", "Draws plots", "Reads CSV", "Compiles"], 0)],
         "Julia shines in scientific computing: <b>DifferentialEquations.jl</b> solves ODEs that model change over time (populations, circuits, planets), and <b>Flux.jl</b> builds neural networks. <b>SciML</b> mixes both: learning models from physics.",
         "using DifferentialEquations\nf(u, p, t) = -0.5u\nprob = ODEProblem(f, 1.0, (0.0, 5.0))\nsol = solve(prob)"),
        ("GPU Compute", "🚀", "GPU & Parallel Computing", "🚀", [
            ("What does a GPU excel at?", "", ["Many simple calculations in parallel", "One huge calculation", "Reading files", "Networking"], 0),
            ("Type the macro that runs loop iterations on threads", "Threads.@___ for i in 1:n", None, ["threads"]),
            ("Which package brings NVIDIA GPU support?", "", ["CUDA.jl", "Plots.jl", "JSON.jl", "HTTP.jl"], 0)],
         "Julia scales from threads to GPUs. <b>Threads.@threads</b> parallelizes loops on CPU cores and <b>CUDA.jl</b> runs array code on NVIDIA GPUs with almost no change: arrays become <b>CuArray</b>. Parallelism pays off when each task is big enough.",
         "using CUDA\na = CuArray(rand(1000))\nb = a .* 2\nprintln(sum(b))")],
    "Scala": [
        ("Spark", "🔥", "Apache Spark Pipelines", "🔥", [
            ("What does Spark do?", "", ["Processes big data across a cluster", "Draws UI", "Compiles Scala", "Manages Git"], 0),
            ("Type the Spark method that groups rows", "df.___('country')", None, ["groupBy"]),
            ("What is lazy evaluation in Spark?", "", ["Work runs only when an action is called", "Spark is slow", "Data is skipped", "Nothing runs"], 0)],
         "<b>Apache Spark</b> processes huge datasets across a cluster. You build a pipeline of <b>transformations</b> (<b>filter</b>, <b>groupBy</b>, <b>join</b>) that are <b>lazy</b>: nothing runs until an <b>action</b> like <b>count</b> or <b>show</b>. DataFrames and Datasets give typed, optimized queries.",
         'val out = df.filter($"age" > 18)\n  .groupBy("country")\n  .count()\nout.show()'),
        ("Akka", "🎭", "Akka Actors & Reactive Systems", "🎭", [
            ("What is an actor?", "", ["An object that processes messages one at a time", "A thread pool", "A database", "A class loader"], 0),
            ("Type the operator that sends a message in Akka", "actor ___ msg", None, ["!"]),
            ("What does supervision do?", "", ["Restarts failed actors", "Compiles code", "Prints logs", "Opens files"], 0)],
         "<b>Akka</b> uses the <b>actor model</b>: each actor owns its state and processes messages one at a time, so there are no locks. Actors send messages with <b>!</b>, and a <b>supervisor</b> decides whether to restart failing children. Great for resilient, reactive systems.",
         'class Greeter extends Actor {\n  def receive = {\n    case name: String => println(s"Hi $name")\n  }\n}\ngreeter ! "Ada"')],
    "Elixir": [
        ("Nx & ML", "🧠", "Machine Learning with Nx", "🧠", [
            ("What is Nx?", "", ["Elixir's numerical computing library", "A web framework", "A database", "A test tool"], 0),
            ("Type the Nx data structure for n-dimensional arrays", "Nx.___", None, ["tensor"]),
            ("Why use Nx?", "", ["Fast numerical code, even on GPUs", "To style pages", "To manage packages", "To write tests"], 0)],
         "<b>Nx</b> brings numerical computing and machine learning to Elixir with <b>tensors</b> (n-dimensional arrays) compiled for CPUs and GPUs. <b>Axon</b> builds neural networks and <b>Bumblebee</b> runs pre-trained models. Combine ML with Elixir's fault-tolerant servers.",
         "t = Nx.tensor([1, 2, 3])\nNx.sum(Nx.multiply(t, 2)) |> IO.inspect()"),
        ("Nerves IoT", "🔌", "Nerves & Embedded IoT", "🔌", [
            ("What is Nerves?", "", ["A framework for embedded devices in Elixir", "A database", "A web server", "A GUI toolkit"], 0),
            ("Type the single-board computer brand name ending in Pi", "Raspberry ___", None, ["Pi"]),
            ("Why use Elixir for IoT?", "", ["Fault tolerance and concurrency", "Tiny RAM use only", "No networking", "No tools"], 0)],
         "<b>Nerves</b> builds firmware for embedded devices like the Raspberry Pi using Elixir. It boots a minimal Linux straight into the Erlang VM, so you get supervision trees, hot updates and concurrency on tiny hardware. Great for IoT fleets.",
         "defmodule Blink do\n  def run do\n    Circuits.GPIO.write(pin, 1)\n    Process.sleep(500)\n  end\nend")],
}
for _n, _sp in SPEC.items():
    _b = len(LANGS[_n][2])
    _lanes = []
    for _i, (_ln, _le, _t, _e, _qs, _tx, _cd) in enumerate(_sp):
        LANGS[_n] = (LANGS[_n][0], LANGS[_n][1], LANGS[_n][2] + [(_t, _e, _qs)])
        TEACH[_n].append((_tx, _cd))
        _lanes.append((_ln, _le, [("l", _b + _i)]))
    BR2[_n] = _lanes


SR = 16000
SFX_DEF = {
    "correct": ([(76, .08), (83, .2)], "sine", .5),
    "wrong": ([(55, .12), (50, .28)], "square", .28),
    "click": ([(90, .03)], "sine", .3),
    "complete": ([(72, .1), (76, .1), (79, .1), (84, .35)], "square", .3),
    "fail": ([(67, .16), (64, .16), (60, .4)], "tri", .5),
    "chest": ([(79, .07), (83, .07), (86, .07), (91, .07), (95, .3)], "sine", .5),
}
CHORDS = [(48, (60, 64, 67)), (45, (57, 60, 64)), (41, (53, 57, 60)), (43, (55, 59, 62))]


def tone(m, dur, kind, vol, dec):
    f, n = 440.0 * 2 ** ((m - 69) / 12), int(SR * dur)
    out = []
    for i in range(n):
        ph = (i * f / SR) % 1.0
        v = math.sin(6.2831853 * ph) if kind == "sine" else (1.0 if ph < 0.5 else -1.0) if kind == "square" else 4 * abs(ph - 0.5) - 1
        out.append(v * vol * min(1.0, i / 120, (n - i) / 120) * (1 - dec * i / n))
    return out


def write_wav(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, x)) * 30000)) for x in samples))


def make_sfx(path, notes, kind, vol):
    smp = []
    for m, d in notes:
        smp += tone(m, d, kind, vol, .6)
    write_wav(path, smp)


def make_music(path):
    beat = 60 / 108
    mel, bass = [], []
    for rep_ in range(2):
        for root, ch in CHORDS:
            for k in range(8):
                idx = (0, 1, 2, 1, 0, 1, 2, 1)[k] if rep_ == 0 else (2, 1, 0, 1, 2, 1, 0, 2)[k]
                mel += tone(ch[idx] + 12, beat / 2, "square", .09, .5)
            for k in range(4):
                bass += tone(root, beat, "tri", .22, .3)
    n = min(len(mel), len(bass))
    write_wav(path + ".tmp", [mel[i] + bass[i] for i in range(n)])
    os.replace(path + ".tmp", path)


class _NoSound:
    ok = False

    def play(self, *a):
        pass

    def get(self, k):
        return True

    def put(self, *a):
        pass


SND = _NoSound()


def _set_snd(x):
    global SND
    SND = x


class Sound:
    D = {"sfx": True, "music": True, "sfxvol": 70, "musvol": 30}

    def __init__(self, st):
        self.st, self.fx, self.mus, self.ok, self.busy = st, {}, None, QSoundEffect is not None, False
        self.dir = os.path.join(os.path.expanduser("~"), ".codingo_audio")

    def get(self, k):
        return self.st.setdefault("settings", {}).get(k, self.D[k])

    def put(self, k, v, keep=True):
        self.st.setdefault("settings", {})[k] = v
        if keep:
            save(self.st)
        self.apply()

    def prepare(self):
        if not self.ok:
            return
        try:
            os.makedirs(self.dir, exist_ok=True)
            for name, (notes, kind, vol) in SFX_DEF.items():
                p = os.path.join(self.dir, f"v1_{name}.wav")
                if not os.path.exists(p):
                    make_sfx(p, notes, kind, vol)
                e = QSoundEffect()
                e.setSource(QUrl.fromLocalFile(p))
                self.fx[name] = e
        except Exception:
            self.ok = False

    def play(self, name):
        e = self.fx.get(name)
        if self.ok and e is not None and self.get("sfx"):
            e.setVolume(self.get("sfxvol") / 100)
            e.play()

    def apply(self):
        if not self.ok:
            return
        want = self.get("music")
        if want and self.mus is None:
            p = os.path.join(self.dir, "v1_music.wav")
            if os.path.exists(p):
                e = QSoundEffect()
                e.setSource(QUrl.fromLocalFile(p))
                e.setLoopCount(getattr(QSoundEffect, "Infinite", -2))
                self.mus = e
            elif not self.busy:
                self.busy = True
                threading.Thread(target=make_music, args=(p,), daemon=True).start()
                QTimer.singleShot(1500, self._again)
                return
        if self.mus is not None:
            self.mus.setVolume(self.get("musvol") / 100)
            if want and not self.mus.isPlaying():
                self.mus.play()
            elif not want and self.mus.isPlaying():
                self.mus.stop()

    def _again(self):
        self.busy = False
        self.apply()


class ClickFilter(QObject):
    def eventFilter(self, o, e):
        try:
            if e.type() == QEvent.MouseButtonRelease and isinstance(o, QPushButton) and o.isEnabled():
                SND.play("click")
        except Exception:
            pass
        return False


QDEF = {
    "lessons_any": ("📚", "Finish {n} lessons", (3, 5), 15),
    "lessons_lang": ("", "Finish {n} {lang} lessons", (3, 5), 25),
    "correct": ("✅", "Answer {n} questions correctly", (15, 25), 15),
    "kills": ("⚔️", "Defeat {n} monsters in the Coding Dungeon", (6, 10), 20),
    "project": ("🛠️", "Complete a project", (1, 1), 30),
    "combo": ("🔥", "Reach a 5-answer combo in one lesson", (1, 1), 20),
    "xp": ("⚡", "Earn {n} XP", (100, 150), 15),
}


class _NoQ:
    def add(self, *a, **k):
        pass

    def roll(self):
        pass

    def summary(self):
        return 0, 0


QST = _NoQ()


def _set_q(x):
    global QST
    QST = x


class Quest:
    def __init__(self, st):
        self.st = st
        self.roll()

    def roll(self):
        t, q = date.today().toordinal(), self.st.get("quests")
        if q and q.get("date") == t:
            return
        r = random.Random(t)
        langs = [l for l, p in self.st["prog"].items() if p > 0 and l in LANGS] or ["Python"]
        lst = []
        for k in [r.choice(["lessons_any", "lessons_lang"])] + r.sample(["correct", "kills", "project", "combo", "xp"], 2):
            ic, tx, (a, b), gm = QDEF[k]
            n = r.randint(a, b)
            lang = r.choice(langs) if k == "lessons_lang" else None
            lst.append({"kind": k, "lang": lang, "goal": n, "prog": 0, "gems": gm, "claimed": False,
                        "text": tx.format(n=n, lang=lang or ""), "icon": LANGS[lang][0] if lang else ic})
        self.st["quests"] = {"date": t, "list": lst, "bonus": False}
        save(self.st)

    def summary(self):
        self.roll()
        lst = self.st["quests"]["list"]
        return sum(x["prog"] >= x["goal"] for x in lst), len(lst)

    def add(self, kind, n=1, lang=None):
        self.roll()
        for qd in self.st["quests"]["list"]:
            k = qd["kind"]
            if (k == kind or (kind == "lessons" and k in ("lessons_any", "lessons_lang"))) and qd.get("lang") in (None, lang) and qd["prog"] < qd["goal"]:
                qd["prog"] = min(qd["goal"], qd["prog"] + n)
                if qd["prog"] >= qd["goal"]:
                    SND.play("chest")
        save(self.st)


def strip_comments(lang, code):
    if lang == "Lua":
        return re.sub(r"--.*", "", code)
    if lang in ("Python", "Ruby", "R", "Julia", "Elixir"):
        return re.sub(r"#.*", "", code)
    return re.sub(r"//.*|/\*[\s\S]*?\*/", "", code)


def syntax_ok(lang, code):
    t = re.sub(r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'", "S", code)
    st = []
    for ch in t:
        if ch in "([{":
            st.append(ch)
        elif ch in ")]}":
            if not st or "([{".index(st.pop()) != ")]}".index(ch):
                return False
    if st:
        return False
    if lang == "Python":
        for ln in t.splitlines():
            x = ln.strip()
            if re.match(r"(for|while|if|elif|else|def)\b", x) and not x.endswith(":"):
                return False
    elif lang == "C":
        if not re.search(r"\bint\s+main\s*\(", t) or re.search(r"\b(printf|return)\b[^;{}\n]*$", t, re.M):
            return False
    elif lang in ("Java", "C++"):
        if not re.search(r"\bmain\s*\(", t) or re.search(r"\b(System\.out\.println?|cout|return)\b[^;{}\n]*$", t, re.M):
            return False
    elif lang == "Rust":
        if not re.search(r"\bfn\s+main\s*\(", t):
            return False
    elif lang == "C#":
        if not re.search(r"\bMain\s*\(", t) or re.search(r"\bConsole\.WriteLine\b[^;{}\n]*$", t, re.M):
            return False
    elif lang == "Go":
        if not re.search(r"\bpackage\s+main\b", t) or not re.search(r"\bfunc\s+main\s*\(", t):
            return False
    elif lang == "Kotlin":
        if not re.search(r"\bfun\s+main\s*\(", t):
            return False
    elif lang == "PHP":
        if "<?php" not in t:
            return False
    elif lang == "Dart":
        if not re.search(r"\bmain\s*\(", t):
            return False
    return True


def check(lang, pi, code):
    c = strip_comments(lang, code)
    res = [("syntax looks valid (brackets, colons, semicolons)", syntax_ok(lang, c))]
    for label, rx in (CHECKS[pi] if pi < 100 else XPJ[pi - 100][6]):
        if rx == "FUNC":
            ok = len(re.findall(DEFRX, c)) >= (2 if lang in ("C", "C++", "Java", "C#", "Rust", "Go", "Kotlin", "Dart") else 1)
        else:
            ok = re.search(PRINT[lang] if rx == "PRINT" else rx, c, re.I) is not None
        res.append((label, ok))
    return res


QSS = f"""
QWidget{{background:#131f24;color:#fff;font-family:'Nunito','Segoe UI','Helvetica Neue',sans-serif;font-size:16px}}
QLabel{{background:transparent}}
QScrollArea{{border:none}}
QScrollBar:vertical{{background:transparent;width:10px;margin:4px 2px}}QScrollBar::handle:vertical{{background:#2b3d46;border-radius:4px;min-height:40px}}QScrollBar::handle:vertical:hover{{background:#3b5360}}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0}}
#top{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a2830,stop:1 #22343e);border-bottom:2px solid #2b3d46}}
#top QWidget{{background:transparent}}
#tab{{border:2px solid transparent;border-radius:14px;padding:8px 12px;font-weight:800;color:#8ea0a8}}
#tab:hover{{background:#22323b}}
#tab:checked{{background:#22323b;border:2px solid #37464f;color:#fff}}
#stats{{font-weight:800;font-size:18px;color:#ffc800}}
#hero{{border-radius:18px;margin:18px 28px 0 28px;padding:24px 30px;font-size:26px;font-weight:900}}
#title{{font-size:28px;font-weight:900}}
#hearts{{font-weight:900;font-size:18px;color:#ff4b4b;padding-left:12px}}
#code{{background:#0e171b;border:2px solid #2b3d46;border-radius:14px;padding:18px;font-family:{MONO};font-size:18px;color:#d6e4ea}}
#opt{{background:#1a2830;border:2px solid #2b3d46;border-bottom:5px solid #2b3d46;border-radius:16px;padding:14px 18px;text-align:left;font-family:{MONO};font-weight:700}}
#opt:hover{{background:#22323b;border-color:#40586a;border-bottom:5px solid #40586a}}
#opt:checked{{border-color:#49c0f8;background:#1b3340;color:#49c0f8}}
#opt[state="good"]{{border-color:#58cc02;background:#1d3a14;color:#89e219}}
#opt[state="bad"]{{border-color:#ff4b4b;background:#3a1717;color:#ff7878}}
#opt:disabled{{color:#8ea0a8}}
#opt[state="good"]:disabled{{color:#89e219}}
#opt[state="bad"]:disabled{{color:#ff7878}}
#daily{{background:#1a2830;border:2px solid #2b3d46;border-bottom:5px solid #ffc800;border-radius:16px;margin:10px 28px 0 28px;padding:14px 20px;text-align:left;font-weight:800;color:#ffc800}}
#daily:hover{{background:#22323b}}
#daily:disabled{{border-bottom:5px solid #58cc02;color:#58cc02}}
#card{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #203139,stop:1 #162228);border:2px solid #2b3d46;border-radius:16px}}
#big{{font-size:24px;font-weight:900}}
#inp{{background:#0e171b;border:2px solid #2b3d46;border-radius:14px;padding:16px;font-family:{MONO};font-size:20px;color:#fff}}
#inp:focus{{border-color:#49c0f8}}
#tog{{background:#2b3d46;border:none;border-bottom:4px solid #22323b;border-radius:14px;padding:8px 24px;font-weight:900;color:#8ea0a8}}
#tog:checked{{background:#58cc02;border-bottom:4px solid #46a302;color:#10200a}}
QSlider::groove:horizontal{{height:10px;background:#2b3d46;border-radius:5px}}
QSlider::sub-page:horizontal{{background:#58cc02;border-radius:5px}}
QSlider::handle:horizontal{{background:#fff;width:22px;margin:-7px 0;border-radius:11px}}
#x{{border:none;font-size:26px;color:#8ea0a8;padding:0 14px 0 0}}
#x:hover{{color:#fff}}
QProgressBar{{background:#2b3d46;border:none;border-radius:8px;min-height:16px;max-height:16px}}
QProgressBar::chunk{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #58cc02,stop:1 #a6f03a);border-radius:8px}}
#fb{{background:#131f24;border-top:2px solid #2b3d46}}
#fb QWidget{{background:transparent}}
#fb[state="good"]{{background:#1d3a14;border-top:2px solid #58cc02}}
#fb[state="bad"]{{background:#3a1717;border-top:2px solid #ff4b4b}}
#ft{{font-size:20px;font-weight:900}}
#fb[state="good"] #ft{{color:#89e219}}
#fb[state="bad"] #ft{{color:#ff7878}}
#act{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #6fe00b,stop:1 #58cc02);border:none;border-bottom:5px solid #46a302;border-radius:16px;padding:14px 44px;font-weight:900;color:#10200a}}
#act:hover{{background:#7bea1a}}
#act:pressed{{border-bottom:2px solid #46a302}}
#act:disabled{{background:#2b3d46;border-bottom:5px solid #22323b;color:#5c7079}}
#act[state="bad"]{{background:#ff4b4b;border-bottom:5px solid #ea2b2b;color:#fff}}
"""


def center(w, mw=720):
    box = QWidget()
    h = QHBoxLayout(box)
    h.setContentsMargins(0, 0, 0, 0)
    w.setMaximumWidth(mw)
    h.addStretch(1)
    h.addWidget(w, 100)
    h.addStretch(1)
    return box


def load():
    st = {"xp": 0, "streak": 0, "last": 0, "done": {}, "prog": {}, "name": "", "lessons": 0, "perfect": 0, "combo": 0, "dailies": 0, "daily": {}, "field": {}, "gems": 0, "chests": 0, "avatar": "🤖", "owned": ["🤖"], "chal": {}, "key": "", "pdone": {}, "extra": {}, "big": {}, "field2": {}}
    try:
        with open(SAVE) as f:
            st.update(json.load(f))
    except Exception:
        pass
    return st


def save(st):
    try:
        with open(SAVE, "w") as f:
            json.dump(st, f)
    except Exception:
        pass


CH = [("⚡", "Speed Round", 25, 3, 6, "Six quick questions and 3 hearts. Be fast and sharp!"),
      ("🧩", "Code Puzzle", 25, 3, 4, "Four typed answers only. No multiple choice to save you!"),
      ("🎯", "Perfect Run", 40, 1, 8, "Eight questions and just ONE heart. One slip and it is over. Wins a chest!")]
UNITS = [(0, "Unit 1", "Foundations"), (8, "Unit 2", "Logic & Loops"), (12, "Unit 3", "Data & Functions"), (16, "Unit 4", "Mastery"),
         ("f", "Crossroads", "Choose Your Field"), ("e", "Boss", "Boss 1")]


class Roadmap(QWidget):
    pick = Signal(int)
    chal = Signal(int)
    extra = Signal(int)
    skip = Signal(int)

    def __init__(self):
        super().__init__()
        self.lang, self.c, self.d, self.hov, self.ph, self.field = "Python", "#58cc02", 0, -1, 0.0, None
        self.t0 = 0.0
        self.cdone = ()
        self.xdone = ()
        self.field2 = None
        rnd = random.Random(7)
        self.stars = [(rnd.random(), rnd.random(), rnd.uniform(0.8, 2.2), rnd.uniform(0, 6.3)) for _ in range(80)]
        self.setMouseTracking(True)
        self.setMinimumHeight(int(self.items()[-1][1] + 140))
        self.t = QTimer(self)
        self.t.timeout.connect(self.tick)
        self.t.start(33)

    def set(self, lang, c, d, field, cdone=(), xdone=(), field2=None):
        self.field2 = field2
        self.cdone = cdone
        self.xdone = xdone
        if lang != self.lang:
            self.t0 = self.ph
        self.lang, self.c, self.d, self.field = lang, c, d, field
        self.update()

    def showEvent(self, e):
        self.t0 = self.ph
        super().showEvent(e)

    def uidx(self, key):
        T, LN = len(TRUNKS[self.lang]), len(BR[self.lang][0][2])
        E, LN2 = len(EXTN.get(self.lang, [])), len(BR2[self.lang][0][2])
        Bi = T + 1 + 2 * LN
        return key if isinstance(key, int) else {"f": T, "e": Bi, "x": Bi + 1, "f2": Bi + 1 + E, "z": Bi + 2 + E + 2 * LN2}[key]

    def items(self):
        TR = TRUNKS[self.lang]
        w, T, LN = self.width(), len(TR), len(BR[self.lang][0][2])
        EX, LN2, PO = EXTN.get(self.lang, []), len(BR2[self.lang][0][2]), POST.get(self.lang, [])
        amp, dx, y, out = min(w * 0.26, 190), min(w * 0.2, 150), 140, []
        starts = [u[0] for u in UN.get(self.lang, UNITS)]
        for i, (k, j) in enumerate(TR):
            if i and i in starts:
                y += 70
            out.append((w / 2 + amp * math.sin(i * 1.1), y, k, j, i, -1))
            y += 150
        y += 70
        out.append((w / 2, y, "f", 0, T, -1))
        y += 200
        for r in range(LN):
            for f in range(2):
                out.append((w / 2 + (dx if f else -dx), y, "l", BR[self.lang][f][2][r][1], T + 1 + r if self.field == f else None, f))
            y += 150
        F = T + 1 + LN
        out.append((w / 2, y + 70, "b", 0, F, -1))
        y += 290
        for n, (k, j) in enumerate(EX):
            out.append((w / 2 + amp * math.sin((n + 1) * 1.1), y, k, j, F + 1 + n, -1))
            y += 150
        S2 = F + 1 + len(EX)
        y += 70
        out.append((w / 2, y, "f", 1, S2, -1))
        y += 200
        for r in range(LN2):
            for f in range(2):
                out.append((w / 2 + (dx if f else -dx), y, "l", BR2[self.lang][f][2][r][1], S2 + 1 + r if self.field2 == f else None, f))
            y += 150
        y += 70
        for n, (k, j) in enumerate(PO):
            out.append((w / 2 + amp * math.sin((n + 1) * 1.1), y, k, j, S2 + 1 + LN2 + n, -1))
            y += 150
        return out

    def ypos(self, d):
        it = self.items()
        return int(next((q[1] for q in it if q[4] == d), it[-1][1]))

    def tick(self):
        self.ph += 0.033
        if self.isVisible():
            self.update()

    def hit(self, pos):
        for i, q in enumerate(self.items()):
            if math.hypot(pos.x() - q[0], pos.y() - q[1]) < 52:
                return q[4]
        return -1

    def side(self):
        I, w, out = self.items(), self.width(), []
        for i in range(len(TRUNKS[self.lang])):
            if i % 4 == 3:
                x, y = I[i][0], I[i][1]
                out.append((x + 175 if x < w / 2 else x - 175, y + 10, i, i // 4 % 3))
        return out

    def banner_at(self, pos):
        I, T, w, LN = self.items(), len(TRUNKS[self.lang]), self.width(), len(BR[self.lang][0][2])
        for key, tag, nm in UN.get(self.lang, UNITS):
            if key == "e" or (key in ("x", "f2", "z") and self.field is None) or (key == "z" and self.field2 is None):
                continue
            q = I[self.uidx(key)]
            if q[4] is not None and q[4] > self.d and QRectF(w / 2 - 170, q[1] - 100, 340, 44).contains(pos):
                return q[4]
        return -1

    def side2(self):
        I, w, out = self.items(), self.width(), []
        for i in range(len(TRUNKS[self.lang])):
            if i % 4 == 1:
                x, y = I[i][0], I[i][1]
                out.append((x + 165 if x < w / 2 else x - 165, y - 15, i))
        return out

    def xhit(self, pos):
        for cx, cy, i in self.side2():
            if math.hypot(pos.x() - cx, pos.y() - cy) < 30 and i < self.d and i not in self.xdone:
                return i
        return -1

    def chit(self, pos):
        for cx, cy, cid, kind in self.side():
            if math.hypot(pos.x() - cx, pos.y() - cy) < 36 and cid < self.d and cid not in self.cdone:
                return cid
        return -1

    def mouseMoveEvent(self, e):
        s = self.hit(e.position())
        h = s if s is not None and 0 <= s <= self.d else -1
        self.hov = h
        self.setCursor(Qt.PointingHandCursor if h >= 0 or self.chit(e.position()) >= 0 or self.xhit(e.position()) >= 0 or self.banner_at(e.position()) >= 0 else Qt.ArrowCursor)

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        bs = self.banner_at(e.position())
        if bs >= 0:
            self.skip.emit(bs)
            return
        c = self.chit(e.position())
        if c >= 0:
            self.chal.emit(c)
            return
        xi = self.xhit(e.position())
        if xi >= 0:
            self.extra.emit(xi)
            return
        s = self.hit(e.position())
        if s is not None and 0 <= s <= self.d:
            self.pick.emit(s)

    def shape(self, g, k, x, y, r, brush, pc):
        g.setBrush(brush)
        if k in ("l", "f"):
            g.setPen(Qt.NoPen)
            g.drawEllipse(QPointF(x, y), r, r)
            return
        g.setPen(QPen(pc, 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if k == "p":
            pts = [QPointF(x + (r - 4) * math.cos(n * math.pi / 3 + math.pi / 6), y + (r - 4) * math.sin(n * math.pi / 3 + math.pi / 6)) for n in range(6)]
        else:
            pts = [QPointF(x + (r - 4) * (1 if n % 2 == 0 else 0.84) * math.cos(n * math.pi / 8), y + (r - 4) * (1 if n % 2 == 0 else 0.84) * math.sin(n * math.pi / 8)) for n in range(16)]
        g.drawPolygon(QPolygonF(pts))

    def paintEvent(self, e):
        g = QPainter(self)
        g.setRenderHint(QPainter.Antialiasing)
        w, h, d, T, LN = self.width(), self.height(), self.d, len(TRUNKS[self.lang]), len(BR[self.lang][0][2])
        E, LN2, NP = len(EXTN.get(self.lang, [])), len(BR2[self.lang][0][2]), len(POST.get(self.lang, []))
        Bi = T + 1 + 2 * LN
        F2 = Bi + 1 + E
        P0 = F2 + 1 + 2 * LN2
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor("#16252c"))
        bg.setColorAt(1, QColor("#0c1418"))
        g.fillRect(self.rect(), bg)
        g.setPen(Qt.NoPen)
        for fx, fy, r, p in self.stars:
            g.setBrush(QColor(255, 255, 255, int(90 + 80 * math.sin(self.ph * 2 + p))))
            g.drawEllipse(QPointF(fx * w, fy * h), r, r)
        col = QColor(self.c)
        for fx, fy, rad, al in ((0.2, 0.06, 460, 46), (0.88, 0.32, 400, 34), (0.12, 0.6, 460, 32), (0.82, 0.88, 420, 38)):
            nb = QRadialGradient(fx * w, fy * h, rad)
            c0, c1 = QColor(col), QColor(col)
            c0.setAlpha(al)
            c1.setAlpha(0)
            nb.setColorAt(0, c0)
            nb.setColorAt(1, c1)
            g.fillRect(self.rect(), nb)
        I = self.items()
        ls = LANGS[self.lang][2]
        edges = ([(i, i + 1) for i in range(T)] + [(T, T + 1), (T, T + 2)]
                 + [(T + 1 + r * 2 + f, T + 3 + r * 2 + f) for r in range(LN - 1) for f in range(2)] + [(T + 1 + (LN - 1) * 2 + f, Bi) for f in range(2)]
                 + [(Bi + n, Bi + n + 1) for n in range(E + 1)] + [(F2, F2 + 1), (F2, F2 + 2)]
                 + [(F2 + 1 + r * 2 + f, F2 + 3 + r * 2 + f) for r in range(LN2 - 1) for f in range(2)] + [(F2 + 1 + (LN2 - 1) * 2 + f, P0) for f in range(2)]
                 + [(P0 + n, P0 + n + 1) for n in range(NP - 1)])
        for a, b in edges:
            my = (I[a][1] + I[b][1]) / 2
            p = QPainterPath(QPointF(I[a][0], I[a][1]))
            p.cubicTo(QPointF(I[a][0], my), QPointF(I[b][0], my), QPointF(I[b][0], I[b][1]))
            live = I[a][4] is not None and I[a][4] < d and I[b][4] is not None
            if live:
                gl = QColor(col)
                gl.setAlpha(45)
                g.setPen(QPen(gl, 34, Qt.SolidLine, Qt.RoundCap))
                g.drawPath(p)
            g.setPen(QPen(QColor("#1d2d35"), 24, Qt.SolidLine, Qt.RoundCap))
            g.drawPath(p)
            if live:
                g.setPen(QPen(col, 10, Qt.SolidLine, Qt.RoundCap))
            else:
                pen = QPen(QColor("#3a505b"), 4, Qt.CustomDashLine, Qt.RoundCap)
                pen.setDashPattern([0.5, 3.5])
                g.setPen(pen)
            g.drawPath(p)
            if live:
                g.setPen(Qt.NoPen)
                g.setBrush(QColor(255, 255, 255, 200))
                for m in range(3):
                    g.drawEllipse(p.pointAtPercent((self.ph * 0.35 + m / 3 + a * 0.13) % 1), 3.4, 3.4)
        f = QFont()
        f.setBold(True)
        f.setPixelSize(15)
        g.setFont(f)
        for key, tag, nm in UN.get(self.lang, UNITS):
            q = I[self.uidx(key)]
            on = q[4] is not None and q[4] <= d
            gr = QLinearGradient(w / 2 - 170, 0, w / 2 + 170, 0)
            gr.setColorAt(0, col if on else QColor("#22323b"))
            gr.setColorAt(1, col.darker(170) if on else QColor("#1a2830"))
            g.setPen(Qt.NoPen)
            g.setBrush(gr)
            g.drawRoundedRect(QRectF(w / 2 - 170, q[1] - 100, 340, 44), 22, 22)
            g.setPen(QColor("#fff") if on else QColor("#5c7079"))
            g.drawText(QRectF(w / 2 - 170, q[1] - 100, 340, 44), Qt.AlignCenter, f"{tag}  ·  {nm}" + ("   ⏩" if key != "e" and q[4] is not None and q[4] > d else ""))
        for br, b0, chosen in ((BR[self.lang], T + 1, self.field), (BR2[self.lang], F2 + 1, self.field2)):
            for n in range(2):
                q = I[b0 + n]
                on = chosen == n
                g.setPen(Qt.NoPen)
                g.setBrush(col if on else QColor("#22323b"))
                g.drawRoundedRect(QRectF(q[0] - 100, q[1] - 90, 200, 34), 17, 17)
                g.setPen(QColor("#fff") if on else QColor("#8ea0a8"))
                g.drawText(QRectF(q[0] - 100, q[1] - 90, 200, 34), Qt.AlignCenter, f"{br[n][1]} {br[n][0]}")
        bounce = math.sin(self.ph * 3) * 5
        for ni, (x, y, k, j, sp, lane) in enumerate(I):
            tt = min(1.0, max(0.0, (self.ph - self.t0 - ni * 0.045) / 0.4))
            if tt <= 0.02:
                continue
            g.setOpacity(min(1.0, tt * 1.6))
            ap = 1 + 2.70158 * (tt - 1) ** 3 + 1.70158 * (tt - 1) ** 2
            st = 2 if sp is None else 0 if sp < d else 1 if sp == d else 2
            r = (54 if k == "b" else 52 if k == "f" else 46 if k == "p" else 40) * (1.08 if sp is not None and sp == self.hov else 1.0) * ap
            ic, title = (ls[j][1], ls[j][0]) if k == "l" else (PROJ[j][1], PROJ[j][0]) if k == "p" else ("🔀", "Choose your field" if j == 0 else "Choose specialization") if k == "f" else ("👾", f"Boss {j + 1}")
            base = QColor("#ffc800") if st == 0 else col if st == 1 else QColor("#2b3d46")
            if st == 1:
                for n in (0, 1):
                    q = (self.ph * 0.9 + n * 0.5) % 1
                    g.setBrush(Qt.NoBrush)
                    g.setPen(QPen(QColor(col.red(), col.green(), col.blue(), int(150 * (1 - q))), 4))
                    g.drawEllipse(QPointF(x, y), r + 8 + 26 * q, r + 8 + 26 * q)
            sh = QRadialGradient(x, y + r + 8, r * 1.25)
            sh.setColorAt(0, QColor(0, 0, 0, 120))
            sh.setColorAt(1, QColor(0, 0, 0, 0))
            g.setPen(Qt.NoPen)
            g.setBrush(sh)
            g.drawEllipse(QPointF(x, y + r + 8), r * 1.25, r * 0.35)
            self.shape(g, k, x, y + 9, r, base.darker(170), base.darker(170))
            rg = QRadialGradient(x - r * 0.3, y - r * 0.45, r * 1.7)
            rg.setColorAt(0, base.lighter(135))
            rg.setColorAt(1, base)
            self.shape(g, k, x, y, r, rg, base)
            g.setPen(Qt.NoPen)
            g.setBrush(QColor(255, 255, 255, 50))
            g.drawEllipse(QPointF(x - r * 0.25, y - r * 0.52), r * 0.45, r * 0.2)
            f2 = QFont()
            f2.setBold(True)
            f2.setPixelSize(int(r * 0.85))
            g.setFont(f2)
            g.setPen(QColor("#fff"))
            g.drawText(QRectF(x - r, y - r - 2, 2 * r, 2 * r), Qt.AlignCenter, "✓" if st == 0 and k != "f" else ic if st < 2 else "🔒")
            f.setPixelSize(15)
            g.setFont(f)
            g.setPen(QColor("#fff") if st < 2 else QColor("#5c7079"))
            g.drawText(QRectF(x - 120, y + r + 14, 240, 24), Qt.AlignCenter, title)
            if st == 1:
                bx, by = x, y - r - 46 + bounce
                g.setPen(Qt.NoPen)
                g.setBrush(QColor("#fff"))
                g.drawRoundedRect(QRectF(bx - 46, by, 92, 32), 12, 12)
                g.drawPolygon(QPolygonF([QPointF(bx - 8, by + 31), QPointF(bx + 8, by + 31), QPointF(bx, by + 40)]))
                f.setPixelSize(14)
                g.setFont(f)
                g.setPen(QColor("#10200a"))
                g.drawText(QRectF(bx - 46, by, 92, 32), Qt.AlignCenter, "CHOOSE!" if k == "f" else "START!")
                f3 = QFont()
                f3.setPixelSize(44)
                g.setFont(f3)
                mx = x - 105 if x > w / 2 else x + 105
                g.drawText(QRectF(mx - 30, y - 30 + bounce, 60, 60), Qt.AlignCenter, "🤖")
        g.setOpacity(1.0)
        for cx, cy, cid, kind in self.side():
            st = 0 if cid in self.cdone else 1 if cid < d else 2
            x0, y0 = I[cid][0], I[cid][1]
            sg = 1 if cx > x0 else -1
            base = QColor("#ffc800") if st == 0 else QColor("#fb923c") if st == 1 else QColor("#2b3d46")
            pen = QPen(base if st < 2 else QColor("#3a505b"), 3, Qt.CustomDashLine, Qt.RoundCap)
            pen.setDashPattern([0.6, 3.2])
            g.setPen(pen)
            g.setBrush(Qt.NoBrush)
            g.drawLine(QPointF(x0 + 46 * sg, y0 + 6), QPointF(cx - 36 * sg, cy))
            r = 30 + (2 * math.sin(self.ph * 4) if st == 1 else 0)
            if st == 1:
                q = (self.ph * 0.9) % 1
                g.setPen(QPen(QColor(251, 146, 60, int(150 * (1 - q))), 3))
                g.drawRoundedRect(QRectF(cx - r - 8 - 14 * q, cy - r - 8 - 14 * q, 2 * (r + 8 + 14 * q), 2 * (r + 8 + 14 * q)), 18, 18)
            g.setPen(Qt.NoPen)
            g.setBrush(base.darker(170))
            g.drawRoundedRect(QRectF(cx - r, cy - r + 6, 2 * r, 2 * r), 14, 14)
            rg = QRadialGradient(cx - r * 0.3, cy - r * 0.45, r * 1.7)
            rg.setColorAt(0, base.lighter(135))
            rg.setColorAt(1, base)
            g.setBrush(rg)
            g.drawRoundedRect(QRectF(cx - r, cy - r, 2 * r, 2 * r), 14, 14)
            f4 = QFont()
            f4.setPixelSize(int(r * 0.95))
            g.setFont(f4)
            g.setPen(QColor("#fff"))
            g.drawText(QRectF(cx - r, cy - r - 2, 2 * r, 2 * r), Qt.AlignCenter, "✓" if st == 0 else CH[kind][0] if st == 1 else "🔒")
            f.setPixelSize(13)
            g.setFont(f)
            g.setPen(QColor("#fff") if st < 2 else QColor("#5c7079"))
            g.drawText(QRectF(cx - 70, cy + r + 8, 140, 20), Qt.AlignCenter, CH[kind][1])
        for cx, cy, i in self.side2():
            st = 0 if i in self.xdone else 1 if i < d else 2
            x0, y0 = I[i][0], I[i][1]
            sg = 1 if cx > x0 else -1
            base = QColor("#ffc800") if st == 0 else QColor("#2dd4bf") if st == 1 else QColor("#2b3d46")
            pen = QPen(base if st < 2 else QColor("#3a505b"), 2, Qt.CustomDashLine, Qt.RoundCap)
            pen.setDashPattern([0.6, 3.2])
            g.setPen(pen)
            g.setBrush(Qt.NoBrush)
            g.drawLine(QPointF(x0 + 44 * sg, y0 + 4), QPointF(cx - 26 * sg, cy))
            r = 24 + (1.5 * math.sin(self.ph * 5 + i) if st == 1 else 0)
            if st == 1:
                q = (self.ph * 0.9 + 0.3) % 1
                g.setPen(QPen(QColor(45, 212, 191, int(150 * (1 - q))), 3))
                g.drawEllipse(QPointF(cx, cy), r + 5 + 14 * q, r + 5 + 14 * q)
            g.setPen(Qt.NoPen)
            g.setBrush(base.darker(170))
            g.drawEllipse(QPointF(cx, cy + 5), r, r)
            rg = QRadialGradient(cx - r * 0.3, cy - r * 0.45, r * 1.7)
            rg.setColorAt(0, base.lighter(135))
            rg.setColorAt(1, base)
            g.setBrush(rg)
            g.drawEllipse(QPointF(cx, cy), r, r)
            f5 = QFont()
            f5.setPixelSize(int(r * 0.95))
            g.setFont(f5)
            g.setPen(QColor("#fff"))
            g.drawText(QRectF(cx - r, cy - r - 2, 2 * r, 2 * r), Qt.AlignCenter, "✓" if st == 0 else "✏️" if st == 1 else "🔒")
            f.setPixelSize(12)
            g.setFont(f)
            g.setPen(QColor("#fff") if st < 2 else QColor("#5c7079"))
            g.drawText(QRectF(cx - 60, cy + r + 6, 120, 18), Qt.AlignCenter, "Extra Practice")


class Home(QWidget):
    start = Signal(str, int)
    back = Signal()
    acct = Signal()
    shop = Signal()
    chal = Signal(str, int)
    tutor = Signal()
    projs = Signal()
    extra = Signal(str, int)
    skip = Signal(str, int)
    settings = Signal()
    dungeon = Signal()
    quests = Signal()
    daily = Signal(str)

    def __init__(self, st):
        super().__init__()
        self.st, self.lang = st, "Python"
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        top = QFrame()
        top.setObjectName("top")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(24, 12, 24, 12)
        self.tabs = {}
        bk = QPushButton("⇄  Languages")
        bk.setObjectName("tab")
        bk.setCursor(Qt.PointingHandCursor)
        bk.clicked.connect(self.back.emit)
        tl.addWidget(bk)
        self.acb = QPushButton()
        self.acb.setObjectName("tab")
        self.acb.setCursor(Qt.PointingHandCursor)
        self.acb.clicked.connect(self.acct.emit)
        tl.addWidget(self.acb)
        sb = QPushButton("🛍️  Shop")
        sb.setObjectName("tab")
        sb.setCursor(Qt.PointingHandCursor)
        sb.clicked.connect(self.shop.emit)
        tl.addWidget(sb)
        ab = QPushButton("🤖  Ask Byte")
        ab.setObjectName("tab")
        ab.setCursor(Qt.PointingHandCursor)
        ab.clicked.connect(self.tutor.emit)
        tl.addWidget(ab)
        pb = QPushButton("🛠️  Projects")
        pb.setObjectName("tab")
        pb.setCursor(Qt.PointingHandCursor)
        pb.clicked.connect(self.projs.emit)
        tl.addWidget(pb)
        db = QPushButton("🏰  Dungeon")
        db.setObjectName("tab")
        db.setCursor(Qt.PointingHandCursor)
        db.clicked.connect(self.dungeon.emit)
        tl.addWidget(db)
        self.qb = QPushButton("📜  Quests")
        self.qb.setObjectName("tab")
        self.qb.setCursor(Qt.PointingHandCursor)
        self.qb.clicked.connect(self.quests.emit)
        tl.addWidget(self.qb)
        gb = QPushButton("⚙️")
        gb.setObjectName("tab")
        gb.setToolTip("Settings")
        gb.setCursor(Qt.PointingHandCursor)
        gb.clicked.connect(self.settings.emit)
        tl.addWidget(gb)
        tl.addStretch()
        self.stats = QLabel()
        self.stats.setObjectName("stats")
        tl.addWidget(self.stats)
        root.addWidget(top)
        self.hero = QLabel()
        self.hero.setObjectName("hero")
        root.addWidget(self.hero)
        self.tip = QLabel()
        self.tip.setStyleSheet("background:#1a2830;border:2px solid #2b3d46;border-radius:14px;padding:10px 16px;color:#b9c8cf;margin:12px 28px 0 28px")
        root.addWidget(self.tip)
        self.dbtn = QPushButton()
        self.dbtn.setObjectName("daily")
        self.dbtn.setCursor(Qt.PointingHandCursor)
        self.dbtn.clicked.connect(lambda: self.daily.emit(self.lang))
        root.addWidget(self.dbtn)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        self.sc = sc
        self.road = Roadmap()
        self.road.pick.connect(lambda i: self.start.emit(self.lang, i))
        self.road.chal.connect(lambda i: self.chal.emit(self.lang, i))
        self.road.extra.connect(lambda i: self.extra.emit(self.lang, i))
        self.road.skip.connect(lambda i: self.skip.emit(self.lang, i))
        sc.setWidget(self.road)
        root.addWidget(sc)
        self.refresh()

    def pick(self, n):
        self.lang = n
        self.refresh()

    def refresh(self):
        ic, c, ls = LANGS[self.lang]
        d = self.st["prog"].get(self.lang, 0)
        self.hero.setText(f"{ic}  {self.lang}   ·   {min(d, total(self.lang))}/{total(self.lang)} steps")
        self.hero.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {c},stop:1 #1f2c34);color:#fff")
        self.tip.setText(random.choice(TIPS))
        self.acb.setText(f"{self.st['avatar']}  {self.st['name'] or 'Account'}")
        qd, qt = QST.summary()
        self.qb.setText(f"📜  Quests {qd}/{qt}")
        dn = self.st["daily"].get(self.lang) == date.today().toordinal()
        self.dbtn.setEnabled(not dn)
        self.dbtn.setText("✅  Daily exercises complete. Come back tomorrow!" if dn else "📅  Daily exercises  ·  5 questions  ·  +25 XP")
        xp = self.st["xp"]
        self.stats.setText(f"🏅 Lv {xp // 150 + 1} {TITLES[min(xp // 150, 5)]}     🔥 {self.st['streak']}     ⚡ {xp % 150}/150     💎 {self.st['gems']}")
        for n, b in self.tabs.items():
            b.setChecked(n == self.lang)
        self.road.set(self.lang, c, d, self.st["field"].get(self.lang), self.st["chal"].get(self.lang, []), self.st["extra"].get(self.lang, []), self.st["field2"].get(self.lang))
        QTimer.singleShot(80, lambda: self.sc.ensureVisible(self.road.width() // 2, self.road.ypos(d), 0, 280))


class Lesson(QWidget):
    done = Signal(bool, int)
    ask = Signal(str, str)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        bar = QHBoxLayout()
        bar.setContentsMargins(28, 22, 28, 0)
        x = QPushButton("✕")
        x.setObjectName("x")
        x.setCursor(Qt.PointingHandCursor)
        x.clicked.connect(lambda: self.done.emit(False, 0))
        self.pb = QProgressBar()
        self.pb.setTextVisible(False)
        self.hl = QLabel()
        self.hl.setObjectName("hearts")
        bar.addWidget(x)
        bar.addWidget(self.pb, 1)
        bar.addWidget(self.hl)
        root.addLayout(bar)
        self.pages = FadeStack()
        root.addWidget(self.pages, 1)
        q = QWidget()
        ql = QVBoxLayout(q)
        ql.setContentsMargins(30, 30, 30, 20)
        ql.setSpacing(18)
        self.pr = QLabel()
        self.pr.setObjectName("title")
        self.pr.setWordWrap(True)
        self.cd = QLabel()
        self.cd.setObjectName("code")
        self.cd.setTextFormat(Qt.PlainText)
        self.ol = QVBoxLayout()
        self.ol.setSpacing(12)
        ql.addWidget(self.pr)
        ql.addWidget(self.cd)
        ql.addLayout(self.ol)
        self.inp = QLineEdit()
        self.inp.setObjectName("inp")
        self.inp.setPlaceholderText("Type your answer…")
        self.inp.textChanged.connect(lambda t: self.act.setEnabled(bool(t.strip()) and not self.checked))
        self.inp.returnPressed.connect(lambda: self.act.isEnabled() and self.go())
        ql.addWidget(self.inp)
        ql.addStretch()
        self.pages.addWidget(center(q))
        self.rt = QLabel()
        self.rt.setAlignment(Qt.AlignCenter)
        self.rt.setTextFormat(Qt.RichText)
        self.pages.addWidget(self.rt)
        ip = QWidget()
        il2 = QVBoxLayout(ip)
        il2.setContentsMargins(30, 30, 30, 20)
        il2.setSpacing(16)
        self.it = QLabel()
        self.it.setObjectName("title")
        self.it.setWordWrap(True)
        self.ib = QLabel()
        self.ib.setWordWrap(True)
        self.ib.setTextFormat(Qt.RichText)
        self.ib.setStyleSheet("font-size:18px;color:#d6e4ea")
        self.ic = QLabel()
        self.ic.setObjectName("code")
        self.ic.setTextFormat(Qt.PlainText)
        il2.addWidget(self.it)
        il2.addWidget(self.ib)
        il2.addWidget(self.ic)
        il2.addStretch()
        self.pages.addWidget(center(ip))
        self.fb = QFrame()
        self.fb.setObjectName("fb")
        fl = QVBoxLayout(self.fb)
        fl.setContentsMargins(30, 18, 30, 18)
        inner = QWidget()
        il = QHBoxLayout(inner)
        il.setContentsMargins(0, 0, 0, 0)
        self.ft = QLabel()
        self.ft.setObjectName("ft")
        self.act = QPushButton("CHECK")
        self.act.setObjectName("act")
        self.act.setCursor(Qt.PointingHandCursor)
        self.act.clicked.connect(self.go)
        self.eb = QPushButton("💡 EXPLAIN")
        self.eb.setObjectName("tab")
        self.eb.setStyleSheet("color:#fff")
        self.eb.setCursor(Qt.PointingHandCursor)
        self.eb.clicked.connect(self.explain)
        self.eb.hide()
        il.addWidget(self.ft, 1)
        il.addWidget(self.eb)
        il.addWidget(self.act)
        fl.addWidget(center(inner))
        root.addWidget(self.fb)

    def repol(self):
        for w in [self.fb, self.act] + self.opts:
            w.style().unpolish(w)
            w.style().polish(w)

    def begin(self, lang, i, boss=None, daily=False, ch=None):
        self.boss = bool(boss) and not daily
        self.daily = daily
        self.lang = lang
        self.queue = list(boss) if boss else list(LANGS[lang][2][i][2])
        self.total = len(self.queue)
        self.solved = self.mistakes = self.combo = self.best = 0
        self.hearts = ch[3] if ch else 3 if self.boss else 5
        self.over = False
        self.opts = []
        if ch:
            t, e, txt, code = ch[1], ch[0], ch[2], ""
        elif daily:
            t, e, txt, code = "Daily Exercises", "📅", "Five quick questions picked for today. Finish them to keep your streak alive and earn <b>+25 bonus XP</b>.", ""
        elif boss:
            t, e, txt, code = f"Boss {getattr(self, 'bossn', 1)}", "👾", "A wild <b>Bug King</b> appears! Answer 10 random questions from everything you learned. You only have <b>3 hearts</b> - lose them all and the bug wins.", ""
        else:
            t, e, _q = LANGS[lang][2][i]
            txt, code = TEACH[lang][i]
        self.it.setText(f"{e}  {t}")
        self.ib.setText("<i style='color:#49c0f8'>🤖 Byte: let me explain!</i><br><br>" + txt)
        self.ic.setText(code)
        self.ic.setVisible(bool(code))
        self.checked = True
        self.intro = True
        self.pages.setCurrentIndex(2)
        self.hl.setText(f"❤ {self.hearts}")
        self.pb.setValue(0)
        self.fb.setProperty("state", "")
        self.act.setProperty("state", "")
        self.ft.setText("")
        self.act.setText("START LESSON")
        self.act.setEnabled(True)
        self.repol()

    def show_q(self):
        self.q = self.queue.pop(0)
        p, c, o, a = self.q
        if o:
            k = random.sample(range(len(o)), len(o))
            o, a = [o[x] for x in k], k.index(a)
            self.q = (p, c, o, a)
        self.pr.setText(p)
        self.cd.setText(c)
        self.cd.setVisible(bool(c))
        while self.ol.count():
            self.ol.takeAt(0).widget().deleteLater()
        self.opts, self.sel, self.checked = [], None, False
        self.eb.hide()
        for i, t in enumerate(o or []):
            b = QPushButton(f"{i + 1}    {t}")
            b.setObjectName("opt")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, i=i: self.pick(i))
            self.ol.addWidget(b)
            self.opts.append(b)
        self.fb.setProperty("state", "")
        self.act.setProperty("state", "")
        self.ft.setText("")
        self.act.setText("CHECK")
        self.inp.setVisible(o is None)
        self.inp.setEnabled(True)
        self.inp.clear()
        self.act.setEnabled(False)
        if o is None:
            self.inp.setFocus()
        self.hl.setText(f"❤ {self.hearts}")
        self.setpb(int(100 * self.solved / self.total))
        self.repol()
        fade(self.pr, 300)
        if c:
            fade(self.cd, 300, 80)
        for n, b in enumerate(self.opts):
            fade(b, 260, 120 + 70 * n)
        if o is None:
            fade(self.inp, 260, 120)

    def pick(self, i):
        if self.checked:
            return
        for j, b in enumerate(self.opts):
            b.setChecked(j == i)
        self.sel = i
        self.act.setEnabled(True)

    def check(self):
        a = self.q[3]
        typed = self.q[2] is None
        if typed:
            ok = "".join(self.inp.text().split()) in ["".join(x.split()) for x in a]
            self.inp.setEnabled(False)
        else:
            ok = self.sel == a
        self.checked = True
        for j, b in enumerate(self.opts):
            b.setEnabled(False)
            if j == a:
                b.setProperty("state", "good")
            elif j == self.sel:
                b.setProperty("state", "bad")
        if ok:
            self.solved += 1
            self.combo += 1
            self.best = max(self.best, self.combo)
            self.bounce(self.inp if typed else self.opts[self.sel])
            SND.play("correct")
            QST.add("correct")
            self.ft.setText(f"✓  {random.choice(PRAISE)}" + (f"   🔥 x{self.combo}" if self.combo > 1 else ""))
        else:
            self.hearts -= 1
            self.mistakes += 1
            self.combo = 0
            self.shake(self.inp if typed else self.opts[self.sel])
            self.shake(self.hl)
            SND.play("wrong")
            self.queue.append(self.q)
            self.ft.setText(f"✗  {random.choice(OOPS)}  Answer: {a[0] if typed else self.q[2][a]}")
        self.fb.setProperty("state", "good" if ok else "bad")
        self.act.setProperty("state", "" if ok else "bad")
        self.act.setText("CONTINUE")
        self.eb.show()
        fade(self.ft, 240)
        self.hl.setText(f"❤ {max(self.hearts, 0)}")
        self.setpb(int(100 * self.solved / self.total))
        self.repol()

    def end(self, win):
        self.over, self.win = True, win
        self.xp = (max(5, 10 * self.total - 4 * self.mistakes) + 2 * self.best + (20 if not self.mistakes else 0) + (30 if self.boss else 0)) if win else 0
        self.gems = ((30 if self.boss else 10 if self.daily else 5) + (5 if not self.mistakes else 0)) if win else 0
        if win:
            self.rt.setText(
                f"<div style='font-size:80px'>{'👑' if self.boss else '🏆'}</div><div style='font-size:34px;font-weight:900;color:#ffc800'>{'Boss defeated!' if self.boss else 'Lesson complete!'}</div>"
                f"<div style='font-size:22px;font-weight:800;color:#49c0f8'>⚡ +{self.xp} XP &nbsp;&nbsp; ❤ {self.hearts} left &nbsp;&nbsp; 💎 +{self.gems}</div><div style='font-size:18px;color:#ffc800'>{self.badges()}</div><div style='font-size:15px;color:#8ea0a8'><br>💡 {random.choice(FACTS)}</div>")
        else:
            self.rt.setText(
                "<div style='font-size:80px'>💔</div><div style='font-size:34px;font-weight:900;color:#ff7878'>Out of hearts</div>"
                "<div style='font-size:20px;color:#8ea0a8'>Try again, you got this.</div>")
        self.pages.setCurrentIndex(1)
        SND.play("complete" if win else "fail")
        if win and self.best >= 5:
            QST.add("combo")
        if win:
            self.fx.burst()
        self.fb.setProperty("state", "")
        self.ft.setText("")
        self.act.setText("CONTINUE")
        self.eb.hide()
        self.act.setEnabled(True)
        self.repol()

    def explain(self):
        p, c, o, a = self.q
        right = a[0] if o is None else o[a]
        mine = self.inp.text() if o is None else (o[self.sel] if self.sel is not None else "")
        t = f"I'm learning {self.lang}. Please explain this question simply and tell me why the right answer is correct.\n\nQuestion: {p}\n"
        t += (f"Code:\n{c}\n" if c else "") + (f"Options: {', '.join(o)}\n" if o else "") + f"Correct answer: {right}\nMy answer: {mine}"
        self.ask.emit(self.lang, t)

    def setpb(self, v):
        a = QPropertyAnimation(self.pb, b"value", self)
        a.setDuration(380)
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.setStartValue(self.pb.value())
        a.setEndValue(v)
        a.start(QAbstractAnimation.DeleteWhenStopped)

    def shake(self, w):
        p = w.pos()
        a = QPropertyAnimation(w, b"pos", self)
        a.setDuration(400)
        for t, dx in ((0, 0), (0.2, -12), (0.4, 12), (0.6, -8), (0.8, 6), (1, 0)):
            a.setKeyValueAt(t, QPoint(p.x() + dx, p.y()))
        a.start(QAbstractAnimation.DeleteWhenStopped)

    def bounce(self, w):
        p = w.pos()
        a = QPropertyAnimation(w, b"pos", self)
        a.setDuration(320)
        for t, dy in ((0, 0), (0.35, -9), (0.7, 2), (1, 0)):
            a.setKeyValueAt(t, QPoint(p.x(), p.y() + dy))
        a.start(QAbstractAnimation.DeleteWhenStopped)

    def badges(self):
        b = []
        if not self.mistakes:
            b.append("💎 Perfect lesson +20")
        if self.best >= 4:
            b.append(f"🔥 Combo x{self.best}")
        if self.boss:
            b.append("👑 Boss slayer +30 · 🎁 Chest")
        return " &nbsp; ".join(b)

    def go(self):
        if self.over:
            self.done.emit(self.win, self.xp)
        elif self.intro:
            self.intro = False
            self.pages.setCurrentIndex(0)
            self.show_q()
        elif not self.checked:
            self.check()
        elif self.hearts <= 0:
            self.end(False)
        elif not self.queue:
            self.end(True)
        else:
            self.show_q()


class Project(QWidget):
    done = Signal(bool, int)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(30, 22, 30, 14)
        bl.setSpacing(12)
        top = QHBoxLayout()
        x = QPushButton("✕")
        x.setObjectName("x")
        x.setCursor(Qt.PointingHandCursor)
        x.clicked.connect(lambda: self.done.emit(False, 0))
        self.hd = QLabel()
        self.hd.setObjectName("title")
        top.addWidget(x)
        top.addWidget(self.hd, 1)
        self.ds = QLabel()
        self.ds.setWordWrap(True)
        self.ds.setTextFormat(Qt.RichText)
        self.ds.setStyleSheet("font-size:17px;color:#d6e4ea")
        self.ed = QPlainTextEdit()
        self.ed.setObjectName("inp")
        self.ed.setStyleSheet("font-size:16px")
        self.ed.setTabStopDistance(32)
        self.out = QLabel()
        self.out.setObjectName("code")
        self.out.setWordWrap(True)
        self.out.setTextFormat(Qt.PlainText)
        self.out.setMinimumHeight(140)
        bl.addLayout(top)
        bl.addWidget(self.ds)
        bl.addWidget(self.ed, 1)
        bl.addWidget(self.out)
        root.addWidget(center(body, 900), 1)
        self.fb = QFrame()
        self.fb.setObjectName("fb")
        fl = QVBoxLayout(self.fb)
        fl.setContentsMargins(30, 18, 30, 18)
        inner = QWidget()
        il = QHBoxLayout(inner)
        il.setContentsMargins(0, 0, 0, 0)
        self.ft = QLabel()
        self.ft.setObjectName("ft")
        self.act = QPushButton("CHECK")
        self.act.setObjectName("act")
        self.act.setCursor(Qt.PointingHandCursor)
        self.act.clicked.connect(self.go)
        il.addWidget(self.ft, 1)
        il.addWidget(self.act)
        fl.addWidget(center(inner, 900))
        root.addWidget(self.fb)

    def repol(self):
        for w in (self.fb, self.act):
            w.style().unpolish(w)
            w.style().polish(w)

    def begin(self, lang, pi):
        if pi >= 100:
            t, e, d = XPJ[pi - 100][:3]
            self.xpv, self.rw = XPJ[pi - 100][5], f"+{XPJ[pi - 100][5]} XP · 💎 {XPJ[pi - 100][4]}" + (" · 🎁 chest" if XPJ[pi - 100][3] == "hard" else "")
        else:
            t, e, d = PROJ[pi]
            self.xpv, self.rw = 50, "+50 XP · 💎 15 · 🎁 chest"
        self.lang, self.pi, self.passed = lang, pi, False
        self.hd.setText(f"{e}  Project: {t}")
        self.ds.setText(d)
        self.ed.setPlainText(skeleton(lang, "your code here") if pi >= 100 else STARTER[lang][pi])
        self.out.setText("Press CHECK to test your code.")
        self.ft.setText("")
        self.act.setText("CHECK")
        self.fb.setProperty("state", "")
        self.act.setProperty("state", "")
        self.repol()

    def begin_big(self, lang, bi, m, code):
        t, e, blurb, ms = BIGP[bi]
        self.lang, self.pi, self.passed, self.ms = lang, 1000 + bi, False, ms[:m + 1]
        self.hd.setText(f"{e}  {t}  ·  Milestone {m + 1}/{len(ms)}")
        self.ds.setText(f"<b>{ms[m][0]}</b><br>{ms[m][1]}<br><span style='color:#8ea0a8'>Your code is saved. Keep building on the same program!</span>")
        self.ed.setPlainText(code or skeleton(lang, "your project starts here"))
        self.out.setText("Press CHECK to test your code. Earlier features must keep working (↩).")
        self.ft.setText("")
        self.act.setText("CHECK")
        self.fb.setProperty("state", "")
        self.act.setProperty("state", "")
        self.xpv = 60
        self.rw = "+60 XP · 💎 15" + (" · 💎 100 bonus · 🎁 chest" if m + 1 == len(ms) else "")
        self.repol()

    def go(self):
        if self.passed:
            self.done.emit(True, self.xpv)
            return
        res = bigcheck(self.lang, self.ms, self.ed.toPlainText()) if self.pi >= 1000 else check(self.lang, self.pi, self.ed.toPlainText())
        self.out.setText("\n".join(("✓  " if g else "✗  ") + t for t, g in res))
        good = all(g for _, g in res)
        self.passed = good
        SND.play("complete" if good else "wrong")
        if good:
            self.fx.burst()
        self.fb.setProperty("state", "good" if good else "bad")
        self.act.setProperty("state", "" if good else "bad")
        self.ft.setText("✓  All checks passed! " + self.rw if good else "✗  Some checks failed. Fix and press CHECK")
        self.act.setText("CONTINUE" if good else "CHECK")
        self.repol()


AV = [("🤖", "Byte", 0), ("🦊", "Fox", 30), ("🐱", "Cat", 30), ("🐼", "Panda", 40), ("👽", "Alien", 60), ("🚀", "Rocket", 70), ("🦄", "Unicorn", 80), ("🥷", "Ninja", 90),
      ("🧙", "Wizard", 100), ("🐉", "Dragon", 120), ("🦖", "T-Rex", 150), ("👑", "Crown", 200)]
MSG = "QPushButton{background:#22323b;border:2px solid #37464f;border-radius:12px;padding:10px 22px;font-weight:800}QPushButton:hover{background:#2b3d46}QLabel{font-size:22px;font-weight:900}"


def wiggle(w):
    p = w.pos()
    a = QPropertyAnimation(w, b"pos", w)
    a.setDuration(600)
    for t, dx in ((0, 0), (0.1, -8), (0.2, 8), (0.3, -8), (0.4, 8), (0.5, -6), (0.6, 6), (0.7, -4), (0.8, 4), (1, 0)):
        a.setKeyValueAt(t, QPoint(p.x() + dx, p.y()))
    a.start(QAbstractAnimation.DeleteWhenStopped)


class Shop(QWidget):
    back = Signal()

    def __init__(self, st):
        super().__init__()
        self.st = st
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.setContentsMargins(28, 20, 28, 0)
        x = QPushButton("←")
        x.setObjectName("x")
        x.setCursor(Qt.PointingHandCursor)
        x.clicked.connect(self.back.emit)
        h = QLabel("Shop")
        h.setObjectName("title")
        self.gl = QLabel()
        self.gl.setObjectName("stats")
        bar.addWidget(x)
        bar.addWidget(h, 1)
        bar.addWidget(self.gl)
        root.addLayout(bar)
        self.body = QWidget()
        self.col = QVBoxLayout(self.body)
        self.col.setSpacing(16)
        self.col.setContentsMargins(30, 20, 30, 30)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(center(self.body, 780))
        root.addWidget(sc, 1)

    def sec(self, t):
        lb = QLabel(t)
        lb.setStyleSheet("font-size:22px;font-weight:900")
        return lb

    def refresh(self):
        st = self.st
        while self.col.count():
            w = self.col.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.gl.setText(f"💎 {st['gems']}")
        self.col.addWidget(self.sec("🎁  Chests"))
        card = QFrame()
        card.setObjectName("card")
        cl = QHBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        self.chest = QLabel("🎁")
        self.chest.setStyleSheet("font-size:60px")
        info = QLabel(f"You have <b>{st['chests']}</b> chest(s)<br><span style='color:#8ea0a8'>Win them from projects and bosses. Loot: gems or a brand new avatar!</span>")
        info.setTextFormat(Qt.RichText)
        info.setWordWrap(True)
        ob = QPushButton("OPEN")
        ob.setObjectName("act")
        ob.setEnabled(st["chests"] > 0)
        ob.setCursor(Qt.PointingHandCursor)
        ob.clicked.connect(self.open)
        bb = QPushButton("BUY  💎 50")
        bb.setObjectName("act")
        bb.setEnabled(st["gems"] >= 50)
        bb.setCursor(Qt.PointingHandCursor)
        bb.clicked.connect(self.buy)
        for w in (ob, bb):
            w.setStyleSheet("padding:12px 22px")
        cl.addWidget(self.chest)
        cl.addWidget(info, 1)
        cl.addWidget(ob)
        cl.addWidget(bb)
        self.col.addWidget(card)
        self.col.addWidget(self.sec("🎭  Avatars"))
        g = QGridLayout()
        g.setSpacing(14)
        for n, (e, nm, pr) in enumerate(AV):
            c = QFrame()
            c.setObjectName("card")
            c.setFixedSize(165, 200)
            v = QVBoxLayout(c)
            v.setAlignment(Qt.AlignHCenter)
            em = QLabel(e)
            em.setAlignment(Qt.AlignCenter)
            em.setStyleSheet("font-size:52px")
            nl = QLabel(nm)
            nl.setAlignment(Qt.AlignCenter)
            nl.setStyleSheet("font-weight:800")
            own, eq = e in st["owned"], e == st["avatar"]
            b = QPushButton("EQUIPPED ✓" if eq else "EQUIP" if own else f"💎 {pr}")
            b.setObjectName("act")
            b.setEnabled(not eq and (own or st["gems"] >= pr))
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("padding:8px 10px;font-size:14px")
            b.clicked.connect(lambda _, e=e, pr=pr: self.act(e, pr))
            if eq:
                c.setStyleSheet("QFrame#card{border:2px solid #58cc02}")
            v.addWidget(em)
            v.addWidget(nl)
            v.addWidget(b)
            g.addWidget(c, n // 4, n % 4)
        gw = QWidget()
        gw.setLayout(g)
        self.col.addWidget(gw)
        self.col.addStretch()

    def act(self, e, pr):
        st = self.st
        if e in st["owned"]:
            st["avatar"] = e
        elif st["gems"] >= pr:
            st["gems"] -= pr
            st["owned"].append(e)
            st["avatar"] = e
            self.fx.burst()
        save(st)
        self.refresh()

    def buy(self):
        if self.st["gems"] >= 50:
            self.st["gems"] -= 50
            self.st["chests"] += 1
            save(self.st)
            self.refresh()

    def open(self):
        wiggle(self.chest)
        QTimer.singleShot(650, self.reveal)

    def reveal(self):
        st = self.st
        if st["chests"] <= 0:
            return
        st["chests"] -= 1
        lock = [a for a in AV if a[0] not in st["owned"]]
        if lock and random.random() < 0.3:
            e, nm, _ = random.choice(lock)
            st["owned"].append(e)
            msg = f"{e}  New avatar: {nm}!"
        else:
            g = random.choice([10, 15, 20, 25, 30, 40])
            st["gems"] += g
            msg = f"💎  +{g} gems!"
        save(st)
        SND.play("chest")
        self.fx.burst()
        self.refresh()
        m = QMessageBox(self)
        m.setWindowTitle("Chest opened!")
        m.setText(msg)
        m.setStyleSheet(MSG)
        m.exec()


STOP = set("the a an is are was what whats how do does did i to of in and it me you can could would explain tell about why my this that for with on use used please give show help understand mean means work works thing stuff really like get make need want know learn".split())
GLOSS = [
    (("variable", "variables"), "A **variable** is a named box that stores a value, like `age = 20`. You can read it or change it later."),
    (("loop", "loops", "iterate", "repeat"), "A **loop** repeats code. `for` loops go through items or count steps; `while` loops run as long as a condition is true."),
    (("function", "functions", "method", "methods"), "A **function** is a reusable block of code with a name. You give it inputs (parameters) and it can give back a result (`return`)."),
    (("array", "arrays", "list", "lists", "vector"), "A **list/array** stores many values in order. You reach each one by its index, and the first index is usually 0."),
    (("string", "strings", "text"), "A **string** is text written inside quotes. You can join, slice and search strings with built-in tools."),
    (("type", "types", "integer", "int", "float", "double", "boolean"), "**Types** say what kind of data a value is: whole numbers (int), decimals (float/double), text (string) and true/false (boolean)."),
    (("if", "condition", "conditions", "else", "branch"), "An **if statement** runs code only when a condition is true. Add `else if` and `else` for other cases; only the first match runs."),
    (("recursion", "recursive"), "**Recursion** is when a function calls itself on a smaller problem until it reaches a simple base case that stops it."),
    (("class", "classes", "object", "objects", "oop"), "A **class** is a blueprint and an **object** is one thing built from it. Objects bundle data (fields) and behavior (methods)."),
    (("pointer", "pointers", "reference", "memory"), "A **pointer/reference** holds the address of a value in memory instead of the value itself, so code can share and change the original."),
    (("bug", "bugs", "debug", "debugging", "error", "errors"), "A **bug** is a mistake in code. Debug by reading the error from the bottom up, checking the line number, and printing values to see what really happens."),
    (("compiler", "compile", "interpreter"), "A **compiler** turns your whole program into machine code before it runs; an **interpreter** runs it line by line."),
    (("operator", "operators"), "**Operators** do things with values: maths (`+ - * / %`), comparison (`==`, `>`) and logic (`and`/`&&`, `or`/`||`, `not`/`!`)."),
]
JOKES = ["Why do programmers prefer dark mode? Because light attracts bugs! 🐛", "There are 10 kinds of people: those who understand binary and those who don't. 😄",
         "A SQL query walks into a bar, sees two tables and asks: can I join you? 🍻", "Why did the developer go broke? He used up all his cache. 💸"]


def stem(w):
    if len(w) > 4 and w.endswith("es"):
        w = w[:-2]
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    return w[:6]


def toks(t):
    return {stem(w) for w in re.findall(r"[a-z0-9+#]+", t.lower()) if w not in STOP}


def clean(t):
    return re.sub(r"<[^>]+>", "", t).replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&").replace("&nbsp;", " ")


SYN = {"output": "print", "display": "print", "iteration": "loop", "iterate": "loop", "repeat": "loop", "decision": "if", "crash": "bug", "broken": "bug",
       "fix": "bug", "exception": "error", "number": "int", "numbers": "int"}
ANA = {
    "variable": "Think of a **labeled jar**: the label is the name and what's inside is the value. You can swap the contents any time.",
    "loop": "Like a **washing machine cycle**: it repeats the same steps until it's done (or you press stop).",
    "function": "Like a **recipe card**: write the steps once, then follow the card whenever you want that dish.",
    "array": "Like a **row of numbered lockers**: each locker holds one item and the numbering starts at 0.",
    "string": "Like a **necklace of letters**: each bead is one character, in order.",
    "type": "Like **containers**: a jar for liquid, a box for books. Each kind of data needs the right container.",
    "if": "Like a **traffic light**: if it's green, go; otherwise stop.",
    "recursion": "Like **Russian nesting dolls**: open one and there's a smaller one inside, until you reach the tiny last doll.",
    "class": "A class is a **cookie cutter** and the objects are the cookies it makes.",
    "pointer": "Like a **street address**: it isn't the house, it tells you where the house is.",
    "bug": "Like a **typo in a recipe**: the cook follows it exactly, so the dish is wrong until you fix that line.",
    "compiler": "Like a **translator** that converts your whole book into the computer's language before reading it.",
    "operator": "Like the **buttons on a calculator**: each one does a specific action on the values.",
}
COMPARE = {
    frozenset(("==", "===")): "`==` converts types before comparing (`'5' == 5` is true). `===` compares value AND type, so it is safer. Use `===` in JavaScript/TypeScript.",
    frozenset(("let", "const")): "`let` makes a variable you can reassign later. `const` makes one that can't be reassigned. Prefer `const` and use `let` only when the value must change.",
    frozenset(("for", "while")): "Use **for** when you know how many rounds (or you're walking through items). Use **while** when you repeat until something becomes true and don't know when.",
    frozenset(("list", "array")): "Arrays have a fixed size and one type of item (C, Java, Rust). Lists (Python, JS) grow and shrink. Both are indexed from 0.",
    frozenset(("compiler", "interpreter")): "A **compiler** translates the whole program first, then it runs fast. An **interpreter** reads and runs line by line, which is easier to test but usually slower.",
    frozenset(("stack", "heap")): "The **stack** stores local variables automatically and is very fast. The **heap** stores memory you request (malloc/new) and must be freed or garbage collected.",
}
RULES = [
    (r"^\s*(print|println!?|printf|console\.log|System\.out\.println|std::cout|cout|fmt\.Println|Console\.WriteLine)\b", "prints something to the screen"),
    (r"^\s*(#include|import|using|use|from\s+\S+\s+import|package)\b", "brings in a library or module so you can use its tools"),
    (r"^\s*(def|func|fn|function)\b|^\s*(public|private|static)\s+[\w<>\[\]]+\s+\w+\s*\(", "defines a function (a reusable block of code)"),
    (r"^\s*(for|foreach)\b", "starts a loop that repeats the block under it"),
    (r"^\s*while\b", "repeats the block as long as the condition is true"),
    (r"^\s*(if|else if|elif)\b", "runs the block only if the condition is true"),
    (r"^\s*else\b", "runs when the earlier conditions were false"),
    (r"^\s*return\b", "sends a result back out of the function"),
    (r"^\s*(class|struct|interface|type|enum)\b", "defines a new type that groups data (and behavior)"),
    (r"^\s*break\b", "leaves the loop immediately"),
    (r"^\s*continue\b", "skips to the next round of the loop"),
    (r"^\s*try\b", "starts a block that watches for errors"),
    (r"^\s*(catch|except|finally)\b", "handles errors or cleans up after the try block"),
    (r"^\s*(let|const|var|int|long|float|double|string|String|bool|boolean|char|auto|val|mut)\b[^()]*=", "creates a variable and gives it a value"),
    (r"^\s*\w+\s*(\+\+|--|[+\-*/]=)", "updates a variable"),
    (r"^\s*\w+(\.\w+)*(\[[^\]]*\])?\s*=\s*[^=]", "stores a new value in a variable"),
    (r"^\s*\w+(\.\w+)*\(.*\)\s*;?\s*$", "calls a function"),
]
MARK = [("Rust", r"\bfn\s+main|println!|\blet\s+mut\b"), ("Go", r"\bfunc\s+main|\bfmt\.|:=|package main"), ("C#", r"Console\.Write|using System"),
        ("Java", r"System\.out|public static void main"), ("C++", r"std::|\bcout\b|#include\s*<iostream>"), ("C", r"#include\s*<std|\bprintf\s*\("),
        ("TypeScript", r":\s*(number|string|boolean)\b|\binterface\b"), ("JavaScript", r"console\.log|\bconst\b|=>|\bfunction\b"), ("Python", r"\bdef\s+\w+\(|\bprint\(|\belif\b|^\s*import\s+\w+\s*$")]
LALIAS = {"python": "Python", "py": "Python", "c++": "C++", "cpp": "C++", "javascript": "JavaScript", "js": "JavaScript", "java": "Java", "rust": "Rust",
          "golang": "Go", "go": "Go", "c#": "C#", "csharp": "C#", "typescript": "TypeScript", "ts": "TypeScript", "c": "C"}


GLOSS.extend([
    (("scope",), "**Scope** is where a variable can be seen. Variables made inside a function or block usually exist only there."),
    (("comment", "comments"), "A **comment** is a note for humans that the computer ignores. Use it to explain WHY the code does something."),
    (("algorithm", "algorithms"), "An **algorithm** is a step-by-step recipe for solving a problem, like the steps for sorting a list."),
    (("api", "apis"), "An **API** is a menu of things one program lets another program ask for, like fetching weather data."),
    (("database", "sql", "db"), "A **database** stores data in organized tables. **SQL** is the language used to ask it questions like `SELECT name FROM users`."),
    (("git", "commit", "branch", "repository"), "**Git** tracks every change to your code. A **commit** is a saved snapshot and a **branch** is a safe side-track for new ideas."),
    (("stack", "queue"), "A **stack** is last-in-first-out (a pile of plates). A **queue** is first-in-first-out (a line at a shop)."),
    (("hash", "dictionary", "dict", "map"), "A **dictionary/map** stores key-value pairs and finds a value by its key almost instantly."),
    (("inheritance", "inherit", "extends"), "**Inheritance** lets a class reuse another class's fields and methods and then add or change some."),
    (("exception", "exceptions", "try", "catch"), "An **exception** is an error raised while running. `try` runs risky code and `catch`/`except` handles the problem so the program doesn't crash."),
    (("null", "nil", "none", "undefined"), "**null / None / nil / undefined** means 'no value here'. Using it like a real value is a very common cause of crashes."),
    (("closure", "lambda", "callback"), "A **lambda/closure** is a small unnamed function you can pass around. A **callback** is a function handed to other code to call later."),
])
ANA.update({"stack": "Like a **stack of plates**: you only add or remove from the top.", "hash": "Like a **phone book**: look up a name and instantly get the number.",
            "api": "Like a **restaurant menu**: it lists what you can order without showing the kitchen.", "database": "Like a **giant spreadsheet** that many apps can read and write.",
            "git": "Like a **save-game system** for your code with unlimited checkpoints.", "inheritance": "Like **family traits**: a child class gets its parent's abilities and can add its own."})
COMPARE.update({
    frozenset(("stack", "queue")): "A **stack** is last-in-first-out (undo button); a **queue** is first-in-first-out (waiting line).",
    frozenset(("class", "object")): "A **class** is the blueprint; an **object** is one thing built from it. One class can make many objects.",
    frozenset(("git", "github")): "**Git** is the tool that tracks your code history on your computer. **GitHub** is a website that hosts Git repositories so teams can share them.",
    frozenset(("frontend", "backend")): "**Frontend** is what users see and click (pages, buttons). **Backend** is the server and database behind it that stores data and runs the rules.",
})
ERR = [
    (r"syntaxerror|syntax error|unexpected token|expected ';'", "A **syntax error** means the code breaks the language's grammar: usually a missing colon, bracket, quote or semicolon. Check the line the error points at (and the one before it)."),
    (r"nameerror|is not defined|undeclared|cannot find symbol|unresolved reference", "The name isn't known here: a typo, a missing import, or the variable was created in a different scope. Check spelling and where it's declared."),
    (r"indexerror|out of range|out of bounds|arrayindexoutofbounds", "You asked for an index past the end. Lists start at 0, so the last valid index is length - 1."),
    (r"typeerror|cannot read propert|is not a function|mismatched types|incompatible types", "A value isn't the type you assumed (text + number, or calling something that isn't a function). Print the value and its type."),
    (r"nullpointer|null pointer|undefined is not|nonetype", "You used a value that is null/None/undefined. Find where it should have been set and guard with an if before using it."),
    (r"segmentation fault|segfault", "A **segfault** means the program touched memory it doesn't own: a bad pointer, an index out of bounds, or use after free. Check pointers, indexes and `free()`."),
    (r"borrow|moved value|lifetime", "Rust's borrow checker protects memory: a value has one owner, you can't use it after it's moved, and you can't mix a mutable borrow with others. Try `&`, `.clone()` or restructure."),
    (r"zerodivision|division by zero|divide by zero", "You divided by zero. Check the divisor before dividing."),
    (r"stack overflow|recursion depth|maximum recursion", "A function kept calling itself without stopping. Add a base case that ends the recursion."),
    (r"indentationerror|unexpected indent", "Python uses indentation for blocks. Use 4 spaces consistently and indent everything inside a for/if/def."),
    (r"permission denied|no such file|filenotfound|enoent", "The file path is wrong or you lack permission. Check the name, the folder you run from, and whether the file exists."),
    (r"timeout|timed out|connection refused", "The network call got no answer. Check the URL/port, that the server is running, and your internet."),
]
CONC = {"print": ("print", "output", "display"), "variable": ("variable", "declare"), "loop": ("loop", "iterate", "repeat"), "function": ("function", "method")}
LRX = r"(?<![\w+#])(python|py|c\+\+|cpp|javascript|js|java|rust|golang|go|c#|csharp|typescript|ts|kotlin|kt|swift|ruby|rb|c)(?![\w+#])"
LALIAS.update({"kotlin": "Kotlin", "kt": "Kotlin", "swift": "Swift", "ruby": "Ruby", "rb": "Ruby"})
MARK[:0] = [("Kotlin", r"\bfun\s+main|\bval\s+\w+\s*[=:]"), ("Swift", r"\bfunc\s+\w+.*->|\bvar\s+\w+:\s*\w+\?|\blet\s+\w+\s*=.*\n.*print\("), ("Ruby", r"\bputs\b|\bend\s*$")]
RULES[:0] = [(r"^\s*(puts|p)\b", "prints something to the screen"), (r"^\s*fun\b", "defines a function"), (r"^\s*val\b[^()]*=", "creates a read-only variable")]
_PS = {"Python": 'print("Hi")', "C": 'printf("Hi\\n");', "JavaScript": 'console.log("Hi");', "Java": 'System.out.println("Hi");', "C++": 'std::cout << "Hi" << std::endl;',
       "Rust": 'println!("Hi");', "C#": 'Console.WriteLine("Hi");', "Go": 'fmt.Println("Hi")', "TypeScript": 'console.log("Hi");', "Kotlin": 'println("Hi")', "Swift": 'print("Hi")', "Ruby": 'puts "Hi"'}
_VS = {"Python": "x = 5", "C": "int x = 5;", "JavaScript": "let x = 5;", "Java": "int x = 5;", "C++": "int x = 5;", "Rust": "let x = 5;", "C#": "int x = 5;",
       "Go": "x := 5", "TypeScript": "let x: number = 5;", "Kotlin": "val x = 5", "Swift": "let x = 5", "Ruby": "x = 5"}
_LS = {"Python": "for i in range(1, 4):\n    print(i)", "C": 'for (int i = 1; i <= 3; i++) {\n    printf("%d", i);\n}', "JavaScript": "for (let i = 1; i <= 3; i++) {\n    console.log(i);\n}",
       "Java": "for (int i = 1; i <= 3; i++) {\n    System.out.println(i);\n}", "C++": "for (int i = 1; i <= 3; i++) {\n    std::cout << i;\n}", "Rust": 'for i in 1..=3 {\n    println!("{}", i);\n}',
       "C#": "for (int i = 1; i <= 3; i++) {\n    Console.WriteLine(i);\n}", "Go": "for i := 1; i <= 3; i++ {\n    fmt.Println(i)\n}", "TypeScript": "for (let i = 1; i <= 3; i++) {\n    console.log(i);\n}",
       "Kotlin": "for (i in 1..3) {\n    println(i)\n}", "Swift": "for i in 1...3 {\n    print(i)\n}", "Ruby": "(1..3).each { |i| puts i }"}
_FS = {"Python": "def add(a, b):\n    return a + b", "C": "int add(int a, int b) {\n    return a + b;\n}", "JavaScript": "function add(a, b) {\n    return a + b;\n}",
       "Java": "static int add(int a, int b) {\n    return a + b;\n}", "C++": "int add(int a, int b) {\n    return a + b;\n}", "Rust": "fn add(a: i32, b: i32) -> i32 {\n    a + b\n}",
       "C#": "static int Add(int a, int b) => a + b;", "Go": "func add(a, b int) int {\n    return a + b\n}", "TypeScript": "function add(a: number, b: number): number {\n    return a + b;\n}",
       "Kotlin": "fun add(a: Int, b: Int) = a + b", "Swift": "func add(_ a: Int, _ b: Int) -> Int {\n    a + b\n}", "Ruby": "def add(a, b) = a + b"}
COOK = {"print": _PS, "variable": _VS, "loop": _LS, "function": _FS}


LALIAS.update({"php": "PHP", "dart": "Dart", "lua": "Lua", "r": "R"})
LRX = LRX.replace("|rb|c)", "|rb|php|dart|lua|r|c)")
MARK[:0] = [("PHP", r"<\?php|\$\w+\s*="), ("Lua", r"\blocal\s+\w+|\bthen\b"), ("R", r"<-|\bdata\.frame"), ("Dart", r"\bvoid\s+main\(\)\s*\{|\bFuture<|StatefulWidget")]
RULES[:0] = [(r"^\s*(echo|cat)\b", "prints something to the screen"), (r"^\s*local\b[^()]*=", "creates a local variable"),
             (r"^\s*\$\w+\s*=", "stores a value in a variable"), (r"^\s*\w+\s*<-", "stores a value in a variable")]
COOK["print"].update({"PHP": 'echo "Hi";', "Dart": "print('Hi');", "Lua": 'print("Hi")', "R": 'print("Hi")'})
COOK["variable"].update({"PHP": "$x = 5;", "Dart": "var x = 5;", "Lua": "local x = 5", "R": "x <- 5"})
COOK["loop"].update({"PHP": 'for ($i = 1; $i <= 3; $i++) {\n    echo $i;\n}', "Dart": "for (var i = 1; i <= 3; i++) {\n  print(i);\n}", "Lua": "for i = 1, 3 do\n  print(i)\nend", "R": "for (i in 1:3) {\n  print(i)\n}"})
COOK["function"].update({"PHP": 'function add($a, $b) {\n    return $a + $b;\n}', "Dart": "int add(int a, int b) => a + b;", "Lua": "function add(a, b)\n  return a + b\nend", "R": "add <- function(a, b) a + b"})


LALIAS.update({"julia": "Julia", "jl": "Julia", "scala": "Scala", "elixir": "Elixir", "ex": "Elixir"})
LRX = LRX.replace("|php|dart|lua|r|c)", "|php|dart|lua|r|julia|jl|scala|elixir|ex|c)")
MARK[:0] = [("Elixir", r"\bIO\.(puts|inspect)|\bdefmodule\b|\|>"), ("Scala", r"\bobject\s+\w+\s+extends|\bcase\s+class\b|println\(s\""), ("Julia", r"\bfor\s+\w+\s+in\s+\d+:\d+|\busing\s+\w+\s*$|\bstruct\s+\w+\s*$")]
RULES[:0] = [(r"^\s*IO\.(puts|inspect)\b", "prints something to the screen")]
COOK["print"].update({"Julia": 'println("Hi")', "Scala": 'println("Hi")', "Elixir": 'IO.puts("Hi")'})
COOK["variable"].update({"Julia": "x = 5", "Scala": "val x = 5", "Elixir": "x = 5"})
COOK["loop"].update({"Julia": "for i in 1:3\n    println(i)\nend", "Scala": "for (i <- 1 to 3) {\n  println(i)\n}", "Elixir": "Enum.each(1..3, fn i -> IO.puts(i) end)"})
COOK["function"].update({"Julia": "add(a, b) = a + b", "Scala": "def add(a: Int, b: Int) = a + b", "Elixir": "def add(a, b), do: a + b"})
CZ = [("ahoj", "hello"), ("cau", "hello"), ("nazdar", "hello"), ("dekuj", "thanks"), ("diky", "thanks"), ("pomoc", "help"), ("smyck", "loop"), ("cykl", "loop"),
      ("promen", "variable"), ("funkc", "function"), ("podmin", "if"), ("chyb", "error"), ("trid", "class"), ("ukazat", "pointer"), ("rekurz", "recursion"),
      ("retez", "string"), ("pole", "list"), ("kviz", "quiz"), ("vysvetl", "explain"), ("priklad", "example"), ("jednodus", "simpler"), ("vtip", "joke"),
      ("co", "what"), ("je", "is"), ("jak", "how"), ("pokrok", "progress"), ("doporuc", "recommend"), ("rozdil", "difference"), ("mezi", "between")]


class Tutor(QWidget):
    back = Signal()

    def __init__(self, st):
        super().__init__()
        self.st, self.lang, self.pend = st, "Python", None
        self.ctx, self.offer, self.concept = None, False, None
        self.chiprow, self.dn, self.wlab = None, 0, None
        self.dots = QTimer(self)
        self.dots.timeout.connect(self.tick)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.setContentsMargins(28, 20, 28, 0)
        x = QPushButton("←")
        x.setObjectName("x")
        x.setCursor(Qt.PointingHandCursor)
        x.clicked.connect(self.back.emit)
        h = QLabel("🤖  Ask Byte  <span style='font-size:13px;color:#58cc02'>● free · offline</span>")
        h.setTextFormat(Qt.RichText)
        h.setObjectName("title")
        bar.addWidget(x)
        bar.addWidget(h, 1)
        root.addLayout(bar)
        self.body = QWidget()
        self.col = QVBoxLayout(self.body)
        self.col.setSpacing(12)
        self.col.setContentsMargins(30, 16, 30, 16)
        self.col.addStretch()
        self.sc = QScrollArea()
        self.sc.setWidgetResizable(True)
        self.sc.setWidget(center(self.body, 780))
        root.addWidget(self.sc, 1)
        chips = QHBoxLayout()
        chips.setContentsMargins(30, 0, 30, 0)
        for t in ("What is a variable?", "for vs while", "Quiz me!"):
            b = QPushButton(t)
            b.setObjectName("tab")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, t=t: self.send(t))
            chips.addWidget(b)
        chips.addStretch()
        root.addLayout(chips)
        row = QHBoxLayout()
        row.setContentsMargins(30, 10, 30, 20)
        self.inp = QLineEdit()
        self.inp.setObjectName("inp")
        self.inp.setPlaceholderText("Ask me anything about coding...")
        self.inp.returnPressed.connect(self.go)
        sb = QPushButton("SEND")
        sb.setObjectName("act")
        sb.setStyleSheet("padding:14px 26px")
        sb.setCursor(Qt.PointingHandCursor)
        sb.clicked.connect(self.go)
        row.addWidget(self.inp, 1)
        row.addWidget(sb)
        root.addLayout(row)
        self.bubble("Hi! I'm **Byte** 🤖, your free tutor that lives inside this app (no internet, no cost). Ask me about any topic, paste code and I'll explain it and hunt for bugs 🐞, tap **💡 Explain** after a question, or say **quiz me**!", False)

    def bubble(self, text, user):
        lb = QLabel(text)
        lb.setWordWrap(True)
        lb.setTextFormat(Qt.PlainText if user else Qt.MarkdownText)
        lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lb.setMaximumWidth(580)
        bg = "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #25576f,stop:1 #1b3d50)" if user else "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #213640,stop:1 #172630)"
        lb.setStyleSheet(f"background:{bg};border:2px solid {'#2f7a9c' if user else '#2b4250'};border-radius:18px;padding:12px 16px;font-size:16px")
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)
        av = QLabel(self.st.get("avatar") or "🙂") if user else QLabel("🤖")
        av.setFixedSize(42, 42)
        av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet("font-size:24px;background:#22323b;border:2px solid #37464f;border-radius:21px")
        if user:
            h.addStretch()
            h.addWidget(lb)
            h.addWidget(av, 0, Qt.AlignTop)
        else:
            h.addWidget(av, 0, Qt.AlignTop)
            h.addWidget(lb)
            h.addStretch()
        self.col.insertWidget(self.col.count() - 1, row)
        fade(row, 220)
        QTimer.singleShot(120, self.bottom)
        return lb

    def bottom(self):
        sb = self.sc.verticalScrollBar()
        a = QPropertyAnimation(sb, b"value", self)
        a.setDuration(300)
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.setStartValue(sb.value())
        a.setEndValue(sb.maximum())
        a.start(QAbstractAnimation.DeleteWhenStopped)

    def chips(self):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(52, 0, 0, 0)
        h.setSpacing(8)
        for lab, msg in (("💡 Example", "example"), ("🧸 Simpler", "simpler"), ("🎯 Quiz me", "quiz me"), ("🗺️ What next?", "what should i study")):
            b = QPushButton(lab)
            b.setObjectName("tab")
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("padding:6px 12px;font-size:14px;border:2px solid #2b3d46;color:#cfe3ea")
            b.clicked.connect(lambda _, m=msg: self.send(m))
            h.addWidget(b)
        h.addStretch()
        self.col.insertWidget(self.col.count() - 1, row)
        fade(row, 220)
        self.chiprow = row
        QTimer.singleShot(150, self.bottom)

    def tick(self):
        self.dn = (self.dn + 1) % 4
        try:
            self.wlab.setText("Byte is thinking" + "." * self.dn)
        except (RuntimeError, AttributeError):
            self.dots.stop()

    def go(self):
        t = self.inp.text().strip()
        if t:
            self.inp.clear()
            self.send(t)

    def send(self, text):
        if self.chiprow is not None:
            try:
                self.chiprow.deleteLater()
            except RuntimeError:
                pass
            self.chiprow = None
        self.bubble(text if len(text) < 300 else text.split("\n")[0], True)
        w = self.wlab = self.bubble("Byte is thinking", False)
        ans = self.reply(text)
        self.dn = 0
        self.dots.start(280)
        QTimer.singleShot(350 + min(len(ans), 500), lambda: self.say(w, ans))

    def say(self, w, ans):
        self.dots.stop()
        try:
            w.setText(ans)
        except RuntimeError:
            return
        self.bottom()
        if self.offer:
            self.chips()

    def cz(self, low):
        low = "".join(c for c in unicodedata.normalize("NFD", low) if unicodedata.category(c) != "Mn")

        def f(m):
            w = m.group(0)
            for k, v in CZ:
                if w == k or (len(k) > 3 and w.startswith(k)):
                    return v
            return w
        out = re.sub(r"[a-z]+", f, low)
        return out.replace(" a ", " and ") if "difference between" in out else out

    def coach(self):
        st, lang = self.st, self.lang
        nd, prog = nodes(lang, st), st["prog"].get(lang, 0)
        weak = sorted(((n, c) for n, c in st.get("weak", {}).get(lang, {}).items() if c > 0), key=lambda x: -x[1])[:3]
        out = [f"📈 **{st['name'] or 'You'}**, you're level **{st['xp'] // 150 + 1}** with a **{st['streak']}-day** streak and **{min(prog, total(lang))}/{total(lang)}** steps done in {lang}."]
        if prog < len(nd):
            k, j = nd[prog]
            nm = LANGS[lang][2][j][0] if k == "l" else PROJ[j][0] if k == "p" else "Choose your field" if k == "f" else "the Boss Battle"
            out.append(f"👉 Next on your roadmap: **{nm}**.")
        if weak:
            out.append("🔁 Worth reviewing: " + ", ".join(f"**{n}**" for n, _ in weak) + ". Say **quiz me** and I'll focus on them.")
        else:
            out.append("✅ No weak spots yet. Keep quizzing me and I'll learn what to practice with you!")
        return "\n\n".join(out)

    def lessons(self, lang=None):
        lang = lang or self.lang
        return list(zip(LANGS[lang][2], TEACH[lang]))

    def docs(self, lang=None):
        return [(f"{e} {t}", clean(tx), cd, toks(t), toks(t + " " + tx + " " + cd), j) for j, ((t, e, qs), (tx, cd)) in enumerate(self.lessons(lang))]

    def rank(self, q, docs):
        N = len(docs)
        idf = {w: math.log(1 + N / (1 + sum(w in d[4] for d in docs))) for w in q}
        return sorted((-sum(idf[w] * (3 if w in d[3] else 1) for w in q if w in d[4]), n) for n, d in enumerate(docs))

    def gloss(self, q):
        for ks, g in GLOSS:
            if q & {stem(k) for k in ks}:
                return ks[0], g
        return None, None

    def define(self, term):
        q = toks(term)
        k, g = self.gloss(q)
        if g:
            return g
        docs = self.docs()
        r = self.rank(q, docs)
        return re.split(r"(?<=[.!?]) ", docs[r[0][1]][1])[0] if q and r[0][0] <= -0.9 else ""

    def looks_code(self, t):
        return bool(("\n" in t and re.search(r"[(){};=:]", t)) or re.search(r"[;{}]", t) or re.search(r"\b(print|printf|console\.log|println!?)\s*\(", t)
                    or re.match(r"^\s*(for|while|if|def|fn|func|int|let|const|var)\b.*[(){};:=]", t))

    def detect(self, code):
        for n, rx in MARK:
            if re.search(rx, code, re.M):
                return n
        return self.lang

    def bugs(self, code, lang):
        out, t = [], re.sub(r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'", "S", code)
        st = []
        for ch in t:
            if ch in "([{":
                st.append(ch)
            elif ch in ")]}":
                if not st or "([{".index(st.pop()) != ")]}".index(ch):
                    out.append("A bracket doesn't match its partner. Count your `(`, `[` and `{` against the closing ones.")
                    st = []
                    break
        if st:
            out.append(f"You opened `{st[-1]}` but never closed it.")
        for n, ln in enumerate(t.splitlines(), 1):
            x = ln.strip()
            if lang == "Python" and re.match(r"(for|while|if|elif|else|def|class)\b", x) and not x.endswith(":"):
                out.append(f"Line {n}: Python needs a colon `:` at the end of `{x[:30]}`.")
            if lang in ("C", "C++", "Java", "C#", "PHP", "Dart") and x and not re.match(r"(#|//|/\*|\*|<\?|\}|\)|else|if\b|for\b|while\b|switch|case|do\b|try|catch|public|private|class|struct|namespace|using)", x) and not x.endswith((";", "{", "}", ",", ":", ")")):
                out.append(f"Line {n}: `{x[:30]}` may be missing a semicolon `;`.")
            if re.search(r"\b(if|while)\s*\(?[^()=!<>]*[^=!<>]=[^=]", x):
                out.append(f"Line {n}: `=` assigns a value. To compare, use `==` (or `===` in JS/TS).")
            if lang in ("JavaScript", "TypeScript") and re.search(r"[^=!]==[^=]", x):
                out.append(f"Line {n}: prefer `===` over `==` so types are compared too.")
            if lang in ("Java", "C#") and re.search(r"==\s*S|S\s*==", x):
                out.append(f"Line {n}: compare Strings with `.equals()`, not `==`.")
            if lang == "C" and re.search(r"==\s*S|S\s*==", x):
                out.append(f"Line {n}: compare C strings with `strcmp(a, b) == 0`.")
            if re.search(r"<=\s*(len\(|\w+\.length|sizeof)", x):
                out.append(f"Line {n}: `<=` with a length reads one item too far (off-by-one). Use `<`.")
        if re.search(r"while\s*\(?\s*(True|true)\s*\)?", t) and not re.search(r"\b(break|return)\b", t):
            out.append("Your `while true` loop has no `break` or `return`, so it may never end.")
        return out

    def analyze(self, t):
        lang = self.detect(t)
        lines = [ln for ln in t.splitlines() if ln.strip() and ln.strip() not in "{}"][:12]
        steps = []
        for ln in lines:
            for rx, ex in RULES:
                if re.search(rx, ln):
                    steps.append(f"- `{ln.strip()[:48]}` : {ex}")
                    break
        bg = self.bugs(t, lang)
        body = "\n".join(steps) if steps else "I couldn't recognize much structure here."
        chk = "\n".join(f"- {b}" for b in bg[:5]) if bg else "I don't see obvious mistakes 👍 (I only catch common ones, so test it too!)"
        return f"🔍 I read your **{lang}** code:\n\n{body}\n\n🐞 **Bug check**\n\n{chk}"

    def reply(self, t):
        low = self.cz(t.lower().strip())
        nm = self.st["name"] or "friend"
        offer, self.offer = self.offer, False
        if "Correct answer:" in t and "Question:" in t:
            return self.why(t)
        if self.pend:
            return self.grade(t)
        if re.search(r"\b(what should i|what to (study|learn|practice)|weak|progress|how am i doing|my level|recommend|review)\b", low):
            return self.coach()
        if re.search(r"\b(quiz|test me|practice)\b", low) or (offer and re.match(r"^(yes|yeah|yep|sure|ok|okay|please|go|do it)\b", low)):
            return self.quiz()
        for rx, ex in ERR:
            if re.search(rx, low) and t.count("\n") < 4:
                return "🚨 " + ex + "\n\nPaste the code that fails and I'll look for the cause 🔍"
        if self.looks_code(t):
            return self.analyze(t)
        if re.match(r"^(hi|hello|hey|yo|sup)\b", low):
            return f"Hey {nm}! 👋 Ask me about a topic, paste some code for me to explain, or say **quiz me**."
        if re.search(r"\b(thanks|thank you|thx)\b", low):
            return "Anytime! 🤖💚 Keep going, you're doing great."
        if re.search(r"\b(joke|funny)\b", low):
            return random.choice(JOKES)
        if re.search(r"\b(who are you|what can you do|help)\b", low):
            return "I'm **Byte**, a free tutor built into this app. I can explain topics, compare ideas (try *for vs while*), explain and debug code you paste, do quick maths, and quiz you. Just ask!"
        m = re.fullmatch(r"(?:what is|what's|whats|calculate|compute|result of)?\s*([\d(][\d\s+\-*/%().]*)\??", low)
        if m and "**" not in low and re.search(r"[+\-*/%]", m.group(1)):
            try:
                v, iv = eval(m.group(1), {"__builtins__": {}}, {}), eval(m.group(1).replace("/", "//"), {"__builtins__": {}}, {})
                note = f"\n\nWith whole numbers, C, C++, Java, C#, Go and Rust truncate division: this gives **{iv}** there." if "/" in m.group(1) and iv != v else ""
                return f"`{m.group(1).strip()}` = **{round(v, 6)}** (Python, JavaScript, TypeScript).{note}"
            except Exception:
                pass
        c = self.ctx
        if c and re.search(r"\b(simpler|simple|eli5|confus\w*|dont get|don't get|not understand|don't understand|analogy)\b", low):
            a = ANA.get(c["key"])
            self.offer = True
            return (a + "\n\nBetter now? You can also say **example** to see code.") if a else "Let's go step by step 🪜 " + re.split(r"(?<=[.!?]) ", c["doc"][1])[0]
        if c and re.search(r"\b(example|show code|another|more)\b", low) and len(low) < 40:
            r = c["rank"]
            if "another" in low or "more" in low:
                c["ptr"] = min(c["ptr"] + 1, len(r) - 1)
            d = c["docs"][r[c["ptr"]][1]]
            c["doc"] = d
            self.offer = True
            return f"Here's another look at **{d[0]}**:\n\n```\n{d[2] or 'No code in this one, try quiz me!'}\n```\n\nTry changing a value and predicting what happens! 🧪"
        lang, pre = self.lang, ""
        ml = re.search(r"\b(?:in|using|for|with)\s+(python|py|c\+\+|cpp|javascript|js|java|rust|golang|go|c#|csharp|typescript|ts|c)(?![\w+#])", low)
        if ml:
            lang = LALIAS[ml.group(1)]
            pre = f"*(answering for {lang})*\n\n"
        ck = self.cook(low)
        if ck:
            return ck
        cm = re.search(r"(?:difference between|compare)\s+(.+?)\s+(?:and|with|to)\s+(.+)|(.+?)\s+(?:vs\.?|versus)\s+(.+)", low)
        if cm:
            a, b = (x.strip(" ?.") for x in ((cm.group(1), cm.group(2)) if cm.group(1) else (cm.group(3), cm.group(4))))
            a, b = re.sub(r"^(a|an|the)\s+", "", a), re.sub(r"^(a|an|the)\s+", "", b)
            key = frozenset((a, b))
            if key in COMPARE:
                return "⚖️ " + COMPARE[key]
            da, db = self.define(a), self.define(b)
            if da and db:
                return f"⚖️ **{a}** vs **{b}**\n\n**{a}**: {da}\n\n**{b}**: {db}"
        docs = self.docs(lang)
        vocab = {w for d in docs for w in re.findall(r"[a-z]{4,}", (d[0] + " " + d[1] + " " + d[2]).lower())} | {k for ks, _ in GLOSS for k in ks}
        cv = {k for ks, _ in GLOSS for k in ks} | {w for d in docs for w in re.findall(r"[a-z]{4,}", d[0].lower())}
        ws = []
        for w in re.findall(r"[a-z0-9+#]+", low):
            if len(w) >= 4 and w not in vocab and w not in STOP and w not in SYN:
                fx = [v for v in difflib.get_close_matches(w, cv, 3, 0.8) if v[0] == w[0]]
                w = fx[0] if fx else w
            ws.append(w)
        q = toks(" ".join(ws + [SYN[w] for w in ws if w in SYN]))
        key, g = self.gloss(q)
        r = self.rank(q, docs) if q else [(0, 0)]
        out = [g] if g else []
        if r[0][0] <= -0.9:
            d = docs[r[0][1]]
            out.append(f"📚 **{d[0]}**\n\n{d[1]}" + (f"\n\n```\n{d[2]}\n```" if d[2] else ""))
            if lang == self.lang:
                nd, prog = nodes(lang, self.st), self.st["prog"].get(lang, 0)
                pos = next((i for i, (k, j) in enumerate(nd) if k == "l" and j == d[5]), None)
                if pos is not None:
                    out.append("✅ You've already finished this lesson." if pos < prog else f"🗺️ You'll reach this lesson at step {pos + 1} of your roadmap.")
            rel = [docs[n][0] for sc, n in r[1:3] if sc <= -0.9]
            if rel:
                out.append("🔎 Related: " + ", ".join(rel))
            self.ctx = {"key": key or "", "doc": d, "rank": r, "ptr": 0, "docs": docs}
        elif g:
            self.ctx = {"key": key, "doc": ("", g, ""), "rank": r, "ptr": 0, "docs": docs}
        if out:
            self.offer = True
            return pre + "\n\n".join(out) + "\n\nWant to test it? Say **yes** or **quiz me**."
        topics = ", ".join(d[0] for d in random.sample(docs, min(5, len(docs))))
        return f"Hmm, I'm not sure about that one 🤔 I know about things like: {topics}. You can also paste code or say **quiz me**!"

    def cook(self, low):
        q = toks(low)
        cn = next((c for c, ks in CONC.items() if q & {stem(k) for k in ks}), None) or (self.concept if re.match(r"^(what about|and|how about|same)\b", low) else None)
        langs = []
        for m in re.finditer(LRX, low):
            n = LALIAS[m.group(1)]
            if n not in langs:
                langs.append(n)
        if cn and langs:
            self.concept = cn
            self.offer = True
            return f"🍳 **{cn}** in {', '.join(langs[:4])}:\n\n" + "\n\n".join(f"**{n}**\n```\n{COOK[cn][n]}\n```" for n in langs[:4] if n in COOK[cn]) + "\n\nWant to test yourself? Say **yes**."
        return None

    def quiz(self):
        pool = [(q, t, clean(tx)) for (t, e, qs), (tx, cd) in self.lessons() for q in qs]
        wkd = self.st.get("weak", {}).get(self.lang, {})
        wk = [p for p in pool if wkd.get(p[1], 0) > 0]
        q, t, tx = random.choice(wk if wk and random.random() < 0.6 else pool)
        p, c, o, a = q
        opts = ai = None
        if o:
            k = random.sample(range(len(o)), len(o))
            opts, ai = [o[x] for x in k], k.index(a)
        self.pend = (q, t, tx, opts, ai)
        body = f"🎯 **Quiz time!**\n\n{p}\n" + (f"\n```\n{c}\n```\n" if c else "")
        if opts:
            return body + "\n" + "\n".join(f"- **{'ABCD'[i]}**  {x}" for i, x in enumerate(opts)) + "\n\nReply with a letter!"
        return body + "\nType your answer!"

    def grade(self, t):
        q, title, tx, opts, ai = self.pend
        self.pend = None
        if opts is None:
            ok = "".join(t.split()) in ["".join(x.split()) for x in q[3]]
            shown = q[3][0]
        else:
            m = re.match(r"^\s*([a-d])\b", t.lower())
            idx = "abcd".index(m.group(1)) if m else next((i for i, x in enumerate(opts) if x.lower() == t.strip().lower()), -1)
            ok, shown = idx == ai, opts[ai]
        wk = self.st.setdefault("weak", {}).setdefault(self.lang, {})
        wk[title] = max(0, wk.get(title, 0) + (-1 if ok else 1))
        save(self.st)
        head = f"{random.choice(PRAISE)} ✅" if ok else f"Not quite 🤔 The answer is **{shown}**."
        return f"{head}\n\n📚 *{title}*: " + " ".join(re.split(r"(?<=[.!?]) ", tx)[:2]) + "\n\nSay **quiz me** for another one!"

    def why(self, t):
        def g(k):
            m = re.search(k + r":\s*(.*)", t)
            return m.group(1).strip() if m else ""
        qn, right, mine = g("Question"), g("Correct answer"), g("My answer")
        m = re.search(r"Code:\n(.*?)\n(?:Options:|Correct answer:)", t, re.S)
        code = m.group(1).strip() if m else ""
        ws = toks(qn + " " + right + " " + code)
        tx = title = None
        for strict in (True, False):
            for (lt, e, qs), (ltx, cd) in self.lessons():
                if tx is None and any(q[0] == qn and (not strict or q[1].strip() == code) for q in qs):
                    tx, title = clean(ltx), f"{e} {lt}"
        if tx is None:
            d = max(self.docs(), key=lambda d: len(d[4] & ws))
            tx, title = d[1], d[0]
        sents = sorted(re.split(r"(?<=[.!?]) ", tx), key=lambda s: -len(toks(s) & ws))
        ok = mine.strip().lower() == right.strip().lower()
        head = "✅ Nice, you got it!" if ok else f"🤔 The right answer is **{right}**."
        more = f" {sents[1]}" if len(sents) > 1 and toks(sents[1]) & ws else ""
        return f"{head}\n\n**Why?** {sents[0]}{more}\n\n📚 *{title}*\n\nWant a bonus question? Say **quiz me**."


class Projects(QWidget):
    back = Signal()
    start = Signal(str, int)
    big = Signal(str, int)

    def __init__(self, st):
        super().__init__()
        self.st = st
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.setContentsMargins(28, 20, 28, 0)
        x = QPushButton("←")
        x.setObjectName("x")
        x.setCursor(Qt.PointingHandCursor)
        x.clicked.connect(self.back.emit)
        h = QLabel("🛠️  Projects")
        h.setObjectName("title")
        self.lg = QLabel()
        self.lg.setObjectName("stats")
        bar.addWidget(x)
        bar.addWidget(h, 1)
        bar.addWidget(self.lg)
        root.addLayout(bar)
        self.body = QWidget()
        self.col = QVBoxLayout(self.body)
        self.col.setSpacing(12)
        self.col.setContentsMargins(30, 16, 30, 30)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(center(self.body, 800))
        root.addWidget(sc, 1)

    def refresh(self, lang):
        pd = self.st["pdone"].get(lang, [])
        while self.col.count():
            w = self.col.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.lg.setText(f"{LANGS[lang][0]} {lang}   ·   {len(pd)}/{len(XPJ)} done")
        sub = QLabel("Build real programs, from easy to hard. Finish one to unlock the next. Change language with ⇄ Languages.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#8ea0a8")
        self.col.addWidget(sub)
        hb = QLabel("🏗️  Long-term projects")
        hb.setStyleSheet("font-size:22px;font-weight:900;color:#a855f7;margin-top:6px")
        self.col.addWidget(hb)
        sb = QLabel("Big projects you build over many sessions. Your code is saved after every attempt, one milestone at a time. Finish all milestones for 💎 100 and a 🎁 chest.")
        sb.setWordWrap(True)
        sb.setStyleSheet("color:#8ea0a8")
        self.col.addWidget(sb)
        bg = self.st["big"].get(lang, {})
        for bi, (t, e, blurb, ms) in enumerate(BIGP):
            m = bg.get(str(bi), {}).get("m", 0)
            fin = m >= len(ms)
            c = QFrame()
            c.setObjectName("card")
            hl = QHBoxLayout(c)
            hl.setContentsMargins(18, 14, 18, 14)
            em = QLabel("🏆" if fin else e)
            em.setStyleSheet("font-size:38px")
            info = QLabel(f"<b style='font-size:18px'>{t}</b><br><span style='color:#b9c8cf'>{blurb}</span><br><span style='color:#a855f7'>" + ("All milestones complete!" if fin else f"Milestone {m + 1}/{len(ms)}: {ms[m][0]}") + "</span>")
            info.setTextFormat(Qt.RichText)
            info.setWordWrap(True)
            pb = QProgressBar()
            pb.setTextVisible(False)
            pb.setValue(m * 100 // len(ms))
            pb.setStyleSheet("QProgressBar::chunk{background:#a855f7}")
            v = QVBoxLayout()
            v.addWidget(info)
            v.addWidget(pb)
            b = QPushButton("✅ DONE" if fin else "CONTINUE" if m else "START")
            b.setObjectName("act")
            b.setEnabled(not fin)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("padding:10px 22px")
            b.clicked.connect(lambda _, bi=bi: self.big.emit(lang, bi))
            hl.addWidget(em)
            hl.addLayout(v, 1)
            hl.addWidget(b)
            self.col.addWidget(c)
        last = None
        for i, (t, e, d, tier, gm, xp, _) in enumerate(XPJ):
            tl, col = TIER[tier]
            if tier != last:
                last = tier
                hd = QLabel(tl)
                hd.setStyleSheet(f"font-size:22px;font-weight:900;color:{col};margin-top:10px")
                self.col.addWidget(hd)
            done, open_ = i in pd, i == 0 or (i - 1) in pd
            c = QFrame()
            c.setObjectName("card")
            hl = QHBoxLayout(c)
            hl.setContentsMargins(18, 14, 18, 14)
            em = QLabel("✅" if done else e if open_ else "🔒")
            em.setStyleSheet("font-size:38px")
            info = QLabel(f"<b style='font-size:18px'>{t}</b><br><span style='color:#b9c8cf'>{d}</span><br><span style='color:#ffc800'>⚡ {xp} XP &nbsp; 💎 {gm}{' &nbsp; 🎁 chest' if tier == 'hard' else ''}</span>")
            info.setTextFormat(Qt.RichText)
            info.setWordWrap(True)
            b = QPushButton("REPLAY" if done else "START" if open_ else "LOCKED")
            b.setObjectName("act")
            b.setEnabled(open_)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("padding:10px 22px")
            b.clicked.connect(lambda _, i=i: self.start.emit(lang, i))
            hl.addWidget(em)
            hl.addWidget(info, 1)
            hl.addWidget(b)
            self.col.addWidget(c)
        self.col.addStretch()


class Settings(QWidget):
    back = Signal()

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.setContentsMargins(28, 20, 28, 0)
        x = QPushButton("←")
        x.setObjectName("x")
        x.setCursor(Qt.PointingHandCursor)
        x.clicked.connect(self.back.emit)
        h = QLabel("⚙️  Settings")
        h.setObjectName("title")
        bar.addWidget(x)
        bar.addWidget(h, 1)
        root.addLayout(bar)
        body = QWidget()
        col = QVBoxLayout(body)
        col.setSpacing(14)
        col.setContentsMargins(30, 16, 30, 30)
        self.note = QLabel("⚠️ Audio isn't available here (QtMultimedia could not start). Check your audio device or install PySide6 with multimedia support.")
        self.note.setWordWrap(True)
        self.note.setStyleSheet("color:#ffc800")
        col.addWidget(self.note)
        self.ctl = {}
        for ic, nm, k, vk, ds in (("🎵", "Music", "music", "musvol", "Background chiptune music that loops while you learn."),
                                  ("🔊", "Sound effects", "sfx", "sfxvol", "Clicks, right and wrong answers, chests and level-complete jingles.")):
            c = QFrame()
            c.setObjectName("card")
            v = QVBoxLayout(c)
            v.setContentsMargins(20, 16, 20, 16)
            top = QHBoxLayout()
            t = QLabel(f"{ic}  {nm}")
            t.setStyleSheet("font-size:20px;font-weight:900")
            b = QPushButton()
            b.setObjectName("tog")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            top.addWidget(t, 1)
            top.addWidget(b)
            d = QLabel(ds)
            d.setWordWrap(True)
            d.setStyleSheet("color:#8ea0a8")
            sl = QSlider(Qt.Horizontal)
            sl.setRange(0, 100)
            v.addLayout(top)
            v.addWidget(d)
            v.addWidget(sl)
            b.toggled.connect(lambda on, k=k, b=b: (b.setText("ON" if on else "OFF"), SND.put(k, on)))
            sl.valueChanged.connect(lambda val, vk=vk: SND.put(vk, val, False))
            sl.sliderReleased.connect(lambda k=k, vk=vk, sl=sl: (SND.put(vk, sl.value()), SND.play("correct") if k == "sfx" else None))
            self.ctl[k] = (b, sl, vk)
            col.addWidget(c)
        row = QHBoxLayout()
        for lab, nm in (("✅ Correct", "correct"), ("❌ Wrong", "wrong"), ("🏆 Complete", "complete"), ("🎁 Chest", "chest")):
            b = QPushButton(lab)
            b.setObjectName("tab")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, nm=nm: SND.play(nm))
            row.addWidget(b)
        row.addStretch()
        col.addWidget(QLabel("Test the sounds:"))
        col.addLayout(row)
        col.addStretch()
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(center(body, 700))
        root.addWidget(sc, 1)

    def refresh(self):
        self.note.setVisible(not SND.ok)
        for k, (b, sl, vk) in self.ctl.items():
            b.blockSignals(True)
            sl.blockSignals(True)
            b.setChecked(bool(SND.get(k)))
            b.setText("ON" if b.isChecked() else "OFF")
            sl.setValue(int(SND.get(vk)))
            b.blockSignals(False)
            sl.blockSignals(False)


MON = [("🐛", "Bug"), ("🕷️", "Spider Bug"), ("🦇", "Null Bat"), ("👻", "Ghost Process"), ("🧟", "Zombie Loop"), ("🐍", "Syntax Snake"), ("🦂", "Off-by-One Scorpion"), ("🤖", "Rogue Compiler")]
BOSS = [("👾", "Bug King"), ("🐉", "Memory Leak Dragon"), ("💀", "Segfault Lich"), ("🦑", "Race Condition Kraken"), ("😈", "Stack Overflow Demon")]
ROOMS = ["m", "m", "t", "m", "r", "b"]
RICON = {"m": "⚔️", "t": "🎁", "r": "❤️", "b": "👹"}


class DungeonView(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.hero, self.cam, self.t, self.ph = "🧙", 0.0, 0.0, 0.0
        self.mode, self.cb, self.kind, self.mon, self.name, self.boss = "idle", None, None, "", "", False
        self.ox, self.hp, self.hpmax, self.mhp, self.mmax = 0.0, 5, 5, 1, 1
        self.hit_t = self.hurt_t = self.lunge_t = -9.0
        self.fl = []
        self.tm = QTimer(self)
        self.tm.timeout.connect(self.tick)

    def showEvent(self, e):
        self.tm.start(33)
        super().showEvent(e)

    def hideEvent(self, e):
        self.tm.stop()
        super().hideEvent(e)

    def reset(self, hero):
        self.hero, self.cam, self.mode, self.kind, self.fl, self.cb = hero, 0.0, "idle", None, [], None

    def set_hp(self, hp, mx, mh, mm):
        self.hp, self.hpmax, self.mhp, self.mmax = hp, mx, mh, mm

    def walk(self, kind, emoji, name, boss, cb):
        self.kind, self.mon, self.name, self.boss, self.cb = kind, emoji, name, boss, cb
        self.ox = self.cam + self.width() + 80
        self.mode, self.ph = "walk", 0.0

    def kill(self, cb):
        self.mode, self.ph, self.cb = "kill", 0.0, cb

    def die(self, cb):
        self.mode, self.ph, self.cb = "die", 0.0, cb

    def pop(self, text, x, y, col):
        self.fl.append([text, x, y, col, self.t])

    def hit_monster(self, dmg, crit):
        self.hit_t = self.lunge_t = self.t
        self.pop(("CRIT -" if crit else "-") + str(dmg), self.mx(), self.fy() - 110, "#ffc800" if crit else "#ffffff")

    def hit_hero(self, dmg):
        self.hurt_t = self.t
        self.pop(f"-{dmg}", self.hx(), self.fy() - 100, "#ff4b4b")

    def hx(self):
        d = self.t - self.lunge_t
        return self.width() * 0.2 + (60 * math.sin(math.pi * d / 0.35) if 0 <= d < 0.35 else 0)

    def mx(self):
        return self.ox - self.cam

    def fy(self):
        return self.height() * 0.82

    def _fire(self):
        cb, self.cb = self.cb, None
        if cb:
            cb()

    def tick(self):
        self.t += 0.033
        self.ph += 0.033
        if self.mode == "walk":
            self.cam += 8
            if self.mx() <= self.width() * (0.66 if self.kind in ("m", "b") else 0.45):
                self.mode, self.ph = ("alert", 0.0) if self.kind in ("m", "b") else ("idle", 0.0)
                if self.mode == "idle":
                    self._fire()
        elif self.mode == "alert" and self.ph > 0.85:
            self.mode = "idle"
            self._fire()
        elif self.mode == "kill" and self.ph > 0.7:
            self.mode, self.kind = "idle", None
            self._fire()
        elif self.mode == "die" and self.ph > 1.0:
            self.mode = "dead"
            self._fire()
        self.fl = [f for f in self.fl if self.t - f[4] < 1.0]
        self.update()

    def sprite(self, g, em, x, y, s, dy=0.0, a=1.0, rot=0.0):
        g.setPen(Qt.NoPen)
        g.setBrush(QColor(0, 0, 0, 90))
        g.drawEllipse(QPointF(x, y + 4), s * 0.45, s * 0.1)
        g.save()
        g.setOpacity(max(0.0, min(1.0, a)))
        g.translate(x, y - s * 0.5 - dy)
        g.rotate(rot)
        f = QFont()
        f.setPixelSize(int(s))
        g.setFont(f)
        g.setPen(QColor("#ffffff"))
        g.drawText(QRectF(-s, -s * 0.7, 2 * s, 1.4 * s), Qt.AlignCenter, em)
        g.restore()

    def bar(self, g, x, y, w, frac, col, label):
        g.setPen(Qt.NoPen)
        g.setBrush(QColor(0, 0, 0, 170))
        g.drawRoundedRect(QRectF(x - w / 2, y, w, 10), 5, 5)
        g.setBrush(QColor(col))
        g.drawRoundedRect(QRectF(x - w / 2, y, max(0.0, w * frac), 10), 5, 5)
        f = QFont()
        f.setBold(True)
        f.setPixelSize(12)
        g.setFont(f)
        g.setPen(QColor("#ffffff"))
        g.drawText(QRectF(x - 90, y - 18, 180, 16), Qt.AlignCenter, label)

    def paintEvent(self, e):
        g = QPainter(self)
        g.setRenderHint(QPainter.Antialiasing)
        w, h, t = self.width(), self.height(), self.t
        wall, fy = int(h * 0.64), self.fy()
        d = t - self.hurt_t
        if 0 <= d < 0.25:
            g.translate(random.uniform(-4, 4), random.uniform(-3, 3))
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor("#0d1015"))
        bg.setColorAt(1, QColor("#1b1f2a"))
        g.fillRect(QRectF(-10, -10, w + 20, h + 20), bg)
        g.setPen(QPen(QColor("#10131a"), 2))
        bh, bw = 24, 56
        for r in range(wall // bh + 1):
            x0 = -((int(self.cam * 0.5) + (r % 2) * (bw // 2)) % bw)
            for k, xx in enumerate(range(x0, w + bw, bw)):
                g.setBrush(QColor("#242836" if (k + r) % 3 else "#202432"))
                g.drawRect(xx, r * bh, bw, bh)
        fl = QLinearGradient(0, wall, 0, h)
        fl.setColorAt(0, QColor("#171a22"))
        fl.setColorAt(1, QColor("#0d0f14"))
        g.fillRect(QRectF(0, wall, w, h - wall), fl)
        g.setPen(QPen(QColor("#0f1218"), 2))
        for k in range(-1, w // 90 + 3):
            xx = k * 90 - self.cam % 90
            g.drawLine(QPointF(xx, wall), QPointF(xx - 40, h))
        for k in range(-1, w // 260 + 3):
            tx, ty = k * 260 + 130 - self.cam % 260, wall * 0.42
            fk = 0.55 + 0.45 * math.sin(t * 9 + k * 1.7)
            gl = QRadialGradient(tx, ty, 150)
            gl.setColorAt(0, QColor(255, 170, 60, int(95 * fk)))
            gl.setColorAt(1, QColor(255, 120, 20, 0))
            g.setPen(Qt.NoPen)
            g.setBrush(gl)
            g.drawEllipse(QPointF(tx, ty), 150, 150)
            g.setBrush(QColor("#4a3a2a"))
            g.drawRect(QRectF(tx - 4, ty + 10, 8, 24))
            f = QFont()
            f.setPixelSize(int(26 + 3 * fk))
            g.setFont(f)
            g.setPen(QColor("#ffffff"))
            g.drawText(QRectF(tx - 20, ty - 26, 40, 40), Qt.AlignCenter, "🔥")
        bob = abs(math.sin(t * 11)) * 7 if self.mode == "walk" else math.sin(t * 3) * 2
        ha, hr = 1.0, 0.0
        if self.mode in ("die", "dead"):
            k = min(1.0, self.ph / 0.9) if self.mode == "die" else 1.0
            ha, hr, bob = 1 - 0.7 * k, 90 * k, 0.0
        self.sprite(g, self.hero, self.hx(), fy, 64, bob, ha, hr)
        if self.mode not in ("die", "dead"):
            self.bar(g, self.hx(), fy - 64 - 30, 84, max(0, self.hp) / max(1, self.hpmax), "#ff4b4b", f"❤ {max(0, self.hp)}/{self.hpmax}")
        if self.kind:
            mx, size = self.mx(), (100 if self.boss else 78 if self.kind in ("m", "b") else 58)
            a, dy, rot = 1.0, math.sin(t * 3.5) * 3, 0.0
            if self.mode == "kill":
                k = min(1.0, self.ph / 0.7)
                a, dy, rot = 1 - k, k * 50, k * 50
            dd = t - self.hit_t
            dx = 9 * math.sin(dd * 60) * (1 - dd / 0.25) if 0 <= dd < 0.25 else 0
            self.sprite(g, self.mon, mx + dx, fy, size, dy, a, rot)
            if self.kind in ("m", "b") and self.mode in ("alert", "idle"):
                self.bar(g, mx, fy - size - 30, 96, max(0, self.mhp) / max(1, self.mmax), "#a855f7", self.name)
        if self.mode == "alert":
            pulse = 1 + 0.15 * math.sin(self.ph * 18)
            g.setPen(Qt.NoPen)
            g.setBrush(QColor("#ff4b4b"))
            g.drawEllipse(QPointF(self.hx(), fy - 140), 17 * pulse, 17 * pulse)
            f = QFont()
            f.setBold(True)
            f.setPixelSize(24)
            g.setFont(f)
            g.setPen(QColor("#ffffff"))
            g.drawText(QRectF(self.hx() - 20, fy - 160, 40, 40), Qt.AlignCenter, "!")
            f.setPixelSize(20)
            g.setFont(f)
            g.setPen(QColor("#ffc800"))
            g.drawText(QRectF(0, 12, w, 30), Qt.AlignCenter, ("⚠ BOSS · " if self.boss else "") + self.name + " appears!")
        for txt, x, y, col, born in self.fl:
            a = t - born
            g.setOpacity(max(0.0, 1 - a))
            f = QFont()
            f.setBold(True)
            f.setPixelSize(26)
            g.setFont(f)
            g.setPen(QColor(col))
            g.drawText(QRectF(x - 80, y - 40 * a, 160, 30), Qt.AlignCenter, txt)
        g.setOpacity(1.0)
        vg = QRadialGradient(w / 2, h * 0.55, w * 0.65)
        vg.setColorAt(0.55, QColor(0, 0, 0, 0))
        vg.setColorAt(1, QColor(0, 0, 0, 175))
        g.fillRect(QRectF(0, 0, w, h), vg)
        if 0 <= d < 0.25:
            g.fillRect(QRectF(0, 0, w, h), QColor(255, 0, 0, int(90 * (1 - d / 0.25))))


class Dungeon(QWidget):
    back = Signal()

    def __init__(self, st):
        super().__init__()
        self.st, self.lang, self.run, self.q, self.checked, self.sel, self.opts = st, "Python", False, None, False, None, []
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.setContentsMargins(28, 20, 28, 0)
        x = QPushButton("←")
        x.setObjectName("x")
        x.setCursor(Qt.PointingHandCursor)
        x.clicked.connect(self.leave)
        h = QLabel("🏰  Coding Dungeon")
        h.setObjectName("title")
        self.hud = QLabel()
        self.hud.setObjectName("stats")
        bar.addWidget(x)
        bar.addWidget(h, 1)
        bar.addWidget(self.hud)
        root.addLayout(bar)
        self.pages = FadeStack()
        root.addWidget(self.pages, 1)
        self.info = QLabel()
        self.info.setTextFormat(Qt.RichText)
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setWordWrap(True)
        self.info.setMaximumWidth(640)
        self.go_btn = QPushButton("ENTER THE DUNGEON")
        self.go_btn.setObjectName("act")
        self.go_btn.setCursor(Qt.PointingHandCursor)
        self.go_btn.clicked.connect(self.begin)
        p0 = QWidget()
        v0 = QVBoxLayout(p0)
        v0.setAlignment(Qt.AlignCenter)
        v0.setSpacing(22)
        v0.addWidget(self.info, 0, Qt.AlignHCenter)
        v0.addWidget(self.go_btn, 0, Qt.AlignHCenter)
        self.pages.addWidget(p0)
        b = QWidget()
        bl = QVBoxLayout(b)
        bl.setContentsMargins(30, 14, 30, 14)
        bl.setSpacing(10)
        self.path = QLabel()
        self.path.setAlignment(Qt.AlignCenter)
        self.path.setTextFormat(Qt.RichText)
        self.path.setStyleSheet("font-size:20px")
        self.hpl = QLabel()
        self.hpl.setStyleSheet("color:#ff7878;font-weight:900")
        self.hp = QProgressBar()
        self.hp.setTextVisible(False)
        self.hp.setStyleSheet("QProgressBar::chunk{background:#ff4b4b}")
        scene = QFrame()
        scene.setObjectName("card")
        sv = QVBoxLayout(scene)
        self.mon = QLabel()
        self.mon.setAlignment(Qt.AlignCenter)
        self.mon.setStyleSheet("font-size:84px")
        self.mn = QLabel()
        self.mn.setAlignment(Qt.AlignCenter)
        self.mn.setStyleSheet("font-weight:900;font-size:18px")
        self.mhp = QProgressBar()
        self.mhp.setTextVisible(False)
        self.mhp.setStyleSheet("QProgressBar::chunk{background:#a855f7}")
        for w in (self.mon, self.mn, self.mhp):
            sv.addWidget(w)
        self.pr = QLabel()
        self.pr.setWordWrap(True)
        self.pr.setStyleSheet("font-size:22px;font-weight:900")
        self.cd = QLabel()
        self.cd.setObjectName("code")
        self.cd.setTextFormat(Qt.PlainText)
        self.ol = QVBoxLayout()
        self.ol.setSpacing(8)
        self.inp = QLineEdit()
        self.inp.setObjectName("inp")
        self.inp.setPlaceholderText("Type your answer...")
        self.inp.textChanged.connect(lambda t: self.act.setEnabled(bool(t.strip()) and not self.checked))
        self.inp.returnPressed.connect(lambda: self.act.isEnabled() and self.go())
        self.fb = QLabel()
        self.fb.setWordWrap(True)
        self.fb.setStyleSheet("font-size:17px;font-weight:800")
        self.act = QPushButton("ATTACK ⚔️")
        self.act.setObjectName("act")
        self.act.setCursor(Qt.PointingHandCursor)
        self.act.clicked.connect(self.go)
        self.scene = scene
        self.view = DungeonView()
        self.qbox = QWidget()
        ql = QVBoxLayout(self.qbox)
        ql.setContentsMargins(0, 0, 0, 0)
        ql.setSpacing(10)
        for w in (self.path, self.hpl, self.hp, self.view):
            bl.addWidget(w)
        for w in (self.pr, self.cd):
            ql.addWidget(w)
        ql.addLayout(self.ol)
        ql.addWidget(self.inp)
        ql.addWidget(self.fb)
        ql.addWidget(self.act, 0, Qt.AlignHCenter)
        bl.addWidget(self.qbox)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(center(b, 760))
        self.pages.addWidget(sc)
        p2 = QWidget()
        v2 = QVBoxLayout(p2)
        v2.setAlignment(Qt.AlignCenter)
        v2.setSpacing(22)
        self.evl = QLabel()
        self.evl.setTextFormat(Qt.RichText)
        self.evl.setAlignment(Qt.AlignCenter)
        nb = QPushButton("CONTINUE")
        nb.setObjectName("act")
        nb.setCursor(Qt.PointingHandCursor)
        nb.clicked.connect(self.nxt)
        v2.addWidget(self.evl)
        v2.addWidget(nb, 0, Qt.AlignHCenter)
        self.pages.addWidget(p2)

    def open(self, lang):
        self.lang, d = lang, self.st.get("dungeon", {})
        self.run = False
        self.info.setText(f"<div style='font-size:64px'>🏰</div><div style='font-size:30px;font-weight:900'>Coding Dungeon</div><br>Fight bugs with your <b>{lang}</b> knowledge! Right answers hit, wrong answers hurt. A combo of 3 deals <b>double damage</b>. Rest rooms heal you, treasure rooms power you up and every floor ends with a boss.<br><br><span style='color:#ffc800'>Best floor {d.get('best', 0)} · Runs {d.get('runs', 0)} · Monsters slain {d.get('kills', 0)}</span>")
        self.go_btn.setText("ENTER THE DUNGEON")
        self.hud.setText("")
        self.pages.setCurrentIndex(0)

    def begin(self):
        self.pool = [q for l in LANGS[self.lang][2] for q in l[2]]
        self.floor, self.room, self.maxhp, self.hpv, self.coins, self.kills, self.streak, self.run = 1, 0, 5, 5, 0, 0, 0, True
        self.view.reset(self.st.get("avatar") or "🧙")
        self.enter()

    def redraw(self):
        self.hud.setText(f"Floor {self.floor}   🪙 {self.coins}   ⚔️ {self.kills}")
        self.hp.setMaximum(self.maxhp)
        self.hp.setValue(max(0, self.hpv))
        self.hpl.setText(f"❤ {max(0, self.hpv)} / {self.maxhp}")
        self.path.setText("  ".join("✔️" if i < self.room else f"<span style='color:#ffc800'>【{RICON[t]}】</span>" if i == self.room else RICON[t] for i, t in enumerate(ROOMS)))

    def enter(self):
        if self.room >= len(ROOMS):
            self.floor += 1
            self.room = 0
            self.coins += 5
            self.hpv = min(self.maxhp, self.hpv + 1)
        t = ROOMS[self.room]
        self.redraw()
        if t in "mb":
            self.fight(t == "b")
        else:
            self.room_event(t)

    def room_event(self, t):
        if t == "t":
            if random.random() < 0.5:
                self.coins += 3
                e, tx = "🎁", "You open a chest and find <b>3 coins</b>!"
            else:
                self.maxhp += 1
                self.hpv += 1
                e, tx = "💖", "A heart crystal! <b>Max HP +1</b>."
            SND.play("chest")
        else:
            self.hpv = min(self.maxhp, self.hpv + 2)
            e, tx = "🏕️", "You rest by a campfire and heal <b>2 HP</b>."
        self.redraw()
        self.evl.setText(f"<div style='font-size:80px'>{e}</div><div style='font-size:22px'>{tx}</div>")
        self.pages.setCurrentIndex(1)
        self.qbox.hide()
        self.view.set_hp(self.hpv, self.maxhp, 1, 1)
        self.view.walk(t, "🎁" if t == "t" else "🏕️", "", False, self.show_event)

    def nxt(self):
        self.room += 1
        self.enter()

    def fight(self, boss):
        e, nm = BOSS[(self.floor - 1) % len(BOSS)] if boss else random.choice(MON)
        self.boss = boss
        self.mmax = self.mhpv = (4 + self.floor) if boss else 2 + (self.floor - 1) // 2
        self.mon.setText(e)
        self.mn.setText(("BOSS · " if boss else "") + nm)
        self.mhp.setMaximum(self.mmax)
        self.mhp.setValue(self.mmax)
        self.pages.setCurrentIndex(1)
        self.qbox.hide()
        self.view.set_hp(self.hpv, self.maxhp, self.mmax, self.mmax)
        self.view.walk("b" if boss else "m", e, nm, boss, self.arrived)

    def arrived(self):
        if self.run:
            self.qbox.show()
            self.ask()

    def after_kill(self):
        if self.run:
            self.room += 1
            self.enter()

    def show_event(self):
        if self.run:
            self.pages.setCurrentIndex(2)

    def repol(self):
        for w in self.opts:
            w.style().unpolish(w)
            w.style().polish(w)

    def ask(self):
        p, c, o, a = random.choice(self.pool)
        if o:
            k = random.sample(range(len(o)), len(o))
            o, a = [o[x] for x in k], k.index(a)
        self.q = (p, c, o, a)
        while self.ol.count():
            self.ol.takeAt(0).widget().deleteLater()
        self.opts, self.sel, self.checked = [], None, False
        for i, t in enumerate(o or []):
            b = QPushButton(f"{i + 1}    {t}")
            b.setObjectName("opt")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, i=i: self.pick(i))
            self.ol.addWidget(b)
            self.opts.append(b)
        self.pr.setText(p)
        self.cd.setText(c)
        self.cd.setVisible(bool(c))
        self.inp.setVisible(o is None)
        self.inp.setEnabled(True)
        self.inp.clear()
        self.fb.setText("")
        self.act.setText("ATTACK ⚔️")
        self.act.setEnabled(False)

    def pick(self, i):
        if self.checked:
            return
        for j, b in enumerate(self.opts):
            b.setChecked(j == i)
        self.sel = i
        self.act.setEnabled(True)

    def check(self):
        p, c, o, a = self.q
        typed = o is None
        ok = ("".join(self.inp.text().split()) in ["".join(x.split()) for x in a]) if typed else self.sel == a
        self.checked = True
        self.inp.setEnabled(False)
        for j, b in enumerate(self.opts):
            b.setEnabled(False)
            if j == a:
                b.setProperty("state", "good")
            elif j == self.sel:
                b.setProperty("state", "bad")
        if ok:
            self.streak += 1
            dmg = 2 if self.streak >= 3 else 1
            self.mhpv = max(0, self.mhpv - dmg)
            msg = f"✅ {'🔥 CRIT! ' if dmg == 2 else ''}You hit for {dmg}."
            SND.play("correct")
            QST.add("correct")
            self.view.hit_monster(dmg, dmg == 2)
        else:
            self.streak = 0
            dmg = 2 if self.boss else 1
            self.hpv -= dmg
            msg = f"❌ Ouch! It hits you for {dmg}. Answer: {a[0] if typed else o[a]}"
            SND.play("wrong")
            wiggle(self.hp)
            self.view.hit_hero(dmg)
        if self.mhpv <= 0:
            msg += "\n💥 Defeated!"
        elif self.hpv <= 0:
            msg += "\n💀 You fall..."
        self.fb.setText(msg)
        self.mhp.setValue(self.mhpv)
        self.view.set_hp(self.hpv, self.maxhp, self.mhpv, self.mmax)
        self.act.setText("CONTINUE")
        self.redraw()
        self.repol()

    def go(self):
        if not self.checked:
            self.check()
        elif self.hpv <= 0:
            self.qbox.hide()
            self.view.die(self.finish)
        elif self.mhpv <= 0:
            self.kills += 1
            self.coins += 3 if self.boss else 1
            QST.add("kills")
            if self.boss:
                SND.play("complete")
                self.fx.burst()
            self.qbox.hide()
            self.view.kill(self.after_kill)
        else:
            self.ask()

    def finish(self):
        if not self.run:
            return
        self.run = False
        cleared = self.floor - 1
        gems, xp, chest = min(self.coins + cleared * 5, 80), min(self.kills * 5 + cleared * 10, 200), 1 if cleared >= 3 else 0
        st = self.st
        st["gems"] += gems
        st["xp"] += xp
        st["chests"] += chest
        d = st.setdefault("dungeon", {"best": 0, "runs": 0, "kills": 0})
        d["best"], d["runs"], d["kills"] = max(d["best"], self.floor), d["runs"] + 1, d["kills"] + self.kills
        save(st)
        dead = self.hpv <= 0
        self.info.setText(f"<div style='font-size:64px'>{'💀' if dead else '🚪'}</div><div style='font-size:28px;font-weight:900'>{'You were defeated' if dead else 'You left the dungeon'}</div><br>Floor reached <b>{self.floor}</b> · Monsters slain <b>{self.kills}</b><br><br><span style='color:#ffc800'>💎 +{gems} gems · ⚡ +{xp} XP{' · 🎁 +1 chest' if chest else ''}</span>")
        self.go_btn.setText("TRY AGAIN")
        self.pages.setCurrentIndex(0)
        if dead:
            SND.play("fail")

    def leave(self):
        if self.run:
            self.finish()
        self.back.emit()


class QuestPage(QWidget):
    back = Signal()

    def __init__(self, st):
        super().__init__()
        self.st = st
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.setContentsMargins(28, 20, 28, 0)
        x = QPushButton("←")
        x.setObjectName("x")
        x.setCursor(Qt.PointingHandCursor)
        x.clicked.connect(self.back.emit)
        h = QLabel("📜  Daily Quests")
        h.setObjectName("title")
        bar.addWidget(x)
        bar.addWidget(h, 1)
        root.addLayout(bar)
        self.body = QWidget()
        self.col = QVBoxLayout(self.body)
        self.col.setSpacing(12)
        self.col.setContentsMargins(30, 16, 30, 30)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(center(self.body, 760))
        root.addWidget(sc, 1)

    def claim(self, qd):
        qd["claimed"] = True
        self.st["gems"] += qd["gems"]
        SND.play("chest")
        q = self.st["quests"]
        if all(x["claimed"] for x in q["list"]) and not q["bonus"]:
            q["bonus"] = True
            self.st["chests"] += 1
            SND.play("complete")
        save(self.st)
        self.refresh()

    def refresh(self):
        QST.roll()
        q = self.st["quests"]
        while self.col.count():
            w = self.col.takeAt(0).widget()
            if w:
                w.deleteLater()
        sub = QLabel("New quests every day. Finish them, claim your rewards, and claim all three for a bonus 🎁 chest!")
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#8ea0a8")
        self.col.addWidget(sub)
        for qd in q["list"]:
            done = qd["prog"] >= qd["goal"]
            c = QFrame()
            c.setObjectName("card")
            hl = QHBoxLayout(c)
            hl.setContentsMargins(18, 14, 18, 14)
            em = QLabel("✅" if qd["claimed"] else qd["icon"])
            em.setStyleSheet("font-size:36px")
            v = QVBoxLayout()
            t = QLabel(f"<b style='font-size:17px'>{qd['text']}</b>")
            t.setTextFormat(Qt.RichText)
            pb = QProgressBar()
            pb.setTextVisible(False)
            pb.setMaximum(qd["goal"])
            pb.setValue(qd["prog"])
            pb.setStyleSheet("QProgressBar::chunk{background:#ffc800}")
            sm = QLabel(f"{qd['prog']}/{qd['goal']}   ·   💎 {qd['gems']}")
            sm.setStyleSheet("color:#ffc800")
            v.addWidget(t)
            v.addWidget(pb)
            v.addWidget(sm)
            b = QPushButton("CLAIMED" if qd["claimed"] else "CLAIM" if done else "IN PROGRESS")
            b.setObjectName("act")
            b.setEnabled(done and not qd["claimed"])
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("padding:10px 18px")
            b.clicked.connect(lambda _, qd=qd: self.claim(qd))
            hl.addWidget(em)
            hl.addLayout(v, 1)
            hl.addWidget(b)
            self.col.addWidget(c)
        bn = QLabel("🎁  Bonus chest: " + ("collected!" if q["bonus"] else "claim all 3 quests"))
        bn.setStyleSheet("font-weight:800;color:#a855f7;margin-top:8px")
        self.col.addWidget(bn)
        self.col.addStretch()


class Welcome(QWidget):
    named = Signal(str)

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setAlignment(Qt.AlignCenter)
        v.setSpacing(18)
        e = QLabel("🤖")
        e.setAlignment(Qt.AlignCenter)
        e.setStyleSheet("font-size:84px")
        t = QLabel("Welcome to Codingo!")
        t.setObjectName("title")
        t.setAlignment(Qt.AlignCenter)
        u = QLabel("I'm Byte. What should I call you?")
        u.setAlignment(Qt.AlignCenter)
        u.setStyleSheet("color:#8ea0a8;font-size:18px")
        self.inp = QLineEdit()
        self.inp.setObjectName("inp")
        self.inp.setPlaceholderText("Your name")
        self.inp.setMaxLength(20)
        self.inp.setAlignment(Qt.AlignCenter)
        self.inp.setFixedWidth(380)
        b = QPushButton("LET'S GO")
        b.setObjectName("act")
        b.setCursor(Qt.PointingHandCursor)
        b.setFixedWidth(380)
        self.inp.returnPressed.connect(self.go)
        b.clicked.connect(self.go)
        for w in (e, t, u):
            v.addWidget(w)
        v.addWidget(self.inp, 0, Qt.AlignHCenter)
        v.addWidget(b, 0, Qt.AlignHCenter)

    def go(self):
        n = self.inp.text().strip()
        if n:
            self.named.emit(n)


class Account(QWidget):
    back = Signal()

    def __init__(self, st):
        super().__init__()
        self.st = st
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.setContentsMargins(28, 20, 28, 0)
        x = QPushButton("←")
        x.setObjectName("x")
        x.setCursor(Qt.PointingHandCursor)
        x.clicked.connect(self.back.emit)
        h = QLabel("Account")
        h.setObjectName("title")
        bar.addWidget(x)
        bar.addWidget(h, 1)
        root.addLayout(bar)
        self.body = QWidget()
        self.col = QVBoxLayout(self.body)
        self.col.setSpacing(14)
        self.col.setContentsMargins(30, 20, 30, 30)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(center(self.body, 700))
        root.addWidget(sc, 1)

    def reset(self):
        lang = getattr(self, "lang", "Python")
        m = QMessageBox(self)
        m.setWindowTitle("Restart progress")
        m.setText("What do you want to restart?\nRoadmap, projects, challenges and quiz history are cleared. Your XP, gems, avatars and name are kept. This cannot be undone.")
        m.setStyleSheet("QPushButton{background:#22323b;border:2px solid #37464f;border-radius:12px;padding:10px 22px;font-weight:800}QPushButton:hover{background:#2b3d46}")
        a = m.addButton(f"{LANGS[lang][0]} {lang} only", QMessageBox.AcceptRole)
        b = m.addButton("All languages", QMessageBox.DestructiveRole)
        m.addButton("Cancel", QMessageBox.RejectRole)
        m.exec()
        c = m.clickedButton()
        if c not in (a, b):
            return
        for k in ("prog", "field", "field2", "chal", "extra", "pdone", "big", "weak", "daily"):
            d = self.st.get(k)
            if isinstance(d, dict):
                d.pop(lang, None) if c is a else d.clear()
        save(self.st)
        self.refresh()

    def ren(self):
        t, ok = QInputDialog.getText(self, "Change name", "Your name:", text=self.st["name"])
        if ok and t.strip():
            self.st["name"] = t.strip()[:20]
            save(self.st)
            self.refresh()

    def refresh(self):
        st = self.st
        xp = st["xp"]
        lv = xp // 150
        while self.col.count():
            w = self.col.takeAt(0).widget()
            if w:
                w.deleteLater()
        av = QLabel(st.get("avatar") or st["name"][:1].upper())
        av.setFixedSize(96, 96)
        av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #a6f03a,stop:1 #3f9b02);border:4px solid #2b3d46;border-radius:48px;font-size:44px;font-weight:900;color:#10200a")
        nm = QLabel(st["name"])
        nm.setObjectName("title")
        sb = QLabel(f"Lv {lv + 1}  ·  {TITLES[min(lv, 5)]}")
        sb.setStyleSheet("color:#ffc800;font-weight:800;font-size:18px")
        pb = QProgressBar()
        pb.setTextVisible(False)
        pb.setValue(xp % 150 * 100 // 150)
        pl = QLabel(f"{xp % 150}/150 XP to the next level")
        pl.setStyleSheet("color:#8ea0a8")
        for w in (av, nm, sb):
            self.col.addWidget(w, 0, Qt.AlignHCenter)
        self.col.addWidget(pb)
        self.col.addWidget(pl, 0, Qt.AlignHCenter)
        g = QGridLayout()
        g.setSpacing(12)
        items = [("⚡", "Total XP", xp), ("🔥", "Day streak", st["streak"]), ("📚", "Lessons done", st["lessons"]),
                 ("💎", "Perfect lessons", st["perfect"]), ("🎯", "Best combo", st["combo"]), ("📅", "Dailies done", st["dailies"]), ("💎", "Gems", st["gems"]), ("🎁", "Chests", st["chests"])]
        for n, (ic, lb, val) in enumerate(items):
            c = QFrame()
            c.setObjectName("card")
            cl = QVBoxLayout(c)
            a = QLabel(f"{ic}  {val}")
            a.setObjectName("big")
            b = QLabel(lb)
            b.setStyleSheet("color:#8ea0a8")
            cl.addWidget(a)
            cl.addWidget(b)
            g.addWidget(c, n // 3, n % 3)
        gw = QWidget()
        gw.setLayout(g)
        self.col.addWidget(gw)
        for n, (ic, c, _) in LANGS.items():
            p = st["prog"].get(n, 0)
            lb = QLabel(f"{ic}  {n}   ·   {min(p, total(n))}/{total(n)} steps")
            lb.setStyleSheet("font-weight:800")
            bar = QProgressBar()
            bar.setTextVisible(False)
            bar.setValue(min(p, total(n)) * 100 // total(n))
            bar.setStyleSheet(f"QProgressBar::chunk{{background:{c}}}")
            self.col.addWidget(lb)
            self.col.addWidget(bar)
        rn = QPushButton("✎  Change name")
        rn.setObjectName("tab")
        rn.setCursor(Qt.PointingHandCursor)
        rn.clicked.connect(self.ren)
        self.col.addWidget(rn, 0, Qt.AlignHCenter)
        rb = QPushButton("🔄  Restart progress")
        rb.setObjectName("tab")
        rb.setStyleSheet("color:#ff7878")
        rb.setCursor(Qt.PointingHandCursor)
        rb.clicked.connect(self.reset)
        self.col.addWidget(rb, 0, Qt.AlignHCenter)
        self.col.addStretch()


def fade(w, ms=260, delay=0):
    e = QGraphicsOpacityEffect(w)
    e.setOpacity(0.0)
    w.setGraphicsEffect(e)
    a = QPropertyAnimation(e, b"opacity", e)
    a.setDuration(ms)
    a.setStartValue(0.0)
    a.setEndValue(1.0)
    a.setEasingCurve(QEasingCurve.OutCubic)

    def done():
        try:
            w.setGraphicsEffect(None)
        except RuntimeError:
            pass

    def run():
        try:
            a.start()
        except RuntimeError:
            pass

    a.finished.connect(lambda: QTimer.singleShot(0, done))
    QTimer.singleShot(delay, run)


class FadeStack(QStackedWidget):
    def setCurrentIndex(self, i):
        old = self.currentIndex()
        super().setCurrentIndex(i)
        w = self.currentWidget()
        if w is None or i == old:
            return
        fade(w, 260)
        p = w.pos()
        a = QPropertyAnimation(w, b"pos", self)
        a.setDuration(260)
        a.setStartValue(QPoint(p.x(), p.y() + 30))
        a.setEndValue(p)
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.start(QAbstractAnimation.DeleteWhenStopped)


class Confetti(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.p = []
        self.n = 0
        self.t = QTimer(self)
        self.t.timeout.connect(self.tick)
        self.hide()

    def burst(self):
        self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()
        cols = ["#58cc02", "#ffc800", "#49c0f8", "#ff4b4b", "#a855f7", "#ff9600"]
        self.p = [[random.uniform(0, self.width()), random.uniform(-400, 0), random.uniform(-2, 2), random.uniform(4, 9), QColor(random.choice(cols)), random.uniform(7, 13)] for _ in range(160)]
        self.n = 0
        self.t.start(16)

    def tick(self):
        self.n += 1
        for q in self.p:
            q[0] += q[2] + math.sin(self.n / 8 + q[5]) * 0.9
            q[1] += q[3]
        self.update()
        if self.n > 160:
            self.t.stop()
            self.hide()

    def paintEvent(self, e):
        g = QPainter(self)
        g.setRenderHint(QPainter.Antialiasing)
        g.setPen(Qt.NoPen)
        for q in self.p:
            x, y, _, _, c, z = q
            g.setBrush(c)
            g.save()
            g.translate(x, y)
            g.rotate((self.n * 6 + x) % 360)
            if int(x) % 3:
                g.drawRect(QRectF(-z / 2, -z * 0.3, z, z * 0.6))
            else:
                g.drawEllipse(QPointF(0, 0), z * 0.4, z * 0.4)
            g.restore()


class Picker(QWidget):
    chose = Signal(str)

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setAlignment(Qt.AlignCenter)
        v.setSpacing(28)
        t = QLabel("What do you want to learn?")
        t.setObjectName("title")
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)
        row = QGridLayout()
        row.setSpacing(20)
        row.setAlignment(Qt.AlignCenter)
        for k, (n, (ic, c, _)) in enumerate(LANGS.items()):
            b = QPushButton(f"{ic}\n{n}")
            b.setFixedSize(190, 150)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{background:#1a2830;border:2px solid #2b3d46;border-bottom:7px solid {c};border-radius:22px;font-size:28px;font-weight:900}}"
                f"QPushButton:hover{{background:#22323b;border-color:{c}}}")
            b.clicked.connect(lambda _, n=n: self.chose.emit(n))
            row.addWidget(b, k // 4, k % 4)
        v.addLayout(row)


class Win(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Codingo")
        self.resize(1340, 780)
        self.st = load()
        _set_snd(Sound(self.st))
        _set_q(Quest(self.st))
        SND.prepare()
        QTimer.singleShot(600, SND.apply)
        self.stack = FadeStack()
        self.setCentralWidget(self.stack)
        self.home, self.les = Home(self.st), Lesson()
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.les)
        self.pick = Picker()
        self.stack.addWidget(self.pick)
        self.prj = Project()
        self.stack.addWidget(self.prj)
        self.prj.done.connect(self.fin)
        self.conf = Confetti(self.stack)
        self.les.fx = self.prj.fx = self.conf
        self.wel, self.acc = Welcome(), Account(self.st)
        self.stack.addWidget(self.wel)
        self.stack.addWidget(self.acc)
        self.wel.named.connect(self.named)
        self.acc.back.connect(lambda: (self.home.refresh(), self.stack.setCurrentIndex(0)))
        self.home.acct.connect(self.show_acc)
        self.home.daily.connect(self.go_daily)
        self.shop = Shop(self.st)
        self.shop.fx = self.conf
        self.stack.addWidget(self.shop)
        self.shop.back.connect(lambda: (self.home.refresh(), self.stack.setCurrentIndex(0)))
        self.home.shop.connect(self.show_shop)
        self.home.chal.connect(self.go_chal)
        self.tutor = Tutor(self.st)
        self.stack.addWidget(self.tutor)
        self.prev = 0
        self.tutor.back.connect(self.close_tutor)
        self.home.tutor.connect(lambda: self.open_tutor(self.home.lang))
        self.les.ask.connect(self.open_tutor)
        self.projs = Projects(self.st)
        self.stack.addWidget(self.projs)
        self.projs.start.connect(self.go_proj)
        self.projs.big.connect(self.go_big)
        self.projs.back.connect(lambda: (self.home.refresh(), self.stack.setCurrentIndex(0)))
        self.home.projs.connect(self.show_projs)
        self.settings = Settings()
        self.stack.addWidget(self.settings)
        self.settings.back.connect(lambda: self.stack.setCurrentIndex(0))
        self.home.settings.connect(self.show_settings)
        self.dng = Dungeon(self.st)
        self.dng.fx = self.conf
        self.stack.addWidget(self.dng)
        self.dng.back.connect(lambda: (self.home.refresh(), self.stack.setCurrentIndex(0)))
        self.qp = QuestPage(self.st)
        self.stack.addWidget(self.qp)
        self.qp.back.connect(lambda: (self.home.refresh(), self.stack.setCurrentIndex(0)))
        self.home.dungeon.connect(self.show_dungeon)
        self.home.quests.connect(self.show_quests)
        self.home.extra.connect(self.go_extra)
        self.home.skip.connect(self.go_skip)
        self.home.refresh()
        if not self.st["name"]:
            self.stack.setCurrentIndex(4)
        self.pick.chose.connect(self.choose)
        self.home.back.connect(lambda: self.stack.setCurrentIndex(2))
        self.stack.setCurrentIndex(2)
        self.home.start.connect(self.go)
        self.les.done.connect(self.fin)

    def named(self, n):
        self.st["name"] = n
        save(self.st)
        self.home.refresh()
        self.stack.setCurrentIndex(2)

    def go_skip(self, lang, tg):
        nd, d = nodes(lang, self.st), self.st["prog"].get(lang, 0)
        js = [j for k, j in nd[d:tg] if k == "l"] or [j for k, j in nd[:tg] if k == "l"][-3:]
        pool = [q for j in js for q in LANGS[lang][2][j][2]]
        T = len(TRUNKS[lang])
        name = next((nm for key, tag, nm in UN.get(lang, UNITS) if (key if isinstance(key, int) else T) == tg), "the next unit")
        qs = random.sample(pool, min(10, len(pool)))
        self.cur = (lang, -400 - tg)
        self.les.begin(lang, 0, qs, True, ("⏩", "Skip Test", f"Pass this test to jump ahead to <b>{name}</b>. {len(qs)} questions from the lessons you would skip, and only <b>3 hearts</b>. Everything before it then counts as done.", 3))
        self.stack.setCurrentIndex(1)

    def go_extra(self, lang, i):
        js = [j for k, j in nodes(lang, self.st)[:i + 1] if k == "l"]
        pool = [q for j in js for q in LANGS[lang][2][j][2]]
        self.cur = (lang, -300 - i)
        self.les.begin(lang, 0, random.sample(pool, min(4, len(pool))), True, ("✏️", "Extra Practice", "Four quick review questions from what you've learned so far. First time reward: <b>💎 8</b>.", 5))
        self.stack.setCurrentIndex(1)

    def show_dungeon(self):
        self.dng.open(self.home.lang)
        self.stack.setCurrentIndex(10)

    def show_quests(self):
        self.qp.refresh()
        self.stack.setCurrentIndex(11)

    def show_settings(self):
        self.settings.refresh()
        self.stack.setCurrentIndex(9)

    def show_projs(self):
        self.projs.refresh(self.home.lang)
        self.stack.setCurrentIndex(8)

    def go_big(self, lang, bi):
        d = self.st["big"].setdefault(lang, {}).setdefault(str(bi), {"m": 0, "code": ""})
        self.cur = (lang, -500 - bi)
        self.prj.begin_big(lang, bi, d["m"], d["code"])
        self.stack.setCurrentIndex(3)

    def keep(self):
        lang, i = self.cur
        d = self.st["big"].setdefault(lang, {}).setdefault(str(-500 - i), {"m": 0, "code": ""})
        d["code"] = self.prj.ed.toPlainText()
        save(self.st)

    def go_proj(self, lang, pid):
        self.cur = (lang, -200 - pid)
        self.prj.begin(lang, 100 + pid)
        self.stack.setCurrentIndex(3)

    def open_tutor(self, lang, text=""):
        self.tutor.lang = lang or self.home.lang
        self.prev = self.stack.currentIndex()
        self.stack.setCurrentIndex(7)
        if text:
            self.tutor.send(text)

    def close_tutor(self):
        if self.prev == 0:
            self.home.refresh()
        self.stack.setCurrentIndex(self.prev)

    def go_chal(self, lang, cid):
        kind = cid // 4 % 3
        em, nm, gm, hr, cnt, tx = CH[kind]
        js = [j for k, j in nodes(lang, self.st)[:cid + 1] if k == "l"]
        pool = [q for j in js for q in LANGS[lang][2][j][2]]
        if kind == 1:
            pool = [q for q in pool if q[2] is None] or pool
        qs = random.sample(pool, min(cnt, len(pool)))
        self.cur = (lang, -100 - cid)
        self.les.begin(lang, 0, qs, True, (em, nm, f"{tx} Reward: <b>💎 {gm}</b>", hr))
        self.stack.setCurrentIndex(1)

    def show_shop(self):
        self.shop.refresh()
        self.stack.setCurrentIndex(6)

    def show_acc(self):
        self.acc.lang = self.home.lang
        self.acc.refresh()
        self.stack.setCurrentIndex(5)

    def pick_field(self, lang, i, w=0):
        key, brs = ("field", BR) if w == 0 else ("field2", BR2)
        if self.st[key].get(lang) is not None:
            return
        m = QMessageBox(self)
        m.setWindowTitle("Choose your field")
        m.setText("Pick the field you want to specialise in.\nThis choice is permanent for this language." if w == 0 else "Pick your specialization: a deep dive that only this language offers.\nThis choice is permanent for this language.")
        m.setStyleSheet("QPushButton{background:#22323b;border:2px solid #37464f;border-radius:12px;padding:10px 18px;font-weight:800}QPushButton:hover{background:#2b3d46}")
        bs = [m.addButton(f"{e}  {n}", QMessageBox.AcceptRole) for n, e, _ in brs[lang]]
        m.addButton("Not yet", QMessageBox.RejectRole)
        m.exec()
        if m.clickedButton() in bs:
            self.st[key][lang] = bs.index(m.clickedButton())
            if self.st["prog"].get(lang, 0) == i:
                self.st["prog"][lang] = i + 1
            save(self.st)
            self.home.refresh()
            SND.play("complete")
            self.conf.burst()

    def go_daily(self, lang):
        self.cur = (lang, -1)
        pool = [q for k, j in nodes(lang, self.st) if k == "l" for q in LANGS[lang][2][j][2]]
        r = random.Random(date.today().toordinal() + sum(map(ord, lang)))
        self.les.begin(lang, 0, r.sample(pool, 5), True)
        self.stack.setCurrentIndex(1)

    def choose(self, n):
        self.home.pick(n)
        self.stack.setCurrentIndex(0)

    def go(self, lang, i):
        self.cur = (lang, i)
        k, j = nodes(lang, self.st)[i]
        if k == "f":
            self.pick_field(lang, i, j)
        elif k == "l":
            self.les.begin(lang, j)
            self.stack.setCurrentIndex(1)
        elif k == "b":
            pool = [q for k, j in nodes(lang, self.st)[:i] if k == "l" for q in LANGS[lang][2][j][2]]
            self.les.bossn = j + 1
            self.les.begin(lang, 0, random.sample(pool, 10))
            self.stack.setCurrentIndex(1)
        else:
            self.prj.begin(lang, j)
            self.stack.setCurrentIndex(3)

    def fin(self, ok, xp):
        if self.cur[1] <= -500:
            self.keep()
        if ok:
            lang, i = self.cur
            st = self.st
            st["xp"] += xp
            st["lessons"] += 1
            kd = "d" if i < 0 else nodes(lang, st)[i][0]
            st["gems"] += 15 if kd == "p" else 0 if i <= -200 else self.les.gems
            if kd in ("p", "b"):
                st["chests"] += 1
            if kd == "l":
                QST.add("lessons", 1, lang)
            if kd == "p" or -300 < i <= -200:
                QST.add("project")
            if i > -300:
                QST.add("xp", max(0, xp))
            if i <= -500:
                bi = -500 - i
                d = st["big"][lang][str(bi)]
                d["m"] += 1
                st["gems"] += 15
                if d["m"] >= len(BIGP[bi][3]):
                    st["gems"] += 100
                    st["chests"] += 1
            elif i <= -400:
                st["prog"][lang] = max(st["prog"].get(lang, 0), -400 - i)
                st["xp"] -= xp
            elif i <= -300:
                ex = -300 - i
                if ex in st["extra"].setdefault(lang, []):
                    st["xp"] -= xp
                else:
                    st["extra"][lang].append(ex)
                    st["gems"] += 8
            elif i <= -200:
                pj = -200 - i
                if pj in st["pdone"].setdefault(lang, []):
                    st["xp"] -= xp
                else:
                    st["pdone"][lang].append(pj)
                    st["gems"] += XPJ[pj][4]
                    st["chests"] += 1 if XPJ[pj][3] == "hard" else 0
            elif i <= -100:
                kc = (-100 - i) // 4 % 3
                st["chal"].setdefault(lang, []).append(-100 - i)
                st["gems"] += CH[kc][2]
                st["chests"] += 1 if kc == 2 else 0
            elif i < 0:
                st["daily"][lang] = date.today().toordinal()
                st["dailies"] += 1
                st["xp"] += 25
            if i > -200 and (i < 0 or nodes(lang, st)[i][0] != "p"):
                st["perfect"] += self.les.mistakes == 0
                st["combo"] = max(st["combo"], self.les.best)
            if i == st["prog"].get(lang, 0):
                st["prog"][lang] = i + 1
            t = date.today().toordinal()
            if st["last"] != t:
                st["streak"] = st["streak"] + 1 if t - st["last"] == 1 else 1
                st["last"] = t
            save(st)
        self.home.refresh()
        if -300 < self.cur[1] <= -200 or self.cur[1] <= -500:
            self.projs.refresh(self.cur[0])
            self.stack.setCurrentIndex(8)
        else:
            self.stack.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.installEventFilter(ClickFilter(app))
    w = Win()
    w.show()
    sys.exit(app.exec())
