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


## To recover the enhanced Universal Dependency (EUD) relations back
- ```en_ewt-ud-dev/test/train.conllu``` are downloaded from [ewt-dev-branch](https://github.com/xiulinyang/UD_English-EWT)
- ```eud_ewt_dev/test/train.conllu``` are the post-processed files that have the recovered eud annotation.
- ```rc-types.py```: the script used to classify sentences based on their eud annotations (which means for the reduced relative clauses, the Cxn value in the misc column will be xxx-red-missingdep-xxx.

- ```rrc-types.py```: the script used to classify reduced relative clauses. The output is stored in the ``eud_train/dev/test`` folders (each folder contains necessary documents for each split of the EWT treebank)

- ```verb_transitivity.tsv```: the tsv file that contains verb transitivity information. 
	

In order to check if there is any mis-classified reduced relative clauses, you can follow the following pipeline:

### correction
1. Go to the ``eud_train/dev/test`` folder and you need to check the following two documents:
	- ```orc/oblrc.txt``` or ```orc/oblrc.conllu```: you need to check if sentences have misclassified examples. 

2. Once you find a misclassification example, you can go check ```eud_ewt_split.conllu``` and you will find that the eud annotation of the sentence and you should correct it. 

3. After all the corrections of one split, you can run ```rc-types.py``` to generate an updated ```eud_ewt_split.conllu```. 

### double check

3. Once you have corrected all sentences, you can make a double check by (1) run ```rc-types.py``` to get the updated ```eud_ewt_split.conllu``` under the ```eud_ewt``` folder; (2) run ```rrc-types.py``` to get the updated reduced relative clause classification and recheck if they are correct. If something is wrong, then follow the correction section. (You need to change the PATH variable at the beginning of each script).


## TODO
- [ ] Add argparse and bash script for easier implementation of the code.
- [ ] Add more detailed instructions in readme. 
