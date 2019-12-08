
from amr import AMR, AMR_Alignment

class JAMR_AMR_Reader:

    special_tokens = []

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

    def load(self, amr_file_name, training=True, verbose=False, remove_wiki=False):
        print('[amr]', 'Start reading data')

        amr = AMR()
        amrs = [amr]

        with open(amr_file_name, encoding='utf8') as f:
            for line in f:
                # empty line, prepare to read next amr
                if not line.strip():
                    if verbose:
                        print(amr)
                    amr = AMR()
                    amrs.append(amr)
                # amr id
                elif line.startswith('# ::id'):
                    amr.id = line.split()[2]
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
                                word_idxs = AMR_Alignment.read_span(val)
                                amr.add_alignment(tokens=word_idxs, nodes=[node_id])
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
                                word_idxs = AMR_Alignment.read_span(val)
                                amr.add_alignment(tokens=word_idxs, edges=[(s,r,t)])
                        if in_quotes:
                            quote_offset += 1
                    amr.edges.append((s,r,t))

        if len(amr.nodes) == 0:
            amrs.pop()
        if remove_wiki:
            for amr in amrs:
                wiki_nodes = []
                for s,r,t in amr.edges.copy():
                    if r==':wiki':
                        amr.edges.remove((s,r,t))
                        del amr.nodes[t]
                        wiki_nodes.append(t)
                for align in amr.alignments:
                    for n in wiki_nodes:
                        if n in align.nodes:
                            align.nodes.remove(n)
        print('[amr]', "Training Data" if training else "Dev Data")
        print('[amr]', "Number of sentences: " + str(len(amrs)))
        return amrs


class Graph_AMR_Reader:

    def __init__(self):
        self.imported = False
        pass

    def parse_amr_(self, tokens, amr_string):
        if not self.imported:
            from penman import PENMANCodec
            from penman.surface import Alignment, RoleAlignment, AlignmentMarker
            self.imported = True
        amr = AMR(tokens=tokens)

        num_alignments = 0

        g = PENMANCodec().decode(amr_string)
        triples = g.triples() if callable(g.triples) else g.triples
        new_alignments = {}
        new_idx = 0

        amr.root = g.top
        for tr in triples:
            s, r, t = tr
            if not r.startswith(':'):
                r = ':'+r
            # an amr node
            if r == ':instance':
                amr.nodes[s] = t
                if s.startswith('x'):
                    new_idx+=1
                # alignment
                if tr in g.epidata:
                    for align in g.epidata[tr]:
                        if isinstance(align, Alignment):
                            amr.add_alignment(tokens=[int(j) for j in align.indices], nodes=[s])
                            num_alignments+=1
            # an amr edge
            else:
                amr.edges.append((s,r,t))
                if s != amr.root and not any(s == t2 for s2, r2, t2 in amr.edges):
                    amr.edges[-1] = (t, r + '-of', s)
                # alignment
                if tr in g.epidata:
                    for align in g.epidata[tr]:
                        if isinstance(align, RoleAlignment):
                            amr.add_alignment(tokens=[int(j) for j in align.indices], edges=[amr.edges[-1]])
                            num_alignments += 1
                        elif isinstance(align, Alignment):
                            new_alignments[amr.edges[-1]] = align.indices
        # attributes
        for i,e in enumerate(amr.edges):
            s,r,t = e
            if t not in amr.nodes:
                amr.nodes[f'x{new_idx}'] = str(t)
                amr.edges[i] = (s, r, f'x{new_idx}')
                if (s, r, t) in new_alignments:
                    align = new_alignments[(s, r, t)]
                    amr.add_alignment(tokens=[int(j) for j in align], nodes=[f'x{new_idx}'])
                    num_alignments += 1
                new_idx += 1
            elif (s, r, t) in new_alignments:
                align = new_alignments[(s, r, t)]
                amr.add_alignment(tokens=[int(j) for j in align], nodes=[t])
                num_alignments += 1
        if num_alignments!=amr_string.count('~e'):
            print(f'Missing alignment: {num_alignments}/{amr_string.count("~e")}\n{amr}', file=sys.stderr)
        return amr

    def load(self, amr_file_name, training=True, verbose=False, remove_wiki=False):
        print('[amr]', 'Start reading data')
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
                        tokens = line[len('# ::tok '):].split()
                    elif line.startswith('# ::id'):
                        id = line.split()[2]
                if amr_string.strip():
                    amr = self.parse_amr_(tokens, amr_string)
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
                for align in amr.alignments:
                    for n in wiki_nodes:
                        if n in align.nodes:
                            align.nodes.remove(n)
        print('[amr]', "Training Data" if training else "Dev Data")
        print('[amr]', "Number of sentences: " + str(len(amrs)))
        return amrs


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Read AMRs from file')
    parser.add_argument('file', type=str, required=True,
                        help='input AMR file (default is JAMR format)')
    parser.add_argument('--graph', action='store_true', help='read AMRs from graph strings')

    args = parser.parse_args()

    if args.graph:
        cr = Graph_AMR_Reader
    else:
        cr = JAMR_AMR_Reader()
    amrs = cr.load(args.file, verbose=False)

    for amr in amrs:
        print(amr.jamr_string())


if __name__ == '__main__':
    main()
