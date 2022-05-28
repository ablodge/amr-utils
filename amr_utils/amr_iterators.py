import re
import warnings
from collections import defaultdict, Counter
from typing import Union, Iterator, Tuple, Dict, Iterable

from amr_utils.amr import AMR, AMR_Notation
from amr_utils.amr_graph import Subgraph_AMR, process_subgraph

Edge = Tuple[str, str, str]
Triple = Tuple[str, str, str]


def _depth_first_edges(amr: AMR, preserve_shape: bool = False, ignore_reentrancies: bool = False,
                       traverse_undirected_graph: bool = False,
                       start_node: str = None, allowed_edges: Iterable[Edge] = None) -> Iterator[Edge]:
    """
    Iterate the edges in an AMR in depth first order
    Args:
        amr (AMR): the AMR to iterate
        ignore_reentrancies (bool): whether to skip reentrant edges when iterating
        preserve_shape (bool): explore the graph exactly as formatted in the original graph string instead of visiting
            edges alphabetically
        traverse_undirected_graph (bool): if set, explore the graph while ignoring edge direction
        start_node (str): if set, explore the graph starting from this node (default: amr.root)
        allowed_edges (Iterable[Tuple[str,str,str]]): if set, explore the graph while only considering these edges

    Yields:
        tuple: pairs of the form (depth, (source_id, relation, target_id))
    """
    root = amr.root if (start_node is None) else start_node
    edges_ = amr.edges if (allowed_edges is None) else allowed_edges
    edges_ = [(i, e) for i, e in enumerate(edges_)]
    # identify each node's child edges
    children = defaultdict(list)
    for i, e in reversed(edges_):
        s, r, t = e
        children[s].append((i, e))
        if traverse_undirected_graph:
            r_inv = AMR_Notation.invert_relation(r)
            children[t].append((i, (t, r_inv, s)))
    # alphabetize edges
    if not preserve_shape:
        for n in children:
            if len(children[n]) > 1:
                children[n] = sorted(children[n], key=lambda x: AMR_Notation.sorted_edge_key(amr, x[-1]),
                                     reverse=True)
    # depth first algorithm
    stack = []  # pairs (depth, edge)
    for edge_idx, edge in children[root]:
        stack.append((1, edge_idx, edge))
    visited_edges = set()
    visited_nodes = {root} if ignore_reentrancies else None
    while stack:
        depth, edge_idx, edge = stack.pop()
        if edge_idx in visited_edges:
            continue
        target = edge[-1]
        visited_edges.add(edge_idx)
        if ignore_reentrancies:
            if target in visited_nodes:
                continue
            visited_nodes.add(target)
        if children[target]:
            if not preserve_shape or amr.shape is None or amr.shape.locate_instance(amr, target) == edge_idx:
                for new_edge_idx, new_edge in children[target]:
                    if new_edge_idx in visited_edges:
                        continue
                    stack.append((depth + 1, new_edge_idx, new_edge))
        yield depth, edge_idx, edge
    if len(visited_edges) < len(edges_):
        missing_edges = [e for e in edges_ if e not in visited_edges]
        warnings.warn(f'[{__name__}] Failed to iterate edges in AMR "{amr.id}" because {len(missing_edges)} of '
                      f'{len(edges_)} edges were unreachable.'
                      f'\nMissing edges: {missing_edges}')


