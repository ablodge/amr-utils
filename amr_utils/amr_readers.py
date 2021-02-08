import os
import re
import sys
import csv

import penman

from amr_utils.alignments import AMR_Alignment, write_to_json, load_from_json
from amr_utils.amr import AMR


class Matedata_Parser:

    token_range_re = re.compile('^(\d-\d|\d(,\d)+)$')

    def __init__(self):
        pass

    def get_token_range(self, string):
        if '-' in string:
            start = int(string.split('-')[0])
            end = int(string.split('-')[-1])
            return [i for i in range(start, end)]
        else:
            return [int(i) for i in string.split(',')]

    def readlines(self, lines):
        metadata = {}
        rows = [self.readline_(line) for line in lines.split('\n')]
        labels = {label for label,_ in rows}
        for label in labels:
            metadata[label] = [val for l,val in rows if label==l]
        return metadata

    def readline_(self, line):
        if not line.startswith('#'):
            label = 'snt'
            metadata = line.strip()
        elif line.startswith('# ::id'):
            label = 'id'
            metadata = line[len('# ::id '):].strip().split()[0]
        elif line.startswith("# ::tok"):
            label = 'tok'
            metadata = line[len('# ::tok '):].strip().split()
        elif line.startswith('# ::snt'):
            label = 'snt'
            metadata = line[len('# ::snt '):].strip()
        elif line.startswith('# ::alignments'):
            label = 'alignments'
            metadata = line[len('# ::alignments '):].strip().split()
        elif line.startswith('# ::'):
            label = line[len('# ::'):].split()[0]
            line = line[len(f'# ::{label} '):]
            rows = [row for row in csv.reader([line],  delimiter='\t', quotechar='"')]
            metadata = rows[0]
            for i,s in enumerate(metadata):
                if self.token_range_re.match(s):
                    metadata[i] = self.get_token_range(s)
        else:
            label = 'snt'
            metadata = line[len('# '):].strip()
        return label, metadata


from penman.model import Model


class TreePenmanModel(Model):
    def deinvert(self, triple):
        return triple

    def invert(self, triple):
        return triple


