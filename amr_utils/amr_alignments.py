from collections import Counter, defaultdict
from typing import Iterable, Tuple, Dict, Any, Optional, List, Union

from sortedcontainers import SortedList

from amr_utils import amr_iterators, amr_graph
from amr_utils.amr import AMR, AMR_Notation
from amr_utils.amr_graph import Subgraph_AMR
from amr_utils.utils import class_name

Edge = Tuple[str, str, str]


class AMR_Alignment:
    """
    This class represents a single AMR Alignment from a collection of tokens to a collection of nodes and/or edges.

    Example Usage:
    ```
    amr = AMR.from_string('''
    (w / want-01
      :ARG0 (b / boy)
      :ARG1 (g / go-02
          :ARG0 b
          :ARG4 (c / city
              :name (n / name :op1 "New"
                  :op2 "York" :op3 "City"))))
    ''',
    tokens=['The', 'boy', 'wants', 'to', 'go', 'to', 'New', 'York', '.'])
    align1 = AMR_Alignment(type='subgraph', tokens=[1], nodes=['b'])
    align2 = AMR_Alignment(type='subgraph', tokens=[2], nodes=['w'])
    align3 = AMR_Alignment(type='subgraph', tokens=[4], nodes=['g'])
    align4 = AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c','n','x0','x1','x2'],
                           edges=[('c',':name','n'), ('n',':op1','x0'), ('n',':op2','x1'), ('n',':op3','x2')])
    align5 = AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                           edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
    align6 = AMR_Alignment(type='arg structure', tokens=[4], nodes=['g'],
                           edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c')])
    align7 = AMR_Alignment(type='reentrancy:control', tokens=[2], edges=[('g',':ARG0','b')])
    ```
    """

    def __init__(self, type: str = None, tokens: Iterable[int] = None, nodes: Iterable[str] = None,
                 edges: Iterable[Edge] = None):
        """
        Create a single AMR Alignment from a collection of tokens to a collection of nodes and/or edges.
        Args:
            type (str): a string representing the alignment type, if there is more than one type of alignment
            tokens (Iterable[int]): token indices for the tokens which are aligned
            nodes (Iterable[str]): node IDs for any nodes which are aligned
            edges (Iterable[Edge]): edges for any edges which are aligned
        """
        self.type = type  # Can be None
        self.tokens = SortedList(tokens) if (tokens is not None) else SortedList()
        self.nodes = SortedList(nodes) if (nodes is not None) else SortedList()
        self.edges = SortedList(edges) if (edges is not None) else SortedList()

    def copy(self):
        """
        Create a copy
        Returns:
            AMR_Alignment: copy
        """
        return AMR_Alignment(type=self.type, tokens=self.tokens.copy(), nodes=self.nodes.copy(),
                             edges=self.edges.copy())

    def to_json(self, amr: AMR = None) -> Dict[str, Any]:
        """
        Convert this alignment to a JSON format for saving to a file
        Returns:
            dict: a dictionary representing this alignment with keys representing tokens, nodes, edges, etc.
        """
        tokens = [t for t in self.tokens]
        nodes = [n for n in self.nodes]
        edges = [e for e in self.edges]
        json_ = {'type': self.type, 'tokens': tokens, 'nodes': nodes, 'edges': edges}
        if not self.nodes:
            del json_['nodes']
        if not self.edges:
            del json_['edges']
        if amr is not None:
            json_['description'] = self.description(amr)
        return json_

    def description(self, amr: AMR) -> str:
        """
        TODO
        Args:
            amr:

        Returns:

        """
        type_ = self.type + ' : ' if (self.type is not None) else ''
        tokens = ' '.join(amr.tokens[t] for t in self.tokens)
        # get subgraph strings (possibly disconnected)
        subgraph = self.get_subgraph(amr)
        return f'{type_}{tokens} => {subgraph.graph_string(pretty_print=False)}'

    def get_subgraph(self, amr: AMR) -> Subgraph_AMR:
        nodes = {n: amr.nodes[n] for n in self.nodes if n in amr.nodes}
        if self.edges:
            edges = self.edges
            for s, r, t in edges:
                if s not in nodes:
                    nodes[s] = '<var>'
                if t not in nodes:
                    nodes[t] = '<var>'
        else:
            edges = [(s, r, t) for s, r, t in amr.edges if s in nodes and t in nodes]
        root = amr_graph.find_best_root(amr, subgraph_nodes=nodes, subgraph_edges=edges)
        # get new node IDs
        node_map = {}
        idx = 0
        var_idx = 0
        for n in amr_iterators.nodes(amr, depth_first=True, subgraph_root=root, subgraph_nodes=nodes):
            if AMR_Notation.is_constant(nodes[n]):
                node_map[n] = f'x{var_idx}'
                var_idx += 1
            else:
                node_map[n] = f'a{idx}'
                idx += 1
        # create subgraph
        sub = Subgraph_AMR(id=amr.id,
                           root=node_map[root],
                           tokens=[amr.tokens[t] for t in self.tokens],
                           edges=[(node_map[s], r, node_map[t]) for s, r, t in edges],
                           nodes={node_map[n]: nodes[n] for n in nodes})
        return sub

    def __str__(self):
        type_ = self.type + ' : ' if (self.type is not None) else ''
        nodes = ', '.join(n for n in self.nodes) if bool(self.nodes) else ''
        edges = ', '.join(f'({s} {r} {t})' for s, r, t in self.edges) if bool(self.edges) else ''
        tokens = ', '.join(str(t) for t in self.tokens)
        sep2 = ', ' if (nodes and edges) else ''
        return f'[{class_name(self)}]: {type_}{tokens} => {nodes}{sep2}{edges}'

    def __bool__(self):
        return bool(self.tokens) and (bool(self.nodes) or bool(self.edges))

    def __eq__(self, other):
        return self.type == other.type and self.tokens == other.tokens \
               and self.nodes == other.nodes and self.edges == other.edges

    def __lt__(self, other):
        if self.type < other.type:
            return True
        elif self.type > other.type:
            return False
        elif self.tokens < other.tokens:
            return True
        elif self.tokens > other.tokens:
            return False
        elif bool(self.nodes) and not bool(other.nodes):
            return True
        elif not bool(self.nodes) and bool(other.nodes):
            return False
        elif self.nodes < other.nodes:
            return True
        elif self.nodes > other.nodes:
            return False
        elif bool(self.edges) and not bool(other.edges):
            return True
        elif not bool(self.edges) and bool(other.edges):
            return False
        elif self.edges < other.edges:
            return True
        else:
            return False


