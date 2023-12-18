from amr_utils.amr_readers import AMR_Reader
from penman.codec import PENMANCodec
from conllu import parse_incr
import json
reader = AMR_Reader()
def get_meta_info(alignment):
    triples = []
    node_token_pair = []
    for i, a in alignment.items():
        tri = []
        n_t_pair =[]
        for x in a:
            if x.tokens and x.nodes:
                n_t_pair.extend((x.tokens, x.nodes))
            if x.edges:
                for edge in x.edges:
                    edge_tupe = []
                    if 'of' in edge[1]:
                        edge = (edge[-1], edge[1][:-3], edge[0])
                        edge_tupe.append(edge)
                    edge_tupe.append(edge)
                    tri.extend(edge_tupe)
        triples.append(tri)
        node_token_pair.append(n_t_pair)
    return triples, node_token_pair

def target_node(conll_gold, grammatical_function):
    '''
    get the head information according to the gold annotation
    :param conll_gold: gold conllu file
    :return: a list of tuples (the head id, the head token, and the grammatical function of the head)
    '''
    head_tokens =[]
    source_tokens =[]
    for i, conll in enumerate(conll_gold):
        tokens = [x for x in conll]
        heads =[]
        sources =[]
        for token in conll:
            if token['deprel'] == 'acl:relcl': #find the relative clauses first
                head_id = int(token['head'])

                head_info = [x for x in tokens if x['id'] == head_id][0]
                head_xpos = head_info['xpos']
                if head_xpos not in ['WDT', 'WP', 'WRB']:
                    head_token = head_info['form']
                    head_rel = [x[0] for x in head_info['deps'] if x[1] == token['id']]
                    if head_rel == []:
                        head_rel = [grammatical_function[0]]
                    if head_rel[0] in grammatical_function or ' '.join(grammatical_function) in head_rel[0] or grammatical_function[0] in head_rel[0]:
                        head = (head_id, head_token)
                        heads.append(head)
                        sources.append((token['id'], token['form']))
        head_tokens.append(heads)
        source_tokens.append(sources)
    return head_tokens, source_tokens


def find_node(node_token_reentrancy, nod_token_pair, head_tokens, raw_text, source_tokens):

    reentrancy = []
    reentrancy_rela = []
    source_num =[]
    head_num =[]
    reen_num = []
    with open(raw_text) as text:
        texts = text.readlines()
    for i, tri in enumerate(node_token_reentrancy):
        to_node = [x[2] for x in tri]
        if len(to_node)!=len(set(to_node)):
            reentrancy.append(tri)
            reentrancy_node = list(set([x for x in to_node if to_node.count(x) > 1]))
            from_node = [x[0] for x in tri if x[2] in reentrancy_node]
            for head_token, source_token in zip(head_tokens[i], source_tokens[i]):

                if head_token:
                    head_num.append(i)
                    token_id = [j for j, x in enumerate(texts[i].strip().split()) if head_token[1] in x]
                    token_id = sorted(token_id, key=lambda x:(x-head_token[0]))[0]
                if source_token:
                    source_num.append(i)
                    # print(source_tokens[i])
                    source_token_id = [j for j, x in enumerate(texts[i].strip().split()) if source_token[1] in x]
                    source_token_id = sorted(source_token_id, key=lambda x: (x - source_token[0]))[0]

                for id, n in enumerate(nod_token_pair[i]):
                    if token_id in n:
                        nodes = nod_token_pair[i][id+1]
                        overlap = [x for x in nodes if x in reentrancy_node]
                    else:
                        overlap=None
                    if source_token_id in n:
                        s_nodes = nod_token_pair[i][id + 1]
                        s_overlap = [x for x in s_nodes if x in from_node]

                        if overlap and s_overlap:
                            print(i)
                            reentrancy_rela.append(tri)
                            reen_num.append(i)

    reentrency_perc = round(len(reentrancy_rela)/len(texts),3)
    print(f'Num of amrs:\t{len(texts)}\nnum of examples that receive reentrancies:\t{len(reentrancy)}\n'
          f'num of examples in which the head node receives reentrancies:\t {len(reentrancy_rela)} ({reentrency_perc})\n'
          f'num of head tokens {len(set(head_num))}\n'
          f'num of source tokens {len(set(source_num))}')
    print(head_num)
    print(source_num)
    print(reen_num)
    print(len(set([x for x in source_num if x in head_num])))
    print(len(reen_num))
    print(len(reen_num) / len(set([x for x in source_num if x in head_num])))


if __name__ =='__main__':
    subgraph = 'ewt/pc.out.subgraph_alignments.json'
    relation = 'ewt/pc.out.relation_alignments.json'
    reentrancy = 'ewt/pc.out.reentrancy_alignments.json'
    conll_gold = open('ewt/pc.conllu', 'r')
    adv_t = 'ewt/pc.txt'
    conll = [x for x in parse_incr(conll_gold)]
    head_tokens, source_tokens = target_node(conll, ['pass'])
    print(head_tokens)
    alignments_subgraph = reader.load_alignments_from_json(subgraph)
    alignments_relation = reader.load_alignments_from_json(relation)
    alignments_reentrancy = reader.load_alignments_from_json(reentrancy)

    triples_all = []
    node_token_pair = []
    triples_reentrancy, node_token_pair_reentrancy = get_meta_info(alignments_reentrancy)
    triples_relation, node_token_pair_relation = get_meta_info(alignments_relation)
    triples_subgraph, node_token_pair_subgraph = get_meta_info(alignments_subgraph)

    for i, x in enumerate(triples_relation):
        x.extend(triples_subgraph[i])
        x.extend(triples_reentrancy[i])
        triples_all.append(x)

    for j, y in enumerate(node_token_pair_relation):
        y.extend(node_token_pair_subgraph[j])
        y.extend(node_token_pair_reentrancy[j])
        node_token_pair.append(y)


    find_node(triples_all, node_token_pair, head_tokens, adv_t, source_tokens)





