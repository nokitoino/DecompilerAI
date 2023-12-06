# DecompilerAI
Converting Assembly back to C code using Transformers.

The main goal of this project is to test different pretrained transformers like the Hugging Face T5 to predict the high-level C/C++ code from raw disassembly.
In order to do this, we first need to scrape a lot of training data. The main idea is to train the Transformer function-wise. We compile our C Code to a binary executable, and diassemble it retrieving the assembly instructions for each function. The model should learn the seq-to-seq translation from Assembly instructions to C/C++ functions.

At the end, by using different methods, we try to retrieve the entire source code, i.e. functions, global variables, used headers from the standard library, comments, pre-processors and structs/classes.
The goal is to retrieve the high-level C/C++ Code that is compileable and functional equivalent with the original binary file.

## Table of Contents
- [Current Stage of Development](#current-stage-of-development)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [Future Plans](#future-plans)
- [Acknowledgments](#acknowledgments)
- [License](#license)
## Current Stage of Development
So far we only work with Linux ELF files and focus on the GCC compiler. We propose an initial model that uses the T5-base model (T5AssemblyC.ipynb), an initial Github Scraper to scrape simple compileable C Code (Scraper.py), an initial training pair generator (CodeToTrain.py), which already involves several homogenization steps for the assembly and C code, as well as a Full-Source-Retrieval script (FSC.py), which takes as input an ELF binary file, and outputs the prediction of the high-level-C Code for the entire binary file. The main branch will focus on a simple workflow to give you an idea of the Transformer capabilities. We will soon give you a replicateable workflow with explanation in [Usage](#usage).

Things we want to improve from now on:
- The Scraper should not be restricted to simple compileable source files. We should also collect larger programs that consists of multiple source and header files (using standard library, even some external libraries pcap, glib, ...) as training data. (Scraper.py)
- The CodeToTrain.py has very straightforward homogenization techniques, which drops valueable informations like the sizes of offsets in the Assembly. This will impact the performance of the Transformer. In the future we will over engineer the homogenization.
- The CodeToTrain.py should be able to involve the .rodata section of an ELF file in the training data generation, with the goal to retrieve global variables/strings/structs ... (CodeToTrain.py)
- The model should be able to work with larger Tokens (T5-Base was tested with moderate results on small functions, LongT5 might be a better alternative) (T5AssemblyC.ipynb)
- The FSC does not care about consistency of variable names/function names (FSC.py)
- The FSC does not involve a proper method to retrieve headers. One can generate a mapping from symbols to libraries. keywords: "nm, readelf, library" (FSC.py)
Furthermore, our idea is to execute the training over object files rather binary files. This experimental idea is subject to our new branch ObjectDecompiler.
We opened a new branch to work on these problems: [v2](https://github.com/nokitoino/DecompilerAI/tree/ObjectDecompiler).

## Installation

Instructions for how to install your project or any dependencies it may have. Incoming...

## Usage

We are currently setting up the main branch, so you can replicate the workflow of scraping, training, and inference. We will also explain the usage very soon.

## Contributing

If you want to contribute to this project, please follow these guidelines. Incoming...

## Future Plans
For simplicity, our first plan is to work on Linux ELF files compiled trough C code and be very restricted to one compiler (gcc). Later one might dare to work with C++. Our goal is also to switch to Windows PE files and use Microsoft DUMPBIN as an alternative to objdump and try different compilers.

## Acknowledgments

We express our sincere gratitude to Prof. Dr. Artur Andrzejak for motivating to this project and giving suggestions.

We would also like to express our sincere gratitude to [bwunicluster 2.0](https://www.scc.kit.edu/dienste/bwUniCluster_2.0.php) for their current invaluable assistance and support during the development of this project. Without their expertise and contributions, we couldn't have trained and tested our models on a large scale. We are truly thankful for their help.

Further Acknoledgments incoming...

## License

This project is licensed under the [GNU General Public License (GPL) version 3](LICENSE.md) - see the [LICENSE.md](LICENSE.md) file for details.
