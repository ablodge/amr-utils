from collections import Counter, defaultdict
from collections.abc import Set
from typing import Iterable, Tuple, Dict, Any, Optional, List, Callable, Iterator

from sortedcontainers import SortedSet

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

    def __init__(self, tokens: Iterable[int], type: str = None, nodes: Iterable[str] = None,
                 edges: Iterable[Edge] = None):
        """
        Create a single AMR Alignment from a collection of tokens to a collection of nodes and/or edges.
        Args:
            tokens (Iterable[int]): token indices for the tokens which are aligned
            type (str): a string representing the alignment type, if there is more than one type of alignment
            nodes (Iterable[str]): node IDs for any nodes which are aligned
            edges (Iterable[Edge]): edges for any edges which are aligned
        """
        self.__type: Optional[str] = type  # Can be None
        self.__tokens: Tuple = tuple(t for t in sorted(tokens)) if (tokens is not None) else tuple()
        self.__nodes: Tuple = tuple(n for n in sorted(nodes)) if (nodes is not None) else tuple()
        self.__edges: Tuple = tuple(e for e in sorted(edges)) if (edges is not None) else tuple()
        self._container: Optional[AMR_Alignment_Set] = None

    def type(self) -> str:
        return self.__type

    def tokens(self) -> Tuple[int, ...]:
        return self.__tokens

    def nodes(self) -> Tuple[str, ...]:
        return self.__nodes

    def edges(self) -> Tuple[Edge, ...]:
        return self.__edges

    def set(self, tokens: Iterable[int] = None, type: str = None, nodes: Iterable[str] = None,
            edges: Iterable[Edge] = None) -> None:
        if self._container is not None:
            self._container.remove(self)
        if type is not None:
            self.__type = type
        if tokens is not None:
            self.__tokens = tuple(t for t in sorted(tokens))
        if nodes is not None:
            self.__nodes = tuple(n for n in sorted(nodes))
        if edges is not None:
            self.__edges = tuple(e for e in sorted(edges))
        if self._container is not None:
            self._container.add(self)

    def add(self, tokens: Iterable[int] = None, nodes: Iterable[str] = None, edges: Iterable[Edge] = None) -> None:
        if self._container is not None:
            self._container.remove(self)
        if type is not None:
            self.__type = type
        if tokens is not None:
            new_tokens = [t for t in self.__tokens]
            new_tokens.extend(tokens)
            self.__tokens = tuple(t for t in sorted(new_tokens))
        if nodes is not None:
            new_nodes = [n for n in self.__nodes]
            new_nodes.extend(nodes)
            self.__nodes = tuple(n for n in sorted(new_nodes))
        if edges is not None:
            new_edges = [e for e in self.__edges]
            new_edges.extend(edges)
            self.__edges = tuple(e for e in sorted(new_edges))
        if self._container is not None:
            self._container.add(self)

    def copy(self) -> 'AMR_Alignment':
        """
        Create a copy
        Returns:
            AMR_Alignment: copy
        """
        return AMR_Alignment(type=self.__type, tokens=self.__tokens, nodes=self.__nodes, edges=self.__edges)

    def to_json(self, amr: AMR = None) -> Dict[str, Any]:
        """
        Convert this alignment to a JSON format for saving to a file
        Returns:
            dict: a dictionary representing this alignment with keys representing tokens, nodes, edges, etc.
        """
        tokens = [t for t in self.__tokens]
        nodes = [n for n in self.__nodes]
        edges = [e for e in self.__edges]
        json_obj = {'type': self.__type, 'tokens': tokens}
        if self.__nodes:
            json_obj['nodes'] = nodes
        if self.__edges:
            json_obj['edges'] = edges
        if amr is not None:
            json_obj['description'] = self.description(amr)
        return json_obj

    def description(self, amr: AMR) -> str:
        """
        Get a human-readable string description of this alignment.
        Args:
            amr (AMR): the corresponding AMR

        Returns:
            str: a human-readable string description of this alignment
        """
        type_ = self.__type + ' : ' if (self.__type is not None) else ''
        tokens = ' '.join(amr.tokens[t] for t in self.__tokens)
        # get subgraph strings (possibly disconnected)
        subgraph = self._get_subgraph(amr, normalize_nodes=True)
        return f'{type_}{tokens} => {subgraph.graph_string(pretty_print=False)}'

    def _get_subgraph(self, amr: AMR, normalize_nodes: bool = False) -> Subgraph_AMR:
        nodes = {n: amr.nodes[n] for n in self.__nodes if n in amr.nodes}
        if self.__edges:
            edges = self.__edges
            for s, r, t in edges:
                if s not in nodes:
                    nodes[s] = '<var>'
                if t not in nodes:
                    nodes[t] = '<var>'
        else:
            edges = [(s, r, t) for s, r, t in amr.edges if s in nodes and t in nodes]
        root = amr_graph.find_best_root(amr, subgraph_nodes=nodes, subgraph_edges=edges)
        # get new node IDs
        if normalize_nodes:
            node_map = {}
            idx = 0
            var_idx = 0
            for n in amr_iterators.nodes(amr, depth_first=True, subgraph_root=root, subgraph_nodes=nodes,
                                         subgraph_edges=edges):
                if AMR_Notation.is_constant(nodes[n]):
                    node_map[n] = f'x{var_idx}'
                    var_idx += 1
                else:
                    node_map[n] = f'a{idx}'
                    idx += 1
            root = node_map[root]
            nodes = {node_map[n]: nodes[n] for n in nodes}
            edges = [(node_map[s], r, node_map[t]) for s, r, t in edges]
        # create subgraph
        sub = Subgraph_AMR(id=amr.id,
                           root=root,
                           tokens=[amr.tokens[t] for t in self.__tokens],
                           nodes=nodes,
                           edges=edges)
        return sub

    def is_connected(self, amr: AMR) -> bool:
        """
        Test whether the subgraph aligned in this alignment is a connected directed graph.
        Args:
            amr (AMR): the corresponding AMR

        Returns:
            bool: True if the aligned subgraph is a connected directed graph
        """
        nodes = set(self.__nodes)
        for s, r, t in self.__edges:
            nodes.add(s)
            nodes.add(t)
        edges = self.__edges if bool(self.__edges) else None
        return amr_graph.is_connected(amr, subgraph_nodes=nodes, subgraph_edges=edges)

    def __str__(self):
        type_ = self.__type + ' : ' if (self.__type is not None) else ''
        nodes = ', '.join(n for n in self.__nodes) if bool(self.__nodes) else ''
        edges = ', '.join(f'({s} {r} {t})' for s, r, t in self.__edges) if bool(self.__edges) else ''
        tokens = ', '.join(str(t) for t in self.__tokens)
        sep2 = ', ' if (nodes and edges) else ''
        return f'[{class_name(self)}] {type_}{tokens} => {nodes}{sep2}{edges}'

    def __bool__(self):
        return bool(self.__tokens) and (bool(self.__nodes) or bool(self.__edges))

    def __eq__(self, other):
        return self.__type == other.__type and self.__tokens == other.__tokens \
               and self.__nodes == other.__nodes and self.__edges == other.__edges

    def __hash__(self):
        return hash((self.__type, self.__tokens, self.__nodes, self.__edges))

    def __lt__(self, other):
        if self.__tokens < other.__tokens:
            return True
        elif self.__tokens > other.__tokens:
            return False
        elif self.__type is None and other.__type is not None:
            return True
        elif self.__type is not None and other.__type is None:
            return False
        elif self.__type < other.__type:
            return True
        elif self.__type > other.__type:
            return False
        elif self.__nodes < other.__nodes:
            return True
        elif self.__nodes > other.__nodes:
            return False
        elif self.__edges < other.__edges:
            return True
        else:
            return False


