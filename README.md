# relative-amr-eval
This repository contains the code and dataset for the paper *The Relative Clauses AMR Parsers Hate Mosts* by Xiulin Yang and Nathan Schneider.


## dataset
The parsed results for ewt can be found in the ```parse_results```folder.
## classification code
- ```rc-types.py```: the code to classify the relative clauses without distinguishing types of reduced relative clauses.
- ```rrc-types.py```: the code to classify reduced relative clauses and add EUD annotations.
## evaluation code
- ```reentrancy.py```: the code to evaluate the output from am-parser
- ```reentrancy_amrlib.py```: the code to evaluate the output from other parsers that need alignment from leamr.
