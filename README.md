# relative-amr-eval
This repository contains the code and dataset for the paper *Comparative Analysis of Seq2Seq and Compositional Models in AMR Parsing: Evaluating Performance on English Relative Clause Reentrancies*.

## dataset
- ```ewt.zip```: the output and alignment from spring
- ```ewt_output.zip```: the output and alignmentfrom am-parser
- ```amrlib.zip```: the output and alignment from amrlib
# classification code
- ```rc-types.py```: the code to classify the relative clauses without distinguishing types of reduced relative clauses.
- ```rrc-types.py```: the code to classify reduced relative clauses and add EUD annotations.
## evaluation code
- ```reentrancy.py```: the code to evaluate the output from am-parser
- ```reentrancy_amrlib.py```: the code to evaluate the output from other parsers that need alignment from leamr.
