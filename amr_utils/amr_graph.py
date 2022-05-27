from typing import Iterable, Tuple, Optional, List, Set, Dict

from amr_utils.amr import AMR
from amr_utils.utils import class_name

Edge = Tuple[str, str, str]


def _get_reachable_nodes(amr: AMR, nodes: Iterable[str] = None, edges: Iterable[Edge] = None,
                         undirected_graph: bool = False) -> Dict[str, Set[str]]:
    nodes = amr.nodes if (nodes is None) else nodes
    edges = amr.edges if (edges is None) else edges
    descendants = {n: {n} for n in nodes}
    for s, r, t in edges:
        if s not in descendants:
            descendants[s] = {s}
        if t not in descendants:
            descendants[t] = {t}
    for s, r, t in edges:
        for n in descendants:
            if s in descendants[n]:
                descendants[n].update(descendants[t])
            if undirected_graph and t in descendants[n]:
                descendants[n].update(descendants[s])
    return descendants


def _best_root(reachable_nodes: Dict[str, Set[str]], nodes: Iterable[str]):
    max_size = 0
    best_root = None
    for n in nodes:
        if len(reachable_nodes[n]) > max_size:
            max_size = len(reachable_nodes[n])
            best_root = n
    return best_root


def is_directed_acyclic_graph(amr: AMR, subgraph_root: str = None, subgraph_nodes: Iterable[str] = None,
                              subgraph_edges: Iterable[Edge] = None) -> bool:
    """
    Test whether this AMR (or a subgraph) is a connected directed acyclic graph with a single root.
    Args:
        amr (AMR): an AMR
        subgraph_root (str): if set, test the subgraph descending from this root (default: amr.root)
        subgraph_nodes (Iterable[str]): if set, test the subgraph containing these nodes (default: amr.nodes)
        subgraph_edges (Iterable[Edge]): if set, test the subgraph containing these edges (default: amr.edges)

    Returns:
        bool: True if amr is a rooted directed acyclic graph, else False
    """
    root, nodes, edges = process_subgraph(amr, subgraph_root=subgraph_root, subgraph_nodes=subgraph_nodes,
                                          subgraph_edges=subgraph_edges)
    reachable_nodes = _get_reachable_nodes(amr, nodes=nodes, edges=edges)
    # check for cycles
    for s, r, t in edges:
        if s in reachable_nodes[t]:
            return False
    # check that all nodes are reachable
    if all(n in reachable_nodes[root] for n in nodes):
        return True
    return False


def has_cycles(amr: AMR, subgraph_nodes: Iterable[str] = None, subgraph_edges: Iterable[Edge] = None) -> bool:
    """
    Test whether an AMR contains cycles
    Args:
        amr (AMR): an AMR
        subgraph_nodes (Iterable[str]): if set, find cycles in the subgraph containing these nodes (default: amr.nodes)
        subgraph_edges (Iterable[Edge]): if set, find cycles in the subgraph containing these edges (default: amr.edges)

    Returns:
        bool: True if the AMR contains cycles, False otherwise
    """
    _, nodes, edges = process_subgraph(amr, subgraph_nodes=subgraph_nodes, subgraph_edges=subgraph_edges,
                                       ignore_root=True)
    reachable_nodes = _get_reachable_nodes(amr, nodes=nodes, edges=edges)
    edges = amr.edges if (subgraph_edges is None) else subgraph_edges
    for s, r, t in edges:
        if s in reachable_nodes[t]:
            return True
    return False


def find_cycles(amr: AMR, subgraph_nodes: Iterable[str] = None, subgraph_edges: Iterable[Edge] = None) \
        -> List[Set[str]]:
    """
    Retrieve any cycles in this AMR as a list of sets of node IDs
    Args:
        amr (AMR): an AMR
        subgraph_nodes (Iterable[str]): if set, find cycles in the subgraph containing these nodes (default: amr.nodes)
        subgraph_edges (Iterable[Edge]): if set, find cycles in the subgraph containing these edges (default: amr.edges)

    Returns:
        List[Set[str]]: a list of sets on node IDs. Each set contains a cycle (defined by its equivalence class of nodes
            reachable from each node in the cycle).
    """
    _, nodes, edges = process_subgraph(amr, subgraph_nodes=subgraph_nodes, subgraph_edges=subgraph_edges,
                                       ignore_root=True)
    reachable_nodes = _get_reachable_nodes(amr, nodes=nodes, edges=edges)
    cycles = []
    equivalence_classes = []
    for s, r, t in edges:
        if s in reachable_nodes[t]:
            cycle = None
            for i, equiv_class in enumerate(equivalence_classes):
                if equiv_class == reachable_nodes[t]:
                    cycle = cycles[i]
                    cycle.add(s)
                    cycle.add(t)
                    break
            if cycle is None:
                cycle = {s, t}
                cycles.append(cycle)
                equiv_class = reachable_nodes[t]
                equivalence_classes.append(equiv_class)
    return cycles


