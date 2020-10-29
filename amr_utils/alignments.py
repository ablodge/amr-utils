import json

class AMR_Alignment:

    def __init__(self, type=None, tokens:list=None, nodes:list=None, edges:list=None, amr=None):
        self.type = type if type else 'basic'
        self.tokens = tokens if tokens else []
        self.nodes = nodes if nodes else []
        self.edges = edges if edges else []
        self.amr = None
        if amr is not None:
            self.amr = amr

    def __bool__(self):
        return bool(self.tokens) and (bool(self.nodes) or bool(self.edges))

    def __str__(self):
        if self.amr is not None:
            return f'<AMR_Alignment: {self.type}>: tokens {self.tokens} nodes {self.nodes} edges {self.edges} ({self.readable(self.amr)})'
        return f'<AMR_Alignment: {self.type}>: tokens {self.tokens} nodes {self.nodes} edges {self.edges}'

    def copy(self):
        align = AMR_Alignment(type=self.type, tokens=self.tokens.copy(), nodes=self.nodes.copy(), edges=self.edges.copy())
        align.amr = self.amr
        return align

    def to_json(self, amr=None):
        if amr is not None:
            return {'type': self.type, 'tokens': self.tokens, 'nodes': self.nodes, 'edges': self.edges, 'string':self.readable(amr)}
        if self.amr is not None:
            return {'type': self.type, 'tokens': self.tokens, 'nodes': self.nodes, 'edges': self.edges, 'string':self.readable(self.amr)}
        return {'type':self.type, 'tokens':self.tokens, 'nodes':self.nodes, 'edges':self.edges}

    def readable(self, amr):
        type = '' if self.type=='basic' else self.type
        nodes = '' if not self.nodes else ", ".join(amr.nodes[n] for n in self.nodes)
        edges = '' if not self.edges else ", ".join(str((amr.nodes[s],r,amr.nodes[t])) for s,r,t in self.edges)
        tokens = " ".join(amr.tokens[t] for t in self.tokens)
        if nodes and edges:
            edges = ', '+edges
        if type:
            type += ' : '
        return f'{type}{tokens} => {nodes}{edges}'


def load_from_json(json_file, amrs=None):
    with open(json_file, 'r', encoding='utf8') as f:
        alignments = json.load(f)
    for k in alignments:
        alignments[k] = [AMR_Alignment(a['type'], a['tokens'], a['nodes'], a['edges']) for a in alignments[k]]
    if amrs:
        amrs = {amr.id:amr for amr in amrs}
        for k in alignments:
            for align in alignments[k]:
                if k in amrs:
                    align.amr = amrs[k]
    return alignments

def write_to_json(json_file, alignments):
    new_alignments = {}
    for k in alignments:
        new_alignments[k] = [a.to_json() for a in alignments[k]]
    with open(json_file, 'w+', encoding='utf8') as f:
        json.dump(new_alignments, f)


def convert_alignment_to_subgraph(align, amr):
    nodes = align.nodes
    sub = amr.get_subgraph(nodes) if nodes else None
    if sub is None:
        return None
    for s,r,t in align.edges:
        if s not in nodes:
            sub.nodes[s] = '<var>'
        if t not in nodes:
            sub.nodes[t] = '<var>'
        if (s,r,t) not in sub.edges:
            sub.edges.append((s,r,t))
        if not sub.root or sub.root==t:
            sub.root = s
    return sub