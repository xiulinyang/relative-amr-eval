from io import open
from pathlib import Path
from conllu import parse_incr
from conllu import parse
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
import os
def read_preannoated_sents(conllus):
    relative_types = []
    relative_clauses =[]
    for conllu in conllus:
        file = open(conllu, 'r')
        sents = [x for x in parse_incr(file)]
        for j, sent in enumerate(sents):
            for i, token in enumerate(sent):
                if token['misc']:
                    if 'Cxn' in token['misc']:
                        relative_types.append(token['misc']['Cxn'])
                        relative_clauses.append(sent)

    return relative_types, relative_clauses

def write_to_conllu(conllu_file, redcl):
    with open(conllu_file, 'w') as conllu:
        for sent in redcl:
            conllu.write(sent.serialize())

# def find_deps_xcomp(sent, depents_id, all_depents):
#     xcomp = [x['id'] for x in tokens if x['id'] in depents_id and x['deprel'] in ['xcomp', 'ccomp']]
#     if xcomp:
#         new_depents=[x['id'] for x in sent if x['head'] in xcomp]
#         all_depents.extend(new_depents)
#         find_deps_xcomp(sent, new_depents, all_depents)

def classify_relatives(relative_clauses):
    reduced_relative_clauses = []
    objects =[]
    subject =[]
    oblique =[]
    passive = []
    others = []

    for clause in relative_clauses:
        for token in clause:
            if token['misc'] and 'Cxn' in token['misc']:
                if '-red-' in token['misc']['Cxn'] and clause not in reduced_relative_clauses:
                    reduced_relative_clauses.append(clause)
                elif '-full-obj' in token['misc']['Cxn'] and clause not in objects:
                    objects.append(clause)
                elif '-full-nsubj' in token['misc']['Cxn'] and clause not in subject:
                    subject.append(clause)
                elif '-full-obl' in token['misc']['Cxn'] and clause not in oblique:
                    oblique.append(clause)
                elif '-full-pass' in token['misc']['Cxn'] and clause not in passive:
                    passive.append(clause)
                elif 'rc_amparser' in token['misc']['Cxn'] and clause not in others:
                    others.append(clause)
    return reduced_relative_clauses, subject, objects, oblique, passive, others


def save_relative_split(file_name, conllu):
    with open(file_name, 'w') as relative:
        relative_split = Path(conllu).read_text().strip().split('\n\n')
        for sent in relative_split:
            for s in sent.split('\n'):
                if s.startswith('# text = '):
                    raw = s[len('# text ='):-1].strip() + ' ' + s[-1]
                    relative.write(f'{raw}\n')


def get_verb_argument(ewt_ud_files):
    sents_all =[]
    for ewt in ewt_ud_files:
        file_all = open(ewt, 'r')
        sents = [x for x in parse_incr(file_all)]
        sents_all.extend(sents)
    verb_argument ={}
    for sent in sents_all:
        for token in sent:
            if token['xpos'] and 'VB' in token['xpos']:
                lemma = token['lemma']
                dependents = [x['deprel'] for x in sent if x['head']==token['id'] if x['deprel'] not in ['nsubj', 'punct']]
                if lemma not in verb_argument:
                    verb_argument[lemma]=dependents
                else:
                    verb_argument[lemma].extend(dependents)
    return verb_argument

def get_transitivity(verb_argument):
    df = pd.read_csv('verb_transitivity.tsv', sep='\t')

    # Initialize an empty dictionary
    verb_dict = {}

    # Iterate through each row
    for index, row in df.iterrows():
        verb = row['verb']
        max_percent = max(row['percent_intrans'], row['percent_trans'], row['percent_ditrans'])

        if max_percent > 0.5:
            if max_percent == row['percent_intrans']:
                verb_dict[verb] = 'intrans'
            elif max_percent == row['percent_trans']:
                verb_dict[verb] = 'trans'
            else:
                verb_dict[verb] = 'ditrans'

        if verb in verb_argument:
            if 'xcomp' in get_most_common(verb_argument, verb) or 'obj' in get_most_common(verb_argument, verb) or 'ccomp' in get_most_common(verb_argument, verb):
                verb_dict[verb] = 'trans'

    for k, v in verb_argument.items():
        if k not in verb_dict:
            if 'xcomp' in get_most_common(verb_argument, k) or 'obj' in get_most_common(verb_argument, k) or 'ccomp' in get_most_common(verb_argument, k):
                verb_dict[k] = 'trans'
            else:
                verb_dict[k] = 'instrans'

    return verb_dict
