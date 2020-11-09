import json
import os
import re
import sys
from collections import Counter

import penman

from amr_utils.alignments import AMR_Alignment
from amr_utils.amr import AMR

class JAMR_AMR_Reader:

    def __init__(self):
        pass

    '''
    Reads AMR Graphs file in JAMR format. If Training==true, it is reading training data set and it will affect the dictionaries.

    JAMR format is ...
    # ::id sentence id
    # ::tok tokens...
    # ::node node_id node alignments
    # ::root root_id root
    # ::edge src label trg src_id trg_id alignments
    amr graph
    '''

    def load(self, amr_file_name, training=True, verbose=False, remove_wiki=False, output_alignments=False):
        print('[amr]', 'Loading AMRs from file:', amr_file_name)

        amr = AMR()
        amrs = [amr]
        alignments = []
        alignments_json = {}

        with open(amr_file_name, encoding='utf8') as f:
            for line in f:
                # empty line, prepare to read next amr
                if not line.strip():
                    if verbose:
                        print(amr)
                    if alignments:
                        alignments_json[amr.id] = [align.to_json(amr) for align in alignments]
                    amr = AMR()
                    amrs.append(amr)
                    alignments = []
                # amr id
                elif line.startswith('# ::id'):
                    amr.id = line.split()[2]
                elif line.startswith('# ::notes'):
                    amr.notes = line.split()[2]
                # amr tokens
                elif line.startswith("# ::tok"):
                    toks = line[len('# ::tok '):]
                    amr.tokens = toks.split()
                # amr root
                elif line.startswith("# ::root"):
                    root = line.split("\t")[1].strip()
                    amr.root = root
                # an amr node
                elif line.startswith("# ::node"):
                    node_id = ''
                    in_quotes = False
                    quote_offset = 0
                    for col, val in enumerate(line.split("\t")):
                        val = val.strip()
                        if val.startswith('"'):
                            in_quotes = True
                        if val.endswith('"'):
                            in_quotes = False
                        # node id
                        if col == 1:
                            node_id = val
                        # node label
                        elif col == 2 + (quote_offset):
                            amr.nodes[node_id] = val
                        # alignment
                        elif col == 3 + (quote_offset):
                            if val.strip():
                                val = val.split(':')
                                word_idxs = [t for t in range(start=int(val[0]), stop=int(val[1]))]
                                align = AMR_Alignment(tokens=word_idxs, nodes=[node_id])
                                alignments.append(align)
                        if in_quotes:
                            quote_offset += 1
                # an amr edge
                elif line.startswith("# ::edge"):
                    s,r,t = '', '', ''
                    in_quotes = False
                    quote_offset = 0
                    for col, val in enumerate(line.split("\t")):
                        val = val.strip()
                        if val.startswith('"'):
                            in_quotes = True
                        if val.endswith('"'):
                            in_quotes = False
                        # edge label
                        if col == 2 + (quote_offset):
                            r = ':'+ val
                        # edge source id
                        elif col == 4 + (quote_offset):
                            s = val
                        # edge target id
                        elif col == 5 + (quote_offset):
                            t = val
                        # alignment
                        elif col == 6 + (quote_offset):
                            if val.strip():
                                val = val.split(':')
                                word_idxs = [t for t in range(start=int(val[0]), stop=int(val[1]))]
                                align = AMR_Alignment(tokens=word_idxs, edges=[(s,r,t)])
                                alignments.append(align)
                        if in_quotes:
                            quote_offset += 1
                    amr.edges.append((s,r,t))

        if len(amr.tokens) == 0:
            amrs.pop()
        if remove_wiki:
            for amr in amrs:
                wiki_nodes = []
                for s,r,t in amr.edges.copy():
                    if r==':wiki':
                        amr.edges.remove((s,r,t))
                        del amr.nodes[t]
                        wiki_nodes.append(t)
                for align in alignments:
                    for n in wiki_nodes:
                        if n in align.nodes:
                            align.nodes.remove(n)
        print('[amr]', "Number of sentences: " + str(len(amrs)))
        if output_alignments:
            return amrs, alignments_json
        else:
            return amrs

from penman.model import Model

class TreePenmanModel(Model):
    def deinvert(self, triple):
        return triple

    def invert(self, triple):
        return triple

