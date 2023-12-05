# DecompilerAI - ObjectDecompiler Branch
The main goal of this project is to test different pretrained transformers like the Hugging Face T5 to predict the high-level C/C++ code from raw disassembly. In order to do this, we first need to scrape a lot of training data. The main idea is to train the Transformer function-wise. We compile our C Code to a binary executable, and diassemble it retrieving the assembly instructions for each function. The model should learn the seq-to-seq translation from Assembly instructions to C/C++ functions.

In this branch we continue to work with ELF files, gcc and objdump. (Eventually, one might use more advanced disassemblers like radare2)
In this branch we will focus on the implementations for the data collection (Scraper.py), data pre-processing (CodeToTrain.py), the training model (T5AssemblyC.ipynb), as well as the Full-Source-Code retrieval (FSC.py), while considering following extensions/modifications with respect to our initial commit (main branch):
- Unlike the main branch, which collects and trains over simple compileable C files, we want to work with larger programs that consists of multiple source and header files. (Scraper.py, CodeToTrain.py)
- Unlike the main branch, we want to train over the object files rather than the final compiled binary file.
  The reason is: The disassembly dump of the binary file is equivalent with the dump of all the object files with the exception of the linker solving memory addresses.
  We do not require all source files to be compileable (due to missing libraries or errors) and can collect much more training data that would otherwise be ignored.
  But we have to be consistent when doing the inference. We have to "reduce" the disassembly of an already linked binary file to an object file, undo what the linker did and homogenize it.

  Our training pairs will be: (homogenize(Disassembler(Assembler(Compiler(Preprocessor(C Code)))))), homogenize(C Code)) // no linking
  The inference will be: model(Homogenize(Unlink(Disassembler(Binary File))))
  Be aware that assembly and disassembly are functional equivalent. The Assembler just loses information of comments, labels, pseudo-commands (for the Assembler) in the process. (Scraper.py, CodeToTrain.py)
- The Scraper should not only find simple compileable source files, but also programs that consists of multiple source and header files.
  The goal is to recursively include the missing headers of a source file and compile it to an object file, and forward this to our CodeToTrain.py as training example together with the source code. (Scraper.py)
- The CodeToTrain.py should be over engineered. We need to make use of the .rodata section in our training for global variables like strings, structs, ect., which was primarily ignored in the training. Despite this, we had impressive results on small functions. Small functions "could be restored" with the exception of the model guessing what the strings could be that have been used. We didn't even remove them from the C Code in the training process. (CodeToTrain.py)
- The model should use LongT5 for training, since other models are heavily restricted with the Token size (T5AssemblyC.ipynb)
- The FSC should find neccessary standard libraries, and use consistent names for functions. One could ignore the process to retrieve global variables. The functions that make use of it, will just directly work with the values rather than labels of global varaibles. That's how Assembly works anyways, one always makes reference to the exact memory address of the value when dealing with them. We hope to fix this problem by asking the model for prediction on a homogenized disassembly and relevant .rodata memory table snippet (FSC.py)

## Acknowledgments

Please check the main branch.

## License

This project is licensed under the [GNU General Public License (GPL) version 3](LICENSE.md) - see the [LICENSE.md](LICENSE.md) file for details.
