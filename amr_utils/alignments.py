import json
import sys


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
            return {'type': self.type, 'tokens': self.tokens.copy(), 'nodes': self.nodes.copy(), 'edges': self.edges.copy(), 'string':self.readable(amr)}
        if self.amr is not None:
            return {'type': self.type, 'tokens': self.tokens.copy(), 'nodes': self.nodes.copy(), 'edges': self.edges.copy(), 'string':self.readable(self.amr)}
        return {'type':self.type, 'tokens':self.tokens.copy(), 'nodes':self.nodes.copy(), 'edges':self.edges.copy()}

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


def load_from_json(json_file, amrs=None, unanonymize=False):
    if amrs:
        amrs = {amr.id:amr for amr in amrs}
    with open(json_file, 'r', encoding='utf8') as f:
        alignments = json.load(f)
    for k in alignments:
        if unanonymize:
            if unanonymize and not amrs:
                raise Exception('To un-anonymize alignments, the parameter "amrs" is required.')
            for a in alignments[k]:
                if 'nodes' not in a:
                    a['nodes'] = []
                if 'edges' not in a:
                    a['edges'] = []
                amr = amrs[k]
                for i,e in enumerate(a['edges']):
                    s,r,t = e
                    if r is None:
                        new_e = [e2 for e2 in amr.edges if e2[0]==s and e2[2]==t]
                        if not new_e:
                            print('Failed to un-anonymize:', amr.id, e, file=sys.stderr)
                        else:
                            new_e = new_e[0]
                            a['edges'][i] = [s, new_e[1], t]
        alignments[k] = [AMR_Alignment(a['type'], a['tokens'], a['nodes'], [tuple(e) for e in a['edges']]) for a in alignments[k]]
    if amrs:
        for k in alignments:
            for align in alignments[k]:
                if k in amrs:
                    align.amr = amrs[k]
    return alignments


def write_to_json(json_file, alignments, anonymize=False, amrs=None):
    new_alignments = {}
    for k in alignments:
        new_alignments[k] = [a.to_json() for a in alignments[k]]
        if anonymize:
            if anonymize and not amrs:
                raise Exception('To anonymize alignments, the parameter "amrs" is required.')
            for a in new_alignments[k]:
                amr = next(amr_ for amr_ in  amrs if amr_.id==k)
                for i,e in enumerate(a['edges']):
                    if len([e2 for e2 in amr.edges if e2[0]==e[0] and e2[2]==e[2]])==1:
                        a['edges'][i] = [e[0],None,e[2]]
                if 'string' in a:
                    del a['string']
                if 'nodes' in a and not a['nodes']:
                    del a['nodes']
                if 'edges' in a and not a['edges']:
                    del a['edges']
    with open(json_file, 'w+', encoding='utf8') as f:
        json.dump(new_alignments, f)