class PENMAN_Wrapper:

    def __init__(self, style='isi'):
        self.style = style

    def parse_amr(self, tokens, amr_string):
        amr = AMR(tokens=tokens)
        g = penman.decode(amr_string, model=TreePenmanModel())
        triples = g.triples() if callable(g.triples) else g.triples

        letter_labels = {}
        isi_labels = {g.top: '1'}
        isi_edge_labels = {}
        jamr_labels = {g.top: '0'}

        new_idx = 0

        isi_edge_idx = {g.top: 1}
        jamr_edge_idx = {g.top: 0}

        nodes = []
        attributes = []
        edges = []
        reentrancies = []

        for i,tr in enumerate(triples):
            s, r, t = tr
            # an amr node
            if r == ':instance':
                if reentrancies and edges[-1]==reentrancies[-1]:
                    s2,r2,t2 = edges[-1]
                    jamr_labels[t2] = jamr_labels[s2] + '.' + str(jamr_edge_idx[s2])
                    isi_labels[t2] = isi_labels[s2] + '.' + str(isi_edge_idx[s2])
                new_s = s
                while new_s in letter_labels:
                    new_idx += 1
                    new_s = f'x{new_idx}'
                letter_labels[s] = new_s
                nodes.append(tr)
            # an amr edge
            elif t not in letter_labels:
                if len(t) > 5 or not t[0].isalpha():
                    if tr in letter_labels:
                        isi_labels['ignore'] = isi_labels[s] + '.' + str(isi_edge_idx[s])
                        isi_edge_labels['ignore'] = isi_labels[s] + '.' + str(isi_edge_idx[s])+'.r'
                        isi_edge_idx[s] += 1
                        jamr_edge_idx[s] += 1
                        continue
                    # attribute
                    new_s = s
                    while new_s in letter_labels:
                        new_idx += 1
                        new_s = f'x{new_idx}'
                    letter_labels[tr] = new_s
                    jamr_labels[tr] = jamr_labels[s] + '.' + str(jamr_edge_idx[s])
                    isi_labels[tr] = isi_labels[s] + '.' + str(isi_edge_idx[s])
                    isi_edge_labels[tr] = isi_labels[s] + '.' + str(isi_edge_idx[s])+'.r'
                    isi_edge_idx[s] += 1
                    jamr_edge_idx[s] += 1
                    attributes.append(tr)
                else:
                    # edge
                    jamr_edge_idx[t] = 0
                    isi_edge_idx[t] = 1
                    jamr_labels[t] = jamr_labels[s] + '.' + str(jamr_edge_idx[s])
                    if i+1<len(triples) and triples[i+1][1]==':instance':
                        jamr_edge_idx[s] += 1
                    isi_labels[t] = isi_labels[s] + '.' + str(isi_edge_idx[s])
                    isi_edge_labels[tr] = isi_labels[s] + '.' + str(isi_edge_idx[s])+'.r'
                    isi_edge_idx[s] += 1
                    edges.append(tr)
            else:
                # reentrancy
                isi_edge_labels[tr] = isi_labels[s] + '.' + str(isi_edge_idx[s]) + '.r'
                isi_edge_idx[s] += 1
                edges.append(tr)
                reentrancies.append(tr)

        default_labels = letter_labels
        if self.style=='isi':
            default_labels = isi_labels
        elif self.style=='jamr':
            default_labels = jamr_labels

        amr.root = default_labels[g.top]
        edge_map = {}
        for tr in nodes:
            s,r,t = tr
            amr.nodes[default_labels[s]] = t
        for tr in attributes:
            s,r,t = tr
            if not r.startswith(':'): r = ':' + r
            amr.nodes[default_labels[tr]] = t
            amr.edges.append((default_labels[s], r, default_labels[tr]))
            edge_map[tr] = (default_labels[s], r, default_labels[tr])
        for tr in edges:
            s, r, t = tr
            if not r.startswith(':'): r = ':' + r
            amr.edges.append((default_labels[s], r, default_labels[t]))
            edge_map[tr] = (default_labels[s], r, default_labels[t])

        aligns = []
        for tr, epidata in g.epidata.items():
            for align in epidata:
                if 'Alignment' in type(align).__name__:
                    indices = align.indices
                    s,r,t = tr
                    if tr[1] == ':instance':
                        align = AMR_Alignment(type='isi', tokens=list(indices), nodes=[default_labels[s]])
                    elif len(t) > 5 or not t[0].isalpha():
                        align = AMR_Alignment(type='isi', tokens=list(indices), nodes=[default_labels[tr]])
                    else:
                        align = AMR_Alignment(type='isi', tokens=list(indices), edges=[edge_map[tr]])
                    aligns.append(align)

        letter_labels = {v: default_labels[k] for k,v in letter_labels.items()}
        jamr_labels = {v: default_labels[k] for k, v in jamr_labels.items()}
        isi_labels = {v: default_labels[k] if k!='ignore' else k for k, v in isi_labels.items()}
        isi_edge_labels = {v: edge_map[k] if k in edge_map else k for k, v in isi_edge_labels.items()}

        return amr, (letter_labels, jamr_labels, isi_labels, isi_edge_labels, aligns)


