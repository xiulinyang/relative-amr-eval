# relative-amr-eval
This repository contains the code and dataset for the paper *The Relative Clauses AMR Parsers Hate Most* by Xiulin Yang and Nathan Schneider.

# To replicate the experiments
First, you need to create a virtual environment with python==3.8 and install all the dependencies.

```
conda create -n venv python==3.8
pip install -r requirements.txt
```

## dataset
The parsed results for ewt can be found in the ```parse_results```folder.
## classification code
- ```rc-types.py```: the code to classify the relative clauses without distinguishing types of reduced relative clauses.
- ```rrc-types.py```: the code to classify reduced relative clauses and add EUD annotations.
## evaluation code
- ```reentrancy.py```: the code to evaluate the output from am-parser
- ```reentrancy_amrlib.py```: the code to evaluate the output from other parsers that need alignment from LEAMR
- ```dep_parse_amr.py```: the code to generate dependency trees for data from AMR 3.0
- ```amrbart_postprocess.py```: the code that post-processes the parses from AMRBART.

## TODO
- [ ] Add argparse and bash script for easier implementation of the code. 
