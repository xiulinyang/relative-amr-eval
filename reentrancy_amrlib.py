from amr_utils.amr_readers import AMR_Reader
from conllu import parse
from pathlib import Path
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
                    if 'of' in edge[1]: #inverse edge
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
    # global head_rel
    head_tokens =[]
    source_tokens =[]
    conll_g = []
    for sent in conll_gold:
        sent = '\n'.join([x for x in sent.split('\n') if '-' not in x.split('\t')[0]])
        conll_g.append(parse(sent)[0])

    for i, conll in enumerate(conll_g):
        tokens = [x for x in conll]
        tokens_split_space = [x[len('# text = '):] for x in conll_gold[i].split('\n') if x.startswith('# text = ')][0].split()
        deprels = ''.join([x['deprel'] for x in tokens])
        heads = []
        sources = []
        head_rel=[]
        if 'acl:relcl' in deprels:
            for k, token in enumerate(conll):
                if token['deprel'] =='acl:relcl': #find the relative clauses first
                    head_id = int(token['head'])
                    head_info = [x for x in tokens if x['id'] == head_id][0]
                    deps = head_info['deps']
                    if deps:
                        deps = ' '.join([x[0] for x in deps])
                    else:
                        deps = grammatical_function[0]

                    if deps and grammatical_function[0] in deps:
                        head_token = head_info['form']
                        if head_info['deps']:
                            head_rel = [x[0] for x in head_info['deps'] if x[1] == token['id']]
                            if head_rel==[]:
                                head_rel = [grammatical_function[0]]
                        else:
                            head_rel = [grammatical_function[0]]

                        if head_rel[0] in grammatical_function or ' '.join(grammatical_function) in head_rel[0] or grammatical_function[0] in head_rel[0]:

                            real_head_token = [(k,x) for k, x in enumerate(tokens_split_space) if head_token in x]
                            real_head_token = sorted(real_head_token, key= lambda x: tokens_split_space.index(x[1])-head_id)
                            head_id = real_head_token[0][0]
                            head = (head_id, head_token)
                            heads.append(head)

                            token_form = token['form']
                            real_token_token = [(k,x) for k, x in enumerate(tokens_split_space) if token_form in x]
                            real_token_token = sorted(real_token_token,
                                                     key=lambda x: tokens_split_space.index(x[1]) - token['id'])

                            sources.append((real_token_token[0][0], token_form))


        else:
            heads.append('dependency error')
            sources.append('dependency error')
        if heads ==[]: #we filter out unqualified sentences that contains for example csubj instead of nsubj
            heads.append('dependency error')
        head_tokens.append(heads)
        source_tokens.append(sources)
    filtered_out = [i for i, x in enumerate(head_tokens) if x==['dependency error']]
    return head_tokens, source_tokens, set(filtered_out)


def find_node(node_token_reentrancy, nod_token_pair, head_tokens, source_tokens, filter_out):
    '''
    :param node_token_reentrancy:
    :param nod_token_pair:
    :param head_tokens:
    :param raw_text:
    :param source_tokens:
    :return:
    '''
    reentrancy = []
    reentrancy_rela = []
    source_num =[]
    head_num =[]
    reen_num = []
    correct_parses =[]
    failed = []
    for i, tri in enumerate(node_token_reentrancy):
        correct_parses.append(i)

        to_node = [x[2] for x in tri]
        for head_token, source_token in zip(head_tokens[i], source_tokens[i]): #first, find the token ids of the head and source tokens.
            if head_token !='dependency error':
                # head token
                token_id = head_token[0]
                # source token
                source_token_id = source_token[0]
                node_id =[]
                for idxx, x in enumerate(nod_token_pair[i]): # get all the token ids that have aligned nodes
                    if idxx%2==0:
                        node_id.extend(x)

                if token_id in node_id:
                    head_num.append(i)
                    # print(i)
                    # print(head_token)
                    # print(token_id)
                    # print(node_id)
                    # print(nod_token_pair[i])


                if source_token_id in node_id:
                    source_num.append(i)
                if len(to_node) != len(set(to_node)):
                    reentrancy_node = list(set([x for x in to_node if to_node.count(x) > 1]))
                    from_node = [x[0] for x in tri if x[2] in reentrancy_node]
                    reentrancy.append(i)
                    overlap = []
                    s_overlap=[]
                    for id, n in enumerate(nod_token_pair[i]):
                        #secondly, check if there is node corresponding to that token
                        if token_id in n:
                            nodes = nod_token_pair[i][id+1]
                            overlap = [x for x in nodes if x in reentrancy_node]
                        if source_token_id in n:
                            s_nodes = nod_token_pair[i][id+1]
                            s_overlap = [x for x in s_nodes if x in from_node]
                            if overlap and s_overlap:
                                reentrancy_rela.append(tri)
                                reen_num.append(i)

    texts = set([x for x in correct_parses if x not in filter_out])
    perc = len(set([x for x in source_num if x in head_num]))
    attainable_recall = round((len(set(reen_num)) / perc) * 100, 1)
    attainale_rate = round(perc / len(texts)*100, 1)
    print([x for x in range(0, 100) if x not in reen_num])
    reentrency_perc = round(len(set(reen_num))/len(texts)*100,1)
    print( f'Num of amrs \t reentrancy recall \t attainable recall \t attainable rate\n'
          f'{len(texts)} \t {reentrency_perc} ({len(set(reen_num))}/{len(texts)}) \t {attainable_recall} ({len(set(reen_num))}/{perc}) \t {attainale_rate} ({perc}/{len(texts)})\n')
          # f'num of head tokens {len(set(head_num))}\n'
          # f'num of source tokens {len(set(source_num))}')
    # print(head_num)
    # print(source_num)


    # print(f'Attainable recall {p} ({len(set(reen_num))}/{perc})')

def main(alignment_foler, conll_gold_file, grammatical_functions):
    subgraph = f'{alignment_foler}.subgraph_alignments.json'
    relation = f'{alignment_foler}.relation_alignments.json'
    reentrancy = f'{alignment_foler}.reentrancy_alignments.json'
    conll_gold = Path(conll_gold_file).read_text().strip().split('\n\n')

    head_tokens, source_tokens, filtered_sent = target_node(conll_gold, grammatical_functions)

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
    find_node(triples_all, node_token_pair, head_tokens, source_tokens, filtered_sent)

if __name__ =='__main__':
    all_rcs = ['sc', 'oc', 'pc', 'oblc', 'orc', 'oblrc']
    rc_types ={'sc':'nsubj', 'oc':'obj', 'pc': 'pass', 'orc': 'obj', 'oblrc':'obl', 'oblc': 'obl'}
    for rc in all_rcs:
        print(f'=============================== {rc_types[rc]}=============================================')
        parser_folder = f'bart_ewt/amrlib_bart_{rc}'
        gold_conll  =f'ewt/{rc}.conllu'
        grammatical_functions = [rc_types[rc]]
        main(parser_folder, gold_conll, grammatical_functions)


