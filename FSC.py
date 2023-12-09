"""
This script tries to recover the source code of an ELF file that was compiled with debug information.
For experimental reasons we commented the retrieval of global variables, so we can execute this script on binaries with no debug information.

HOW TO USE:
python3 FSC.py elf_file

Output: source.c, which contains the predicted C Code for our small simple program.

This script is just a quick experimental demonstration of our model that was trained on about 10k simple compileable C files.
The model has a size of 851 MB and is publicly available at https://huggingface.co/nokitoino/gccDecompilerExperimental/tree/main.
The model was trained on the BwUniCluster 2.0 on one Nvidia Tesla V100 for about 2-3 hours using T5-Base.
In the future we will publish detailed train/val loss graphs.

The model is quite useless in its current state.
Do not execute this script on property that does not belong to you.
We always respect the intellectual property of others.


There is alot of improvements to be done here.

Developed by Akin Yilmaz.
"""
import argparse
import subprocess
import re

#We need to load the model to ask predictions.
from transformers import T5Tokenizer, T5ForConditionalGeneration, AdamW
import torch

parser = argparse.ArgumentParser("FSC")
parser.add_argument("file", help="ELF file of which we recover the full source code")
args = parser.parse_args()

symbol_header_mapping = {
    "#include <stdio.h>": [
        "printf@@GLIBC_2.2.5",
        "fprintf@@GLIBC_2.2.5",
        "sprintf@@GLIBC_2.2.5",
        "snprintf@@GLIBC_2.2.5",
        "fopen@@GLIBC_2.2.5",
        "fclose@@GLIBC_2.2.5",
        "fgets@@GLIBC_2.2.5",
        "fputs@@GLIBC_2.2.5",
        "fread@@GLIBC_2.2.5",
        "fwrite@@GLIBC_2.2.5",
    ],
    "#include <stdlib.h>": [
        "malloc@@GLIBC_2.2.5",
        "free@@GLIBC_2.2.5",
        "calloc@@GLIBC_2.2.5",
        "realloc@@GLIBC_2.2.5",
        "atoi@@GLIBC_2.2.5",
        "atof@@GLIBC_2.2.5",
        "rand@@GLIBC_2.2.5",
        "srand@@GLIBC_2.2.5",
        "abs@@GLIBC_2.2.5",
        "labs@@GLIBC_2.2.5",
    ],
    "#include <string.h>": [
        "strcpy@@GLIBC_2.2.5",
        "strncpy@@GLIBC_2.2.5",
        "strlen@@GLIBC_2.2.5",
        "strcmp@@GLIBC_2.2.5",
        "strcat@@GLIBC_2.2.5",
        "strncat@@GLIBC_2.2.5",
        "strstr@@GLIBC_2.2.5",
        "strtok@@GLIBC_2.2.5",
        "strpbrk@@GLIBC_2.2.5",
        "strrchr@@GLIBC_2.2.5",
    ],
    "#include <math.h>": [
        "sin@@GLIBC_2.2.5",
        "cos@@GLIBC_2.2.5",
        "tan@@GLIBC_2.2.5",
        "sqrt@@GLIBC_2.2.5",
        "pow@@GLIBC_2.2.5",
        "log@@GLIBC_2.2.5",
        "exp@@GLIBC_2.2.5",
        "log10@@GLIBC_2.2.5",
        "ceil@@GLIBC_2.2.5",
        "floor@@GLIBC_2.2.5",
    ],
    "#include <unistd.h>": [
        "write@@GLIBC_2.2.5",
        "read@@GLIBC_2.2.5",
        "close@@GLIBC_2.2.5",
        "fork@@GLIBC_2.2.5",
        "pipe@@GLIBC_2.2.5",
        "dup@@GLIBC_2.2.5",
        "getpid@@GLIBC_2.2.5",
        "sleep@@GLIBC_2.2.5",
        "usleep@@GLIBC_2.2.5",
    ],
    "#include <pthread.h>": [
        "pthread_create@@GLIBC_2.2.5",
        "pthread_join@@GLIBC_2.2.5",
        "pthread_mutex_lock@@GLIBC_2.2.5",
        "pthread_mutex_unlock@@GLIBC_2.2.5",
        "pthread_cond_wait@@GLIBC_2.2.5",
        "pthread_cond_signal@@GLIBC_2.2.5",
        "pthread_rwlock_init@@GLIBC_2.2.5",
        "pthread_rwlock_destroy@@GLIBC_2.2.5",
        "pthread_rwlock_rdlock@@GLIBC_2.2.5",
        "pthread_rwlock_wrlock@@GLIBC_2.2.5",
    ],
    "#include <netinet/in.h>": [
        "socket@@GLIBC_2.2.5",
        "bind@@GLIBC_2.2.5",
        "listen@@GLIBC_2.2.5",
        "accept@@GLIBC_2.2.5",
        "inet_addr@@GLIBC_2.2.5",
        "htons@@GLIBC_2.2.5",
        "htonl@@GLIBC_2.2.5",
        "ntohs@@GLIBC_2.2.5",
        "ntohl@@GLIBC_2.2.5",
    ],
    "#include <sys/types.h>": [
        "open@@GLIBC_2.2.5",
        "close@@GLIBC_2.2.5",
        "read@@GLIBC_2.2.5",
        "write@@GLIBC_2.2.5",
        "lseek@@GLIBC_2.2.5",
        "stat@@GLIBC_2.2.5",
        "fstat@@GLIBC_2.2.5",
        "unlink@@GLIBC_2.2.5",
        "rename@@GLIBC_2.2.5",
    ],
    "#include <time.h>": [
        "clock@@GLIBC_2.2.5",
        "time@@GLIBC_2.2.5",
        "ctime@@GLIBC_2.2.5",
        "difftime@@GLIBC_2.2.5",
        "strftime@@GLIBC_2.2.5",
        "localtime@@GLIBC_2.2.5",
        "mktime@@GLIBC_2.2.5",
        "gmtime@@GLIBC_2.2.5",
        "asctime@@GLIBC_2.2.5",
    ],
    "#include <fcntl.h>": [
        "open@@GLIBC_2.2.5",
        "close@@GLIBC_2.2.5",
        "read@@GLIBC_2.2.5",
        "write@@GLIBC_2.2.5",
        "fcntl@@GLIBC_2.2.5",
        "ioctl@@GLIBC_2.2.5",
        "pipe2@@GLIBC_2.2.5",
        "dup2@@GLIBC_2.2.5",
        "select@@GLIBC_2.2.5",
    ],
    # Add more headers and symbols as needed...
}


