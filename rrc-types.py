from io import open
from pathlib import Path
from conllu import parse_incr
from conllu import parse
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd

def read_preannoated_sents(conllu):
    relative_types = []
    relative_clauses =[]
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
                elif 'rc' in token['misc']['Cxn'] and clause not in others:
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
            if 'xcomp' in get_most_common(verb_argument, verb) or 'obj' in get_most_common(verb_argument, verb):
                verb_dict[verb] = 'trans'
            elif 'ccomp' in get_most_common(verb_argument, verb):
                verb_dict[verb] = 'intrans'

    for k, v in verb_argument.items():
        if k not in verb_dict:
            if 'xcomp' in get_most_common(verb_argument, k) or 'obj' in get_most_common(verb_argument, k):
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
                        if 'VB' in token['xpos']:
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


# advrc_rule, orc_rule, cops_rule, mannual_annotation_rule = eud_transformation(sents_reduced)

if __name__ =='__main__':
    ewts = ['en_ewt-ud-dev.conllu', 'en_ewt-ud-test.conllu', 'en_ewt-ud-train.conllu']
    relative_types, relative_clauses = read_preannoated_sents('ewt_train.conllu')
    print(len(relative_types))
    # classify full relative clauses
    # reduced_relative_clauses, subject, objects, oblique, passive, others = classify_relatives(relative_clauses)
    # reduced_relative_clauses = len(reduced_relative_clauses)  # Replace with your list
    # subjects = len(subject)  # Replace with your list
    # objects = len(objects)  # Replace with your list
    # oblique = len(oblique)  # Replace with your list
    # passive = len(passive)  # Replace with your list
    # others = len(others)  # Replace with your list
    #
    # # List names
    # categories = ['Reduced', 'Subject', 'Objects', 'Oblique', 'Passive', 'Others']
    #
    # # List lengths
    # lengths = [reduced_relative_clauses, subjects, objects, oblique, passive, others]
    #
    # # Creating histogram
    # bars = plt.bar(categories, lengths, color='lightsteelblue')
    #
    # # Adding the numbers on top of each bar
    # for bar in bars:
    #     yval = bar.get_height()
    #     plt.text(bar.get_x() + bar.get_width() / 2, yval, yval, ha='center', va='bottom')
    #
    # plt.xlabel('Relative Clause Categories')
    # plt.ylabel('Counts')
    # plt.title('Lengths of Different Lists')
    # plt.show()
    # write_to_conllu('ewt/oblc.conllu', oblique)
    # write_to_conllu('ewt/others.conllu', others)
    # write_to_conllu('ewt/sc.conllu', subject)
    # write_to_conllu('ewt/oc.conllu', objects)
    # write_to_conllu('ewt/pc.conllu', passive)
    # write_to_conllu('ewt/reduced.conllu', reduced_relative_clauses)
    #
    # save_relative_split('ewt/oblc.txt', 'ewt/oblc.conllu')
    # save_relative_split('ewt/others.txt','ewt/others.conllu')
    # save_relative_split('ewt/sc.txt','ewt/sc.conllu')
    # save_relative_split('ewt/oc.txt', 'ewt/oc.conllu')
    # save_relative_split('ewt/pc.txt', 'ewt/pc.conllu')
    # save_relative_split('ewt/reduced.txt', 'ewt/reduced.conllu')
    #
    # # classify reduced relative clauses
    # verb_argument = get_verb_argument(ewts)
    # verb_dict = get_transitivity(verb_argument)
    # oblrc, orc, manual = eud_transformation(reduced_relative_clauses, verb_dict)
    #
    #
    # write_to_conllu('ewt/oblrc.conllu', oblrc)
    # write_to_conllu('ewt/orc.conllu', orc)
    # write_to_conllu('ewt/needcheck.conllu', manual)
    # save_relative_split('ewt/oblrc.txt', 'ewt/oblrc.conllu')
    # save_relative_split('ewt/orc.txt','ewt/orc.conllu')
    # save_relative_split('ewt/needcheck.txt', 'ewt/needcheck.conllu')
    #
    #
