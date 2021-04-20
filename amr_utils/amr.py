import sys

from amr_utils.alignments import AMR_Alignment


class AMR:

    def __init__(self, tokens:list=None, id=None, root=None, nodes:dict=None, edges:list=None, metadata:dict=None):

        if edges is None: edges = []
        if nodes is None: nodes = {}
        if tokens is None: tokens = []
        if metadata is None: metadata = {}

        self.tokens = tokens
        self.root = root
        self.nodes = nodes
        self.edges = edges
        self.id = 'None' if id is None else id
        self.metadata = metadata

    def copy(self):
        return AMR(self.tokens.copy(), self.id, self.root, self.nodes.copy(), self.edges.copy(), self.metadata.copy())

    def __str__(self):
        return metadata_string(self)

    def graph_string(self):
        return graph_string(self)

    def amr_string(self):
        return metadata_string(self) + graph_string(self)+'\n\n'

    def get_alignment(self, alignments, token_id=None, node_id=None, edge=None):
        if not isinstance(alignments, dict):
            raise Exception('Alignments object must be a dict.')
        if self.id not in alignments:
            return AMR_Alignment()
        for align in alignments[self.id]:
            if token_id is not None and token_id in align.tokens:
                return align
            if node_id is not None and node_id in align.nodes:
                return align
            if edge is not None and edge in align.edges:
                return align
        return AMR_Alignment()

    def triples(self, normalize_inverse_edges=False):
        taken_nodes = {self.root}
        yield self.root, ':instance', self.nodes[self.root]
        for s,r,t in self.edges:
            if not self.nodes[t][0].isalpha() or self.nodes[t] in ['imperative', 'expressive', 'interrogative']:
                yield s, r, self.nodes[t]
                continue
            if normalize_inverse_edges and r.endswith('-of') and r not in [':consist-of', ':prep-out-of', ':prep-on-behalf-of']:
                yield t, r[:-len('-of')], s
            else:
                yield s, r, t
            if t not in taken_nodes:
                yield t, ':instance', self.nodes[t]
                taken_nodes.add(t)

    def _rename_node(self, a, b):
        if b in self.nodes:
            raise Exception('Rename Node: Tried to use existing node name:', b)
        self.nodes[b] = self.nodes[a]
        del self.nodes[a]
        if self.root == a:
            self.root = b
        for i, e in enumerate(self.edges):
            s,r,t = e
            if a in [s, t]:
                if s==a: s=b
                if t==a: t=b
                self.edges[i] = (s,r,t)



def metadata_string(amr):
    '''
        # ::id sentence id
        # ::tok tokens...
        # ::node node_id node alignments
        # ::root root_id root
        # ::edge src label trg src_id trg_id alignments
    '''
    output = ''
    # id
    if amr.id:
        output += f'# ::id {amr.id}\n'
    # tokens
    output += '# ::tok ' + (' '.join(amr.tokens)) + '\n'
    # metadata
    for label in amr.metadata:
        if label not in ['tok','id','node','root','edge','alignments']:
            output += f'# ::{label} {str(amr.metadata[label])}\n'
    # nodes
    for n in amr.nodes:
        output += f'# ::node\t{n}\t{amr.nodes[n].replace(" ","_") if n in amr.nodes else "None"}\n'
    # root
    root = amr.root
    if amr.root:
        output += f'# ::root\t{root}\t{amr.nodes[root] if root in amr.nodes else "None"}\n'
    # edges
    for i, e in enumerate(amr.edges):
        s, r, t = e
        r = r.replace(':', '')
        output += f'# ::edge\t{amr.nodes[s] if s in amr.nodes else "None"}\t{r}\t{amr.nodes[t] if t in amr.nodes else "None"}\t{s}\t{t}\n'

    return output


def graph_string(amr):
    amr_string = f'[[{amr.root}]]'
    new_ids = {}
    for n in amr.nodes:
        new_id = amr.nodes[n][0] if amr.nodes[n] else 'x'
        if new_id.isalpha() and new_id.islower():
            if new_id in new_ids.values():
                j = 2
                while f'{new_id}{j}' in new_ids.values():
                    j += 1
                new_id = f'{new_id}{j}'
        else:
            j = 0
            while f'x{j}' in new_ids.values():
                j += 1
            new_id = f'x{j}'
        new_ids[n] = new_id
    depth = 1
    nodes = {amr.root}
    completed = set()
    while '[[' in amr_string:
        tab = '\t' * depth
        for n in nodes.copy():
            id = new_ids[n] if n in new_ids else 'x91'
            concept = amr.nodes[n] if n in new_ids and amr.nodes[n] else 'None'
            edges = sorted([e for e in amr.edges if e[0] == n], key=lambda x: x[1])
            targets = set(t for s, r, t in edges)
            edges = [f'{r} [[{t}]]' for s, r, t in edges]
            children = f'\n{tab}'.join(edges)
            if children:
                children = f'\n{tab}' + children
            if n not in completed:
                if (concept[0].isalpha() and concept not in ['imperative', 'expressive', 'interrogative']) or targets:
                    amr_string = amr_string.replace(f'[[{n}]]', f'({id}/{concept}{children})', 1)
                else:
                    amr_string = amr_string.replace(f'[[{n}]]', f'{concept}')
                completed.add(n)
            amr_string = amr_string.replace(f'[[{n}]]', f'{id}')
            nodes.remove(n)
            nodes.update(targets)
        depth += 1
    if len(completed) < len(amr.nodes):
        missing_nodes = [n for n in amr.nodes if n not in completed]
        missing_edges = [(s, r, t) for s, r, t in amr.edges if s in missing_nodes or t in missing_nodes]
        missing_nodes= ', '.join(f'{n}/{amr.nodes[n]}' for n in missing_nodes)
        missing_edges = ', '.join(f'{s}/{amr.nodes[s]} {r} {t}/{amr.nodes[t]}' for s,r,t in missing_edges)
        print('[amr]', 'Failed to print AMR, '
              + str(len(completed)) + ' of ' + str(len(amr.nodes)) + ' nodes printed:\n '
              + str(amr.id) +':\n'
              + amr_string + '\n'
              + 'Missing nodes: ' + missing_nodes +'\n'
              + 'Missing edges: ' + missing_edges +'\n',
              file=sys.stderr)
    if not amr_string.startswith('('):
        amr_string = '(' + amr_string + ')'
    if len(amr.nodes) == 0:
        amr_string = '(a/amr-empty)'

    return amr_string
