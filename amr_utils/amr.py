
from amr_utils import style
from amr_utils.alignments import AMR_Alignment


class AMR:

    def __init__(self, id=None, tokens:list=None, root=None, nodes:dict=None, edges:list=None):

        if edges is None: edges = []
        if nodes is None: nodes = {}
        if tokens is None: tokens = []

        self.tokens = tokens
        self.root = root
        self.nodes = nodes
        self.edges = edges
        self.id = 'None' if id is None else id

    def copy(self):
        return AMR(self.id, self.tokens.copy(), self.root, self.nodes.copy(), self.edges.copy())

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

    def get_alignment(self, alignments=None, token_id=None, node_id=None, edge=None):
        if alignments is None:
            alignments = {self.id : self.alignments}
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
