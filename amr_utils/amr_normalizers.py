from typing import Union, Dict, Callable, List

from amr_utils import amr_iterators, amr_graph
from amr_utils.amr import AMR_Notation, AMR
from amr_utils.amr_alignments import AMR_Alignment_Set


def rename_nodes(amr: AMR, id_map: Union[Dict[str, str], Callable[[int], str]], alignments: AMR_Alignment_Set = None) \
        -> None:
    """
    Rename AMR nodes according to `id_map`.
    Args:
        amr (AMR): AMR to apply changes to
        id_map (dict or function): a dictionary or function that defines how each node should be renamed
        alignments (AMR_Alignment_Set): alignments for this AMR

    Returns:
        None
    """
    if isinstance(id_map, Callable):
        id_map = {k: id_map(i) for i, k in enumerate(amr.nodes)}
    # rename nodes
    new_nodes = {}
    for old_n in amr.nodes:
        new_n = id_map[old_n]
        new_nodes[new_n] = amr.nodes[old_n]
    amr.nodes = new_nodes
    amr.root = id_map[amr.root]
    # rename edges
    for i, e in enumerate(amr.edges):
        s, r, t = e
        s = id_map[s]
        t = id_map[t]
        amr.edges[i] = (s, r, t)

    # rename nodes in shape
    if amr.shape is not None:
        triples = amr.shape.triples
        for i, tr in enumerate(triples):
            s, r, t = tr
            if AMR_Notation.is_constant(t) or r == ':instance':
                triples[i] = (id_map[s], r, t)
            else:
                triples[i] = (id_map[s], r, id_map[t])
        attribute_nodes = amr.shape.attribute_nodes
        for i in attribute_nodes:
            attribute_nodes[i] = id_map[attribute_nodes[i]]
        instance_locations = amr.shape.instance_locations
        for n in instance_locations:
            edge_idx, edge = instance_locations[n]
            s, r, t = edge
            instance_locations[n] = (edge_idx, (id_map[s], r, id_map[t]))

    # rename alignments
    if alignments is not None:
        for align in alignments:
            nodes = [id_map[n] for n in align.nodes()]
            edges = [(id_map[s], r, id_map[t]) for s, r, t in align.edges()]
            align.set(nodes=nodes, edges=edges)


def remove_wiki(amr: AMR) -> None:
    """
    Remove :wiki edges from AMR.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    for s, r, t in amr.edges.copy():
        if r == ':wiki':
            amr.edges.remove((s, r, t))
            del amr.nodes[t]


def remove_duplicate_edges(amr: AMR) -> None:
    """
    Remove duplicate edges, where an edge has the same source node, relation, and target node as another edge.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    new_edges = []
    seen_edges = set()
    for s, r, t in amr.edges[:]:
        if (s, r, t) in seen_edges:
            continue
        if (t, AMR_Notation.invert_relation(r), s) in seen_edges:
            continue
        seen_edges.add((s, r, t))
        new_edges.append((s, r, t))
    amr.edges = new_edges


def normalize_shape(amr: AMR) -> None:
    """
    Convert the AMR to a standard shape with alphabetized edges and no cycles.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    new_edges = []
    for e in amr_iterators.edges(amr, traverse_undirected_graph=True, breadth_first=True):
        new_edges.append(e)
    amr.edges = new_edges
    amr.shape = None


def reassign_root(amr: AMR, root: str) -> None:
    """
    Make `root` the new AMR root and restructure the AMR accordingly.
    Args:
        amr (AMR): AMR to apply changes to
        root (str): new node id in `amr` that will become the new root

    Returns:
        None
    """
    amr.root = root
    normalize_shape(amr)


def remove_cycles(amr: AMR) -> None:
    """
    Remove cycles by inverting as few edges as possible. See also `normalize_shape()`.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    reachable_nodes = amr_graph._get_reachable_nodes(amr)
    seen_nodes = {amr.root}
    cyclical_edges = []
    for components in amr_graph.find_connected_components(amr):
        for s, r, t in amr_iterators.edges(amr, breadth_first=True, subgraph_root=components[0]):
            if s in reachable_nodes[t] and t in seen_nodes:
                cyclical_edges.append((s, r, t))
            seen_nodes.add(t)
    for i, e in enumerate(amr.edges):
        if e in cyclical_edges:
            s, r, t = e
            r = AMR_Notation.invert_relation(r)
            amr.edges[i] = (t, r, s)
    # handle amr.shape
    # TODO


def normalize_inverse_edges(amr: AMR) -> None:
    """
    Convert inverse edges to normal edges, possibly creating a non-DAG AMR.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    for i, e in enumerate(amr.edges):
        amr.edges[i] = AMR_Notation.normalize_edge(e)


def _contract_nodes(amr: AMR, nodes: List[str], anchor_concept: str):
    new_node = AMR_Notation.new_node_id(amr)
    amr.nodes[new_node] = anchor_concept

    for n in nodes:
        if n in amr.nodes:
            del amr.nodes[n]

    edges_to_remove = set()
    for i, e in enumerate(amr.edges):
        s, r, t = e
        if s in nodes and t in nodes:
            edges_to_remove.add(e)
        elif s in nodes:
            amr.edges[i] = (new_node, r, t)
        elif t in nodes:
            amr.edges[i] = (s, r, new_node)
    amr.edges = [e for e in amr.edges if e not in edges_to_remove]
    return new_node


def recategorize_graph(amr: AMR, anonymize: bool = False) -> None:
    """
    Restructure an AMR graph such that common subgraphs are simplified, such as named entities, constructions, and
    complex notation that is specific to AMR.
    Args:
        amr (AMR): AMR to apply changes to
        anonymize (bool): if True, remove identifying attributes of named entities such as names, date attributes, and
            quantity attributes. This is useful to do when separating the task of named entity recognition and the task
            of semantic parsing.

    Returns:
        None
    """
    # named entities
    for _, attr, sub_amr in amr_iterators.named_entities(amr.copy()):
        new_concept = attr['type']
        if 'name' in attr:
            new_concept = 'named-'+new_concept
        contracted_node = _contract_nodes(amr, [n for n in sub_amr.nodes], new_concept)
        if not anonymize:
            new_node = AMR_Notation.new_node_id(amr)
            if 'name' in attr:
                value = f'"{attr["name"]}"'
            else:
                value = [f'{k}:{v}' for k, v in attr.items() if k not in ['type', 'wiki']]
                value = '"' + ','.join(value) + '"'
            amr.nodes[new_node] = value
            amr.edges.append((contracted_node, ':value', new_node))

    # rate-entity-91
    # cause-01 => :cause
    # cite-01 => :cite
    # cost-01 => :cost
    # mean-01 => :meaning
    # have-org-role-91 => :role or  :employed-by
    # have-rel-role-91 => :role
    # include-91 => :subset or :superset
    # instead-of-91 => :instead-of
    # have-degree-91
    # have-quant-91
    # TODO


def decategorize_graph(amr) -> None:
    """
    Undo graph re-categorization and restore an AMR to the standard format. This can be applied after
    `recategorize_graph()` to restore an AMR to its original form. (Note: if `recategorize_graph` was called with
    `anonymize` set to True, attributes identifying attributes of named entities will still be missing from the AMR.)
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    raise NotImplementedError()
