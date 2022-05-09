import re
import warnings
from typing import Tuple, Any, List, Dict, Container

from amr_utils.utils import class_name


class AMR:

    def __init__(self, tokens: List[str] = None, id: str = None, root: str = None, nodes: Dict[str, str] = None,
                 edges: List[Tuple[str, str, str]] = None, metadata: Dict[str, Any] = None,
                 reentrancy_artifacts: Dict[str, Tuple[str, str, str]] = None):
        """

        Args:
            tokens (list[str]):
            id (str):
            root (str):
            nodes (dict[str,str]):
            edges (list[tuple[str,str,str]]):
            metadata (dict[str,Any]):
        """

        self.tokens = tokens if (tokens is not None) else []
        self.root = root  # might be None
        self.nodes = nodes if (nodes is not None) else []
        self.edges = edges if (edges is not None) else []
        self.id = id if (id is not None) else 'None'
        self.metadata = metadata
        self.reentrancy_artifacts = reentrancy_artifacts  # might be None

    def __str__(self):
        return f'[{class_name(self)}: {self.id}]: ' + self.graph_string()

    def copy(self):
        """
        Create a copy of this AMR.
        Returns:
            AMR: a copy of this AMR
        """
        reentrancy_artifacts = self.reentrancy_artifacts.copy() if (self.reentrancy_artifacts is not None) else None
        return AMR(tokens=self.tokens.copy(), id=self.id, root=self.root, nodes=self.nodes.copy(),
                   edges=self.edges.copy(), metadata=self.metadata.copy(), reentrancy_artifacts=reentrancy_artifacts)

    def graph_string(self, pretty_print: bool = False, indent: str = '\t'):
        """

        Args:
            pretty_print (bool): Use indentation to make the graph string more human readable
            indent (str): String to use when indenting. This parameter is only used if pretty_print is set.
                          Suggested values: '\t' or '    '.

        Returns:
            str: this AMR represented as a string
        """
        amr_string, completed_nodes = self._graph_string(pretty_print=pretty_print, indent=indent)
        # handle errors
        if len(completed_nodes) < len(self.nodes):
            missing_nodes = {n: self.nodes[n] for n in self.nodes if n not in completed_nodes}
            warnings.warn(f'[{class_name(self)}] Failed to print AMR {self.id} '
                          f'{len(missing_nodes)} of {len(self.nodes)} nodes were unreachable.\n'
                          f'Missing: {missing_nodes}\n'
                          + amr_string)
        return amr_string

    def triples(self, normalize_inverse_relations=False):
        """
        Iterate the triples in this AMR. Each triple takes the form (source_id, relation, target_id)
        or (source_id, relation, value). By default, :instance triples are yielded first, then edges,
        then attributes. To get the triples in a graph order, use `amr_iterators.triples()`
        Args:
            normalize_inverse_relations (bool): convert inverse relations to normal relations

        Yields:
            tuple: AMR triples of the form (source_id, relation, target_id) or (source_id, relation, value)
        """
        # instance triples
        for n in self.nodes:
            if AMR_Notation.is_attribute(self.nodes[n]):
                if not self.nodes[n][0].isalpha() or any(r == ':mode' for s, r, t in self.edges if t == n):
                    continue
            yield n, ':instance', self.nodes[n]
        # edge triples
        for s, r, t in self.edges:
            if AMR_Notation.is_attribute(self.nodes[t]) and not (r != ':mode' and self.nodes[t][0].isalpha()):
                continue
            if normalize_inverse_relations and AMR_Notation.is_inverse_relation(r):
                yield t, r[:-len('-of')], s
            else:
                yield s, r, t
        # attribute triples
        for s, r, t in self.edges:
            if AMR_Notation.is_attribute(self.nodes[t]):
                yield s, r, self.nodes[t]

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

    def _is_valid_instance_location(self, edge):
        s, r, t = edge
        if self.reentrancy_artifacts is None:
            return True
        else:
            if t not in self.reentrancy_artifacts or edge == self.reentrancy_artifacts[t]:
                return True
            return False

    def _graph_string(self, pretty_print: bool = True, indent: bool = '\t',
                      subgraph_root: str = None, subgraph_nodes: Container[str] = None):
        root = self.root if subgraph_root is None else subgraph_root
        nodes = self.nodes if subgraph_nodes is None else subgraph_nodes
        if root is None or root not in nodes:
            return '(a / amr-empty)'
        completed_nodes = set()
        completed_concepts = set()
        node_map = None
        if not all(n[0].isalpha() for n in self.nodes):
            node_map = self._default_node_ids()
        # add root node
        node_id = root if node_map is None else node_map[root]
        concept = self.nodes[root]
        amr_string = [f'({node_id} / {concept}']
        completed_concepts.add(root)
        completed_nodes.add(root)
        prev_depth = 1
        start_parens = 1
        end_parens = 0

        for depth, next_edge in self._depth_first_edges(alphabetical_edges=False, ignore_reentrancies=False,
                                                        subgraph_root=subgraph_root, subgraph_nodes=subgraph_nodes):
            s, r, t = next_edge
            if depth < prev_depth:
                for _ in range(prev_depth - depth):
                    amr_string.append(')')
                    end_parens += 1
            if pretty_print:
                whitespace = '\n' + (indent * depth)
            else:
                whitespace = ' '
            node_id = t if node_map is None else node_map[t]
            concept = self.nodes[t]
            if AMR_Notation.is_attribute(concept) and not (concept[0].isalpha() and r != ':mode'):
                # attribute
                amr_string.append(f'{whitespace}{r} {concept}')
                completed_nodes.add(t)
            elif t not in completed_concepts and self._is_valid_instance_location(next_edge):
                # new concept
                amr_string.extend([f'{whitespace}{r} ', f'({node_id} / {concept}'])
                completed_concepts.add(t)
                start_parens += 1
                depth += 1
            else:
                # reentrancy
                amr_string.append(f'{whitespace}{r} {node_id}')
            completed_nodes.add(t)
            if start_parens - end_parens != depth:
                raise Exception(f'[{class_name(self)}] Failed to print AMR, Mismatched Parentheses:',
                                self.id, ''.join(amr_string))
            prev_depth = depth
        for _ in range(prev_depth):
            amr_string.append(')')
            end_parens += 1
        if start_parens != end_parens:
            raise Exception(f'[{class_name(self)}] Failed to print AMR, Mismatched Parentheses:',
                            self.id, ''.join(amr_string))
        amr_string = ''.join(amr_string)
        return amr_string, completed_nodes

    def _depth_first_edges(self, alphabetical_edges: bool = False, ignore_reentrancies: bool = False,
                           subgraph_root: str = None, subgraph_nodes: Container[str] = None):
        """
        Iterate the edges in an AMR in depth first order
        """
        # assign root
        if subgraph_root is None:
            root = self.root
        else:
            root = subgraph_root
        if root is None:
            return
        # identify each nodes child edges
        children = {n: [] for n in self.nodes}
        edges_ = [(i, e) for i, e in enumerate(self.edges)]
        if subgraph_nodes is None:
            for i, e in reversed(edges_):
                s, r, t = e
                children[s].append((i, e))
        else:
            for i, e in reversed(edges_):
                s, r, t = e
                if s in subgraph_nodes:
                    children[s].append((i, e))
        # alphabetize edges
        if alphabetical_edges:
            for n in self.nodes:
                if len(children[n]) > 1:
                    children[n] = sorted(children[n], key=lambda x: AMR_Notation.lexicographic_edge_key(self, x[-1]),
                                         reverse=True)
        # depth first algorithm
        stack = []  # pairs (depth, edge)
        for edge_idx, edge in children[root]:
            stack.append((1, edge_idx, edge))
        visited_edges = set()
        visited_nodes = {root} if ignore_reentrancies else None
        while stack:
            depth, edge_idx, edge = stack.pop()
            target = edge[-1]
            if edge_idx in visited_edges: continue
            if ignore_reentrancies:
                if target in visited_nodes:
                    continue
                visited_nodes.add(target)
            visited_edges.add(edge_idx)
            if children[target] and not target == root:
                if alphabetical_edges or self._is_valid_instance_location(edge):
                    for edge2_idx, edge2 in children[target]:
                        stack.append((depth + 1, edge2_idx, edge2))
            yield depth, edge


