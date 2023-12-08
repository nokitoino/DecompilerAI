'''
This script creates from a directory of C files training pairs of the form (C Code, Disassembly).

HOW TO USE:
1. Move all the C files into a local directory called C_COMPILE. Note: The Scraper does this automatically.
2. python3 CodeToTrain.py
You fill find two text files in your local directory: function.txt and assembly.txt that contain the training data, which is ready to be used by the model.

This script was developed by Akin Yilmaz, in close exchange with the initial model developer Philip S.
'''
from tree_sitter import Language, Parser
import os,re
import numpy as np
import subprocess
import time


# Build the language lib
Language.build_library(
    'build/my-languages.so',
    [
        'tree-sitter-c'
    ]
)

# Load C language
C_LANGUAGE = Language('build/my-languages.so', 'c')

# Create the parser for C
parser = Parser()
parser.set_language(C_LANGUAGE)


#Extract the function names from C Code using Tree-Spitter


def getCodeTree(code):
    return parser.parse(bytes(code, "utf8"))
def extract_function_names(code,tree):
    # Get the root node of the syntax tree
    root_node = tree.root_node
    function_names = []
    for node in root_node.children:
        if node.type == "function_definition":
            # Extract the function name
            function_name_node = node.children[1] #children[0] int children[1] function1 children[2] {body}
            function_name = code[function_name_node.start_byte : function_name_node.end_byte] 
            function_names.append(function_name.split("(")[0].replace("*","").rstrip()) #Filters the name only, and remove pointer * stars
    return function_names
escapes = '\b\n\r\t\\'
def filter_escape(string):
    for c in escapes:
        string = string.replace(c, '')
    return string.replace('   ',' ')

def extract_function(code,tree): # working on this now
    # Get the root node of the syntax tree
    root_node = tree.root_node
    function = []
    for node in root_node.children:
        if node.type == "function_definition":
            # Extract the entire function
            function_node_type = node.children[0]
            function_node_dec = node.children[1] #children[0] int children[1] function1 children[2] {body}
            function_node_body = node.children[2]
            function_type = code[function_node_type.start_byte : function_node_type.end_byte]
            function_dec = code[function_node_dec.start_byte : function_node_dec.end_byte]
            function_body = code[function_node_body.start_byte : function_node_body.end_byte]
            function.append(filter_escape(function_type+" "+function_dec+function_body)) #Returns the entire function and removes escapes
    return function


def extract_variable_names(code):
  variable_names = []
  def traverse(node):
      if node.type=="declaration":
        if c_code[node.start_byte : node.end_byte] != "compound statement": #This string also counts as "declaration"
          variable_names.append(c_code[node.start_byte : node.end_byte].split(";")[0].split("=")[0].split(" ")[1])
      for child in node.children: #If no children it terminates
          traverse(child)

  traverse(parser.parse(bytes(code, "utf8")).root_node)
  return variable_names
def objdump_to_string(file_path):
    output_str = ""
    disassemble_str = ""
    objdump_command = f"objdump -d -M intel {file_path}"
    output_str = subprocess.getoutput(objdump_command)
    return output_str

def objdump_rodata_to_string(file_path): #extracts the rodata with readelf
    output_bytes = subprocess.check_output(["readelf", "-p", ".rodata", file_path])
    return output_bytes.decode("utf-8", errors="ignore")

"""def homogenizeC(code): #In case the accurary goes up using this method, we can try following:
  #Every function that is almost identical, we leave out one.
  #Relabel variables and functions
  variable_names = extract_variable_names(code)
  function_names = extract_function_names(code)
  hom_var_name = "var"
  counter = 0
  for variable in variable_names:
    code = re.sub(r'\b'+re.escape(variable)+r'\b', hom_var_name+str(counter), code)
    counter = counter + 1
  hom_func_name = "func"
  counter2 = 0
  for function in function_names:
    code = re.sub(r'\b'+re.escape(function)+r'\b', hom_func_name+str(counter2), code)
    counter2 = counter2 + 1
  #Removes unnecessary white spaces
  code = re.sub(r'\s*([^\w\s])\s*', r'\1',code)
  #Remove comments
  return filter_escape(code)"""
