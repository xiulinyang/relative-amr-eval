import penman
from pathlib import Path
from conllu import parse
from penman.graph import Graph
from penman.codec import PENMANCodec
from conllu import parse_incr
from conllu import parse




def target_node(conll_gold, grammatical_function):
    '''
    get the head information according to the gold annotation
    :param conll_gold: gold conllu file
    :return: a list of tuples (the head id, the head token, and the grammatical function of the head)
    '''
    head_tokens =[]
    preds_node = []
    for i, conll in enumerate(conll_gold):
        tokens = [x for x in conll]
        heads =[]
        preds=[]
        for token in conll:
            if token['deprel'] == 'acl:relcl': #find the relative clauses first

                head_id = int(token['head'])
                head_info = [x for x in tokens if x['id'] == head_id][0]
                head_xpos = head_info['xpos']
                if head_xpos not in ['WDT', 'WP', 'WRB']:
                    head_token = head_info['form']
                    head_rel = [x[0] for x in head_info['deps'] if x[1]==token['id']]
                    if head_rel==[]:
                        head_rel =grammatical_function
                    if head_rel[0] in grammatical_function or grammatical_function[0] in head_rel[0]: #TODO: find a better way to
                        preds.append((token['id'], token['form']))
                        head = (head_id, head_token)
                        heads.append(head)
        head_tokens.append(heads)
        preds_node.append(preds)
    return head_tokens, preds_node

def find_node(alignment, head_id, source_id):
    '''
    to find the node that represents the head token
    :param alignment: the alignment document
    :param head_id: the head_id returned from the target_node function
    :return:
    '''
    assert len(alignment)==len(head_id)
    head_nodes =[]
    source_nodes =[]
    for i, alignment_element in enumerate(alignment):

        sentence = alignment_element.split('nodealignment=')[0].strip().split('\n')
        node_token_alignment = alignment_element.split('nodealignment=')[1][1:-2].strip().split(', ')
        head_node = []
        source_node =[]
        token_id = [x.split('@@')[0] for x in node_token_alignment]
        token_node = [x.split('@@')[-1] for x in node_token_alignment]
        for j, token in enumerate(sentence):
            for h in head_id[i]:

                if h[1] in token.split('\t')[1]:

                    head_id[i].remove(h)
                    nodes = [y for x, y in zip(token_id, token_node) if int(x)-1==j] #find the target node
                    for x in nodes:
                        head_node.append(x)

            for k in source_id[i]:
                if k[1] in token.split('\t')[1]:

                    source_id[i].remove(k)
                    s_nodes = [y for x, y in zip(token_id, token_node) if int(x)-1==j] #find the target node
                    for x in s_nodes:
                        source_node.append(x)


        head_nodes.append(head_node)
        source_nodes.append(source_node)
    return head_nodes, source_nodes

def find_reentrancies(pred_amr, head_nodes, source_nodes):
    reentrancies = []
    reentrancies_general = []
    codec = PENMANCodec()
    head_num =[]
    source_num=[]
    reen_num =[]
    for i, x in enumerate(pred_amr):
        drs_triple = codec.decode(x).triples
        label_node_pair = {x[0]:x[2].replace('\"', '') for x in drs_triple if x[1]==':instance'}
        to_node = [x[2] for x in drs_triple if x[1]!=':instance' and x[2].startswith('u_') ] #only works for amparser
        # to_node_name = [label_node_pair[x[2]] for x in drs_triple if x[1]!=':instance' and x[2].startswith('u_')]
        if len(to_node) != len(set(to_node)):
            reentrancies_general.append(drs_triple)
            reentrancy_node = list(set([label_node_pair[x] for x in to_node if to_node.count(x) > 1]))
            reentrancy_to_node = [x for x in to_node if to_node.count(x)>1]
            reentrancy_from_node = [label_node_pair[x[0]] for x in drs_triple if x[2] in reentrancy_to_node]
            print(reentrancy_node) #the node that has renentrancies
            print(head_nodes[i]) # the real node that should have reentrancies
            overlap = [x for x in reentrancy_node if x in head_nodes[i]]
            from_source = [x for x in reentrancy_from_node if x in source_nodes[i]]
            if overlap and from_source:
                reentrancies.append(drs_triple)
                reen_num.append(i)
        if head_nodes[i]:
            head_num.append(i)
        if source_nodes[i]:
            source_num.append(i)
    reentrency_perc = round(len(reentrancies)/len(pred_amr),3)
    print(f'Num of amrs:\t{len(pred_amr)}\nnum of examples that receive reentrancies:\t{len(reentrancies_general)}\n'
          f'num of examples in which the head node receives reentrancies:\t {len(reentrancies)} ({reentrency_perc})\n'
          f'num of head tokens that receive a node: {len(head_num)}\n'
          f'num of source tokens that receive a node: {len(source_num)}')
    print(head_num)
    print(source_num)
    print(reen_num)
    print(len(set([x for x in source_num if x in head_num])))
    print(len(reen_num))
    print(len(reen_num)/len(set([x for x in source_num if x in head_num])))
    print(len(set([x for x in reen_num if x in source_num and x in head_num])))




if __name__== '__main__':
    pred_amr = Path('output_ewt/orc.txt').read_text().strip().split('\n\n')
    alignment = Path('output_ewt/alignment_orc.txt').read_text().strip().split('sentence=')[1:]
    conll_gold = open('ewt/orc.conllu', 'r')
    conll = [x for x in parse_incr(conll_gold)]
    head_id, pred_id = target_node(conll, ['obj'])
    print(pred_id)
    head_nodes, source_nodes = find_node(alignment, head_id, pred_id)
    # print(len(head_id))
    # print(len(alignment))
    # print(len(pred_amr))

    print(head_nodes)
    print(source_nodes)


    find_reentrancies(pred_amr, head_nodes, source_nodes)