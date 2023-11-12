# RevEngAI
Converting Assembly back to C Code using Transformers.

The main goal of this project is to test different pretrained transformers like the Hugging Face T5 to predict the high-level C/C++ code from raw disassembly.
In order to do this, we first need to scrape a lot of training data. The main idea is to train the Transformer function-wise. We compile our C Code to a binary executable, and diassemble it retrieving the assembly instructions. The model should learn the seq-to-seq translation from Assembly to C/C++.

By using different methods, we try to retrieve the entire source code, like global variables, used headers, comments, pre-processors, whereby some of these could again make use of further models. We need to make sure the entire source code should have the same context. If one function makes use of a global variable, then adjust the variable names accordingly, since the model retrieves the functions implementation independent from the rest of the binary.