def homogenizeC(code):
  # Remove single-line comments //
  code = re.sub(r'//.*', '', code)
  # Remove multi-line comments /**/
  code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
  #Removes unnecessary white spaces
  code = re.sub(r'\s*([^\w\s])\s*', r'\1',code)
  return filter_escape(code)

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
    #for k in range(len(function_addresses)):  # ersetze jedes Vorkommen von Funktionenadressen, das Model weiß nicht wie viele Funktionen es gibt.
    #    col2replaced = col2replaced.replace(function_addresses[k],"FUNC "+str(k))
    col2_replace_adr.append(re.sub(r"call\s+\w+\s+(.*)",r"call   \1",re.sub(r'<(.*?)\+0x[0-9a-fA-F]+(.*?)>', r'<\1\2>',col2replaced))) #entfernt die Offsets beim call <main+0x51>
  return col0,col1,col2_replace_adr

def get_file_list(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(file_path)
    return file_list

#Extracts the instructions of a function. The pattern is the first line of the function in Assembly
#Example "0000000000001149 <function1>:"
def extract_block(text, pattern_string):
    start_index = text.find(pattern_string)
    if start_index == -1:
        return None  # Pattern not found in the text
    start_index = start_index + len(pattern_string)+1
    end_index = text.find("\n\n", start_index)
    if end_index == -1:
        return None  # Newline character not found
    return text[start_index:end_index]
#Splits the assembly objdump into row-adressable columns for a given function-block
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
def extract_rodata(rodata):
    rodata = rodata.split("\n")
    strings = []
    for line in rodata[2:-1]: #Ignore first line "String dump of section '.rodata':" and last empty line "   "
        line = line.split("]  ")[1]
        strings.append(line)
    return strings
function_txt_path="function.txt"
assembly_txt_path="assembly.txt"
if os.path.exists(function_txt_path):
  os.unlink(function_txt_path)
if os.path.exists(assembly_txt_path):
  os.unlink(assembly_txt_path)
counter =  0
max_file_number = 30000#amount of files to be read
st = time.time()
with open(function_txt_path, "a") as function_file:
    with open(assembly_txt_path, "a") as assembly_file:
        blockLineCount = 0
        functionBlock = ""
        assemblyBlock = ""

        for cfile in get_file_list("C_COMPILE"):
          try:
              counter = counter + 1
              if counter % 100  == 0:
                  print(counter)
              if counter >= max_file_number:
                  break
              gcc_command = f"gcc -o program {cfile}"
              gcc_process = subprocess.run(gcc_command, shell=True, capture_output=True)
              if gcc_process.returncode == 0:
                  # Read code from the file
                  with open(cfile, "r", encoding="utf-8", errors="ignore") as file:
                      c_code = file.read()#homogenization might disturb the function finding in objdump

                  #clang -o quelle.exe Quelle.c Clang alternative
                  tree = getCodeTree(c_code)
                  function_names = extract_function_names(c_code,tree)

                  functions = extract_function(c_code,tree) # Homogenize before writing to functions.txt

                  for i in range(len(functions)):
                      functions[i] = homogenizeC(functions[i])
                  file_path = 'program'
                  output_str = objdump_to_string(file_path)
                  output_rodata_str = objdump_rodata_to_string(file_path)
                  #print(extract_rodata(output_rodata_str))
                  lines = output_str.splitlines()
                  patterns=[]
                  for line in lines:
                      for function in function_names:
                          if  "<"+function+">:" in line:
                              patterns.append(line)
                  assembly = []
                  function_addresses = [pattern.split(" ")[0].lstrip("0") for pattern in patterns] # stores the addresses the functions are stored at 1149 main function...

                  for pattern in patterns:
                    col0,col1,col2 = extract_column(extract_block(output_str,pattern)) #extracts columns for one function
                    #print(extract_block(output_str,pattern))
                    #print("____________________________ UNHOMOGENIZED v")
                    #for element in col2:
                    #    print(element)
                    col2_to_string="\n".join(col2)
                    pattern = r"\[(?:.*?)(0x[0-9a-fA-F]+)(?:.*?)\]"
                    #pattern = r"0x[0-9a-fA-F]+"
                    matches = re.findall(pattern, col2_to_string)
                    word_set = list(set(matches)) # We use set to avoid duplicates, and convert to array to get it sorted -> same offsets get same name (which is the index)
                    #On each extraction collect the offsets and put into a dictionary
                    #print("____________________________ HOMOGENIZED v")
                    col0,col1,col2 = homogenizeAssembly(col0,col1,col2,function_addresses,word_set)
                    #for element in col2:
                    #    print(element)
                    assembly.append(";".join(col2)) #Delimiter for assembly array

                  if len(function_names) != len(assembly) or len(functions)!=len(assembly):
                      continue
                  for function in functions:
                      function_file.write(function + "\n")
                  for function_assembly in assembly:
                      assembly_file.write(function_assembly + "\n")
              else:
                ...
          except Exception as e:
            print(f"An unexpected error occurred: {e}")
et = time.time()
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')