class AMR_Alignment_Set(Set):
    """
    This class represents a set of alignments for a single AMR. `AMR_Alignment_Set` is iterable and implements basic
    methods of the class `Set`, while keeping member alignments in a sorted order.

    TODO

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
    alignments = AMR_Alignment_Set(amr)
    alignments.align(type='subgraph', tokens=[1], nodes=['b'])
    alignments.align(type='subgraph', tokens=[2], nodes=['w'])
    alignments.align(type='subgraph', tokens=[4], nodes=['g'])
    alignments.align(type='subgraph', tokens=[6, 7], nodes=['c','n','x0','x1','x2'],
                     edges=[('c',':name','n'), ('n',':op1','x0'), ('n',':op2','x1'), ('n',':op3','x2')])
    alignments.align(type='arg structure', tokens=[2], nodes=['w'],
                     edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
    alignments.align(type='arg structure', tokens=[4], nodes=['g'],
                     edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c')])
    alignments.align(type='reentrancy:control', tokens=[2], edges=[('g',':ARG0','b')])

    for alignment in alignments:
        print(alignment)
    ```
    """

    def __init__(self, amr: AMR, alignments: Iterable[AMR_Alignment] = None):
        """
        Create a Set of AMR Alignments for a single AMR.
        Args:
            amr (AMR): the AMR for these alignments
            alignments (Iterable[AMR_Alignment]): alignments to be included
        """
        self.amr = amr
        self.__alignments = SortedSet()
        if alignments is not None:
            for align in alignments:
                self.add(align)

    @staticmethod
    def from_json(amr, json_obj: List[Dict[str, Any]]) -> 'AMR_Alignment_Set':
        """
        Create a Set of AMR Alignments for a single AMR from a JSON object.
        Args:
            amr (AMR): the corresponding AMR
            json_obj (List[Dict[str, Any]]): a list of dictionaries representing an alignment set in JSON form

        Returns:
            AMR_Alignment_Set: an alignment set for a single AMR
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

    def __iter__(self) -> Iterator[AMR_Alignment]:
        return self.__alignments.__iter__()

    def __len__(self):
        return len(self.__alignments)

    def __contains__(self, alignment: AMR_Alignment) -> bool:
        return alignment in self.__alignments

    def __str__(self):
        align_strings = []
        for a in self:
            align_strings.append(f'\t[{class_name(a)}] {a.description(self.amr)}')
        align_strings = ',\n'.join(align_strings)
        return f'[{class_name(self)}] {{\n{align_strings}\n}}'

    def align(self, tokens: Iterable[int], type: str = None, nodes: Iterable[str] = None,
              edges: Iterable[Edge] = None) -> None:
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
        Add an AMR alignment.
        Args:
            alignment (AMR_Alignment): a single AMR alignment from tokens to nodes and/or edges

        Returns:
            None
        """
        if alignment._container is not None:
            if alignment._container is self:
                return
            else:
                raise Exception(f'[{class_name(self)}] This AMR_Alignment already has an AMR_Alignment_Set. '
                                'An AMR_Alignment is only allowed one AMR_Alignment_Set. Please use the `copy()` '
                                'method if you want to add an identical alignment.')
        if alignment not in self:
            alignment._container = self
            self.__alignments.add(alignment)

    def remove(self, alignment: AMR_Alignment):
        """
        Remove an AMR alignment.
        Args:
            alignment (AMR_Alignment): a single AMR alignment from tokens to nodes and/or edges

        Returns:
            None
        """
        alignment._container = None
        self.__alignments.remove(alignment)

    def get(self, token_id: int = None, type: str = None, node: str = None, edge: Edge = None) \
            -> Optional[AMR_Alignment]:
        """
        Get the first alignment matching this description. You can retrieve the alignment by type, a contained token,
        node, or edge, or some combination. If `token_id` is specified, 'get()' uses binary search (O(log N)), otherwise
        linear search (O(N)) is used.

        Example Usage:
        ```
        # get the alignment of the 3rd token
        align = alignments.get(token_id=2)
        # get the alignment of the node "a"
        align = alignments.get(node='a')
        # get the alignment of type "subgraph" AND containing the edge ('a', ':op1', 'b')
        align = alignments.get(type='subgraph', edge=('a', ':op1', 'b'))
        ```
        Args:
            type (str): an alignment type
            token_id (int): the index of a token
            node (str): a node ID
            edge (Tuple[str,str,str]): an edge, a tuple of the form (source_id, relation, target_id)

        Returns:
            Optional[AMR_Alignment]: the matching AMR alignment (or None if no match is found)
        """
        iter_ = self if (token_id is None) else self._binary_search_iter(token_id)
        for align in iter_:
            if self._is_match(align, token_id, type, node, edge):
                return align

    def get_all(self, token_id: int = None, type: str = None, node: str = None, edge: Edge = None) \
            -> List[AMR_Alignment]:
        """
        Get a list of the alignments matching this description. You can retrieve alignments by type, a contained token,
        node, or edge, or some combination using linear search (O(N)).

        Example Usage:
        ```
        # get all alignments containing the 3rd token
        align = alignments.get_all(token_id=2)
        # get all alignments containing the node "a"
        align = alignments.get_all(node='a')
        # get all alignments of type "subgraph" AND containing the edge ('a', ':op1', 'b')
        align = alignments.get_all(type='subgraph', edge=('a', ':op1', 'b'))
        ```
        Args:
            type (str): an alignment type
            token_id (int): the index of a token
            node (str): a node ID
            edge (Tuple[str,str,str]): an edge, a tuple of the form (source_id, relation, target_id)

        Returns:
            List[AMR_Alignment]: a list of matching AMR alignments
        """
        aligns = []
        iter_ = self if (token_id is None) else self._linear_search_iter(token_id)
        for align in iter_:
            if self._is_match(align, token_id, type, node, edge):
                aligns.append(align)
        return aligns

    @staticmethod
    def _is_match(align: AMR_Alignment, token_id: int = None, type: str = None, node: str = None,
                  edge: Edge = None) -> bool:
        if (type is None or type == align.type()) and \
                (token_id is None or token_id in align.tokens()) and \
                (node is None or node in align.nodes()) and \
                (edge is None or edge in align.edges()):
            return True
        return False

    def _linear_search_iter(self, token_id: int):
        for align in self:
            tokens_ = align.tokens()
            if tokens_ and tokens_[0] > token_id:
                break
            yield align

    def _binary_search_iter(self, token_id: int):
        start_idx = self.__alignments.index(AMR_Alignment(tokens=[token_id]))
        for align in self.__alignments.islice(start=start_idx):
            tokens_ = align.tokens()
            if tokens_ and tokens_[0] > token_id:
                break
            yield align
        if start_idx > 0:
            for align in self.__alignments.islice(start=start_idx-1, reverse=True):
                yield align

    def find(self, condition: Callable[[AMR_Alignment], bool]) -> Optional[AMR_Alignment]:
        """
        Get the first alignment matching `condition` using linear search (O(N)).
        Args:
            condition (function: AMR_Alignment -> bool): a condition to test

        Returns:
            Optional[AMR_Alignment]: the matching AMR alignment
        """
        for align in self:
            if condition(align):
                return align
        return None

    def find_all(self, condition: Callable[[AMR_Alignment], bool]) -> List[AMR_Alignment]:
        """
        Get a list of alignments matching `condition` using linear search (O(N)).
        Args:
            condition (function: AMR_Alignment -> bool): a condition to test

        Returns:
            List[AMR_Alignment]: a list of matching AMR alignments
        """
        return [align for align in self if condition(align)]

    def to_json(self, anonymize: bool = False) -> List[Dict[str, Any]]:
        """
        Convert this alignment set to a JSON format for saving to a file
        Args:
            anonymize (bool): if set, remove any information that would reveal the AMR graph's structure to keep data
                anonymous. Replace relations with ":_".

        Returns:
            List[Dict[str, Any]]: a JSON representation of the alignment set
        """
        amr = self.amr if not anonymize else None
        if anonymize:
            json_ = [a.to_json(amr=amr) for a in self]
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
        Test whether every subgraph aligned in these alignments is a connected directed graph.

        Returns:
            bool: True if every aligned subgraph is a connected directed graph
        """
        return all(align.is_connected(self.amr) for align in self)

    def is_projective(self) -> bool:
        """
        Test whether these alignments are projective. If alignments are projective, every node and its descendents will
        be aligned to some token range and that token range won't be aligned to anything else. Projectivity suggests
        that the linear order of words matches the structure of the graph in a straightforward way.
        Returns:
            bool: True if all alignments in this Alignment set are projective, otherwise false
        """
        align = self.find_nonprojective_alignment()
        if align is None:
            return True
        return False

    def find_nonprojective_alignment(self, alignments: List[AMR_Alignment] = None) -> Optional[AMR_Alignment]:
        """
        Find a non-projective AMR Alignment. An alignment is non-projective if it creates a crossing edge, i.e., if the
        existence of the alignment results in a token range that is not aligned to just the descendants of a single
        node.
        Returns:
            AMR_Alignment: the first AMR_Alignment found to be non-projective
        """
        if alignments is None:
            alignments = self.__alignments
        reachable_nodes = amr_graph._get_reachable_nodes(self.amr)
        aligned_tokens = defaultdict(set)
        aligned_nodes = defaultdict(set)
        for align in alignments:
            for n in align.nodes():
                aligned_tokens[n].update(align.tokens())
            for s, r, t in align.edges():
                aligned_tokens[s].update(align.tokens())
            for tok in align.tokens():
                aligned_nodes[tok].update(align.nodes())
                aligned_nodes[tok].update(s for s, r, t in align.edges())
        nodes = [n for n in amr_iterators.nodes(self.amr, breadth_first=True)]
        for n in reversed(nodes):
            if len(reachable_nodes[n]) == 1:
                continue
            min_token_idx = float('inf')
            max_token_idx = float('-inf')
            for n2 in reachable_nodes[n]:
                for tok in aligned_tokens[n2]:
                    if tok < min_token_idx:
                        min_token_idx = tok
                    if tok > max_token_idx:
                        max_token_idx = tok
            for tok in range(min_token_idx, max_token_idx+1):
                for n2 in aligned_nodes[tok]:
                    if n2 not in reachable_nodes[n]:
                        return self.get(token_id=tok, node=n2)
        return None

    @staticmethod
    def _check_ids_match(amr: AMR,  json_alignment_list: List[Dict[str, Any]]):
        # check that node IDs match those of the AMR
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
    def _unanonymize_edges(amr: AMR, json_alignment_list: List[Dict[str, Any]]):
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