def _breadth_first_edges(amr: AMR, preserve_shape: bool = False, ignore_reentrancies: bool = False,
                         traverse_undirected_graph: bool = False, start_node: str = None,
                         allowed_edges: Iterable[Edge] = None) \
        -> Iterator[Edge]:
    """
    Iterate the edges in an AMR in breadth first order
    Args:
        amr (AMR): the AMR to iterate
        preserve_shape (bool): explore the graph exactly as formatted in the original graph string instead of visiting
            edges alphabetically
        ignore_reentrancies (bool): whether to skip reentrant edges when iterating
        traverse_undirected_graph (bool): if set, explore the graph while ignoring edge direction
        start_node (str): if set, explore the graph starting from this node (default: amr.root)
        allowed_edges (Iterable[Tuple[str,str,str]]): if set, explore the graph while only considering these edges

    Yields:
        tuple: pairs of the form (depth, (source_id, relation, target_id))
    """
    root = amr.root if (start_node is None) else start_node
    edges_ = amr.edges if (allowed_edges is None) else allowed_edges
    nodes_to_visit = [(1, root)]
    children = defaultdict(list)
    for i, edge in enumerate(edges_):
        s, r, t = edge
        children[s].append((i, edge))
        if traverse_undirected_graph:
            r_inv = AMR_Notation.invert_relation(r)
            children[t].append((i, (t, r_inv, s)))
    if not preserve_shape:
        for n in children:
            if len(children[n]) > 1:
                children[n] = sorted(children[n], key=lambda x: AMR_Notation.sorted_edge_key(amr, x[1]))
    visited_nodes = {root} if ignore_reentrancies else None
    visited_edges = set()
    planned_nodes = {root}
    # breadth first algorithm
    while nodes_to_visit:
        next_nodes_to_visit = []
        for depth, n in nodes_to_visit:
            for edge_idx, edge in children[n]:
                if edge_idx in visited_edges:
                    continue
                target = edge[-1]
                if ignore_reentrancies:
                    if target in visited_nodes:
                        continue
                    visited_nodes.add(target)
                if not preserve_shape or amr.shape is None or amr.shape.locate_instance(amr, target) == edge_idx:
                    if children[target] and target not in planned_nodes:
                        next_nodes_to_visit.append((depth + 1, target))
                        planned_nodes.add(target)
                yield depth, edge_idx, edge
                visited_edges.add(edge_idx)
        nodes_to_visit = next_nodes_to_visit
    if len(visited_edges) < len(edges_):
        missing_edges = [e for e in edges_ if e not in visited_edges]
        warnings.warn(f'[{__name__}] Failed to iterate edges in AMR "{amr.id}" because {len(missing_edges)} of '
                      f'{len(edges_)} edges were unreachable.'
                      f'\nMissing edges: {missing_edges}')


def edges(amr: AMR, depth_first: bool = False, breadth_first: bool = False, preserve_shape: bool = False,
          traverse_undirected_graph: bool = False, subgraph_root: str = None, subgraph_edges: Iterable[Edge] = None) \
        -> Iterator[Edge]:
    """
    Iterate AMR edges
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): use depth first search
        breadth_first (bool): use breadth first search
        preserve_shape (bool): explore the graph exactly as formatted in the original graph string instead of visiting
            edges alphabetically
        traverse_undirected_graph (bool): if set, explore the graph while ignoring edge direction
        subgraph_root (str): if set, explore the graph starting from this node (default: amr.root)
        subgraph_edges (Iterable[Tuple[str,str,str]]): if set, explore the graph while only considering these edges

    Yields:
        tuple: edges, which are tuples of the form (source_id, relation, target_id)
    """
    root, _, edges_ = process_subgraph(amr, subgraph_root=subgraph_root, subgraph_edges=subgraph_edges,
                                                        undirected_graph=traverse_undirected_graph, ignore_nodes=True)
    if depth_first:
        edge_iter = _depth_first_edges(amr, preserve_shape=preserve_shape,
                                       traverse_undirected_graph=traverse_undirected_graph,
                                       start_node=root, allowed_edges=edges_)
    elif breadth_first:
        edge_iter = _breadth_first_edges(amr, preserve_shape=preserve_shape,
                                         traverse_undirected_graph=traverse_undirected_graph,
                                         start_node=root, allowed_edges=edges_)
    elif subgraph_edges is not None:
        edge_iter = [e for e in amr.edges if e in subgraph_edges]
    else:
        edge_iter = amr.edges
    if depth_first or breadth_first:
        for _, _, edge in edge_iter:
            yield edge
    else:
        for edge in edge_iter:
            yield edge


