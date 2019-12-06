import sys
from collections import Counter

from amr import JAMR_AMR_Reader
from style import HTML_AMR

amr_pairs = {}

def style(assign_node_color=None, assign_node_desc=None, assign_edge_color=None, assign_edge_desc=None,
          assign_token_color=None, assign_token_desc=None):
    output = '<!DOCTYPE html>\n'
    output += '<html>\n'
    output += '<style>\n'
    output += HTML_AMR.style_sheet()
    output += '</style>\n\n'
    output += '<body>\n'
    for id  in amr_pairs:
        amr1, amr2 = amr_pairs[id]
        output += '1:\n'
        output += HTML_AMR.html(amr1,
                                assign_node_color, assign_node_desc,
                                assign_edge_color, assign_edge_desc,
                                assign_token_color, assign_token_desc)
        output += '2:\n'
        output += HTML_AMR.html(amr2,
                                assign_node_color, assign_node_desc,
                                assign_edge_color, assign_edge_desc,
                                assign_token_color, assign_token_desc)
    output += '</body>\n'
    output += '</html>\n'
    return output


def is_correct_node(amr, n):
    amr1, amr2 = amr_pairs[amr.id]
    node = amr.nodes[n]
    amr1_nodes = [amr1.nodes[m] for m in amr1.nodes]
    amr2_nodes = [amr2.nodes[m] for m in amr2.nodes]
    if node in amr1_nodes and node in amr2_nodes:
        return 'green'
    return 'red'

def is_correct_edge(amr, e):
    amr1, amr2 = amr_pairs[amr.id]
    s,r,t = e
    edge = (amr.nodes[s],r,amr.nodes[t])
    amr1_edges = [(amr1.nodes[s2],r2,amr1.nodes[t2]) for s2,r2,t2 in amr1.edges]
    amr2_edges = [(amr2.nodes[s2],r2,amr2.nodes[t2]) for s2,r2,t2 in amr2.edges]
    if edge in amr1_edges and edge in amr2_edges:
        return 'green'
    return 'red'


def main():
    global amr_pairs
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    outfile = sys.argv[3]

    cr = JAMR_AMR_Reader()
    amrs1 = cr.load(file1, verbose=False, remove_wiki=True)
    amrs2 = cr.load(file2, verbose=False, remove_wiki=True)
    for amr1, amr2 in zip(amrs1, amrs2):
        amr2.id = amr1.id
        amr_pairs[amr1.id] = (amr1,amr2)
    output = style(assign_node_color=is_correct_node,
                   assign_edge_color=is_correct_edge)

    with open(outfile, 'w+', encoding='utf8') as f:
        f.write(output)


if __name__=='__main__':
    main()
