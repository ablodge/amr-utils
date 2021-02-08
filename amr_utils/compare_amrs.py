import sys

from amr_readers import AMR_Reader
from style import HTML_AMR

from graph_utils import simple_node_map

amr_pairs = {}
node_maps = {}
version = 1

def style(assign_node_color=None, assign_node_desc=None, assign_edge_color=None, assign_edge_desc=None,
          assign_token_color=None, assign_token_desc=None, limit=None):
    global version
    output = '<!DOCTYPE html>\n'
    output += '<html>\n'
    output += '<style>\n'
    output += HTML_AMR.style_sheet()
    output += '</style>\n\n'
    output += '<body>\n'
    i = 0
    for id  in amr_pairs:
        amr1, amr2 = amr_pairs[id]
        output += '1:\n'
        version = 1
        output += HTML_AMR.html(amr1,
                                assign_node_color, assign_node_desc,
                                assign_edge_color, assign_edge_desc,
                                assign_token_color, assign_token_desc)
        output += '2:\n'
        version = 2
        output += HTML_AMR.html(amr2,
                                assign_node_color, assign_node_desc,
                                assign_edge_color, assign_edge_desc,
                                assign_token_color, assign_token_desc)
        i+=1
        if limit and i>limit:
            break
    output += '</body>\n'
    output += '</html>\n'
    return output


def is_correct_node(amr, n):
    amr1, amr2 = amr_pairs[amr.id]
    if version==1:
        other_amr = amr2
        node_map = node_maps[amr.id][0]
    else:
        other_amr = amr1
        node_map = node_maps[amr.id][1]
    if amr.nodes[n] == other_amr.nodes[node_map[n]]:
        return 'green'
    return 'red'

def is_correct_edge(amr, e):
    amr1, amr2 = amr_pairs[amr.id]
    s,r,t = e
    if version == 1:
        other_amr = amr2
        node_map = node_maps[amr.id][0]
    else:
        other_amr = amr1
        node_map = node_maps[amr.id][1]
    if (node_map[s],r,node_map[t]) in other_amr.edges:
        return 'green'
    return 'red'


def is_correct_node_desc(amr, n):
    amr1, amr2 = amr_pairs[amr.id]
    if version == 1:
        other_amr = amr2
        node_map = node_maps[amr.id][0]
    else:
        other_amr = amr1
        node_map = node_maps[amr.id][1]
    if amr.nodes[n] == other_amr.nodes[node_map[n]]:
        return ''
    return f'{amr.nodes[n]} != {other_amr.nodes[node_map[n]]}'

def is_correct_edge_desc(amr, e):
    amr1, amr2 = amr_pairs[amr.id]
    s, r, t = e
    if version == 1:
        other_amr = amr2
        node_map = node_maps[amr.id][0]
    else:
        other_amr = amr1
        node_map = node_maps[amr.id][1]
    if (node_map[s], r, node_map[t]) in other_amr.edges:
        return ''
    return f'({other_amr.nodes[node_map[s]]} {r} {other_amr.nodes[node_map[t]]}) not in other AMR'

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
    for amr1, amr2 in zip(amrs1, amrs2):
        amr1.id = amr2.id
        node_maps[amr1.id] = (simple_node_map(amr1, amr2), simple_node_map(amr2, amr1))
        amr_pairs[amr1.id] = (amr1,amr2)
    output = style(assign_node_color=is_correct_node,
                   assign_node_desc=is_correct_node_desc,
                   assign_edge_color=is_correct_edge,
                   assign_edge_desc=is_correct_edge_desc,
                   limit=2000
                  )

    with open(outfile, 'w+', encoding='utf8') as f:
        f.write(output)


if __name__=='__main__':
    main()
