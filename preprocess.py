import stanza
from stanza.utils.conll import CoNLL
from pathlib import Path
stanza.download('en')
nlp = stanza.Pipeline(lang='en', tokenize_pretokenized=True)
print("Stanza version:", stanza.__version__)


def generate_parses(rc_file, target_conll):
    rcs= Path(rc_file).read_text().strip().split('\n')
    rcs =[x.split() for x in rcs]
    obj = nlp(rcs)
    CoNLL.write_doc2conll(obj, target_conll)

rc = 'rc/object_rrc.txt'
target_conll ='rc/orc.conllu'
generate_parses(rc, target_conll)