class LDC_AMR_Reader:

    START_ID = '1'

    def __init__(self):
        self.alignment_style = 'isi'
        pass

    def parse_tokens(self, line):
        line = line[len('# ::tok '):]
        tokens = line.split()
        if '<' in line and '>' in line:
            tokens_reformat = []
            is_xml = False
            for i,tok in enumerate(tokens):
                if is_xml:
                    tokens_reformat[-1] += '_'+tok
                    if '>'in tok:
                        is_xml = False
                else:
                    tokens_reformat.append(tok)
                    if tok.startswith('<') and not '>' in tok:
                        if len(tok)>1 and (tok[1].isalpha() or tok[1] =='/'):
                            if i+1<len(tokens) and '=' in tokens[i+1]:
                                is_xml = True
            tokens = tokens_reformat
        return tokens

    def parse_amr_(self, tokens, amr_string):
        amr = AMR(tokens=tokens)

        g = penman.decode(amr_string, model=TreePenmanModel())
        triples = g.triples() if callable(g.triples) else g.triples
        node_map = {}
        new_idx = 0

        rename_nodes = {g.top:self.START_ID}
        edge_idx = {g.top:0}
        amr.root = self.START_ID
        last_node_id = self.START_ID
        for tr in triples:
            s, r, t = tr
            if not r.startswith(':'):
                r = ':'+r
            # an amr node
            if r == ':instance':
                if last_node_id != rename_nodes[s]:
                    old_node = rename_nodes[s]
                    new_node = last_node_id
                    rename_nodes[s] = new_node
                    for i,e in enumerate(amr.edges):
                        s2,r,t2 = e
                        if s2==old_node:
                            amr.edges[i] = (new_node,r,t2)
                        if t2==old_node:
                            amr.edges[i] = (s2,r,new_node)
                new_s = rename_nodes[s]
                node_map[s] = new_s
                s = new_s
                amr.nodes[s] = t
                if s.startswith('x'):
                    new_idx+=1
            # an amr edge
            else:
                parent, child = s,t
                if child not in rename_nodes:
                    if len(t)>5 or not t[0].isalpha():
                        # attribute
                        edge_idx[parent] += 1
                        rename_nodes[tr] = rename_nodes[parent] + '.' + str(edge_idx[parent])
                        new_t = rename_nodes[tr]
                        amr.nodes[new_t] = str(t)
                        node_map[tr] = new_t
                    else:
                        # edge
                        edge_idx[child] = 0
                        edge_idx[parent] += 1
                        rename_nodes[child] = rename_nodes[parent]+'.'+str(edge_idx[parent])
                        last_node_id = rename_nodes[child]
                else:
                    # reentrancy
                    edge_idx[parent] += 1
                    last_node_id = rename_nodes[parent] + '.' + str(edge_idx[parent])
                new_s = rename_nodes[s]
                new_t = rename_nodes[t] if t in rename_nodes else rename_nodes[tr]
                amr.edges.append((new_s,r,new_t))
        return amr, triples, node_map

    def load(self, amr_file_name, training=True, verbose=False, remove_wiki=False, output_alignments=False, alignment_style='isi'):
        self.alignment_style = alignment_style
        print('[amr]', 'Loading AMRs from file:', amr_file_name)
        amrs = []
        alignments_all = {}
        # alignments_json = {}

        with open(amr_file_name, 'r', encoding='utf8') as f:
            sents = f.read().replace('\r','').split('\n\n')
            for sent in sents:
                prefix = '\n'.join(line for line in sent.split('\n') if line.strip().startswith('#'))
                amr_string = ''.join(line for line in sent.split('\n') if not line.strip().startswith('#'))
                amr_string = re.sub(' +',' ',amr_string)

                tokens = []
                id = None
                align_string = None
                for line in prefix.split('\n'):
                    if line.startswith('# ::tok '):
                        tokens = self.parse_tokens(line)
                    elif line.startswith('# ::id'):
                        id = line.split()[2]
                    elif line.startswith('# ::alignments '):
                        align_string = line
                if amr_string.strip():
                    amr, triples, node_map = self.parse_amr_(tokens, amr_string)
                    if self.alignment_style=='isi':
                        labels = isi_style_labels(triples)
                    elif self.alignment_style=='jamr':
                        labels = jamr_style_labels(triples, node_map)
                    else:
                        raise Exception(f'Unrecognized alignment style {self.alignment_style} should be "isi" or "jamr" instead')
                    amr.id = id
                    amrs.append(amr)
                    if verbose:
                        print(amr)
                    if align_string:
                        if self.alignment_style == 'isi':
                            alignments = parse_isi_alignments(amr, line, labels)
                        elif self.alignment_style == 'jamr':
                            alignments = parse_jamr_alignments(amr, line, labels)
                        # alignments_json[id] = [align.to_json(amr) for align in alignments]
                        alignments_all[id] = alignments
        if remove_wiki:
            for amr in amrs:
                wiki_nodes = []
                for s,r,t in amr.edges.copy():
                    if r==':wiki':
                        amr.edges.remove((s,r,t))
                        del amr.nodes[t]
                        wiki_nodes.append(t)
                if amr.id in alignments_all:
                    for align in alignments_all[amr.id]:
                        for n in wiki_nodes:
                            if n in align.nodes:
                                align.nodes.remove(n)
        print('[amr]', "Number of sentences: " + str(len(amrs)))

        if output_alignments:
            return amrs, alignments_all
        else:
            return amrs