def getObjectdump(file):
    objdump_command = f"objdump -d -M intel {file}"
    return subprocess.getoutput(objdump_command)
def getHeaders(file):
    # We make use of the following fact:
    # The underscore prefix is reserved for variables used by the compiler and standard library
    output = [] #will contain all includes that were used in the source file
    readelf_command = f"readelf -s {file}|grep 'FUNC    GLOBAL DEFAULT  UND'"
    readelflines = subprocess.getoutput(readelf_command)
    arr = readelflines.split("\n")
    headers_symbol = []
    for line in arr:
        if "@" in line and "]@GLIBC" not in line and "(" not in line:
            line = line.split()[-1]
            if not line[0] == "_":
                headers_symbol.append(line)
    for header_symbol in headers_symbol:
        for header_dict, symbols in symbol_header_mapping.items():
            for symbol in symbols:
                if header_symbol in symbol:
                    output.append(header_dict)
                    break
        else:
            ...
            #print(f"The symbol '{header_symbol}' was not found in the dictionary.")
    return set(output) #converts to set to remove duplicates
def getGlobalVariableTypes(variables):
    # Define the commands to run
    commands = [
        "break main",
        "run"
    ]
    for variable in variables:
        commands.append(f"ptype {variable}")
    commands.append("quit")

    # Create a subprocess to run GDB
    proc = subprocess.Popen(
        ["gdb", "./program"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True  # Use text mode for input/output
    )

    # Loop through the commands and send them to GDB
    for cmd in commands:
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    # Read the output of the last command
    output = []
    for line in proc.stdout:
        if "type =" in line:
            output.append(line.split("= ")[1].rsplit("\n", 1)[0])

    # Close the subprocess
    proc.stdin.close()
    proc.stdout.close()
    proc.stderr.close()
    proc.wait()
    return output
def getGlobalVariablesValues(variables):
    # Define the commands to run
    commands = [
        "break main",
        "run"
    ]
    for variable in variables:
        commands.append(f"print {variable}")
    commands.append("quit")

    # Create a subprocess to run GDB
    proc = subprocess.Popen(
        ["gdb", "./program"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True  # Use text mode for input/output
    )

    # Loop through the commands and send them to GDB
    for cmd in commands:
        proc.stdin.write(cmd+"\n")
        proc.stdin.flush()

    # Read the output of the last command
    output = []
    for line in proc.stdout:
        if "(gdb) $" in line:
            output.append(line.split("= ")[1].rsplit("\n",1)[0])

    # Close the subprocess
    proc.stdin.close()
    proc.stdout.close()
    proc.stderr.close()
    proc.wait()
    return output

def getGlobalVariables(file):
    # We make use of the following fact:
    # The underscore prefix is reserved for variables used by the compiler and standard library
    readelf_command = f"readelf -s {file}|grep 'OBJECT  GLOBAL'"
    variable_symbols = subprocess.getoutput(readelf_command)
    arr = variable_symbols.split("\n")
    variable_names = []
    for line in arr:
        if "@" not in line:
            line = line.split()[-1]
            if not line[0] == "_":
                variable_names.append(line)
    return variable_names

def getFunctionNames(file):  # A dirty way to only extract the functions we defined in our C Code
    # We make use of the following fact:
    # The underscore prefix is reserved for functions and types used by the compiler and standard library
    # We cannot use the @ symbol
    readelf_command = f"readelf -s {file}|grep 'FUNC    GLOBAL'"
    function_symbols = subprocess.getoutput(readelf_command)
    arr = function_symbols.split("\n")
    function_names = []
    for line in arr:
        if "@" not in line:
            line = line.split()[-1]
            if not line[0] == "_":
                function_names.append(line)
    return function_names

def extract_column(block):
  col0 = []
  col1 = []
  col2 = []
  for line in block.splitlines():
    row_split = line.split("\t")
    col0.append(row_split[0])
    col1.append(row_split[1])
    #In the third column we have to check for NOP, since there might be no Assembly instruction
    if len(row_split)==2:
      col2.append("")
    else:
      col2.append(row_split[2])
  return (col0,col1,col2)
def extract_block(text, pattern_string):
    start_index = text.find(pattern_string)
    if start_index == -1:
        return None  # Pattern not found in the text
    start_index = start_index + len(pattern_string) + 1
    end_index = text.find("\n\n", start_index)
    if end_index == -1:
        return None  # Newline character not found
    return text[start_index:end_index]

def homogenizeAssembly(col0,col1,col2,function_addresses,offset_set): #Input are the 3 blocks of objdump, each array element corresponds to one line of (adress, binary instructions, assembly instructions)
  """
  We replace every occurence of function addresses by labels, whereby we maintain the relative adress.
  function address 0x15 -> FUNC1
                   0x20 -> LVL1 (Level refers to the relative distance to the adress of the function)
                   ...

  """
  col0_filtered = [element.split(':')[0].split("    ")[1] for element in col0] #we get the addresses
  #print(col0_filtered)
  col2_replace_adr = []
  #Dieser Block könnte effizienter implementiert werden.
  for i in range(len(col2)):# i iterator für Zeile der Maschineninstructions
    col2replaced = col2[i].split("#")[0] #Zeile lesen (und Kommentare entfernen, d.h. ab # unrelevant für uns)
    #Replace OFFSETS in [] Brackets. Identical offsets get identical names.
    for l in range(len(offset_set)):
        pattern = r'(\[.*?)({})(.*?\])'.format(offset_set[l])
        replacement = r'\1({})\3'.format(l) #Here instead of OS replace identical Offsets by same name
        col2replaced = re.sub(pattern,replacement, col2replaced)
    #Replace any address by relative values. 0 for function address 1 for next machine instruction address
    for j in range(len(col0_filtered)): #gefilterte Addressen werden mit j-Index ersetzt: 1149 -> OFF0, 1150 -> OFF1 ... wenn der Block mit Addresse 1149 anfängt
        col2replaced = col2replaced.replace(col0_filtered[j], "OFS "+str(j))
    #Replace any function address by some number, the model should still distinguish call FUNC1 and call FUNC2 ...
    for k in range(len(function_addresses)):  # ersetze jedes Vorkommen von Funktionenadressen, das Model weiß nicht wie viele Funktionen es gibt.
        col2replaced = col2replaced.replace(function_addresses[k],"FUNC "+str(k))
    col2_replace_adr.append(re.sub(r"call\s+\w+\s+(.*)",r"call   \1",re.sub(r'<(.*?)\+0x[0-9a-fA-F]+(.*?)>', r'<\1\2>',col2replaced))) #entfernt die Offsets beim call <main+0x51>
  return col0,col1,col2_replace_adr
def getFunctionPatterns(objdump, function_names):
    lines = objdump.splitlines()
    patterns = []
    for line in lines:
        for function in function_names:
            if "<" + function + ">:" in line:
                patterns.append(line)
    return patterns

def predict(tokenizer, model, input_sequence):
    input_ids = tokenizer(input_sequence, return_tensors="pt").input_ids.to(device)
    outputs = model.generate(input_ids, max_length=300, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
if args.file:
    objdump = getObjectdump(args.file)
    function_names = getFunctionNames(args.file)
    patterns = getFunctionPatterns(objdump, function_names)
    assembly = [] #This will contain an array the homogenized assembly for each function and we will ask the model for prediciton
    function_addresses = [pattern.split(" ")[0].lstrip("0") for pattern in
                          patterns]  # stores the addresses the functions are stored at 1149 main function...

    #
    for pattern in patterns:
        col0, col1, col2 = extract_column(extract_block(objdump, pattern))  # extracts columns for one function
        # print(extract_block(output_str,pattern))
        # print("____________________________ UNHOMOGENIZED v")
        # for element in col2:
        #    print(element)
        col2_to_string = "\n".join(col2)
        pattern = r"\[(?:.*?)(0x[0-9a-fA-F]+)(?:.*?)\]"
        # pattern = r"0x[0-9a-fA-F]+"
        matches = re.findall(pattern, col2_to_string)
        word_set = list(
            set(matches))  # We use set to avoid duplicates, and convert to array to get it sorted -> same offsets get same name (which is the index)
        # On each extraction collect the offsets and put into a dictionary
        # print("____________________________ HOMOGENIZED v")
        col0, col1, col2 = homogenizeAssembly(col0, col1, col2, function_addresses, word_set)
        # for element in col2:
        #    print(element)
        assembly.append(";".join(col2))  # Delimiter for assembly array
    variables = getGlobalVariables(args.file)
    values = getGlobalVariablesValues(variables)
    types = getGlobalVariableTypes(variables)
    includes = getHeaders(args.file)

    #Build the source file
    C_Code_includes = ""
    C_Code_globalVariables = ""
    C_Code_functions = ""

    C_Code_includes = "\n".join(includes)+"\n"
    #for i in range(len(variables)):
    #    C_Code_globalVariables+=f"\n{types[i]} {variables[i]}  = {values[i]}"

    #Prepare the model to execute locally
    seed = 42
    torch.manual_seed(seed) #For deterministic outputs, can be commented out.
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = T5Tokenizer.from_pretrained("nokitoino/gccDecompilerExperimental")
    model = T5ForConditionalGeneration.from_pretrained("nokitoino/gccDecompilerExperimental").to(device)

    predictions = []
    for function_assembly in assembly:
        predictions.append(predict(tokenizer, model,function_assembly))  #ASK THE MODEL FOR PREDICTION HERE
    C_Code_functions = "\n".join(predictions)

    C_Code = C_Code_includes+C_Code_globalVariables+C_Code_functions

    print(C_Code_includes)
    # Save the predictions to a temporary file
    temp_file_path = "source.c"
    with open(temp_file_path, "w") as temp_file:
        temp_file.write(C_Code)

    # Use clang-format to beautify the C code
    clang_format_command = f"clang-format -i {temp_file_path}"
    subprocess.run(clang_format_command, shell=True)

    # Read the beautified code back
    with open(temp_file_path, "r") as temp_file:
        beautified_code = temp_file.read()
    print(beautified_code)