class AMR_Notation:
    FRAME_RE = re.compile(r'^([a-z]+[-])*[a-z]+[-][0-9]{2,3}$')
    RELATION_PREFIXES_RE = re.compile(r'^:(ARG\d|arg\d|snt[1-9]\d*|op[1-9]\d*)(-of)?$')

    @staticmethod
    def is_frame(concept):
        """

        Args:
            concept:

        Returns:

        """
        return bool(AMR_Notation.FRAME_RE.match(concept))

    @staticmethod
    def is_attribute(concept):
        """

        Args:
            concept:

        Returns:

        """
        if not concept[0].isalpha():
            return True
        if concept in ['imperative', 'expressive']:
            return True
        return False

    @staticmethod
    def is_inverse_relation(relation):
        """

        Args:
            relation:

        Returns:

        """
        return (relation.endswith('-of') and relation not in
                [':consist-of', ':prep-out-of', ':prep-on-behalf-of'])

    @staticmethod
    def invert_relation(relation):
        """

        Args:
            relation:

        Returns:

        """
        if relation == ':domain':
            return ':mod'
        elif relation == ':mod':
            return ':domain'
        elif AMR_Notation.is_inverse_relation(relation):
            return relation[:-len('-of')]
        return relation + '-of'

    @staticmethod
    def lexicographic_edge_key(amr: AMR, edge: Tuple[str, str, str]):
        """

        Args:
            amr:
            edge:

        Returns:

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
    def is_relation(relation: str):
        """

        Args:
            relation:

        Returns:

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