def isi_style_labels(triples):
    edge_labels = {}

    root = triples[0][0]

    rename_nodes = {root: '1'}
    edge_idx = Counter()
    last_node_id = '1'

    for tr in triples:
        s, r, t = tr
        if not r.startswith(':'):
            r = ':' + r
        # an amr node
        if r == ':instance':
            if last_node_id != rename_nodes[s]:
                # new node
                old_node = rename_nodes[s]
                new_node = last_node_id
                rename_nodes[s] = new_node
                for edge_name in edge_labels:
                    s2, r, t2 = edge_labels[edge_name]
                    if s2 == old_node:
                        edge_labels[edge_name] = (new_node, r, t2)
                    if t2 == old_node:
                        edge_labels[edge_name] = (s2, r, new_node)
        # an amr edge
        else:
            parent, child = s, t
            # normal edge
            if child not in rename_nodes:
                if len(t) > 5 or not t[0].isalpha():
                    # attribute
                    edge_idx[parent] += 1
                    rename_nodes[tr] = rename_nodes[parent] + '.' + str(edge_idx[parent])
                    edge_name = rename_nodes[tr] + '.r'
                else:
                    # edge
                    edge_idx[child] = 0
                    edge_idx[parent] += 1
                    rename_nodes[child] = rename_nodes[parent] + '.' + str(edge_idx[parent])
                    edge_name = rename_nodes[child] + '.r'
                    last_node_id = rename_nodes[child]
            # reentrancy
            else:
                edge_idx[parent] += 1
                last_node_id = rename_nodes[parent] + '.' + str(edge_idx[parent])
                edge_name = rename_nodes[parent] + '.' + str(edge_idx[parent]) + '.r'
            # if s != amr.root and not any(s == t2 for s2, r2, t2 in amr.edges):
            #     amr.edges[-1] = (t, r + '-of', s)
            edge_labels[edge_name] = (rename_nodes[parent], r, rename_nodes[child] if child in rename_nodes else rename_nodes[tr])
    return edge_labels


def jamr_style_labels(triples, node_map):
    node_labels = {}

    root = triples[0][0]

    rename_nodes = {root: '0'}
    edge_idx = Counter()
    last_node_id = '0'
    last_parent = None
    last_child = None
    found_new_id = False

    for tr in triples:
        s, r, t = tr
        if not r.startswith(':'):
            r = ':' + r
        # an amr node
        if r == ':instance':
            if last_node_id != rename_nodes[s]:
                new_node = last_node_id
                rename_nodes[s] = new_node
            old_s = node_map[s]
            new_s = rename_nodes[s]
            node_labels[new_s] = old_s
            found_new_id = False
        # an amr edge
        else:
            if found_new_id:
                del rename_nodes[last_child]
                edge_idx[last_parent] -= 1
            parent, child = s, t
            if child not in rename_nodes:
                if len(t) > 5 or not t[0].isalpha():
                    # attribute
                    rename_nodes[tr] = rename_nodes[parent] + '.' + str(edge_idx[parent])
                    edge_idx[parent] += 1
                    old_t = node_map[tr]
                    new_t = rename_nodes[tr]
                    node_labels[new_t] = old_t
                    found_new_id = False
                else:
                    # edge
                    edge_idx[child] = 0
                    rename_nodes[child] = rename_nodes[parent] + '.' + str(edge_idx[parent])
                    edge_idx[parent] += 1
                    last_node_id = rename_nodes[child]
                    last_parent = parent
                    last_child = child
                    found_new_id = True
            else:
                # reentrancy
                last_node_id = rename_nodes[parent] + '.' + str(edge_idx[parent])
                # edge_idx[parent] += 1
                found_new_id = False
    return node_labels