def nodes(amr: AMR, depth_first: bool = False, breadth_first: bool = False, preserve_shape: bool = False,
          traverse_undirected_graph: bool = False,
          subgraph_root: str = None, subgraph_nodes: Iterable[str] = None) -> Iterator[str]:
    """
    Iterate AMR nodes
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): use depth first search
        breadth_first (bool): use breadth first search
        preserve_shape (bool): explore the graph exactly as formatted in the original graph string instead of visiting
            edges alphabetically
        traverse_undirected_graph (bool): if set, explore the graph while ignoring edge direction
        subgraph_root (str): if set, explore the graph starting from this node (default: amr.root)
        subgraph_nodes (Iterable[str]): if set, explore the subgraph consisting of these nodes

    Yields:
        str: node IDs
    """
    root, nodes_, edges_ = process_subgraph(amr, subgraph_root=subgraph_root, subgraph_nodes=subgraph_nodes,
                                            undirected_graph=traverse_undirected_graph)
    if depth_first or breadth_first:
        if depth_first:
            edge_iter = _depth_first_edges(amr, ignore_reentrancies=True, preserve_shape=preserve_shape,
                                           traverse_undirected_graph=traverse_undirected_graph,
                                           start_node=root, allowed_edges=edges_)
        else:
            edge_iter = _breadth_first_edges(amr, ignore_reentrancies=True, preserve_shape=preserve_shape,
                                             traverse_undirected_graph=traverse_undirected_graph,
                                             start_node=root, allowed_edges=edges_)
        if root in nodes_:
            if root not in amr.nodes:
                warnings.warn(f'[{__name__}] The node "{root}" in AMR "{amr.id}" has no concept.')
            yield root
        for _, _, e in edge_iter:
            s, r, t = e
            if t in nodes_:
                if t not in amr.nodes:
                    warnings.warn(f'[{__name__}] The node "{t}" in AMR "{amr.id}" has no concept.')
                yield t
    else:
        for n in nodes_:
            if n not in amr.nodes:
                warnings.warn(f'[{__name__}] The node "{n}" in AMR "{amr.id}" has no concept.')
            yield n


def reentrancies(amr: AMR, depth_first: bool = False, breadth_first: bool = False, preserve_shape: bool = False,
                 traverse_undirected_graph: bool = False) -> Iterator[Tuple[str, Edge]]:
    """
    Iterate AMR reentrancies. A reentrancy occurs when a node has more than one parent edge.
    Reentrancies are what make AMRs graph-structured rather than tree-structured.
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): use depth first search
        breadth_first (bool): use breadth first search
        preserve_shape (bool): explore the graph exactly as formatted in the original graph string instead of visiting
            edges alphabetically
        traverse_undirected_graph (bool): if set, explore the graph while ignoring edge direction

    Yields:
        tuple: (node, edge) pairs for each node with a reentrancy and each parent edge
    """
    parents = defaultdict(list)
    for s, r, t in edges(amr, depth_first=depth_first, breadth_first=breadth_first,
                         preserve_shape=preserve_shape, traverse_undirected_graph=traverse_undirected_graph):
        parents[t].append((s, r, t))
    if preserve_shape and amr.shape is not None:
        node_mentions = Counter()
        for edge_idx, e in enumerate(amr.edges):
            s, r, t = e
            if amr.shape.locate_instance(amr, t) == edge_idx and parents[t][0] != (s, r, t):
                parents[t].remove((s, r, t))
                parents[t].insert(0, (s, r, t))
            node_mentions[t] += 1
    for n in nodes(amr, depth_first=depth_first, breadth_first=breadth_first,
                   preserve_shape=preserve_shape, traverse_undirected_graph=traverse_undirected_graph):
        if len(parents[n]) > 1:
            yield n, [e for e in parents[n]]
        elif n == amr.root and len(parents[n]) > 0:
            yield n, [e for e in parents[n]]