class AMR_Reader:

    def __init__(self, style='isi'):
        self.style=style

    def load(self, amr_file_name, remove_wiki=False, output_alignments=False):
        print('[amr]', 'Loading AMRs from file:', amr_file_name)
        amrs = []
        alignments = {}
        penman_wrapper = PENMAN_Wrapper(style=self.style)
        metadata_parser = Matedata_Parser()

        with open(amr_file_name, 'r', encoding='utf8') as f:
            sents = f.read().replace('\r', '').split('\n\n')
            amr_idx = 0
            for sent in sents:
                prefix = '\n'.join(line for line in sent.split('\n') if line.strip().startswith('#'))
                amr_string = ''.join(line for i, line in enumerate(sent.split('\n')) if not line.strip().startswith('#') and i>0).strip()
                amr_string = re.sub(' +', ' ', amr_string)
                if not amr_string: continue
                if not amr_string.startswith('(') or not amr_string.endswith(')'):
                    raise Exception('Could not parse AMR from: ', amr_string)
                metadata = metadata_parser.readlines(prefix)
                tokens = metadata['tok'][0] if 'tok' in metadata else metadata['snt'][0].split()
                tokens = self._clean_tokens(tokens)
                if 'node' in metadata and False:
                    amr, aligns = self._parse_amr_from_metadata(tokens, metadata)
                    amr.id = metadata['id'][0]
                    if output_alignments:
                        alignments[amr.id] = aligns
                else:
                    amr, other_stuff = penman_wrapper.parse_amr(tokens, amr_string)
                    if 'id' in amr.id:
                        amr.id = metadata['id'][0]
                    else:
                        amr.id = str(amr_idx)
                    if output_alignments:
                        alignments[amr.id] = []
                        if 'alignments' in metadata:
                            aligns = metadata['alignments'][0]
                            if any('|' in a for a in aligns):
                                jamr_labels = other_stuff[1]
                                alignments[amr.id] = self._parse_jamr_alignments(amr, amr_file_name, aligns, jamr_labels, metadata_parser)
                            else:
                                isi_labels, isi_edge_labels = other_stuff[2:4]
                                alignments[amr.id] = self._parse_isi_alignments(amr, amr_file_name, aligns, isi_labels, isi_edge_labels)
                        else:
                            aligns = other_stuff[4]
                            alignments[amr.id] = aligns
                amrs.append(amr)
                amr_idx += 1
        if remove_wiki:
            for amr in amrs:
                wiki_nodes = []
                wiki_edges = []
                for s, r, t in amr.edges.copy():
                    if r == ':wiki':
                        amr.edges.remove((s, r, t))
                        del amr.nodes[t]
                        wiki_nodes.append(t)
                        wiki_edges.append((s,r,t))
                for align in alignments:
                    for n in wiki_nodes:
                        if n in align.nodes:
                            align.nodes.remove(n)
                    for e in wiki_edges:
                        if e in align.edges:
                            align.edges.remove(e)
        if output_alignments:
            return amrs, alignments
        return amrs

    def load_from_dir(self, dir, remove_wiki=False, output_alignments=False):
        all_amrs = []
        all_alignments = {}

        taken_ids = set()
        for filename in os.listdir(dir):
            if filename.endswith('.txt'):
                print(filename)
                file = os.path.join(dir, filename)
                amrs, aligns = self.load(file, output_alignments=True, remove_wiki=remove_wiki)
                for amr in amrs:
                    if amr.id.isdigit():
                        old_id = amr.id
                        amr.id = filename+':'+old_id
                        aligns[amr.id] = aligns[old_id]
                        del aligns[old_id]
                for amr in amrs:
                    if amr.id in taken_ids:
                        old_id = amr.id
                        amr.id += '#2'
                        if old_id in aligns:
                            aligns[amr.id] = aligns[old_id]
                            del aligns[old_id]
                    taken_ids.add(amr.id)
                all_amrs.extend(amrs)
                all_alignments.update(aligns)
        if output_alignments:
            return all_amrs, all_alignments
        return all_amrs

    @staticmethod
    def write_to_file(output_file, amrs):
        with open(output_file, 'w+', encoding='utf8') as f:
            for amr in amrs:
                f.write(amr.jamr_string())

    @staticmethod
    def load_alignments_from_json(json_file, amrs):
        return load_from_json(json_file, amrs=amrs)

    @staticmethod
    def write_alignments_to_json(json_file, alignments):
        write_to_json(json_file, alignments)

    @staticmethod
    def _parse_jamr_alignments(amr, amr_file, aligns, jamr_labels, metadata_parser):
        aligns = [(metadata_parser.get_token_range(a.split('|')[0]), a.split('|')[-1].split('+')) for a in aligns if '|' in a]

        alignments = []
        for toks, components in aligns:
            if not all(n in jamr_labels for n in components) or any(t>=len(amr.tokens) for t in toks):
                raise Exception('Could not parse alignment:', amr_file, amr.id, toks, components)
            nodes = [jamr_labels[n] for n in components]
            new_align = AMR_Alignment(type='jamr', tokens=toks, nodes=nodes)
            alignments.append(new_align)
        return alignments

    @staticmethod
    def _parse_isi_alignments(amr, amr_file, aligns, isi_labels, isi_edge_labels):
        aligns = [(int(a.split('-')[0]), a.split('-')[-1]) for a in aligns if '-' in a]

        alignments = []
        xml_offset = 1 if amr.tokens[0].startswith('<') and amr.tokens[0].endswith('>') else 0
        if any(t + xml_offset >= len(amr.tokens) for t, n in aligns):
            xml_offset = 0

        for tok, component in aligns:
            tok += xml_offset
            nodes = []
            edges = []
            if component.replace('.r', '') in isi_labels:
                # node or attribute
                n = isi_labels[component.replace('.r', '')]
                if n=='ignore': continue
                nodes.append(n)
                if n not in amr.nodes:
                    raise Exception('Could not parse alignment:', amr_file, amr.id, tok, component)
            elif not component.endswith('.r') and component not in isi_labels and component + '.r' in isi_edge_labels:
                # reentrancy
                e = isi_edge_labels[component + '.r']
                edges.append(e)
                if e not in amr.edges:
                    raise Exception('Could not parse alignment:', amr_file, amr.id, tok, component)
            elif component.endswith('.r'):
                # edge
                e = isi_edge_labels[component]
                if e == 'ignore': continue
                edges.append(e)
                if e not in amr.edges:
                    raise Exception('Could not parse alignment:', amr_file, amr.id, tok, component)
            elif component == '0.r':
                nodes.append(amr.root)
            else:
                raise Exception('Could not parse alignment:', amr_file, amr.id, tok, component)
            if tok >= len(amr.tokens):
                raise Exception('Could not parse alignment:', amr_file, amr.id, tok, component)
            new_align = AMR_Alignment(type='isi', tokens=[tok], nodes=nodes, edges=edges)
            alignments.append(new_align)
        return alignments

    @staticmethod
    def _parse_amr_from_metadata(tokens, metadata):
        '''
           Metadata format is ...
           # ::id sentence id
           # ::tok tokens...
           # ::node node_id node alignments
           # ::root root_id root
           # ::edge src label trg src_id trg_id alignments
           amr graph
           '''
        amr = AMR(tokens)
        if 'id' in metadata:
            amr.id = metadata['id'][0]
        alignments = []

        nodes = metadata['node']
        edges = metadata['edge'] if 'edge'in metadata else []
        root = metadata['root'][0]
        amr.root = root[0]
        for data in nodes:
            n, label = data[:2]
            if len(data)>2:
                toks = data[2]
                alignments.append(AMR_Alignment(type='jamr', nodes=[n], tokens=toks))
            amr.nodes[n] = label
        for data in edges:
            _, r, _, s, t = data[:5]
            if len(data)>5:
                toks = data[5]
                alignments.append(AMR_Alignment(type='jamr', edges=[(s,r,t)], tokens=toks))
            if not r.startswith(':'): r = ':'+r
            amr.edges.append((s,r,t))
        return amr, alignments

    @staticmethod
    def _clean_tokens(tokens):
        line = ' '.join(tokens)
        if '<' in line and '>' in line:
            tokens_reformat = []
            is_xml = False
            for i, tok in enumerate(tokens):
                if is_xml:
                    tokens_reformat[-1] += '_' + tok
                    if '>' in tok:
                        is_xml = False
                else:
                    tokens_reformat.append(tok)
                    if tok.startswith('<') and not '>' in tok:
                        if len(tok) > 1 and (tok[1].isalpha() or tok[1] == '/'):
                            if i + 1 < len(tokens) and '=' in tokens[i + 1]:
                                is_xml = True
            tokens = tokens_reformat
        return tokens



def main():
    dir = sys.argv[1]
    output_file = sys.argv[2]

    reader = AMR_Reader()
    amrs, alignments = reader.load_from_dir(dir, output_alignments=True)

    reader.write_to_file(output_file, amrs)
    reader.write_alignments_to_json(output_file.replace('.txt','.alignments.json'), alignments)



if __name__ == '__main__':
    main()
