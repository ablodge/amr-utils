import re
import warnings
from collections import Counter
from typing import Tuple, Any, List, Dict, Optional, Iterable, Iterator

from amr_utils.utils import class_name

Edge = Tuple[str, str, str]
Triple = Tuple[str, str, str]


class AMR:
    """
    This class implements a simple interface for representing and manipulating Abstract Meaning Representation data.
    Abstract Meaning Representation (AMR) is a computational representation of sentence (See https://amr.isi.edu/).
    An AMR represents "who did what to whom" for a given sentence. It includes information such as word senses,
    semantic role labels, and named entity types. AMRs are represented as a directed acyclic graph, where nodes
    represent people, places, things, and events, and edges represent the relationships between them. For example:

    # ::tok The boy wants to go to New York .
    (w / want-01
        :ARG0 (b / boy)
        :ARG1 (g / go-02
            :ARG0 b
            :ARG4 (c / city
                :name (n / name
                    :op1 "New" :op2 "York" :op3 "City"))))

    For more on AMR notation, see https://github.com/amrisi/amr-guidelines/blob/master/amr.md.

    A note about implementation: several classes for storing AMRs exist and differ from this one a few ways. First, this
    class does not treat instance relations and attribute relations as special, unary relations. Instead, to keep the
    data simple and easy to use, everything is represented in terms of labelled nodes and labeled edges. Instance
    relations and constants are converted to node labels, and attributes are treated the same as edges. Second, the date
    in this class is entirely mutable, making it easy to add or remove nodes and edges. Third, inverse edges such as
    :ARG0-of are not normalized by default, so that it is easier to interpret the AMR's DAG structure.

    To read AMRs from a file, see `amr_readers.AMR_Reader`.

    Attributes:
        id (str): a unique ID for the sentence this AMR represents
        tokens (List[str]): a list of tokens for the sentence this AMR represents
        root (str): the node ID of the root node
        nodes (Dict[str, str]): a dictionary from node IDs to node labels
        edges (List[Tuple[str,str,str]]): a list of triples of the form (source_id, relation, target_id)
        metadata (Dict[str, Any]): a dictionary of metadata for this AMR, with keys such as 'snt', 'alignments',
            'notes', etc.

    Example Usage:
    > amr = AMR(tokens=['Dogs', 'chase', 'cats', '.'],
    >           root='c',
    >           nodes={'c': 'chase-01', 'd': 'dog', 'c2': 'cat'},
    >           edges=[('c', ':ARG0', 'd'), ('c', ':ARG1', 'c2')]
    >           )
    > for node_id, label in amr.nodes.items():
    >     print(node_id, label)
    > for source_id, relation, target_id in amr.edges.items():
    >     print(node_id, relation, target_id)
    > print(amr.graph_string())
    """

    def __init__(self, sent_id: str = None, tokens: List[str] = None, root: str = None, nodes: Dict[str, str] = None,
                 edges: List[Edge] = None, metadata: Dict[str, Any] = None, shape: 'AMR_Shape' = None):
        """
        Create an AMR
        Args:
            sent_id (str): a unique ID for the sentence this AMR represents
            tokens (List[str]): a list of tokens for the sentence this AMR represents
            root (str): the node ID of the root node
            nodes (Dict[str, str]): a dictionary from node IDs to node labels
            edges (List[Tuple[str,str,str]]): a list of triples of the form (source_id, relation, target_id)
            metadata (Dict[str, Any]): a dictionary of metadata for this AMR, with keys such as 'snt', 'alignments',
                'notes', etc.
            shape (AMR_Shape): an extra parameter which saves the exact AMR shape, to preserve formatting
        """

        self.tokens = tokens if (tokens is not None) else []
        self.root = root  # might be None
        self.nodes = nodes if (nodes is not None) else {}
        self.edges = edges if (edges is not None) else []
        self.id = sent_id if (sent_id is not None) else 'None'
        self.metadata = metadata if (metadata is not None) else {}
        self.shape = shape if (shape is not None) else None

    def __str__(self):
        return f'[{class_name(self)} {self.id}]: ' + self.graph_string()

    def copy(self):
        """
        Create a copy
        Returns:
            AMR: copy
        """
        amr = AMR(tokens=self.tokens.copy(), sent_id=self.id, root=self.root, nodes=self.nodes.copy(),
                  edges=self.edges.copy(), metadata=self.metadata.copy())
        if self.shape is not None:
            amr.shape = self.shape.copy()
        return amr

    def triples(self, normalize_inverse_relations=False) -> Iterator[Triple]:
        """
        Iterate the triples in this AMR. Each triple takes the form (source_id, relation, target_id)
        or (source_id, relation, value). By default, :instance triples are yielded first, then edges,
        then attributes. To get the triples in a graph ordering, use `depth_first_triples()`
        Args:
            normalize_inverse_relations (bool): convert inverse relations to normal relations
        Yields:
            tuple: AMR triples of the form (source_id, relation, target_id) or (source_id, relation, value)
        """
        # instance triples
        for n in self.nodes:
            if AMR_Notation.is_constant(self.nodes[n]):
                if not self.nodes[n][0].isalpha() or \
                        any(e[-1] == n and AMR_Notation.is_attribute(self, e) for e in self.edges):
                    continue
            yield n, ':instance', self.nodes[n]
        # edge triples
        for s, r, t in self.edges:
            if s not in self.nodes:
                warnings.warn(f'[{class_name(self)}] The node {s} in AMR {self.id} has no concept.')
            if t not in self.nodes:
                warnings.warn(f'[{class_name(self)}] The node {t} in AMR {self.id} has no concept.')
            elif AMR_Notation.is_attribute(self, (s, r, t)):
                continue
            if normalize_inverse_relations and AMR_Notation.is_inverse_relation(r):
                yield t, r[:-len('-of')], s
            else:
                yield s, r, t
        # attribute triples
        for s, r, t in self.edges:
            if t in self.nodes and AMR_Notation.is_attribute(self, (s, r, t)):
                yield s, r, self.nodes[t]

    def depth_first_triples(self, subgraph_root: str = None, subgraph_nodes: Iterable[str] = None,
                            subgraph_edges: Iterable[Edge] = None, normalize_inverse_relations: bool = False) -> \
            Iterator[Tuple[int, Triple]]:
        """
        Iterate the triples in this AMR in depth first order. Each triple takes the form
        (source_id, relation, target_id) or (source_id, relation, value).
        Args:
            subgraph_root (str): if set, iterate triples of the subgraph starting at this root
            subgraph_nodes (Iterable[str]): if set, iterate triples of the subgraph containing these nodes (and any
                connecting or outgoing edges)
            subgraph_edges (Iterable[Triple[str,str,str]]): if set, iterate triples of the subgraph while only
                considering these edges
            normalize_inverse_relations (bool): convert inverse relations to normal relations
        Yields:
            tuple[int,tuple[str,str,str]]: an int indicating depth, an AMR triple of the form
                (source_id, relation, target_id) or (source_id, relation, value)
        """
        root = self.root if (subgraph_root is None) else subgraph_root
        nodes = self.nodes if (subgraph_nodes is None) else {n for n in subgraph_nodes}
        edges = self.edges if (subgraph_edges is None) else [e for e in subgraph_edges if e in self.edges]
        # identify each node's child edges
        children = {n: [] for n in self.nodes}
        edges = [(i, e) for i, e in enumerate(edges)]
        for i, e in reversed(edges):
            s, r, t = e
            if s in nodes:
                children[s].append((i, e))
        # depth first algorithm
        visited_edges = set()
        completed_nodes = set()
        node_mentions = Counter()
        stack = []  # pairs (depth, edge_idx, edge)
        if root is None:
            self._handle_missing_nodes(nodes)
            return
        if root in self.nodes:
            yield 1, (root, ':instance', self.nodes[root])
        else:
            if not any(root in [s,t] for s,r,t in self.edges):
                warnings.warn(f'[{class_name(self)}] The node {root} in AMR {self.id} does not exist.')
                return
            warnings.warn(f'[{class_name(self)}] The node {root} in AMR {self.id} has no concept.')
        for edge_idx, edge in children[root]:
            stack.append((1, edge_idx, edge))
        completed_nodes.add(root)
        while stack:
            depth, edge_idx, edge = stack.pop()
            visited_edges.add(edge_idx)
            target = edge[-1]

            if target in self.nodes and AMR_Notation.is_attribute(self, edge):
                # attribute
                s, r, t = edge
                yield depth, (s, r, self.nodes[t])
                completed_nodes.add(t)
            else:
                # relation
                if normalize_inverse_relations and AMR_Notation.is_inverse_relation(edge[1]):
                    s, r, t = edge
                    yield depth, (t, r[:-len('-of')], s)
                else:
                    yield depth, edge
                if target not in completed_nodes and target in nodes:
                    if self.shape is None or self.shape.locate_instance(target) == node_mentions[target]:
                        # instance
                        if target in self.nodes:
                            yield depth + 1, (target, ':instance', self.nodes[target])
                        else:
                            warnings.warn(f'[{class_name(self)}] The node {target} in AMR {self.id} has no concept.')
                        completed_nodes.add(target)
                        # update stack
                        for new_edge_idx, new_edge in children[target]:
                            if new_edge_idx in visited_edges:
                                continue
                            stack.append((depth + 1, new_edge_idx, new_edge))
                node_mentions[target] += 1
        if subgraph_root and not subgraph_nodes:
            return
        if len(completed_nodes) < len(nodes):
            self._handle_missing_nodes([n for n in nodes if n not in completed_nodes])

    def graph_string(self, pretty_print: bool = False, indent: str = '\t'):
        """
        Build a string representation for this AMR graph as a PENMAN string.
        Args:
            pretty_print (bool): Use indentation to make the PENMAN string more human-readable
            indent (str): String to use when indenting. Suggested values: '\t' or '    '.
                          This parameter is only used if pretty_print is set.
        Returns:
            str: PENMAN string for this AMR
        """
        amr_sequence = self._graph_string_as_list()
        return self._format_graph_string(amr_sequence, indent=indent, pretty_print=pretty_print)

    def subgraph_string(self, subgraph_root: str, subgraph_nodes: Iterable[str] = None,
                        subgraph_edges: Iterable[Edge] = None, pretty_print: bool = False, indent: str = '\t'):
        """
        Build a string representation for a subgraph of this AMR as a PENMAN string.
        Args:
            subgraph_root (str): the subgraph's root node ID
            subgraph_nodes (Iterable[str]): nodes to be included in the subgraph
            subgraph_edges (Iterable[tuple[str,str,str]]): edges to be included in the subgraph, if set, otherwise by
                default any edge whose source is in subgraph_nodes will be included.
            pretty_print (bool): Use indentation to make the PENMAN string more human-readable
            indent (str): String to use when indenting. Suggested values: '\t' or '    '.
                          This parameter is only used if pretty_print is set.
        Returns:
            str: PENMAN string
        """
        if subgraph_nodes:
            subgraph_nodes = [n for n in subgraph_nodes if n in self.nodes]
        amr_sequence = self._graph_string_as_list(subgraph_root, subgraph_nodes, subgraph_edges)
        return self._format_graph_string(amr_sequence, indent=indent, pretty_print=pretty_print)

    def _default_node_ids(self):
        node_ids = {}
        for n in self.nodes:
            letter = self.nodes[n][0].lower()
            if not letter.isalpha():
                i = 0
                while f'x{i}' in node_ids:
                    i += 1
                node_ids[n] = f'x{i}'
            elif letter in node_ids:
                i = 2
                while f'{letter}{i}' in node_ids:
                    i += 1
                node_ids[n] = f'{letter}{i}'
            else:
                node_ids[n] = letter
        return node_ids

    def _format_graph_string(self, amr_sequence: List[str], pretty_print: bool = False, indent: str = '\t') -> str:
        depth = 0
        for i, element in enumerate(amr_sequence):
            if element == '(':
                depth += 1
            elif element == ')':
                depth -= 1
            elif element.startswith(':'):
                r = element
                whitespace = '\n' + (indent * depth) if pretty_print else ' '
                amr_sequence[i] = f'{whitespace}{r} '
            elif element == '/':
                amr_sequence[i] = ' / '
        amr_string = ''.join(amr_sequence)
        return amr_string

    def _graph_string_as_list(self, subgraph_root: str = None, subgraph_nodes: Iterable[str] = None,
                              subgraph_edges: Iterable[Edge] = None) -> List[str]:
        root = self.root if (subgraph_root is None) else subgraph_root
        nodes = self.nodes if (subgraph_nodes is None) else subgraph_nodes
        if root is None or root not in nodes:
            if nodes:
                self._handle_missing_nodes(set(nodes))
            return ['(', 'a', '/', 'amr-empty', ')']
        amr_sequence = []
        completed_nodes = set()
        node_map = None
        if not all(n[0].isalpha() for n in nodes):
            node_map = self._default_node_ids()
        nodes_todo = [root]
        prev_depth = 0
        for depth, triple in self.depth_first_triples(subgraph_root=subgraph_root, subgraph_nodes=subgraph_nodes,
                                                      subgraph_edges=subgraph_edges):
            s, r, t = triple
            if nodes_todo:
                node_id = nodes_todo.pop()
                if r == ':instance':
                    amr_sequence.append('(')
                amr_sequence.append(node_id)
            if depth < prev_depth:
                for _ in range(prev_depth - depth):
                    amr_sequence.append(')')
            node_id = t if (node_map is None) else node_map[t]
            if r == ':instance':
                # new concept
                amr_sequence.extend(['/', t])
                completed_nodes.add(s)
            elif AMR_Notation.is_constant(t):
                # attribute
                amr_sequence.extend([r, t])
                completed_nodes.add(f'attr{len(completed_nodes)}')
            else:
                # relation
                amr_sequence.append(r)
                nodes_todo.append(node_id)
            prev_depth = depth
        if nodes_todo:
            node_id = nodes_todo.pop()
            amr_sequence.append(node_id)
        for _ in range(prev_depth):
            amr_sequence.append(')')
        if amr_sequence.count('(') != amr_sequence.count(')'):
            raise Exception(f'[{class_name(self)}] Failed to print AMR, Mismatched Parentheses:',
                            self.id, ' '.join(amr_sequence))
        return amr_sequence

    def _handle_missing_nodes(self, missing_nodes):
        from amr_utils.amr_graph import find_connected_components
        components = find_connected_components(self, nodes=missing_nodes)
        msg = f'[{class_name(self)}] Failed to iterate AMR {self.id} ' \
              f'({len(missing_nodes)} of {len(self.nodes)} nodes were unreachable).\n'
        for component in components:
            root = component[0]
            sg_string = self.subgraph_string(root, component, pretty_print=False)
            msg += 'Missing: '+sg_string + '\n'
        warnings.warn(msg)