def _num_range(s):
    if '-' in s:
        start, end = s.split('-')
        return [n for n in range(int(start), int(end))]
    return [int(s)]

def parse_jamr_alignments(amr, line, node_labels):

    line = line[len('# ::alignments '):]
    if '::annotator' in line:
        line = line[:line.index('::annotator')]
    alignments_pairs = line.split()
    alignments_pairs = [s for s in alignments_pairs if '*' not in s]
    alignments_pairs = [a.split('|') for a in alignments_pairs]
    alignments_pairs = [(_num_range(a[0]), a[1].split('+')) for a in alignments_pairs]
    alignments = []
    xml_offset = 1 if amr.tokens[0].startswith('<') and amr.tokens[0].endswith('>') else 0
    if any(t[0] + xml_offset >= len(amr.tokens) for t, n in alignments_pairs):
        xml_offset = 0

    for toks, labels in alignments_pairs:
        tokens = [tok + xml_offset for tok in toks]
        nodes = []
        edges = []
        for label in labels:
            if label not in node_labels:
                raise Exception()
            node = node_labels[label]
            if node not in amr.nodes:
                raise Exception('Missing node:', node)
            nodes.append(node)
        align = AMR_Alignment(type='jamr', nodes=nodes, edges=edges, tokens=tokens)
        alignments.append(align)
    return alignments

def parse_isi_alignments(amr, line, edge_labels):

    line = line[len('# ::alignments '):]
    alignments_pairs = line.split()
    alignments_pairs = [s for s in alignments_pairs if '*' not in s]
    alignments_pairs = [a.split('-') for a in alignments_pairs]
    alignments_pairs = [(int(a[0]), a[1]) for a in alignments_pairs]
    alignments = []
    xml_offset = 1 if amr.tokens[0].startswith('<') and amr.tokens[0].endswith('>') else 0
    if any(t + xml_offset >= len(amr.tokens) for t, n in alignments_pairs):
        xml_offset = 0

    for tok, label in alignments_pairs:
        tokens = [tok + xml_offset]
        nodes = []
        edges = []
        type = 'isi'
        if not label.endswith('.r'):
            if label in amr.nodes:
                nodes.append(label)
            else:
                type = 'reentrancy'
                edges.append(edge_labels[label+'.r'])
        else:
            if label!='0.r':
                edges.append(edge_labels[label])
            else:
                type = 'root'
                nodes.append(amr.root)
        if type=='isi':
            align = AMR_Alignment(type=type, nodes=nodes, edges=edges, tokens=tokens)
            alignments.append(align)
    return alignments


