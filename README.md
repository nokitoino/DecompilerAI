# DecompilerAI
Converting Assembly back to C code using Transformers.

The main goal of this project is to use transformers like the Hugging Face T5 to predict the high-level C/C++ code from raw disassembly.
In order to do this, we first need to scrape a lot of training data. The main idea is to train the Transformer function-wise. We compile our C Code to a binary executable, and disassemble it retrieving the assembly instructions for each function. The model should learn the seq-to-seq translation from Assembly instructions to C/C++ functions.

At the end, by using different methods, we try to retrieve the entire source code, i.e. functions, global variables, used headers from the standard library, comments, pre-processors and structs/classes.
The goal is to retrieve the high-level C/C++ Code that is compileable and functional equivalent with the original binary file.

## Table of Contents
- [Current Stage of Development](#current-stage-of-development)
- [Installation](#installation)
- [Usage](#usage)
- [Hardware Requirements](#hardware-requirements)
- [Contributing](#contributing)
- [Future Plans](#future-plans)
- [Acknowledgments](#acknowledgments)
- [License](#license)
## Current Stage of Development
So far we only work with Linux ELF files and focus on the GCC compiler. We propose an initial model that uses the T5-base model (T5AssemblyC.ipynb), an initial Github Scraper to scrape simple compileable C Code (Scraper.py), an initial training pair generator (CodeToTrain.py), which already involves several homogenization steps for the assembly and C code, as well as a Full-Source-Retrieval script (FSC.py), which takes as input an ELF binary file, and outputs the prediction for the high-level C Code. The main branch will focus on a simple workflow to give you an idea of the Transformer capabilities. We give you a replicateable workflow with explanation in [Usage](#usage).

Things we want to improve from now on:
- The Scraper should not be restricted to simple compileable source files. We should also collect larger programs that consists of multiple source and header files (using standard library, even some external libraries pcap, glib, ...) as training data (Scraper.py).
- The CodeToTrain.py has very straightforward homogenization techniques:
  - which drops valueable informations like the sizes of offsets in the Assembly.
  - which does not keep literals between the Assembly and C Code consistent (Transformers can't calculate, i.e. can't translate large numbers to their respective HEX representation).
  - which replaces absolute addresses by relative offsets (Again, Transformers can't calculate, this negatively impacts control flow, use labels instead).
  - which cannot deal with pointers/absolute addresses into other memory sections (How do we know how many bytes are needed from other memory sections? How do we deal with pointer arithmetics?).
  - which ignores information about other functions that are called within the to reverse engineered function (return type, parameter type).
  - which ignores information about other functions that make use of the to reverse engineered function.
  - which doesn't care about constant folding happening in the C code compilation i.e. the Assembly will contain optimized expressions.
  - ... (and the list goes on)
    
  Among other aspects these will negatively impact the performance of the Transformer when not solved.
  Initial model predicts an unseen C-SMITH generated function (trained on 10k C files):

  Original:
  ```c
  int main (int argc, char* argv[])
  {
      int print_hash_value = 0;
      if (argc == 2 && strcmp(argv[1], "1") == 0)
          print_hash_value = 1;
      
      platform_main_begin();
      func_1();
      platform_main_end(0,0);
      
      return 0;
  }
  ```
  Prediction:
  ```c
  int main(int argc, char *argv[]) {
    int i = 0;
    if (argc == 2) {
      if (strcmp(argv[1], "0") == 0) {
        i = 1;
      }
      platform_main_begin();
      func_1();
      platform_main_end();
    }
    return 0;
  }
  ```
  You can clearly see many aspects the prediction fail with. It can't deal with strings, since we do not give this information. It doesn't know where the conditional branch ends, and it omits the argument values for the last function call.
  In the future we will over engineer the homogenization (CodeToTrain.py).
- The model should be able to work with larger Tokens (T5-Base was tested with moderate results on small functions, LongT5 might be a better alternative) (T5AssemblyC.ipynb).
- The FSC does not care about consistency of variable names/function names (FSC.py).
- The FSC does not involve a proper method to retrieve headers. One can generate a mapping from symbols to libraries. keywords: "nm, readelf, library" (FSC.py).
Furthermore, our idea is to execute the training over object files rather binary files. This experimental idea is subject to our new branch ObjectDecompiler (Scraper.py, CodeToTrain.py, FSC.py).
We opened a new branch to work on these problems: [ObjectDecompiler](https://github.com/nokitoino/DecompilerAI/tree/ObjectDecompiler).

## Installation
Make sure you use Linux, or a Windows-Subsystem for Linux. Soon we will test the scripts to run on Windows. To train the model effectively please check [Hardware Requirements](#hardware-requirements).
### Clone the branch
```
git clone -b main https://github.com/nokitoino/DecompilerAI.git
```
### Install Python modules
Make sure you have installed python3 by  `python3 --version` and Jupyter Notebook.
First, install the required python modules.
#### Install python modules automatically
```
pip install -r requirements.txt
```
#### Alternative: Install python modules manually
```
pip install torch
pip install transformers
pip install sentencepiece
pip install matplotlib
pip install scikit-learn
pip install tree_sitter
pip install tqdm

```

### Install additional libraries
```
sudo apt install clang-format
sudo apt-get install build-essential
git clone https://github.com/tree-sitter/tree-sitter-c
```
Why the libraries? The build-essential installs the GCC compiler. In the FSC.py and CodeToTrain.py we use tree-sitter, which is a Parser that must be installed, along with the C-grammar that has to be cloned.
In the FSC.py we use clang-format to format our final retrieved source code.

## Usage
Your directory should now consist: tree-sitter-c/, CodeToTrain.py, Scraper.py, FSC.py, T5AssemblyC.ipynb
We now describe the entire workflow.
### 1. Collect training data
Open the Scraper.py and set `GITHUB_TOKEN` to your Personal Github Token.
```
python3 Scraper.py
```
This will create a directory with C files.
### 2. Create training pairs
Now we would like to create homogenized training pairs of the form `(C Code, Disassembly)`.
```
python3 CodeToTrain.py
```
### 3. Train the model
Now you can open the Jupyter Notebook and execute the training. Make sure you have enough training data and the right hardware to start the training.
```
jupyter-notebook T5AssemblyC.ipynb
```
### 4. Inference
The last step is to connect the FSC.py script with your model. Just substitute our model with your model by giving the local path to the model and tokenizer directory.
You can also manually do an inference by using the code provided in the Jupyter Notebook.
### One-Click-Demo
We have uploaded a trained model to Hugging Face and connected it with the FSC. Just execute:
```
python3 FSC.py file
```
Substitute `file` with the path to the ELF file.
## Hardware Requirements
The model was trained on one GPU of NVIDIA V100 TESLA 32GB.
The other scripts were run on Intel Core i7-9570H CPU, NVIDIA GTX 1660 TI 6GB, 16 GB RAM. You should be able to run them on lower specs.

## Contributing
If you want to contribute to this project, please follow these guidelines. Incoming...

## Future Plans
For simplicity, our first plan is to work on Linux ELF files compiled trough C code and be very restricted to one compiler (gcc). We might soon try to conduct different experiments, like trying to finetune a pretrained model (on a large corpus doing Masked Label Prediction, to understand the semantics/context of code) to increase the accuracy.
Other things that can be done is hyper-parameter search, training on optimized/unoptimized code by different compilers, ...
Later one might dare to work with C++. Our goal is also to switch to Windows PE files and use Microsoft DUMPBIN as an alternative to objdump and try different compilers.

## Acknowledgments
We express our sincere gratitude to Prof. Dr. Artur Andrzejak for motivating to this project and giving suggestions.

We would also like to express our sincere gratitude to [bwunicluster 2.0](https://www.scc.kit.edu/dienste/bwUniCluster_2.0.php) for their current invaluable assistance and support during the development of this project. Without their expertise and contributions, we couldn't have trained and tested our models on a large scale. We are truly thankful for their help.

The initial approach was a collaborative project by students Akin and Philip.
Akin worked on the pre-processing part, and Philip on the model.
Both were steadily in close exchange to get the workflow running in order to train a decompiler using the T5-small.
We would like to continue with this project by experimenting with new techniques and work with larger models like the LongT5, which can process input lengths up to 16000 Tokens.

Further Acknowledgments incoming...

## License

This project is licensed under the [GNU General Public License (GPL) version 3](LICENSE.md) - see the [LICENSE.md](LICENSE.md) file for details.
