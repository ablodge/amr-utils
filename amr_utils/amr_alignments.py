import json
import sys
from collections import Counter, defaultdict
from typing import Iterable, Callable, Tuple, Dict, Any, Optional, List

from sortedcontainers import SortedList

from amr_utils.amr import AMR
from amr_utils.utils import class_name


class AMR_Alignment:

    def __init__(self, type: str = None, tokens: Iterable[int] = None, nodes: Iterable[str] = None,
                 edges: Iterable[Tuple[str, str, str]] = None):
        """

        Args:
            type:
            tokens:
            nodes:
            edges:
        """
        self.type = type if type else ''
        self.tokens = SortedList(tokens) if (tokens is not None) else SortedList()
        self.nodes = SortedList(nodes) if (nodes is not None) else SortedList()
        self.edges = SortedList(edges) if (edges is not None) else SortedList()

    def copy(self):
        """

        Returns:

        """
        return AMR_Alignment(type=self.type, tokens=self.tokens.copy(), nodes=self.nodes.copy(),
                             edges=self.edges.copy())

    def to_json(self, amr: AMR = None) -> Dict[str, Any]:
        """

        Returns:

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
            json_['readable'] = self.readable(amr)
        return json_

    def readable(self, amr) -> str:
        type = self.type
        nodes = ', '.join(amr.nodes[n] for n in self.nodes) if bool(self.nodes) else ''
        edges = ', '.join(str((amr.nodes[s], r, amr.nodes[t])) for s, r, t in self.edges) if bool(self.edges) else ''
        tokens = ' '.join(amr.tokens[t] for t in self.tokens)
        sep1 = ' : ' if type else ''
        sep2 = ', ' if (nodes and edges) else ''
        return f'{type}{sep1}{tokens} => {nodes}{sep2}{edges}'

    def __str__(self):
        type = self.type
        nodes = ', '.join(n for n in self.nodes) if bool(self.nodes) else ''
        edges = ', '.join(f'{s} {r} {t}' for s, r, t in self.edges) if bool(self.edges) else ''
        tokens = ' '.join(str(t) for t in self.tokens)
        sep1 = ' : ' if type else ''
        sep2 = ', ' if (nodes and edges) else ''
        return f'[{class_name(self)}]: {type}{sep1}{tokens} => {nodes}{sep2}{edges}'

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

    def __init__(self, amr: AMR, alignments: Iterable[AMR_Alignment] = None):
        """

        Args:
            amr:
            alignments:
        """
        self.amr = amr
        self.alignments = SortedList()
        self.token_spans = SortedList()
        if alignments is not None:
            for align in alignments:
                self.add(align)

    def align(self, type: str = None, tokens: Iterable[int] = None, nodes: Iterable[str] = None,
              edges: Iterable[Tuple[str, str, str]] = None):
        """

        Args:
            type:
            tokens:
            nodes:
            edges:

        Returns:

        """
        align = self.find(lambda a: set(a.tokens) == set(tokens) and (type is None or a.type == type))
        if align is None:
            self.add(AMR_Alignment(type=type, tokens=tokens, nodes=nodes, edges=edges))
        else:
            if nodes:
                for n in nodes:
                    if n not in align.nodes:
                        align.nodes.add(n)
            if edges:
                for e in edges:
                    if e not in align.edges:
                        align.edges.add(e)

    def add(self, alignment: AMR_Alignment):
        """

        Args:
            alignment:

        Returns:

        """
        if tuple(alignment.tokens) not in self.token_spans:
            self.token_spans.add(tuple(alignment.tokens))
        self.alignments.add(alignment)

    def remove(self, alignment: AMR_Alignment):
        """

        Args:
            alignment:

        Returns:

        """
        self.alignments.remove(alignment)

    def get(self, type=None, token_id=None, node=None, edge=None) -> Optional[AMR_Alignment]:
        """

        Args:
            type:
            token_id:
            node:
            edge:

        Returns:

        """
        for align in self:
            if (token_id is None or token_id in align.tokens) and \
                    (node is None or node in align.nodes) and \
                    (edge is None or edge in align.edges) and \
                    (type is None or type == align.type):
                return align
        return None

    def get_all(self, type=None, token_id=None, node=None, edge=None) -> List[AMR_Alignment]:
        """

        Args:
            type:
            token_id:
            node:
            edge:

        Returns:

        """
        aligns = []
        for align in self:
            if (token_id is None or token_id in align.tokens) and \
                    (node is None or node in align.nodes) and \
                    (edge is None or edge in align.edges) and \
                    (type is None or type == align.type):
                aligns.append(align)
        return aligns

    def find(self, condition: Callable[[AMR_Alignment], bool]) -> Optional[AMR_Alignment]:
        """

        Args:
            condition:

        Returns:

        """
        for align in self:
            if condition(align):
                return align
        return None

    def find_all(self, condition: Callable[[AMR_Alignment], bool]) -> List[AMR_Alignment]:
        """

        Args:
            condition:

        Returns:

        """
        aligns = []
        for align in self:
            if condition(align):
                aligns.append(align)
        return aligns

    def __iter__(self):
        return self.alignments

    def __len__(self):
        return len(self.alignments)

    def __str__(self):
        return f'[{class_name(self)}] {"; ".join(a.readable() for a in self)}'

    def to_json(self, anonymize=True) -> List[Dict[str, Any]]:
        """

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
        raise NotImplemented()

    def is_projective(self) -> bool:
        raise NotImplemented()


class AMR_Alignment_Reader:

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
                    s, r, t = e[0], e[1], e[2]
                    if r == ':_':
                        s, r, t = map_unlabeled_edges[(s, t)]
                    json_align['edges'][i] = (s, r, t)

    def load_from_json(self, json_file: str, unanonymize: bool = False, amrs: Iterable[AMR] = None):
        alignment_sets = []
        if unanonymize and not amrs:
            raise Exception('To un-anonymize alignments, the parameter "amrs" is required.')
        with open(json_file, 'r', encoding='utf8') as f:
            json_alignments = json.load(f)
        amrs_from_id = {}
        for amr in amrs:
            amrs_from_id[amr.id] = amr
        for amr_id in json_alignments:
            amr = amrs_from_id[amr_id]
            self._check_ids_match(amr, json_alignments[amr_id])
            if unanonymize:
                self._unanonymize_edges(amr, json_alignments[amr_id])
            alignment_list = []
            for json_align in json_alignments[amr_id]:
                nodes = json_align['nodes'] if ('nodes' in json_align) else []
                edges = [(e[0], e[1], e[2]) for e in json_align['edges']] if ('edges' in json_align) else []
                alignment = AMR_Alignment(type=json_align['type'], tokens=json_align['tokens'],
                                          nodes=nodes, edges=edges)
                alignment_list.append(alignment)
            alignment_sets.append(AMR_Alignment_Set(amr, alignment_list))
        return alignment_sets