def find_best_root(amr: AMR, subgraph_nodes: Iterable[str] = None,
                   subgraph_edges: Iterable[Edge] = None) -> Optional[str]:
    """
    Retrieve the node which has the highest number of descendant nodes
    Args:
        amr (AMR): an AMR
        subgraph_nodes (Iterable[str]): if set, find the root in the subgraph containing these nodes
            (default: amr.nodes)
        subgraph_edges (Iterable[Edge]): if set, find the root in the subgraph containing these edges
            (default: amr.edges)

    Returns:
        Optional[str]: a node ID which is the best root, or None if the graph is empty
    """
    _, nodes, edges = process_subgraph(amr, subgraph_nodes=subgraph_nodes, subgraph_edges=subgraph_edges,
                                       ignore_root=True)
    reachable_nodes = _get_reachable_nodes(amr, nodes=nodes, edges=edges)
    return _best_root(reachable_nodes, nodes)


def is_connected(amr: AMR, undirected_graph: bool = False,
                 subgraph_nodes: Iterable[str] = None, subgraph_edges: Iterable[Edge] = None) -> bool:
    """
    Test whether this AMR (or a subgraph) is a connected directed graph. Connectivity in a directed graph means that
    every node can be reach from some root node. If you instead want undirected connectivity, set the parameter
    `undirected_graph` to True.
    Args:
        amr (AMR): an AMR
        undirected_graph (bool): if True, check if the graph is connected as an undirected graph
        subgraph_nodes (Iterable[str]): if set, test the subgraph containing these nodes (default: amr.nodes)
        subgraph_edges (Iterable[Edge]): if set, test the subgraph containing these edges (default: amr.edges)

    Returns:
        bool: True if the AMR (or subgraph) is connected, otherwise False
    """
    _, nodes, edges = process_subgraph(amr, subgraph_nodes=subgraph_nodes, subgraph_edges=subgraph_edges,
                                       ignore_root=True)
    reachable_nodes = _get_reachable_nodes(amr, nodes=nodes, edges=edges, undirected_graph=undirected_graph)

    for n in reachable_nodes:
        if all(m in reachable_nodes[n] for m in nodes):
            return True
    return False


def find_connected_components(amr: AMR, undirected_graph: bool = False,
                              subgraph_nodes: Iterable[str] = None, subgraph_edges: Iterable[Edge] = None) \
        -> List[List[str]]:
    """
    Retrieve connected components of a possibly disconnected AMR (or a subgraph) as a list of lists of node IDs.
    Connectivity in a directed graph means that every node can be reach from some root node. If you instead want
    undirected connectivity, set the parameter `undirected_graph` to True.
    Args:
        amr (AMR): an AMR
        undirected_graph (bool): if True, find components that are connected as undirected graphs
        subgraph_nodes (Iterable[str]): if set, find components for the subgraph containing these nodes
            (default: amr.nodes)
        subgraph_edges (Iterable[Edge]): if set, find components for the subgraph containing these edges
            (default: amr.edges)

    Returns:
        List[List[str]]: A list of lists of node IDs. Each smaller list contains node IDs for a single connected
            component.
    """
    _, nodes, edges = process_subgraph(amr, subgraph_nodes=subgraph_nodes, subgraph_edges=subgraph_edges,
                                       ignore_root=True)
    reachable_nodes = _get_reachable_nodes(amr, nodes=nodes, edges=edges, undirected_graph=undirected_graph)

    components = []
    main_component = None
    unconnected_nodes = {n for n in nodes}
    # component attached to root
    if amr.root is not None and amr.root in nodes:
        main_component = [amr.root]
        main_component.extend(n for n in reachable_nodes[amr.root] if n in unconnected_nodes and n != amr.root)
        for n in main_component:
            unconnected_nodes.remove(n)
    # disconnected components
    while unconnected_nodes:
        new_root = _best_root(reachable_nodes, unconnected_nodes)
        component_nodes = [new_root]
        component_nodes.extend(n for n in reachable_nodes[new_root] if n in unconnected_nodes and n != new_root)
        components.append(component_nodes)
        for n in component_nodes:
            unconnected_nodes.remove(n)
    components = sorted(components, key=lambda ns: len(ns), reverse=True)
    if main_component:
        components.insert(0, main_component)
    return components