def get_most_common(verb_argument, token):
    most_common = Counter(verb_argument[token]).most_common(3)
    most_common = [x[0] for x in most_common]
    return most_common


def find_deps_comp(sent, xcomp_id):
    return [x['deprel'] for x in sent if x['head']==xcomp_id]

def get_eud_token_id(word):
    return [x[1] for x in word['deps']]

def get_eud(word, id):
    return [x[0] for x in word['deps'] if x[1]==id][0]

def eud_transformation(sents, verb_dict):
    mannual_annotation = []
    advrc = []
    orc = []
    advrc_sentid = []
    orc_sentid = []
    special_cases = ['xcomp', 'ccomp']
    for j, sent in enumerate(sents):
        sent_id = sent.metadata['sent_id']
        for token in sent:
            if token['deprel'] == 'acl:relcl' and '-red-' in token['misc']['Cxn']:  # find the predicate verb in the relative clause
                head = [x for x in sent if token['head'] ==x['id']][0]
                head_dep = [x for x in sent if x['id'] == token['head']][0]  # find the head token
                head_deps = [x['xpos'] for x in sent if x['head'] == token['id']]
                all_deps = [x for x in sent if x['head'] == token['id']]
                all_deps_deprels = [x['deprel'] for x in all_deps]

                if not set(special_cases).isdisjoint(set(all_deps_deprels)):
                    xcomp_id = [x['id'] for x in all_deps if x['deprel'] in special_cases][0]
                    all_deps_deprels.extend(find_deps_comp(sent, xcomp_id))
                    mannual_annotation.append(sent)
                for d in all_deps:
                    if 'obl' in d['deprel']:
                        dep_obl = [x['deprel'] for x in sent if x['head'] == d['id']]
                        if 'case' in dep_obl:
                            all_deps_deprels.remove(d['deprel'])

                head_deps = [x for x in head_deps if x in ['WDT', 'WP', 'WRB']]
                if head_deps == [] and head_dep['xpos'] not in ['WDT', 'WP','WRB']:  # find the reduced head and filter out the free relative clauses
                    head_index = [j for j, x in enumerate(sent) if x['id'] == head_dep['id']][0]
                    if token['id'] in get_eud_token_id(head):
                        eud = get_eud(head, token['id'])
                        if 'obj' in eud and sent not in orc:
                            orc.append(sent)
                            orc_sentid.append(sent_id)

                        elif 'obl' in eud and sent not in advrc:
                            advrc.append(sent)
                            advrc_sentid.append(sent_id)

                        else:
                            mannual_annotation.append(sent)
                    else:
                        if 'pstrand' in token['misc']['Cxn']:
                            if sent_id not in advrc_sentid:
                                sent[head_index]['deps'].append(('obl', token['id']))
                                advrc.append(sent)
                                advrc_sentid.append(sent_id)
                            else:
                                advrc[-1][head_index]['deps'].append(('obl', token['id']))
                        elif 'auxstrand' in token['misc']['Cxn']:
                            if sent_id not in orc_sentid:
                                sent[head_index]['deps'].append(('obj', token['id']))
                                orc.append(sent)
                                orc_sentid.append(sent_id)
                            else:
                                orc[-1][head_index]['deps'].append(('obj', token['id']))

                        elif 'VB' in token['xpos']:
                            verb = token['lemma']
                            if 'pass' in ''.join(all_deps_deprels):
                                if sent_id not in advrc_sentid:
                                    sent[head_index]['deps'].append(('obl', token['id']))
                                    advrc.append(sent)
                                    advrc_sentid.append(sent_id)
                                else:
                                    advrc[-1][head_index]['deps'].append(('obl', token['id']))

                            elif verb_dict[verb] in ['trans', 'ditrans']:
                                if 'obj' not in all_deps_deprels:
                                    if sent_id not in orc_sentid:
                                        sent[head_index]['deps'].append(('obj', token['id']))
                                        orc.append(sent)
                                        orc_sentid.append(sent_id)
                                    else:
                                        orc[-1][head_index]['deps'].append(('obj', token['id']))

                                else:
                                    if sent_id not in advrc_sentid:
                                        sent[head_index]['deps'].append(('obl', token['id']))
                                        advrc.append(sent)
                                        advrc_sentid.append(sent_id)
                                    else:
                                        advrc[-1][head_index]['deps'].append(('obl', token['id']))

                            elif verb_dict[verb] == 'intrans':
                                if sent_id not in advrc_sentid:
                                    sent[head_index]['deps'].append(('obl', token['id']))
                                    advrc.append(sent)
                                    advrc_sentid.append(sent_id)
                                else:
                                    advrc[-1][head_index]['deps'].append(('obl', token['id']))


                        else:
                            if sent_id not in advrc_sentid:
                                sent[head_index]['deps'].append(('obl', token['id']))
                                advrc.append(sent)
                                advrc_sentid.append(sent_id)
                            else:

                                advrc[-1][head_index]['deps'].append(('obl', token['id']))



    return advrc, orc, mannual_annotation

