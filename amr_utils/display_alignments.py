import sys

from amr_utils.amr_readers import AMR_Reader
from amr_utils.graph_utils import is_rooted_dag, get_subgraph
from amr_utils.style import HTML_AMR


def is_aligned_node(amr, n, alignments):
    align = amr.get_alignment(alignments, node_id=n)
    if align:
        return 'green'
    return ''


def is_aligned_edge(amr, e, alignments):
    align = amr.get_alignment(alignments, edge=e)
    return 'grey' if align else ''


def is_aligned_token(amr, t, alignments):
    align = amr.get_alignment(alignments, token_id=t)
    return 'green' if align else ''


def get_node_aligned_tokens(amr, n, alignments):
    align = amr.get_alignment(alignments, node_id=n)
    if align:
        return ' '.join(amr.tokens[t] for t in align.tokens)
    return ''


def get_edge_aligned_tokens(amr, e, alignments):
    align = amr.get_alignment(alignments, edge=e)
    if align:
        return ' '.join(amr.tokens[t] for t in align.tokens)
    return ''


def get_token_aligned_subgraph(amr, tok, alignments):
    align = amr.get_alignment(alignments, token_id=tok)
    if align:
        elems = [amr.nodes[n] for n in align.nodes]
        elems += [r for s,r,t in align.edges]
        # return ' '.join(elems)
        edges = [(s,r,t) for s,r,t in amr.edges if ((s,r,t) in align.edges or (s in align.nodes and t in align.nodes))]
        sg = get_subgraph(amr, align.nodes, edges)
        if is_rooted_dag(amr, align.nodes):
            out = sg.graph_string()
        else:
            out = ', '.join(elems)
        return out
    return ''


def style(amrs, alignments, outfile):
    output = HTML_AMR.style(amrs[:5000],
                            assign_node_color=is_aligned_node,
                            assign_edge_color=is_aligned_edge,
                            assign_token_color=is_aligned_token,
                            assign_node_desc=get_node_aligned_tokens,
                            assign_edge_desc=get_edge_aligned_tokens,
                            assign_token_desc=get_token_aligned_subgraph,
                            other_args=alignments)

    with open(outfile, 'w+', encoding='utf8') as f:
        f.write(output)


def main():
    file = sys.argv[1]
    align_file = sys.argv[2]
    outfile = sys.argv[3]

    reader = AMR_Reader()
    amrs = reader.load(file, remove_wiki=True)
    alignments = reader.load_alignments_from_json(align_file, amrs)
    style(amrs[:5000], alignments, outfile)


if __name__=='__main__':
    main()