def break_into_connected_components(amr: AMR, undirected_graph: bool = False,
                                    subgraph_nodes: Iterable[str] = None, subgraph_edges: Iterable[Edge] = None) \
        -> List[AMR]:
    """
    Retrieve connected components of a possibly disconnected AMR (or a subgraph) as a list of AMRs. Connectivity in a
    directed graph means that every node can be reach from some root node. If you instead want undirected
    connectivity, set the parameter `undirected_graph` to True.
    Args:
        amr (AMR): an AMR
        undirected_graph (bool): if True, find components that are connected as undirected graphs
        subgraph_nodes (Iterable[str]): if set, find components for the subgraph containing these nodes
            (default: amr.nodes)
        subgraph_edges (Iterable[Edge]): if set, find components for the subgraph containing these edges
            (default: amr.edges)

    Returns:
        List[List[str]]: A list of AMRs, each of which has a connected graph.
    """
    components = find_connected_components(amr, subgraph_nodes=subgraph_nodes, subgraph_edges=subgraph_edges,
                                           undirected_graph=undirected_graph)
    amrs = []
    for nodes in components:
        nodes = {n: amr.nodes[n] for n in nodes}
        edges = [(s, r, t) for s, r, t in amr.edges if (s in nodes)]
        root = find_best_root(amr, subgraph_nodes=nodes, subgraph_edges=edges)
        amr_ = get_subgraph(amr, subgraph_root=root, subgraph_nodes=nodes, subgraph_edges=edges)
        amrs.append(amr_)
    return amrs


def find_shortest_path(amr: AMR, n1: str, n2: str, undirected_graph: bool = False,
                       subgraph_edges: Iterable[Edge] = None) -> Optional[List[str]]:
    """
    Retrieve the shortest directed path between two nodes as a list of path IDs. If you want the shortest undirected
    path, set the parameter `undirected_graph` to True.
    Args:
        amr (AMR): an AMR
        n1 (str): starting node ID
        n2 (str): ending node ID
        undirected_graph (bool): if True, find the shorted undirected path, ignoring the direction of edges
        subgraph_edges (Iterable[Edge]): if set, find path in the subgraph containing these edges
            (default: amr.edges)

    Returns:
        List[str]: a list of node IDs if a path exists, else None
    """
    paths = {n1: [n1]}
    from amr_utils.amr_iterators import breadth_first_edges
    edge_iter = breadth_first_edges(amr, subgraph_root=n1,
                                    subgraph_edges=subgraph_edges,
                                    traverse_undirected_graph=undirected_graph)
    for _, e in edge_iter:
        s, r, t = e
        if s in paths and t not in paths:
            paths[t] = paths[s] + [t]
            if t == n2:
                return paths[t]
    return None