def triples(amr: AMR, depth_first: bool = False, breadth_first: bool = False, preserve_shape: bool = False,
            normalize_inverse_relations: bool = False, traverse_undirected_graph: bool = False,
            subgraph_root: str = None, subgraph_nodes: Iterable[str] = None, subgraph_edges: Iterable[Edge] = None) \
        -> Iterator[Triple]:
    """
    Iterate AMR triples
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): use depth first search
        breadth_first (bool): use breadth first search
        preserve_shape (bool): explore the graph exactly as formatted in the original graph string instead of visiting
            edges alphabetically
        normalize_inverse_relations (bool): convert inverse relations to normal relations
        traverse_undirected_graph (bool): if set, explore the graph while ignoring edge direction
        subgraph_root (str): if set, explore the graph starting from this node (default: amr.root)
        subgraph_nodes (Iterable[str]): if set, explore the subgraph consisting of these nodes
        subgraph_edges (Iterable[Tuple[str,str,str]]): if set, explore the graph while only considering these edges

    Yields:
        tuple: triples of the form (source_id, relation, target_id) or (source_id, relation, value)
    """
    root, nodes_, edges_ = process_subgraph(amr, subgraph_root=subgraph_root, subgraph_nodes=subgraph_nodes,
                                            subgraph_edges=subgraph_edges, undirected_graph=traverse_undirected_graph)
    if depth_first:
        edge_iter = _depth_first_edges(amr, preserve_shape=preserve_shape,
                                       traverse_undirected_graph=traverse_undirected_graph,
                                       start_node=root, allowed_edges=edges_)
    elif breadth_first:
        edge_iter = _breadth_first_edges(amr, preserve_shape=preserve_shape,
                                         traverse_undirected_graph=traverse_undirected_graph,
                                         start_node=root, allowed_edges=edges_)
    elif subgraph_edges is not None:
        edge_iter = [(0, i, e) for i, e in enumerate(amr.edges) if e in subgraph_edges]
    else:
        edge_iter = [(0, i, e) for i, e in enumerate(amr.edges)]
    completed_nodes = {root}
    # root
    if root in nodes_:
        if root in amr.nodes:
            yield root, ':instance', amr.nodes[root]
        else:
            warnings.warn(f'[{__name__}] The node "{root}" in AMR "{amr.id}" has no concept.')
    for _, edge_idx, e in edge_iter:
        s, r, t = e
        if AMR_Notation.is_attribute(amr, (s, r, t)):
            # attribute
            yield s, r, amr.nodes[t]
        else:
            # relation
            if normalize_inverse_relations and AMR_Notation.is_inverse_relation(r):
                r_inv = AMR_Notation.invert_relation(r)
                yield t, r_inv, s
            else:
                yield s, r, t
            # instance
            if t in nodes_ and t not in completed_nodes \
                    and (not preserve_shape or amr.shape is None or amr.shape.locate_instance(amr, t) == edge_idx):
                if t in amr.nodes:
                    yield t, ':instance', amr.nodes[t]
                else:
                    warnings.warn(f'[{__name__}] The node "{t}" in AMR "{amr.id}" has no concept.')
                completed_nodes.add(t)


def instances(amr: AMR, depth_first: bool = False, breadth_first: bool = False, preserve_shape: bool = False,
              traverse_undirected_graph: bool = False,
              subgraph_root: str = None, subgraph_nodes: Iterable[str] = None) -> Iterator[Triple]:
    """
    Iterate AMR instance triples
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): use depth first search
        breadth_first (bool): use breadth first search
        preserve_shape (bool): explore the graph exactly as formatted in the original graph string instead of visiting
            edges alphabetically
        traverse_undirected_graph (bool): if set, explore the graph while ignoring edge direction
        subgraph_root (str): if set, explore the graph starting from this node (default: amr.root)
        subgraph_nodes (Iterable[str]): if set, explore the subgraph consisting of these nodes

    Yields:
        tuple: triples of the form (node_id, ':instance', concept)
    """
    triple_iter = triples(amr, depth_first=depth_first, breadth_first=breadth_first, preserve_shape=preserve_shape,
                          traverse_undirected_graph=traverse_undirected_graph, subgraph_root=subgraph_root,
                          subgraph_nodes=subgraph_nodes)
    for s, r, t in triple_iter:
        if r == ':instance':
            yield s, r, t


