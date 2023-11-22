# RevEngAI
Converting Assembly back to C code using Transformers.

The main goal of this project is to test different pretrained transformers like the Hugging Face T5 to predict the high-level C/C++ code from raw disassembly.
In order to do this, we first need to scrape a lot of training data. The main idea is to train the Transformer function-wise. We compile our C Code to a binary executable, and diassemble it retrieving the assembly instructions for each function. The model should learn the seq-to-seq translation from Assembly instructions to C/C++ functions.

At the end, by using different methods, we try to retrieve the entire source code, i.e. additionally global variables, used headers, comments, pre-processors, typedef whereby some of these could again make use of further models. We need to make sure the entire source code should have the same context. If one function makes use of a global variable, then adjust the variable names accordingly, since the model retrieves the functions implementation independent from the rest of the binary.

## Table of Contents
- [Current Stage of Development](#current-stage-of-development)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Current Stage of Development
So far we only work with Linux ELF files. We propose an initial model that uses the T5-small model. An initial Github Scraper (we will later convert to using the Hugging Face Github Dataset), an initial training pair generator CodeToTrain.py, which already involves several homogenization steps for the assembly and C code, as well as an FSC.py (Full-Source-Retrieval) script, which takes as input an ELF binary file, and outputs the prediction for the high-level-C Code for the entire binary.

Things we want to improve from now on:
- The Scraper should be able to compile multi-source-code files (that use standard library, even some external libraries pcap, glib, ...)
- The homogenization does not care about strings and global variables yet. (CodeToTrain.py)
- The FSC does not care about consistency of variable names (FSC.py)
- The FSC does not involve a proper method to retrieve headers (FSC.py)
- The model should be tested with different parameters
- The T5-large should be tested, as it contains more Tokens

## Installation

Instructions for how to install your project or any dependencies it may have. Incoming...

## Usage

How to use your project, including examples and code snippets. Incoming...

## Contributing

If you want to contribute to this project, please follow these guidelines. Incoming...

## Acknowledgments

We express our sincere gratitude to Prof. Dr. Artur Andrzejak for motivating to this project and giving suggestions.

We would also like to express our sincere gratitude to [bwunicluster 2.0](https://www.scc.kit.edu/dienste/bwUniCluster_2.0.php) for their current invaluable assistance and support during the development of this project. Without their expertise and contributions, we couldn't have trained and tested our models on a large scale. We are truly thankful for their help.

Further Acknoledgments incoming...

## License

This project is licensed under the [GNU General Public License (GPL) version 3](LICENSE.md) - see the [LICENSE.md](LICENSE.md) file for details.