class AMR_Shape:
    """
    Two AMRs are considered equivalent if their graphs are equivalent, but for formatting, it is sometimes important
    to keep track of smaller details of an AMR's shape. When an AMR is read from a string or file, this class is used
    to save information like the ordering of edges and the placement of instance relations. That assures that the AMR's
    formatting doesn't change in unexpected ways when it is read and re-written to a file.

    This class can also be used to keep track of annotator artifacts, such as the placement of instance relations for
    nodes with more than one parent.
    """

    def __init__(self, triples: List[Triple]):
        """
        Create an AMR_Shape from a list of triples
        Args:
            triples (List[Tuple[str,str,str]]): a list of triples of the form (source_id, relation, target_id)
                                                or (source_id, relation, value).
        """
        self.triples = triples
        self.instance_placements = {}
        node_mentions = Counter()
        root = triples[0][0]
        node_mentions[root] = 1
        for triple in triples:
            s, r, t = triple
            if r == ':instance':
                if node_mentions[s] > 1:
                    self.instance_placements[s] = node_mentions[s] - 1
            elif AMR_Notation.is_constant(t):
                pass
            else:
                node_mentions[t] += 1

    def locate_instance(self, node) -> int:
        """
        Get the location of this node's instance relation as an index
        Args:
            node: a node ID

        Returns:
            int: the index of the node mention (in depth first order) where the instance relation is placed
        """
        if node in self.instance_placements:
            return self.instance_placements[node]
        return 0

    def copy(self):
        """
        Create a copy
        Returns:
            AMR_Shape: copy
        """
        return AMR_Shape(self.triples.copy())