def relations(amr: AMR, depth_first: bool = False, breadth_first: bool = False, preserve_shape: bool = False,
              normalize_inverse_relations: bool = False, traverse_undirected_graph: bool = False,
              subgraph_root: str = None, subgraph_edges: Iterable[Edge] = None) \
        -> Iterator[Triple]:
    """
    Iterate AMR relation triples
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): use depth first search
        breadth_first (bool): use breadth first search
        preserve_shape (bool): explore the graph exactly as formatted in the original graph string instead of visiting
            edges alphabetically
        normalize_inverse_relations (bool): convert inverse relations to normal relations
        traverse_undirected_graph (bool): if set, explore the graph while ignoring edge direction
        subgraph_root (str): if set, explore the graph starting from this node (default: amr.root)
        subgraph_edges (Iterable[Tuple[str,str,str]]): if set, explore the graph while only considering these edges

    Yields:
        tuple: triples of the form (source_id, relation, target_id)
    """
    triple_iter = triples(amr, depth_first=depth_first, breadth_first=breadth_first,
                          preserve_shape=preserve_shape,
                          traverse_undirected_graph=traverse_undirected_graph, subgraph_root=subgraph_root,
                          subgraph_edges=subgraph_edges, normalize_inverse_relations=normalize_inverse_relations)
    for s, r, t in triple_iter:
        if r != ':instance' and not AMR_Notation.is_constant(t):
            yield s, r, t


def attributes(amr: AMR, depth_first: bool = False, breadth_first: bool = False, preserve_shape: bool = False,
               traverse_undirected_graph: bool = False, subgraph_root: str = None,
               subgraph_edges: Iterable[Edge] = None) \
        -> Iterator[Triple]:
    """
    Iterate AMR attributes
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): use depth first search
        breadth_first (bool): use breadth first search
        preserve_shape (bool): explore the graph exactly as formatted in the original graph string instead of visiting
            edges alphabetically
        traverse_undirected_graph (bool): if set, explore the graph while ignoring edge direction
        subgraph_root (str): if set, explore the graph starting from this node (default: amr.root)
        subgraph_edges (Iterable[Tuple[str,str,str]]): if set, explore the graph while only considering these edges

    Yields:
        tuple: triples of the form (source_id, relation, value)
    """
    triple_iter = triples(amr, depth_first=depth_first, breadth_first=breadth_first,
                          preserve_shape=preserve_shape,
                          traverse_undirected_graph=traverse_undirected_graph, subgraph_root=subgraph_root,
                          subgraph_edges=subgraph_edges)
    for s, r, t in triple_iter:
        if AMR_Notation.is_constant(t):
            yield s, r, t


