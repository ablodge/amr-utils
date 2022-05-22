import re
import warnings
from collections import Counter, defaultdict
from typing import Tuple, Any, List, Dict, Optional, Iterable

import penman

from amr_utils.utils import class_name, silence_warnings

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
    > # equivalently:
    > amr = AMR.from_string(
    > '''
    > (c / chase-01
    >   :ARG0 (d / dog)
    >   :ARG1 (c / cat))
    > ''',
    > tokens=['Dogs', 'chase', 'cats', '.']
    > )
    > for node_id, label in amr.nodes.items():
    >     print(node_id, label)
    > for source_id, relation, target_id in amr.edges.items():
    >     print(node_id, relation, target_id)
    > print(amr.graph_string())
    >
    """

    class _TreePenmanModel(penman.model.Model):
        def deinvert(self, triple):
            return triple

        def invert(self, triple):
            return triple

    _penman_model = _TreePenmanModel()

    def __init__(self, id: str = None, tokens: List[str] = None, root: str = None, nodes: Dict[str, str] = None,
                 edges: List[Edge] = None, metadata: Dict[str, Any] = None, shape: 'AMR_Shape' = None):
        """
        Create an AMR
        Args:
            id (str): a unique ID for the sentence this AMR represents
            tokens (List[str]): a list of tokens for the sentence this AMR represents
            root (str): the node ID of the root node
            nodes (Dict[str, str]): a dictionary from node IDs to node labels
            edges (List[Tuple[str,str,str]]): a list of triples of the form (source_id, relation, target_id)
            metadata (Dict[str, Any]): a dictionary of metadata for this AMR, with keys such as 'snt', 'alignments',
                'notes', etc.
            shape (AMR_Shape): an extra parameter which saves the exact AMR shape, to preserve formatting
        """

        self.id = id  # might be None
        self.tokens = tokens  # might be None
        self.root = root  # might be None
        self.nodes = nodes if (nodes is not None) else {}
        self.edges = edges if (edges is not None) else []
        self.metadata = metadata if (metadata is not None) else {}
        self.shape = shape  # might be None

    @staticmethod
    def from_string(amr_string: str, id: str = None, tokens: List[str] = None, metadata: Dict[str, Any] = None):
        """
        Construct an AMR from `amr_string`. To read AMRs from a file, see `amr_readers.AMR_Reader`.
        Args:
            amr_string (str): a string representing an AMR graph (with or without metadata)
            id (str): a unique ID for the sentence this AMR represents
            tokens (List[str]): a list of tokens for the sentence this AMR represents
            metadata (Dict[str, Any]): a dictionary of metadata for this AMR, with keys such as 'snt', 'alignments',
                'notes', etc.

        Returns:
            AMR: an AMR

        Example Usage:
        > amr = AMR.from_string(
        >     '''
        >     (c / chase-01
        >       :ARG0 (d / dog)
        >       :ARG1 (c / cat))
        >     ''',
        >     id='1',
        >     tokens=['Dogs', 'chase', 'cats', '.']
        >     )
        > # equivalently
        > amr = AMR.from_string(
        >     '''
        >     # ::id 1
        >     # ::tok Dogs chase cats .
        >     (c / chase-01
        >       :ARG0 (d / dog)
        >       :ARG1 (c / cat))
        >     '''
        >     )
        """
        metadata_string = None
        if not Metadata.AMR_START_RE.match(amr_string):
            metadata_string, amr_string = Metadata.separate_metadata(amr_string)
        else:
            amr_string = amr_string.strip()
        with silence_warnings():
            try:
                penman_graph = penman.decode(amr_string, model=AMR._penman_model)
            except Exception:
                AMR._test_parens(amr_string)
                raise Exception(f'[{AMR}] Failed to read AMR from string:\n', amr_string)

        root = penman_graph.top
        nodes = {s: t for s, r, t in penman_graph.triples if r == ':instance'}
        edges = []
        new_attribute_nodes = {}
        num_parents = Counter()
        for i, triple in enumerate(penman_graph.triples):
            s, r, t = triple
            if r == ':instance':
                # an amr node
                pass
            elif AMR_Notation.is_constant(t):
                # attribute
                idx = 0
                while f'x{idx}' in nodes:
                    idx += 1
                new_n = f'x{idx}'
                new_attribute_nodes[i] = new_n
                nodes[new_n] = t
                edges.append((s, r, new_n))
            else:
                # edge
                edges.append((s, r, t))
                num_parents[t] += 1

        amr = AMR(root=root, nodes=nodes, edges=edges)
        amr.shape = AMR_Shape(penman_graph.triples, new_attribute_nodes)
        if metadata_string is not None:
            amr.id, amr.tokens, amr.metadata = Metadata.read_metadata(metadata_string)
        amr.id = id if (id is not None) else amr.id
        amr.tokens = tokens if (tokens is not None) else amr.tokens
        amr.metadata = metadata if (metadata is not None) else amr.metadata
        return amr

    def __str__(self):
        return f'[{class_name(self)} {self.id}]: ' + self.graph_string()

    def copy(self):
        """
        Create a copy
        Returns:
            AMR: copy
        """
        amr = AMR(tokens=self.tokens.copy(), id=self.id, root=self.root, nodes=self.nodes.copy(),
                  edges=self.edges.copy(), metadata=self.metadata.copy())
        if self.shape is not None:
            amr.shape = self.shape.copy()
        return amr

    def triples(self, normalize_inverse_relations=False) -> List[Triple]:
        """
        Get the triples in this AMR. Each triple takes the form (source_id, relation, target_id)
        or (source_id, relation, value). By default, :instance triples are appended first, then edges,
        then attributes. To get the triples in a graph ordering, use `depth_first_triples()`
        Args:
            normalize_inverse_relations (bool): convert inverse relations to normal relations
        Returns:
            List[tuple]: AMR triples of the form (source_id, relation, target_id) or (source_id, relation, value)
        """
        triples_ = []
        # instance triples
        for n in self.nodes:
            if AMR_Notation.is_constant(self.nodes[n]):
                if not self.nodes[n][0].isalpha() or \
                        any(e[-1] == n and AMR_Notation.is_attribute(self, e) for e in self.edges):
                    continue
            triples_.append((n, ':instance', self.nodes[n]))
        # edge triples
        for s, r, t in self.edges:
            if s not in self.nodes:
                warnings.warn(f'[{class_name(self)}] The node "{s}" in AMR "{self.id}" has no concept.')
            if t not in self.nodes:
                warnings.warn(f'[{class_name(self)}] The node "{t}" in AMR "{self.id}" has no concept.')
            elif AMR_Notation.is_attribute(self, (s, r, t)):
                continue
            if normalize_inverse_relations and AMR_Notation.is_inverse_relation(r):
                triples_.append((t, r[:-len('-of')], s))
            else:
                triples_.append((s, r, t))
        # attribute triples
        for s, r, t in self.edges:
            if t in self.nodes and AMR_Notation.is_attribute(self, (s, r, t)):
                triples_.append((s, r, self.nodes[t]))
        return triples_

    def depth_first_triples(self, subgraph_root: str = None, subgraph_nodes: Iterable[str] = None,
                            subgraph_edges: Iterable[Edge] = None, normalize_inverse_relations: bool = False) -> \
            List[Tuple[int, Triple]]:
        """
        Get the triples in this AMR in depth first order as a list of (depth, triple) pairs. Each triple takes the form
        (source_id, relation, target_id) or (source_id, relation, value).

        This function is called when building an AMR graph string. If you want to make a custom AMR Writer, you should
        call this function. You can use `AMR._graph_string()` as a template for building a graph string from triples.
        Args:
            subgraph_root (str): if set, list triples of the subgraph starting at this root
            subgraph_nodes (Iterable[str]): if set, list triples of the subgraph containing these nodes (and any
                connecting or outgoing edges)
            subgraph_edges (Iterable[Triple[str,str,str]]): if set, list triples of the subgraph while only
                considering these edges
            normalize_inverse_relations (bool): convert inverse relations to normal relations
        Returns:
            List[Tuple[int,Tuple[str,str,str]]]: a list of pairs (depth, triple) with AMR triples of the form
                (source_id, relation, target_id) or (source_id, relation, value)
        """
        preserve_shape = True
        if (subgraph_root is not None) or (subgraph_nodes is not None) or (subgraph_edges is not None):
            from amr_utils.amr_graph import process_subgraph
            preserve_shape = False
            root, nodes, edges = process_subgraph(self, subgraph_root, subgraph_nodes, subgraph_edges)
        else:
            root = self.root
            nodes = self.nodes
            edges = self.edges
        # test root
        if root not in self.nodes:
            if root is None:
                if nodes:
                    raise Exception(f'[{class_name(self)}] Cannot iterate AMR "{self.id}" because the root is None.')
                else:
                    return []
            elif not any(root in [s, t] for s, r, t in self.edges):
                raise Exception(f'[{class_name(self)}] Cannot iterate AMR "{self.id}" because the root node "{root}" '
                                f'does not exist.')
        # identify each node's child edges
        children = defaultdict(list)
        edges = [(i, e) for i, e in enumerate(edges)]
        for i, e in reversed(edges):
            s, r, t = e
            if s in nodes:
                children[s].append((i, e))
        # depth first algorithm
        visited_edges = set()
        completed_nodes = set()
        stack = []  # pairs (depth, edge_idx, edge)
        triples = []
        if root in self.nodes:
            triples.append((1, (root, ':instance', self.nodes[root])))
        else:
            warnings.warn(f'[{class_name(self)}] The node "{root}" in AMR "{self.id}" has no concept.')
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
                triples.append((depth, (s, r, self.nodes[t])))
                completed_nodes.add(t)
            else:
                # relation
                if normalize_inverse_relations and AMR_Notation.is_inverse_relation(edge[1]):
                    s, r, t = edge
                    triples.append((depth, (t, r[:-len('-of')], s)))
                else:
                    triples.append((depth, edge))
                if target not in completed_nodes and (subgraph_nodes is None or target in nodes):
                    if not preserve_shape or self.shape is None or self.shape.locate_instance(self, target) == edge_idx:
                        # instance
                        if target in self.nodes:
                            triples.append((depth + 1, (target, ':instance', self.nodes[target])))
                        else:
                            warnings.warn(
                                f'[{class_name(self)}] The node "{target}" in AMR "{self.id}" has no concept.')
                        completed_nodes.add(target)
                        # update stack
                        for new_edge_idx, new_edge in children[target]:
                            if new_edge_idx in visited_edges:
                                continue
                            stack.append((depth + 1, new_edge_idx, new_edge))
        if len(completed_nodes) < len(nodes):
            self._handle_missing_nodes([n for n in nodes if n not in completed_nodes])
        return triples

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
        return self._graph_string(indent=indent, pretty_print=pretty_print)

    def subgraph_string(self, subgraph_root: str, subgraph_nodes: Iterable[str] = None,
                        subgraph_edges: Iterable[Edge] = None, pretty_print: bool = False, indent: str = '\t'):
        """
        Build a string representation for a subgraph of this AMR as a PENMAN string.
        Args:
            subgraph_root (str): the subgraph's root node ID
            subgraph_nodes (Iterable[str]): nodes to be included in the subgraph (if not set, the subgraph will include
                all descendents of subgraph_root.)
            subgraph_edges (Iterable[tuple[str,str,str]]): edges to be included in the subgraph (if not set, the
                subgraph will include all edges whose source is in subgraph_nodes.)
            pretty_print (bool): Use indentation to make the PENMAN string more human-readable
            indent (str): String to use when indenting. Suggested values: '\t' or '    '.
                          This parameter is only used if pretty_print is set.
        Returns:
            str: PENMAN string
        """
        return self._graph_string(subgraph_root=subgraph_root, subgraph_nodes=subgraph_nodes,
                                  subgraph_edges=subgraph_edges, indent=indent, pretty_print=pretty_print)

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

    def _graph_string(self, pretty_print: bool = False, indent: str = '\t', subgraph_root: str = None,
                      subgraph_nodes: Iterable[str] = None, subgraph_edges: Iterable[Edge] = None) -> str:
        amr_sequence = []
        node_id_map = None
        if not all(n[0].isalpha() for n in self.nodes):
            node_id_map = self._default_node_ids()
        prev_depth = 0
        triples = self.depth_first_triples(subgraph_root=subgraph_root, subgraph_nodes=subgraph_nodes,
                                           subgraph_edges=subgraph_edges)
        if triples:
            # root node
            _, triple = triples[0]
            root = triple[0]
            node_id = root if (node_id_map is None) else node_id_map[root]
            amr_sequence.extend([f'(', node_id])
        for i, _ in enumerate(triples):
            depth, triple = _
            s, r, t = triple
            if depth < prev_depth:
                for _ in range(prev_depth - depth):
                    amr_sequence.append(')')
            if r == ':instance':
                # new concept
                amr_sequence.append(f' / {t}')
            else:
                whitespace = '\n' + (indent * depth) if pretty_print else ' '
                if AMR_Notation.is_constant(t):
                    # attribute
                    amr_sequence.append(f'{whitespace}{r} {t}')
                elif i + 1 < len(triples) and triples[i + 1][-1][1] == ':instance':
                    # relation
                    node_id = t if (node_id_map is None) else node_id_map[t]
                    amr_sequence.extend([f'{whitespace}{r} ', '(', node_id])
                else:
                    # reentrancy
                    node_id = t if (node_id_map is None) else node_id_map[t]
                    amr_sequence.append(f'{whitespace}{r} {node_id}')
            prev_depth = depth
        for _ in range(prev_depth):
            amr_sequence.append(')')
        if not amr_sequence:
            return '(a / amr-empty)'
        amr_string = ''.join(amr_sequence)
        if amr_sequence.count('(') != amr_sequence.count(')'):
            raise Exception(f'[{class_name(self)}] Failed to print AMR, Mismatched Parentheses:',
                            self.id, amr_string)
        return amr_string

    def _handle_missing_nodes(self, missing_nodes):
        from amr_utils.amr_graph import find_connected_components
        components = find_connected_components(self, subgraph_nodes=missing_nodes)
        msg = f'[{class_name(self)}] Failed to iterate AMR "{self.id}" ' \
              f'({len(missing_nodes)} of {len(self.nodes)} nodes were unreachable).\n'
        for component in components:
            root = component[0]
            sg_string = self.subgraph_string(root, component, pretty_print=False)
            msg += 'Missing: ' + sg_string + '\n'
        warnings.warn(msg)

    @staticmethod
    def _test_parens(amr_string):
        count = 0
        in_quote = False
        finished = False
        prev_char = None
        last_paren_idx = 0
        for i, char in enumerate(amr_string):
            if char == '"' and not prev_char == '\\':
                in_quote = not in_quote
            elif in_quote:
                continue
            elif char == "(":
                count += 1
                if finished:
                    raise Exception(f'[{class_name(AMR)}] Cannot parse AMR string. Reached end of parentheses early.'
                                    f'\nParentheses end: {amr_string[:last_paren_idx + 1]}'
                                    f'\nRemaining string: {amr_string[last_paren_idx + 1]:}')
                last_paren_idx = i
            elif char == ")":
                count -= 1
                if finished:
                    raise Exception(f'[{class_name(AMR)}] Cannot parse AMR string. Reached end of parentheses early.'
                                    f'\nParentheses end: {amr_string[:last_paren_idx + 1]}'
                                    f'\nRemaining string: {amr_string[last_paren_idx + 1]:}')
                last_paren_idx = i
            if count == 0:
                finished = True
            prev_char = char
        if count > 0:
            raise Exception(f'[{class_name(AMR)}] Cannot parse AMR string. ')


class AMR_Shape:
    """
    Two AMRs are considered equivalent if their graphs are equivalent, but for formatting, it is sometimes important
    to keep track of smaller details of an AMR's shape. When an AMR is read from a string or file, this class is used
    to save information like the ordering of edges and the placement of instance relations. That assures that the AMR's
    formatting doesn't change in unexpected ways when it is read and re-written to a file.

    This class can also be used to keep track of annotator artifacts, such as the placement of instance relations for
    nodes with more than one parent.
    """

    def __init__(self, triples: List[Triple], attribute_nodes: Dict[int, str]):
        """
        Create an AMR_Shape from a list of triples
        Args:
            triples (List[Tuple[str,str,str]]): a list of triples of the form (source_id, relation, target_id)
                                                or (source_id, relation, value).
        """
        self.triples = triples
        self.attribute_nodes = attribute_nodes
        parents = Counter()
        for s, r, t in self.triples:
            parents[t] += 1
        self.instance_locations = {}
        prev_triple = None
        edge_idx = 0
        for triple in triples:
            s, r, t = triple
            if r == ':instance':
                if parents[s] > 1:
                    self.instance_locations[s] = (edge_idx - 1, prev_triple)
            else:
                edge_idx += 1
            prev_triple = triple

    def locate_instance(self, amr, node) -> int:
        """
        Get the location of this node's instance as an edge index for the edge pointing to the instance location
        Args:
            amr: the AMR
            node: a node ID

        Returns:
            int: the edge index of the edge pointing to where the instance relation is placed
        """
        if node == amr.root:
            return -1
        if node in self.instance_locations:
            edge_idx, edge = self.instance_locations[node]
            if amr.edges[edge_idx] == edge:
                return edge_idx
            elif edge in amr.edges:
                return amr.edges.index(edge)
        for i, e in enumerate(amr.edges):
            s, r, t = e
            if t == node:
                return i
        raise Exception(f'[{class_name(self)}] Failed to locate instance. '
                        f'This typically happens when one or more edges have been deleted.')

    def copy(self):
        """
        Create a copy
        Returns:
            AMR_Shape: copy
        """
        return AMR_Shape(self.triples.copy(), self.attribute_nodes.copy())


class Metadata:
    """
    This class contains static functions for handling AMR metadata.

    An example of AMR metadata:

    # ::id 1 ::date 2020-05-21
    # ::tok The boy wants to go to New York .
    # ::snt The boy wants to go to New York.
    """

    SPLIT_METADATA_RE = re.compile(r'(?<=[^#])[\t ]::(?=\S+)')
    METADATA_RE = re.compile(r'# ::(?P<tag>\S+)(?P<value>.*)')
    AMR_START_RE = re.compile(r'^\s*\(', flags=re.MULTILINE)

    @staticmethod
    def read_metadata(metadata_string: str):
        """
        Read a string containing AMR metadata
        Args:
            metadata_string: a string

        Returns:
            tuple: a sentence ID string, a list of tokens, a dict of remaining metadata
        """
        lines = Metadata.SPLIT_METADATA_RE.sub('\n# ::', metadata_string).split('\n')
        lines = [line.strip() for line in lines]
        sent_id = None
        tokens = []
        metadata = {}
        for line in lines:
            tag, val = Metadata._parse_line(line)
            if tag is None:
                continue
            if tag == 'id':
                sent_id = val
            elif tag == 'tok':
                tokens = val.split()
            elif tag in ['root', 'node', 'edge']:
                continue
            else:
                metadata[tag] = val
        return sent_id, tokens, metadata

    @staticmethod
    def separate_metadata(amr_string):
        """
        Separate a string into a pair of strings (metadata string, AMR string)
        Args:
            amr_string: a string representing an AMR graph

        Returns:
            tuple: a pair of strings (metadata string, AMR string)
        """
        amr_starts = []
        for m in Metadata.AMR_START_RE.finditer(amr_string):
            amr_starts.append(m.start())
            break
        if len(amr_starts) == 0:
            raise Exception(f'[{Metadata}] Did not find AMR in string:\n', amr_string)
        return amr_string[:amr_starts[0]].strip(), amr_string[amr_starts[0]:].strip()

    @staticmethod
    def _parse_line(line: str):
        if not line.startswith('# ::'):
            if not line.strip():
                return None, None
            tag = 'snt'
            val = line[1:].strip() if line.startswith('#') else line.strip()
            return tag, val
        match = Metadata.METADATA_RE.match(line)
        if not match:
            raise Exception('Failed to parse metadata:', line)
        tag = match.group('tag')
        val = match.group('value').strip()
        return tag, val


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
    def sorted_edge_key(amr: AMR, edge: Edge):
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