class AMR_Notation:
    """
    This class contains static methods related to AMR notation such as methods for inverting or reifying a relation or
    testing whether a string is an AMR constant, an AMR frame, or a standard AMR relation.
    """
    FRAME_RE = re.compile(r'^([a-z]+-)+\d{2,3}$')
    RELATION_PREFIXES_RE = re.compile(r'^:(ARG\d\d?|arg\d\d?|snt[1-9]\d{0,2}|op[1-9]\d{0,2})(-of)?$')

    @staticmethod
    def is_frame(concept) -> bool:
        """
        Test if this string is the format of an AMR frame
        Args:
            concept (str): string to test

        Returns:
            bool: True if and only if this is a frame
        """
        return bool(AMR_Notation.FRAME_RE.match(concept))

    @staticmethod
    def is_constant(concept: str) -> bool:
        """
        Test if this string is the format of an AMR constant
        Args:
            concept (str): string to test

        Returns:
            bool: True if and only if this is a constant
        """
        if not concept[0].isalpha():
            return True
        if concept in ['imperative', 'expressive']:
            return True
        return False

    @staticmethod
    def is_attribute(amr: AMR, edge: Edge) -> bool:
        """
        Test if this edge is an attribute
        Args:
            amr (AMR): the AMR
            edge (Tuple[str,str,str]): edge to test

        Returns:
            bool: True if and only if this is an attribute
        """
        concept = amr.nodes[edge[-1]]
        if not concept[0].isalpha():
            return True
        if concept in ['imperative', 'expressive'] and edge[1] == ':mode':
            return True
        return False

    @staticmethod
    def is_inverse_relation(relation) -> bool:
        """
        Test if this relation is an inverse relation
        Args:
            relation (str): relation

        Returns:
            bool: True if and only if this is an inverse relation
        """
        return (relation.endswith('-of') and relation not in
                [':consist-of', ':prep-out-of', ':prep-on-behalf-of'])

    @staticmethod
    def invert_relation(relation) -> str:
        """
        Turn non-inverse relations into inverse relations and inverse relations into non-inverse relations.
        Args:
            relation (str): relation

        Returns:
            str: inverted relation
        """
        if relation == ':domain':
            return ':mod'
        elif relation == ':mod':
            return ':domain'
        elif AMR_Notation.is_inverse_relation(relation):
            return relation[:-len('-of')]
        return relation + '-of'

    @staticmethod
    def lexicographic_edge_key(amr: AMR, edge: Edge):
        """
        Create a key for this edge that can be used in `sorted()` to sort edges alphabetically.
        Rather than alphabetizing edges by their string representation, this key also properly orders numbers so that
        :snt1, :snt2, ..., :snt10, :snt11 are properly ordered by number.
        Args:
            amr (AMR): an AMR
            edge (Tuple[str,str,str]): an edge

        Returns:
            Tuple: a key that can be used in `sorted()` to completely order edges
        """
        s, r, t = edge
        digits = -1
        inv = ''
        if AMR_Notation.is_inverse_relation(r):
            inv = '-of'
            r = r[:-len(inv)]
        for prefix in [':ARG', ':op', ':snt']:
            if r.startswith(prefix) and r[len(prefix):].isdigit():
                digits = int(r[len(prefix):])
                r = prefix
                break
        return r, digits, inv, amr.nodes[t]

    @staticmethod
    def is_relation(relation: str) -> bool:
        """
        Test whether this string is an existing AMR relation, i.e. a relation specified by the AMR guidelines.
        This includes inverse relations and numbered relations such as :ARG0, ..., :ARG99, :op1, ..., :op999,
        and :snt1, ..., :snt999.
        Args:
            relation: string to test

        Returns:
            bool: True if and only if this is an existing relation
        """
        if relation in [':domain', ':mod']:
            return True
        if AMR_Notation.is_inverse_relation(relation):
            relation = relation[:-len('-of')]
        if AMR_Notation.RELATION_PREFIXES_RE.match(relation):
            return True
        elif relation in AMR_Notation.STANDARD_RELATIONS:
            return True
        elif relation in AMR_Notation.QUANTITY_RELATIONS:
            return True
        elif relation in AMR_Notation.DATE_TIME_RELATIONS:
            return True
        elif relation in AMR_Notation.PREP_RELATIONS:
            return True
        elif relation in AMR_Notation.CONJ_RELATIONS:
            return True
        return False

    @staticmethod
    def reify_relation(relation: str) -> Optional[Tuple[str, str, str]]:
        """
        Get the reification of this relation as a node and incoming/outgoing relations.
        For example, :age becomes age-01 when reified, so `reify_relation(':age')` will
        return ':ARG1-of', 'age-01', ':ARG2'.
        Args:
            relation: relation to reify

        Returns:
            tuple: an incoming relation, a node label which reifies the relation, an outgoing edge
        """
        if relation in AMR_Notation.REIFICATIONS:
            return AMR_Notation.REIFICATIONS[relation]
        return None

    STANDARD_RELATIONS = [
        ':accompanier',
        ':age',
        ':beneficiary',
        ':cause',
        ':concession',
        ':condition',
        ':consist-of',
        ':cost',
        ':degree',
        ':destination',
        ':direction',
        # ':domain',
        ':duration',
        ':employed-by',
        ':example',
        ':extent',
        ':frequency',
        ':instrument',
        ':li',
        ':location',
        ':manner',
        ':meaning',
        ':medium',
        # ':mod',
        ':mode',
        ':name',
        ':ord',
        ':part',
        ':path',
        ':polarity',
        ':polite',
        ':poss',
        ':purpose',
        ':role',
        ':source',
        ':subevent',
        ':subset',
        ':superset',
        ':time',
        ':topic',
        ':value',
    ]

    DATE_TIME_RELATIONS = [
        #
        ':day',
        ':month',
        ':year',
        ':weekday',
        ':time',
        ':timezone',
        ':quarter',
        ':dayperiod',
        ':season',
        ':year2',
        ':decade',
        ':century',
        ':calendar',
        ':era',
        # ':mod',
    ]

    QUANTITY_RELATIONS = [
        #
        ':quant',
        ':unit',
        ':scale',
    ]

    PREP_RELATIONS = [
        #
        ':prep-against',
        ':prep-along-with',
        ':prep-amid',
        ':prep-among',
        ':prep-as',
        ':prep-at',
        ':prep-by',
        ':prep-for',
        ':prep-from',
        ':prep-in',
        ':prep-in-addition-to',
        ':prep-into',
        ':prep-on',
        ':prep-on-behalf-of',
        ':prep-out-of',
        ':prep-to',
        ':prep-toward',
        ':prep-under',
        ':prep-with',
        ':prep-without',
    ]

    CONJ_RELATIONS = [
        ':conj-as-if',
    ]

    REIFICATIONS = {
        ':accompanier': (':ARG1-of', 'accompany-01', ':ARG0'),
        ':age': (':ARG1-of', 'age-01', ':ARG2'),
        ':beneficiary': (':ARG1-of', 'receive-01', ':ARG0'),  # also benefit-01
        ':concession': (':ARG1-of', 'have-concession-91', ':ARG2'),
        ':condition': (':ARG1-of', 'have-condition-91', ':ARG2'),
        ':degree': (':ARG2-of', 'have-degree-91', ':ARG3'),
        ':destination': (':ARG1-of', 'be-destined-for-91', ':ARG2'),
        ':duration': (':ARG1-of', 'last-01', ':ARG2'),
        ':example': (':ARG1-of', 'exemplify-01', ':ARG0'),
        ':extent': (':ARG1-of', 'have-extent-91', ':ARG2'),
        ':frequency': (':ARG1-of', 'have-frequency-91', ':ARG2'),
        ':instrument': (':ARG1-of', 'have-instrument-91', ':ARG2'),
        ':li': (':ARG1-of', 'have-li-91', ':ARG2'),
        ':location': (':ARG1-of', 'be-located-at-91', ':ARG2'),
        ':manner': (':ARG1-of', 'have-manner-91', ':ARG2'),
        ':mod': (':ARG1-of', 'have-mod-91', ':ARG2'),
        ':name': (':ARG1-of', 'have-name-91', ':ARG2'),
        ':ord': (':ARG1-of', 'have-ord-91', ':ARG2'),
        ':part': (':ARG1-of', 'have-part-91', ':ARG2'),
        ':poss': (':ARG0-of', 'have-03', ':ARG1'),  # also own-01
        ':polarity': (':ARG1-of', 'have-polarity-91', ':ARG2'),
        ':purpose': (':ARG1-of', 'have-purpose-91', ':ARG2'),
        ':quant': (':ARG1-of', 'have-quant-91', ':ARG2'),
        ':source': (':ARG1-of', 'be-from-91', ':ARG2'),
        ':subevent': (':ARG1-of', 'have-subevent-91', ':ARG2'),
        ':time': (':ARG1-of', 'be-temporally-at-91', ':ARG2'),
        ':topic': (':ARG0-of', 'concern-02', ':ARG1'),
        ':value': (':ARG1-of', 'have-value-91', ':ARG2'),

    }