def recover_info_back(original_split, advrc, orc, mannual_annotation):
    to_change_set = advrc+orc+mannual_annotation
    to_change_set = {x.metadata['sent_id']: x for x in to_change_set}
    file = open(original_split, 'r')
    sents = [x for x in parse_incr(file)]
    for i, sent in enumerate(sents):
        sent_id = sent.metadata['sent_id']
        if sent_id in to_change_set:
            sents[i] = to_change_set[sent_id]
    return sents

if __name__ =='__main__':
    PATH = 'eud_ewt_test'
    if not os.path.exists(PATH):
        os.mkdir(PATH)
    ewts = ['en_ewt-ud-dev.conllu', 'en_ewt-ud-test.conllu', 'en_ewt-ud-train.conllu']
    annotated_ewts = [f'{PATH}.conllu']
    relative_types, relative_clauses = read_preannoated_sents(annotated_ewts)
    print(Counter(relative_types).most_common())
    print(len(relative_types))
    # classify full relative clauses
    reduced_relative_clauses, subject, objects, oblique, passive, others = classify_relatives(relative_clauses)
    write_to_conllu(f'{PATH}/reduced.conllu', reduced_relative_clauses)
    save_relative_split(f'{PATH}/reduced.txt', f'{PATH}/reduced.conllu')

    # classify reduced relative clauses
    verb_argument = get_verb_argument(ewts)
    verb_dict = get_transitivity(verb_argument)
    oblrc, orc, manual = eud_transformation(reduced_relative_clauses, verb_dict)

    write_to_conllu(f'{PATH}/oblrc.conllu', oblrc)
    write_to_conllu(f'{PATH}/orc.conllu', orc)
    write_to_conllu(f'{PATH}/needcheck.conllu', manual)
    save_relative_split(f'{PATH}/oblrc.txt', f'{PATH}/oblrc.conllu')
    save_relative_split(f'{PATH}/orc.txt',f'{PATH}/orc.conllu')
    save_relative_split(f'{PATH}/needcheck.txt', f'{PATH}/needcheck.conllu')

    train_sents = recover_info_back(f'{PATH}.conllu', oblrc, orc, manual)
    write_to_conllu(f'{PATH}/eud_{PATH}.conllu', train_sents)