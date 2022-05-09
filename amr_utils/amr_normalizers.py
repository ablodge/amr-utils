from typing import Union, Dict, Callable

from amr_utils import amr_iterators
from amr_utils.amr import AMR_Notation, AMR


def remove_wiki(amr: AMR):
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


def remove_duplicate_triples(amr: AMR):
    """
    Remove duplicate triples, where a triple is composed of the same source, relation, and target of another triple.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    new_edges = []
    seen_edges = set()
    for e in amr.edges[:]:
        if e not in seen_edges:
            new_edges.append(e)
        seen_edges.add(e)
    amr.edges = new_edges


def remove_artifacts(amr: AMR):
    """
    Remove annotator artifacts that affect the placement of :instance for nodes with more than one parent.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    amr.reentrancy_artifacts = None


def normalize_shape(amr: AMR):
    """
    Convert the AMR to a standard shape with alphabetized edges and no cycles.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    new_edges = []
    for e in amr_iterators.traverse_graph(amr, alphabetical_edges=True):
        new_edges.append(e)
    amr.edges = new_edges
    amr.edges = [e for e in amr_iterators.edges(amr, depth_first=True)]
    amr.reentrancy_artifacts = None


def rename_nodes(amr: AMR, map: Union[Dict[str, str], Callable[[str], str]]):
    """
    Rename AMR nodes according to `map`.
    Args:
        amr (AMR): AMR to apply changes to
        map (dict or function): a dictionary or function that defines how each node should be renamed

    Returns:
        None
    """
    if isinstance(map, dict):
        map = map.__getitem__
    new_nodes = {}
    for old_n in amr.nodes:
        new_n = map(old_n)
        new_nodes[new_n] = amr.nodes[old_n]
    amr.nodes = new_nodes
    amr.root = map(amr.root)
    for i, e in enumerate(amr.edges):
        s, r, t = e
        s = map(s)
        t = map(t)
        amr.edges[i] = (s, r, t)
    if amr.reentrancy_artifacts is not None:
        new_artifacts = {}
        for n in amr.reentrancy_artifacts:
            s, r, t = amr.reentrancy_artifacts[n]
            new_artifacts[map(n)] = (map(s), r, map(t))
        amr.reentrancy_artifacts = new_artifacts


def reassign_root(amr: AMR, root: str):
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


def remove_cycles(amr: AMR):
    """
    Remove cycles by inverting as few edges as possible.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    descendants = {n: {n} for n in amr.nodes}
    for s, r, t in amr.edges:
        for n in descendants:
            if s in descendants[n]:
                descendants[n].update(descendants[t])
    seen_nodes = {amr.root}
    cyclical_edges = []
    for i, e in enumerate(amr_iterators.edges(amr, breadth_first=True)):
        s, r, t = e
        if s in descendants[t] and t in seen_nodes:
            cyclical_edges.append(i)
        seen_nodes.add(t)
    for i in cyclical_edges:
        s, r, t = amr.edges[i]
        r = AMR_Notation.invert_relation(r)
        amr.edges[i] = (t, r, s)


def normalize_inverse_edges(amr: AMR) -> None:
    """
    Convert inverse edges to normal edges, possibly creating a non-DAG AMR.
    Args:
        amr (AMR): AMR to apply changes to

    Returns:
        None
    """
    for i, e in enumerate(amr.edges):
        s, r, t = e
        if AMR_Notation.is_inverse_relation(r):
            r = AMR_Notation.invert_relation(r)
            amr.edges[i] = (t, r, s)