def subgraphs_by_pattern(amr: AMR, subgraph_pattern: Union[str, 'Subgraph_Pattern']) \
        -> Iterator[Subgraph_AMR]:
    """
    Find and iterate subgraphs in an AMR based on a subgraph pattern (See `Subgraph_Pattern`).
    Args:
        amr (AMR): the AMR to iterate
        subgraph_pattern (str or Subgraph_Pattern):

    Yields:
        Subgraph_AMR: an AMR representing a subgraph in `amr` matching `subgraph_pattern`
    """
    if isinstance(subgraph_pattern, str):
        subgraph_pattern = Subgraph_Pattern(subgraph_pattern)
    if not subgraph_pattern.nodes:
        return

    neighbors = defaultdict(list)
    for s, r, t in edges(amr, breadth_first=True):
        neighbors[s].append((s, r, t, False))
        neighbors[t].append((t, AMR_Notation.invert_relation(r), s, True))

    nodes_ = [n for n in nodes(amr)]
    for n in nodes_:
        concept = ''
        if n in amr.nodes:
            concept = amr.nodes[n]
        if subgraph_pattern.wildcard_match(concept, subgraph_pattern.nodes['0']):
            found_match = True
            node_map = defaultdict(list)
            identified_edges = []
            node_map['0'].append(n)
            taken = set()
            for sg_s, sg_r, sg_t in subgraph_pattern.edges:
                passed = False
                if sg_r.endswith('?'):
                    passed = True
                possible_edges = [e for n2 in node_map[sg_s] for e in neighbors[n2]]
                found_edges = []
                for s, r, t, inv in possible_edges:
                    target_concept = ''
                    if t in amr.nodes:
                        target_concept = amr.nodes[t]
                    if s in node_map[sg_s] \
                            and subgraph_pattern.wildcard_match(r, sg_r) \
                            and subgraph_pattern.wildcard_match(target_concept, subgraph_pattern.nodes[sg_t]) \
                            and (s, r, t) not in taken:
                        node_map[sg_t].append(t)
                        found_edges.append((s, r, t) if not inv else (t, AMR_Notation.invert_relation(r), s))
                        taken.add((s, r, t))
                        taken.add((t, AMR_Notation.invert_relation(r), s))
                        passed = True
                if passed:
                    identified_edges.extend(found_edges)
                else:
                    found_match = False
                    break
            if found_match:
                sg_nodes = {}
                for sub_n in node_map:
                    for n2 in node_map[sub_n]:
                        if n2 in amr.nodes:
                            sg_nodes[n2] = amr.nodes[n2]
                root = node_map['0'][0]
                yield Subgraph_AMR(id=amr.id, root=root, nodes=sg_nodes, edges=identified_edges)


def named_entities(amr: AMR) -> Iterator[Tuple[str, Dict[str, str], Subgraph_AMR]]:
    """
    Iterate named entities (including dates, times, quantities, etc.) retrieving an named entity tag, a dict of
    attributes, and the subgraph as an AMR.

    Named entity tags are based on the OntoNotes NER layer and include 20 labels:
        PERSON, NORP, FAC, ORG, GPE, LOC, PRODUCT, EVENT, WORK_OF_ART, LAW, LANGUAGE, DATE, TIME, PERCENT, MONEY,
        QUANTITY, ORDINAL, CARDINAL, BIOMEDICAL, OTHER
    Args:
        amr (AMR): the AMR to iterate

    Yield:
        Tuple[str, dict, Subgraph_AMR]: the NER tag, a dictionary of NER attributes,
            an AMR representing the named entity subgraph
    """
    if isinstance(Subgraph_Pattern.NE_PATTERN, str):
        Subgraph_Pattern.NE_PATTERN = Subgraph_Pattern(Subgraph_Pattern.NE_PATTERN)
    if isinstance(Subgraph_Pattern.DATE_PATTERN, str):
        Subgraph_Pattern.DATE_PATTERN = Subgraph_Pattern(Subgraph_Pattern.DATE_PATTERN)
    if isinstance(Subgraph_Pattern.QUANTITY_PATTERN, str):
        Subgraph_Pattern.QUANTITY_PATTERN = Subgraph_Pattern(Subgraph_Pattern.QUANTITY_PATTERN)
    if isinstance(Subgraph_Pattern.VALUE_PATTERN, str):
        Subgraph_Pattern.VALUE_PATTERN = Subgraph_Pattern(Subgraph_Pattern.VALUE_PATTERN)

    for sub_amr in subgraphs_by_pattern(amr, Subgraph_Pattern.NE_PATTERN):
        ne_type = amr.nodes[sub_amr.root]
        attr = {'type': ne_type, 'name': None}
        name = []
        for s, r, t in sorted(sub_amr.edges, key=lambda _: AMR_Notation.sorted_edge_key(sub_amr, _)):
            if r.startswith(':op'):
                name.append(sub_amr.nodes[t].replace('"', ''))
            elif r != ':name':
                attr[r[1:]] = sub_amr.nodes[t].replace('"', '')
        name = ' '.join(name)
        attr['name'] = name
        ne_tag = 'OTHER'
        for tag, labels in AMR_Notation.NER_TYPES.items():
            if ne_type in labels:
                ne_tag = tag
                break
        yield ne_tag, attr, sub_amr

    for PATTERN in [Subgraph_Pattern.DATE_PATTERN, Subgraph_Pattern.QUANTITY_PATTERN, Subgraph_Pattern.VALUE_PATTERN]:
        for sub_amr in subgraphs_by_pattern(amr, PATTERN):
            ne_type = amr.nodes[sub_amr.root]
            attr = {'type': ne_type}
            for s, r, t in sorted(sub_amr.edges, key=lambda _: AMR_Notation.sorted_edge_key(sub_amr, _)):
                attr[r[1:]] = sub_amr.nodes[t].replace('"', '')
            ne_tag = 'OTHER'
            for tag in ['PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']:
                labels = AMR_Notation.NER_TYPES[tag]
                if ne_type in labels:
                    ne_tag = tag
                    break
            if ne_type == 'date-entity':
                if 'time' in attr or 'dayperiod' in attr:
                    ne_tag = 'TIME'
                else:
                    ne_tag = 'DATE'
            yield ne_tag, attr, sub_amr


