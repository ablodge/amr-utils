import sys

from amr_utils.amr_readers import AMR_Reader
from amr_utils.graph_utils import is_rooted_dag
from amr_utils.style import HTML_AMR


def is_aligned_node(amr, n):
    align = amr.get_alignment(node_id=n)
    if align:
        return 'green'
    return ''

def is_aligned_edge(amr, e):
    align = amr.get_alignment(edge=e)
    return 'grey' if align else ''

def is_aligned_token(amr, t):
    align = amr.get_alignment(token_id=t)
    return 'green' if align else ''

def get_node_aligned_tokens(amr, n):
    align = amr.get_alignment(node_id=n)
    if align:
        return ' '.join(amr.tokens[t] for t in align.tokens)
    return ''

def get_edge_aligned_tokens(amr, e):
    align = amr.get_alignment(edge=e)
    if align:
        return ' '.join(amr.tokens[t] for t in align.tokens)
    return ''

def get_token_aligned_subgraph(amr, tok):
    align = amr.get_alignment(token_id=tok)
    if align:
        elems = [amr.nodes[n] for n in align.nodes]
        elems += [r for s,r,t in align.edges]
        # return ' '.join(elems)
        sg = amr.get_subgraph(align.nodes)
        for e in align.edges:
            if e not in sg.edges:
                sg.edges.append(e)
            s,r,t = e
            if sg.root == t:
                sg.root = s
            for n in [s,t]:
                if n not in sg.nodes:
                    sg.nodes[n] = '<var>'
            if not sg.root:
                sg.root = s
        if is_rooted_dag(sg):
            out = sg.graph_string()
        else:
            out = ', '.join(elems)
        return out
    return ''

def style(amrs, outfile):
    output = HTML_AMR.style(amrs[:5000],
                            assign_node_color=is_aligned_node,
                            assign_edge_color=is_aligned_edge,
                            assign_token_color=is_aligned_token,
                            assign_node_desc=get_node_aligned_tokens,
                            assign_edge_desc=get_edge_aligned_tokens,
                            assign_token_desc=get_token_aligned_subgraph)

    with open(outfile, 'w+', encoding='utf8') as f:
        f.write(output)

def main():
    file = sys.argv[-2]
    outfile = sys.argv[-1]

    reader = AMR_Reader()
    amrs = reader.load(file, remove_wiki=True)
    style(amrs[:5000], outfile)


if __name__=='__main__':
    main()
