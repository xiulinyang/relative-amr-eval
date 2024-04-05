import glob
from pathlib import Path
import stanza
from stanza.utils.conll import CoNLL
from conllu import parse
from pathlib import Path
from tqdm import tqdm
# stanza.download('en')
# nlp = stanza.Pipeline(lang='en')
# print("Stanza version:", stanza.__version__)


# conllu_data = ""
amrs_paths = glob.glob('/Users/xiulinyang/Downloads/amr_annotation_3.0/data/amrs/split/test/*')
all_sents =[]
amr_dic = {}
test_sents = Path('/Users/xiulinyang/Desktop/TODO/relativeClause/amr/amr3_dep_test.conllu').read_text().strip().split('\n\n')
print(len(test_sents))
with open('amr3_gold_test.txt', 'w') as test_gold, open('amr/test.txt', 'w') as test_text:
    for amr in amrs_paths:
        amrs = Path(amr).read_text().strip().split('\n\n')[1:]
        for amr in amrs:
            amr_sent = amr.split('\n')[1][len('# ::snt '):]
            amr_string = '\n'.join(amr.split('\n')[3:])
            amr_dic[amr_sent] = amr_string

    for i, a in tqdm(enumerate(test_sents)):
        try:
            parsed_info = parse(a)[0]
            deprel = [x['deprel'] for x in parsed_info]
            if 'acl:relcl' in deprel:
                sent = a.split('\n')[0][len('# text = '):]
                # if sent.strip()!= test_sents[i].split('\n')[0][len('# text = '):].strip():
                #     print(sent)
                #     print(test_sents[i].split('\n')[0][len('# text = '):])
                amr_graph = amr_dic[sent]
                test_gold.write(f'# ::snt {sent}\n')
                test_gold.write(f'{amr_graph}\n\n')
                test_text.write(f'{sent}\n')

        except:
            print('wrongsplit')

