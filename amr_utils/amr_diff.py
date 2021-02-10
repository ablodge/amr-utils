import sys

from amr_readers import AMR_Reader
from style import HTML_AMR


from amr_utils.graph_utils import get_node_alignment

phase = 1

def style(amr_pairs, other_args, assign_node_color=None, assign_node_desc=None, assign_edge_color=None, assign_edge_desc=None,
          assign_token_color=None, assign_token_desc=None, limit=None):
    global phase
    output = '<!DOCTYPE html>\n'
    output += '<html>\n'
    output += '<style>\n'
    output += HTML_AMR.style_sheet()
    output += '</style>\n\n'
    output += '<body>\n'
    i = 0
    for id in amr_pairs:
        amr1, amr2 = amr_pairs[id]
        prec, rec, f1 = other_args[id][-3:]
        output += f'AMR 1:\n'
        phase = 1
        output += HTML_AMR.html(amr1,
                                assign_node_color, assign_node_desc,
                                assign_edge_color, assign_edge_desc,
                                assign_token_color, assign_token_desc,
                                other_args)
        output += 'AMR 2:\n'
        phase = 2
        output += HTML_AMR.html(amr2,
                                assign_node_color, assign_node_desc,
                                assign_edge_color, assign_edge_desc,
                                assign_token_color, assign_token_desc,
                                other_args)
        output += f'SMATCH: precision {100*prec:.1f} recall {100*rec:.1f} f1 {100*f1:.1f}\n'
        output += '<hr>\n'
        i+=1
        if limit and i>limit:
            break
    output += '</body>\n'
    output += '</html>\n'
    return output


def is_correct_node(amr, n, other_args):
    amr1, amr2, map1, map2 = other_args[amr.id][:4]
    if phase==1:
        other_amr = amr2
        node_map = map1
    else:
        other_amr = amr1
        node_map = map2
    if amr.nodes[n] == other_amr.nodes[node_map[n]]:
        return ''
    return 'red'


def is_correct_edge(amr, e, other_args=None):
    amr1, amr2, map1, map2 = other_args[amr.id][:4]
    s,r,t = e
    if phase == 1:
        other_amr = amr2
        node_map = map1
    else:
        other_amr = amr1
        node_map = map2
    if (node_map[s],r,node_map[t]) in other_amr.edges:
        return ''
    return 'red'


def is_correct_node_desc(amr, n, other_args=None):
    amr1, amr2, map1, map2 = other_args[amr.id][:4]
    if phase == 1:
        other_amr = amr2
        node_map = map1
    else:
        other_amr = amr1
        node_map = map2
    if amr.nodes[n] == other_amr.nodes[node_map[n]]:
        return ''
    return f'{amr.nodes[n]} != {other_amr.nodes[node_map[n]]}'


def is_correct_edge_desc(amr, e, other_args=None):
    amr1, amr2, map1, map2 = other_args[amr.id][:4]
    s, r, t = e
    if phase == 1:
        other_amr = amr2
        node_map = map1
    else:
        other_amr = amr1
        node_map = map2
    if (node_map[s], r, node_map[t]) in other_amr.edges:
        return ''
    # attribute
    if not amr.nodes[t][0].isalpha() or amr.nodes[t] in ['imperative', 'expressive', 'interrogative']:
        return f'No corresponding attribute {other_amr.nodes[node_map[s]]} {r} {amr.nodes[t]}'
    # relation
    return f'No corresponding relation {other_amr.nodes[node_map[s]]} {r} {other_amr.nodes[node_map[t]]}'

def main():
    global amr_pairs
    import argparse

    # parser = argparse.ArgumentParser(description='Visually compare two AMR files')
    # parser.add_argument('files', type=str, nargs=2, required=True,
    #                     help='input files (AMRs in JAMR format)')
    # parser.add_argument('output', type=str, required=True,
    #                     help='output file (html)')
    # args = parser.parse_args()

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    outfile = sys.argv[3]

    reader = AMR_Reader()
    amrs1 = reader.load(file1, remove_wiki=True)
    amrs2 = reader.load(file2, remove_wiki=True)

    other_args = {}
    amr_pairs = {}
    for amr1, amr2 in zip(amrs1, amrs2):
        map1, prec, rec, f1 = get_node_alignment(amr1, amr2)
        map2, _, _, _ = get_node_alignment(amr2, amr1)
        amr2.id = amr1.id
        other_args[amr1.id] = (amr1, amr2, map1, map2, prec, rec, f1)
        amr_pairs[amr1.id] = (amr1, amr2)
    output = style(amr_pairs,
                   other_args,
                   assign_node_color=is_correct_node,
                   assign_node_desc=is_correct_node_desc,
                   assign_edge_color=is_correct_edge,
                   assign_edge_desc=is_correct_edge_desc,
                   limit=2000
                  )

    with open(outfile, 'w+', encoding='utf8') as f:
        f.write(output)


if __name__=='__main__':
    main()