class AMR_Alignment_Set:
    """
    TODO
    """

    def __init__(self, amr: AMR, alignments: Iterable[AMR_Alignment] = None):
        """
        Create a Set of AMR Alignments for a single AMR.
        Args:
            amr (AMR): an AMR
            alignments (Iterable[AMR_Alignment]): alignments to be included
        """
        self.amr = amr
        self.alignments = SortedList()
        self.token_spans = SortedList()
        if alignments is not None:
            for align in alignments:
                self.add(align)

    @staticmethod
    def from_json(amr, json_obj: List[Dict[str, Any]]) -> 'AMR_Alignment_Set':
        """
        TODO
        Args:
            amr:
            json_obj:

        Returns:

        """
        AMR_Alignment_Set._check_ids_match(amr, json_obj)
        AMR_Alignment_Set._unanonymize_edges(amr, json_obj)
        alignment_list = []
        for json_align in json_obj:
            nodes = json_align['nodes'] if ('nodes' in json_align) else []
            edges = [(e[0], e[1], e[2]) for e in json_align['edges']] if ('edges' in json_align) else []
            alignment = AMR_Alignment(type=json_align['type'], tokens=json_align['tokens'],
                                      nodes=nodes, edges=edges)
            alignment_list.append(alignment)
        return AMR_Alignment_Set(amr, alignment_list)

    def align(self, type: str = None, tokens: Iterable[int] = None, nodes: Iterable[str] = None,
                 edges: Iterable[Edge] = None):
        """
        Create and add a single AMR Alignment from a collection of tokens to a collection of nodes and/or edges.
        This is a shorthand for:
        ```
        self.add(AMR_Alignment(type, tokens, nodes, edges))
        ```
        Args:
            type (str): a string representing the alignment type, if there is more than one type of alignment
            tokens (Iterable[int]): token indices for the tokens which are aligned
            nodes (Iterable[str]): node IDs for any nodes which are aligned
            edges (Iterable[Edge]): edges for any edges which are aligned
        """
        self.add(AMR_Alignment(type=type, tokens=tokens, nodes=nodes, edges=edges))

    def add(self, alignment: AMR_Alignment):
        """
        TODO
        Args:
            alignment:

        Returns:

        """
        if tuple(alignment.tokens) not in self.token_spans:
            self.token_spans.add(tuple(alignment.tokens))
        self.alignments.add(alignment)

    def remove(self, alignment: AMR_Alignment):
        """
        TODO
        Args:
            alignment:

        Returns:

        """
        self.alignments.remove(alignment)

    def get(self, type: str = None, token_id: Union[int, Iterable[int]] = None, node: Union[str, Iterable[str]] = None,
            edge: Union[Edge, Iterable[Edge]] = None) -> Optional[AMR_Alignment]:
        """
        TODO
        Args:
            type:
            token_id:
            node:
            edge:

        Returns:

        """
        for align in self.finditer(type, token_id, node, edge):
            return align

    def get_all(self, type: str = None, token_id: Union[int, Iterable[int]] = None,
                node: Union[str, Iterable[str]] = None, edge: Union[Edge, Iterable[Edge]] = None) \
            -> List[AMR_Alignment]:
        """
        TODO
        Args:
            type:
            token_id:
            node:
            edge:

        Returns:

        """
        aligns = []
        for align in self.finditer(type, token_id, node, edge):
            aligns.append(align)
        return aligns

    def finditer(self, type: str = None, token_id: Union[int, Iterable[int]] = None,
                 node: Union[str, Iterable[str]] = None, edge: Union[Edge, Iterable[Edge]] = None) \
            -> List[AMR_Alignment]:
        """
        TODO
        Args:
            type:
            token_id:
            node:
            edge:

        Returns:

        """
        if isinstance(token_id, int):
            token_id = [token_id]
        if isinstance(node, str):
            node = [node]
        if edge and isinstance(edge[0], str):
            edge = [edge]
        for align in self:
            if (type is None or type == align.type) and \
                    (token_id is None or all(t in align.tokens for t in token_id)) and \
                    (node is None or all(n in align.tokens for n in node)) and \
                    (edge is None or all(e in align.edges for e in edge)):
                yield align

    def __iter__(self):
        return self.alignments

    def __len__(self):
        return len(self.alignments)

    def __str__(self):
        return f'[{class_name(self)}] {"; ".join(a.description() for a in self)}'

    def to_json(self, anonymize=False) -> List[Dict[str, Any]]:
        """
        TODO
        Args:
            anonymize:

        Returns:

        """
        if anonymize:
            json_ = [a.to_json() for a in self]
            count_unlabeled_edges = Counter()
            for s, r, t in self.amr.edges:
                count_unlabeled_edges[(s, t)] += 1
            for a in json_:
                for i, e in a['edges']:
                    s, r, t = e
                    if count_unlabeled_edges[(s, t)] == 1:
                        a['edges'][i] = (s, ':_', t)
        else:
            return [a.to_json(self.amr) for a in self]

    def is_connected(self) -> bool:
        """
        TODO
        Returns:

        """
        raise NotImplemented()

    def is_projective(self) -> bool:
        """
        TODO
        Returns:
            bool:
        """
        align = self.find_nonprojective_alignment()
        if align is None:
            return True
        return False

    def find_nonprojective_alignment(self) -> Optional[AMR_Alignment]:
        """
        TODO
        Returns:
            AMR_Alignment:
        """
        reachable_nodes = amr_graph._get_reachable_nodes(self.amr)
        nodes = [n for n in amr_iterators.nodes(self.amr, breadth_first=True)]
        for n in reversed(nodes):
            min_token_idx = float('inf')
            max_token_idx = float('-inf')
            for n2 in reachable_nodes[n]:
                for align in self.get_all(node=n2):
                    for t in align.tokens:
                        if t < min_token_idx:
                            min_token_idx = t
                        if t > max_token_idx:
                            max_token_idx = t
            for align in self:
                if any(min_token_idx <= t <= max_token_idx for t in align.tokens):
                    for n2 in align.nodes:
                        if n2 not in reachable_nodes[n]:
                            return align
                    for s, r, t in align.edges:
                        if not (s in reachable_nodes[n] or t in reachable_nodes[n]):
                            return align
        return None

    @staticmethod
    def _check_ids_match(amr: AMR, json_alignment_list):
        # check ids
        node_ids = set()
        for align in json_alignment_list:
            nodes = align['nodes'] if ('nodes' in align) else []
            edges = align['edges'] if ('edges' in align) else []
            for node in nodes:
                node_ids.add(node)
            for edge in edges:
                node_ids.add(edge[0])
                node_ids.add(edge[2])
        if any(n not in amr.nodes for n in node_ids):
            raise Exception(f'Failed to anonymize alignments for {amr.id}. '
                            'This typically means the alignment ids do not match the AMR ids.'
                            f'\nAMR node IDs: {set(amr.nodes.keys())}'
                            f'\nAMR_Alignment node IDs: {node_ids}')

    @staticmethod
    def _unanonymize_edges(amr, json_alignment_list):
        map_unlabeled_edges = defaultdict(list)
        for s, r, t in amr.edges:
            map_unlabeled_edges[(s, t)].append((s, r, t))
        for json_align in json_alignment_list:
            if 'edges' in json_align:
                for i, e in enumerate(json_align['edges']):
                    s, r, t = e
                    if r == ':_' or r is None:
                        s, r, t = map_unlabeled_edges[(s, t)]
                    json_align['edges'][i] = (s, r, t)
