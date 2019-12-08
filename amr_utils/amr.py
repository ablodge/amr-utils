
import re, sys
import style

class AMR:

    def __init__(self, id=None, tokens:list=None, root=None, nodes:dict=None, edges:list=None, alignments:list=None):

        if edges is None: edges = []
        if nodes is None: nodes = {}
        if tokens is None: tokens = []

        self.tokens = tokens
        self.root = root
        self.nodes = nodes
        self.edges = edges
        self.id = 'None' if id is None else id
        self.alignments = alignments if alignments else []
        self.alignments = list(sorted(self.alignments,key = lambda x:x.tokens[0]))
        self.duplicates = []

    def add_alignment(self, tokens, nodes=None, edges=None):
        for t in tokens:
            if t>=len(self.tokens):
                print(f'Tokens out of range: {t} {" ".join(self.tokens)}', file=sys.stderr)
        for align in self.alignments:
            if align.tokens==tokens:
                if nodes:
                    for n in nodes:
                        if n not in align.nodes:
                            align.nodes.append(n)
                if edges:
                    for e in edges:
                        if e not in align.edges:
                            align.edges.append(e)
                return
        self.alignments.append(AMR_Alignment(tokens=tokens, nodes=nodes, edges=edges))

    def get_alignment(self, token_id=None, node_id=None, edge=None):
        for align in self.alignments:
            if token_id is not None and token_id not in align.tokens:
                continue
            if node_id is not None and node_id not in align.nodes:
                continue
            if edge is not None and edge not in align.edges:
                continue
            return align
        return AMR_Alignment()

    def copy(self):
        return AMR(self.id, self.tokens.copy(), self.root, self.nodes.copy(), self.edges.copy(), [a.copy() for a in self.alignments])

    def get_subgraph(self, node_ids:list):
        if not node_ids:
            return AMR()
        potential_root = node_ids.copy()
        sg_edges = []
        for x, r, y in self.edges:
            if x in node_ids and y in node_ids:
                sg_edges.append((x, r, y))
                if y in potential_root:
                    potential_root.remove(y)
        root = potential_root[0] if len(potential_root) > 0 else node_ids[0]
        return AMR(root=root,
                   edges=sg_edges,
                   nodes={n: self.nodes[n] for n in node_ids})

    def __str__(self):
        return style.default_string(self)

    def graph_string(self):
        return style.graph_string(self)

    def jamr_string(self):
        return style.jamr_string(self)

class AMR_Alignment:

    def __init__(self, tokens:list=None, nodes:list=None, edges:list=None):
        self.tokens = tokens if tokens else []
        self.nodes = nodes if nodes else []
        self.edges = edges if edges else []

    def __bool__(self):
        return bool(self.tokens) and (bool(self.nodes) or bool(self.edges))

    def __str__(self):
        return f'<AMR_Alignment>: tokens {self.tokens} nodes {self.nodes} edges {self.edges}'

    def copy(self):
        return AMR_Alignment(tokens=self.tokens.copy(), nodes=self.nodes.copy(), edges=self.edges.copy())

    def write_span(self):
        if len(self.tokens)==0:
            return ''
        elif len(self.tokens)==1:
            return f'{self.tokens[0]}-{self.tokens[0]+1}'
        elif all(self.tokens[i]==self.tokens[i+1]-1 for i in range(0,len(self.tokens)-1)):
            return f'{self.tokens[0]}-{self.tokens[-1]+1}'
        else:
            return ','.join(str(t) for t in self.tokens)

    @staticmethod
    def read_span(span):
        if '-' in span:
            start, end = span.split('-')
            return list(range(int(start),int(end)))
        elif ',' in span:
            return [int(t) for t in span.split(',')]
        elif span.isdigit():
            return [int(span)]
        elif not span.strip():
            return []
        else:
            raise ValueError(f'Invalid Argument: {span}')