class Subgraph_Pattern:
    """
    This class makes it possible to search AMRs for complex patterns based on a simple string description.

    Example:
    ```
    # matches nodes labelled "and" or "or" along with their ":op" arguments
    conjunction_pattern = Subgraph_Pattern('(and|or :op* *)')
    # matches subgraphs for countries beginning with "A"
    county_pattern = Subgraph_Pattern('(country :name (name :op1 "A* :op*? *))')
    ```

    Subgraph patterns support a number of useful string match features for general (but non-recursive) pattern matching.
    Wildcard match: * (nodes or relations)
    Prefix match: abc* (nodes or relations)
    Suffix match: *abc (nodes or relations)
    Disjunction: abc|def (nodes or relations)
    Optional match: abc? (relations only)

    The order of operations is wildcard match < disjunction < optional match (e.g., abc*|*def? matches an optional
    string beginning with "abc" or ending with "def").
    """
    NE_PATTERN = '* :name (name :op* *) :wiki? *'
    DATE_PATTERN = 'date-entity :day|month|year|weekday|time|timezone|quarter|dayperiod|season|year2|decade|century|' \
                   'calendar|era|mod *'
    QUANTITY_PATTERN = '*-quantity :unit|scale|quant *'
    VALUE_PATTERN = '* :value *'

    ELEMENT_RE = re.compile(r'[(]|[)]|[^\s()]+')

    def __init__(self, description: str):
        """
        Construct a Subgraph Pattern
        Args:
            description (str): a string description of the subgraph pattern
        """
        path = []
        sg_nodes = {}
        sg_edges = []
        new_level = False
        new_edge = False
        relation = None
        for element in self.ELEMENT_RE.findall(description):
            if element == '(':
                new_level = True
            elif element == ')':
                path.pop()
            elif element.startswith(':'):
                relation = element
                new_edge = True
            else:
                node_id = str(len(sg_nodes))
                if new_edge:
                    sg_edges.append((path[-1], relation, node_id))
                    new_edge = False
                if new_level or not path:
                    path.append(node_id)
                    new_level = False
                sg_nodes[node_id] = element
        self.nodes = sg_nodes
        self.edges = sg_edges

    @staticmethod
    def wildcard_match(label: str, pattern: str) -> bool:
        """
        Test whether a node or relation label matches a wildcard pattern
        Args:
            label: the label of a node or relation
            pattern: a wildcard pattern representing a node or relation

        Returns:
            bool: True if label matches pattern
        """
        if label.startswith(':'):
            label = label[1:]
        if pattern.endswith('?'):
            pattern = pattern[:-1]
        patterns = pattern.split('|') if ('|' in pattern) else [pattern]
        for p in patterns:
            if p.startswith(':'):
                p = p[1:]
            if label == p \
                    or p == '*' \
                    or (p[0] == '*' and label.endswith(p[1:])) \
                    or (p[-1] == '*' and label.startswith(p[:-1])):
                return True
        return False