def process_subgraph(amr, subgraph_root: str = None, subgraph_nodes: Iterable[str] = None,
                     subgraph_edges: Iterable[Edge] = None, ignore_root: bool = False, ignore_nodes: bool = False,
                     undirected_graph: bool = False) \
        -> Tuple[Optional[str], Set[str], List[Edge]]:
    """
    This function is called by amr_utils functions that take subgraphs as optional parameters in order to provide
    flexibility and consistency in interpreting subgraph parameters and to assure subgraph parameters are well-defined.
    Args:
        amr (AMR): an AMR
        subgraph_root (str): the subgraph root (default: amr.root)
        subgraph_nodes (Iterable[str]): nodes in the subgraph (default: amr.nodes)
        subgraph_edges (Iterable[Edge]): edges in the subgraph (default: amr.edges)
        ignore_root (bool): if set, skip processing of subgraph root to save time
        ignore_nodes (bool): if set, skip processing of subgraph nodes to save time
        undirected_graph (bool): if set, infer subgraph nodes and edges based on an undirected graph of the AMR

    Returns:
        tuple: a subgraph root ID, a set of subgraph node IDs, a list of subgraph edges
    """
    if (subgraph_root is None) and (subgraph_nodes is None) and (subgraph_edges is None):
        if ignore_nodes:
            nodes_ = set()
        else:
            nodes_ = {n for n in amr.nodes}
            nodes_.update(s for s, _, _ in amr.edges)
            nodes_.update(t for _, _, t in amr.edges)
        return amr.root, nodes_, amr.edges.copy()
    if subgraph_root is not None:
        # clean subgraph root
        if subgraph_root not in amr.nodes:
            if not any(subgraph_root in [s, t] for s, r, t in amr.edges):
                raise Exception(f'[{__name__}] Subgraph root "{subgraph_root}" '
                                f'does not exist in AMR "{amr.id}".')
            if subgraph_nodes is not None and subgraph_root not in subgraph_nodes:
                raise Exception(f'[{__name__}] Subgraph root "{subgraph_root}" is not contained in '
                                f'nodes {set(subgraph_nodes)} in AMR "{amr.id}".')
    if subgraph_nodes is not None:
        # clean subgraph nodes
        if any(n not in amr.nodes for n in subgraph_nodes):
            missing_concept_nodes = {s for s, _, _ in amr.edges if s not in amr.nodes}
            missing_concept_nodes.update(t for _, _, t in amr.edges if t not in amr.nodes)
            for n in subgraph_nodes:
                if n not in amr.nodes and n not in missing_concept_nodes:
                    raise Exception(f'[{__name__}] Node "{n}" does not exist in AMR "{amr.id}".')
        subgraph_nodes = set(subgraph_nodes)
    if subgraph_edges is not None:
        # clean subgraph edges
        # existing_edges = set(amr.edges)
        # for e in subgraph_edges:
        #     if e not in existing_edges:
        #         raise Exception(f'[{__name__}] Edge "{e}" does not exist in AMR "{amr.id}".')
        subgraph_edges = [e for e in amr.edges if e in set(subgraph_edges)]
    if subgraph_nodes is None:
        # find subgraph nodes (based on root or edges)
        # Note: We can't ignore this computation if ignore_nodes is set because subgraph_edges may depend on it.
        if subgraph_edges is not None:
            subgraph_nodes = {s for s, r, t in subgraph_edges}
            subgraph_nodes.update(t for s, r, t in subgraph_edges)
        elif undirected_graph:
            subgraph_nodes = {n for n in amr.nodes}
            subgraph_nodes.update(s for s, _, _ in amr.edges)
            subgraph_nodes.update(t for _, _, t in amr.edges)
        else:
            descendants = _get_reachable_nodes(amr)
            subgraph_nodes = descendants[subgraph_root]
    if subgraph_edges is None:
        # find subgraph edges (based on nodes)
        subgraph_edges = [(s, r, t) for s, r, t in amr.edges if (s in subgraph_nodes and t in subgraph_nodes)]
    if subgraph_root is None:
        # assign subgraph root
        if amr.root in subgraph_nodes:
            subgraph_root = amr.root
        elif not ignore_root:
            # find best root
            reachable_nodes = _get_reachable_nodes(amr, subgraph_nodes, subgraph_edges)
            subgraph_root = _best_root(reachable_nodes, subgraph_nodes)
    return subgraph_root, subgraph_nodes, subgraph_edges


def get_subgraph(amr: AMR, subgraph_root: str = None, subgraph_nodes: Iterable[str] = None, subgraph_edges: Iterable[Edge] = None) -> AMR:
    """
    Get an AMR which is a subgraph of this AMR specified by subgraph_root, subgraph_nodes, and subgraph_edges
    Args:
        amr (AMR): an AMR
        subgraph_root (str): the root of the subgraph
        subgraph_nodes (Iterable[str]): the nodes contained in the subgraph
        subgraph_edges (Iterable[Edge]): the edges contained in the subgraph

    Returns:
        AMR: a new AMR which is a subgraph of the given AMR
    """
    root, nodes, edges = process_subgraph(amr, subgraph_root=subgraph_root, subgraph_nodes=subgraph_nodes,
                                          subgraph_edges=subgraph_edges)
    sub = Subgraph_AMR(root=root,
              edges=[e for e in edges],
              nodes={n: amr.nodes[n] for n in nodes})
    return sub


class Subgraph_AMR(AMR):

    def __init__(self, id: str = None, tokens: List[str] = None, root: str = None, nodes: Dict[str, str] = None,
                 edges: List[Edge] = None):
        super().__init__(id=id, root=root, nodes=nodes, edges=edges, tokens=tokens)

    def __str__(self):
        graph_strings = []
        for component in find_connected_components(self):
            root = component[0]
            edges = [(s, r, t) for s, r, t in self.edges if s in component]
            sg_string = self.subgraph_string(subgraph_root=root, subgraph_nodes=component, subgraph_edges=edges,
                                             pretty_print=False)
            graph_strings.append(sg_string)
        return f'[{class_name(self)} {self.id}]: ' + ', '.join(graph_strings)