class Graph_AMR_Reader:

    def __init__(self):
        pass

    def parse_amr_(self, tokens, amr_string):
        amr = AMR(tokens=tokens)

        g = penman.decode(amr_string, model=TreePenmanModel())
        triples = g.triples() if callable(g.triples) else g.triples
        node_map = {}
        new_idx = 0

        rename_nodes = {g.top:g.top}
        edge_idx = {g.top:0}
        amr.root = g.top
        last_node_id = None
        for tr in triples:
            s, r, t = tr
            if not r.startswith(':'):
                r = ':'+r
            # an amr node
            if r == ':instance':
                if last_node_id != rename_nodes[s]:
                    old_node = rename_nodes[s]
                    new_node = s
                    rename_nodes[s] = new_node
                    for i,e in enumerate(amr.edges):
                        s2,r,t2 = e
                        if s2==old_node:
                            amr.edges[i] = (new_node,r,t2)
                        if t2==old_node:
                            amr.edges[i] = (s2,r,new_node)
                new_s = rename_nodes[s]
                node_map[s] = new_s
                s = new_s
                amr.nodes[s] = t
                if s.startswith('x'):
                    new_idx+=1
            # an amr edge
            else:
                parent, child = s,t
                if child not in rename_nodes:
                    if len(t)>5 or not t[0].isalpha():
                        # attribute
                        edge_idx[parent] += 1
                        letter = 'x'
                        taken = set(rename_nodes.values())
                        if letter in taken:
                            i = 2
                            while f'{letter}{i}' in taken:
                                i+=1
                            letter = f'{letter}{i}'
                        rename_nodes[tr] = letter
                        new_t = rename_nodes[tr]
                        amr.nodes[new_t] = str(t)
                        node_map[tr] = new_t
                    else:
                        # edge
                        edge_idx[child] = 0
                        edge_idx[parent] += 1
                        rename_nodes[child] = child
                        last_node_id = rename_nodes[child]
                else:
                    # reentrancy
                    edge_idx[parent] += 1
                    last_node_id = child
                new_s = rename_nodes[s]
                new_t = rename_nodes[t] if t in rename_nodes else rename_nodes[tr]
                amr.edges.append((new_s,r,new_t))
        return amr, triples, node_map

    def load(self, amr_file_name, verbose=False, remove_wiki=False):
        print('[amr]', 'Loading AMRs from file:', amr_file_name)
        amrs = []

        with open(amr_file_name, 'r', encoding='utf8') as f:
            sents = f.read().replace('\r','').split('\n\n')
            for sent in sents:
                prefix = '\n'.join(line for line in sent.split('\n') if line.strip().startswith('#'))
                amr_string = ''.join(line for line in sent.split('\n') if not line.strip().startswith('#'))
                amr_string = re.sub(' +',' ',amr_string)

                tokens = []
                id = None
                for line in prefix.split('\n'):
                    if line.startswith('# ::tok '):
                        tokens = list(line.split()[2:])
                    elif line.startswith('# ::id'):
                        id = line.split()[2]
                if amr_string.strip():
                    amr, triples, node_map = self.parse_amr_(tokens, amr_string)
                    amr.id = id
                    amrs.append(amr)
                    if verbose:
                        print(amr)
        if remove_wiki:
            for amr in amrs:
                wiki_nodes = []
                for s,r,t in amr.edges.copy():
                    if r==':wiki':
                        amr.edges.remove((s,r,t))
                        del amr.nodes[t]
                        wiki_nodes.append(t)
        print('[amr]', "Number of sentences: " + str(len(amrs)))

        return amrs


def main():
    # import argparse
    #
    # parser = argparse.ArgumentParser(description='Read AMRs from file')
    # parser.add_argument('file', type=str, required=True,
    #                     help='input AMR file (default is JAMR format)')
    # parser.add_argument('--graph', action='store_true', help='read AMRs from graph strings')
    #
    # args = parser.parse_args()
    dir = sys.argv[1]
    output_file = sys.argv[2]

    cr = LDC_AMR_Reader()
    dir_amrs = []
    alignments = {}

    taken_ids = set()
    for filename in os.listdir(dir):
        if filename.endswith('.txt'):
            print(filename)
            file = os.path.join(dir, filename)
            amrs, aligns = cr.load(file, verbose=False, output_alignments=True)
            for amr in amrs:
                if amr.id in taken_ids:
                    old_id = amr.id
                    amr.id += '#2'
                    if old_id in aligns:
                        aligns[amr.id] = aligns[old_id]
                        del aligns[old_id]
                taken_ids.add(amr.id)
            dir_amrs.extend(amrs)
            alignments.update(aligns)

    with open(output_file, 'w+', encoding='utf8') as f:
        for amr in dir_amrs:
            f.write(amr.jamr_string())

    amrs = {}
    for amr in dir_amrs:
        amrs[amr.id] = amr
    if len(amrs)!=len(dir_amrs):
        raise Exception("Cannot parse multiple AMRs with the same id")
    filename = output_file.replace('.txt','')
    type = None
    for k in alignments:
        if not type and alignments[k]:
            type = alignments[k][0].type
        alignments[k] = [a.to_json(amrs[k]) for a in alignments[k]]
    align_file = filename+f'.{type}_alignments.json'
    with open(align_file, 'w+', encoding='utf8') as f:
        json.dump(alignments, f)



if __name__ == '__main__':
    main()
