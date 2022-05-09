from amr_utils.amr import AMR, AMR_Notation


def depth_first_edges(amr: AMR, alphabetical_edges: bool = True, ignore_reentrancies: bool = False,
                      root: str = None):
    """
    Iterate the edges in an AMR in depth first order
    Args:
        amr (AMR): the AMR to iterate
        root (str): node from which to start exploration (default: amr.root)
        ignore_reentrancies (bool): whether to skip reentrant edges when iterating
        alphabetical_edges (bool): whether to explore edges in alphabetical order rather than their incidental order

    Yields:
        tuple: pairs of the form (depth, (source_id, relation, target_id))
    """
    for depth, e in amr._depth_first_edges(alphabetical_edges=alphabetical_edges, ignore_reentrancies=ignore_reentrancies, subgraph_root=root):
        yield depth, e


def breadth_first_edges(amr: AMR, alphabetical_edges: bool = True, ignore_reentrancies: bool = False,
                        root: str = None):
    """
    Iterate the edges in an AMR in breadth first order
    Args:
        amr (AMR): the AMR to iterate
        root (str): node from which to start exploration (default: amr.root)
        ignore_reentrancies (bool): whether to skip reentrant edges when iterating
        alphabetical_edges (bool): whether to explore edges in alphabetical order rather than their incidental order

    Yields:
        tuple: pairs of the form (depth, (source_id, relation, target_id))
    """
    if root is None:
        root = amr.root
        if amr.root is None:
            return
    nodes_to_visit = [(1, root)]
    children = {n: [] for n in amr.nodes}
    for i, e in enumerate(amr.edges):
        s, r, t = e
        children[s].append((i, e))
    if alphabetical_edges:
        for n in amr.nodes:
            if len(children[n])>1:
                children[n] = sorted(children[n], key=lambda x: AMR_Notation.lexicographic_edge_key(amr, x[1]))
    visited_edges = set()
    visited_nodes = {root} if ignore_reentrancies else None
    while nodes_to_visit:
        next_nodes_to_visit = []
        path_found = False
        for depth, n in nodes_to_visit:
            for edge_idx, e in children[n]:
                target = e[-1]
                if edge_idx in visited_edges: continue
                visited_edges.add(edge_idx)
                if target not in nodes_to_visit and children[target] and target != root:
                    if alphabetical_edges or amr._is_valid_instance_location(e):
                        next_nodes_to_visit.append((depth+1, target))
                        path_found = True
                if ignore_reentrancies:
                    if target in visited_nodes:
                        continue
                    visited_nodes.add(target)
                yield depth, e
        nodes_to_visit = next_nodes_to_visit
        if not path_found:
            return


def traverse_graph(amr: AMR, alphabetical_edges: bool = True, root: str= None):
    """
    Iterate the edges in an AMR graph in breadth first order, ignoring edge direction
    Args:
        amr (AMR): the AMR to iterate
        root (str): node from which to start exploration (default: amr.root)
        alphabetical_edges (bool): whether to explore edges in alphabetical order rather than their incidental order

    Yields:
        tuple: pairs of the form (depth, (source_id, relation, target_id))
    """
    if root is None:
        root = amr.root
        if amr.root is None:
            return
    nodes_to_visit = [(1, root)]
    children = {n: [] for n in amr.nodes}
    for i, e in enumerate(amr.edges):
        s, r, t = e
        children[s].append((i, e))
        r = AMR_Notation.invert_relation(r)
        children[t].append((i, (t, r, s)))
    if alphabetical_edges:
        for n in amr.nodes:
            if len(children[n])>1:
                children[n] = sorted(children[n], key=lambda x: AMR_Notation.lexicographic_edge_key(amr, x[1]))
    visited_edges = set()
    while True:
        next_nodes_to_visit = []
        path_found = False
        for depth, n in nodes_to_visit:
            for edge_idx, e in children[n]:
                s, r, t = e
                if edge_idx in visited_edges:
                    continue
                visited_edges.add(edge_idx)
                if t not in nodes_to_visit and children[t]:
                    next_nodes_to_visit.append((depth+1, t))
                    path_found = True
                yield depth, e
        nodes_to_visit = next_nodes_to_visit
        if not path_found:
            return


def triples(amr: AMR, depth_first: bool = False, breadth_first: bool = False):
    """
    Iterate AMR triples
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): whether to use depth first search
        breadth_first (bool): whether to use breadth first search

    Yields:
        tuple: tuples of the form (source_id, relation, target_id) or (source_id, relation, value)
    """
    if depth_first or breadth_first:
        visited_nodes = set()
        yield amr.root, ':instance', amr.nodes[amr.root]
        for s,r,t in edges(amr, depth_first, breadth_first, ignore_attributes=False):
            if AMR_Notation.is_attribute(amr.nodes[t]):
                yield s, r, amr.nodes[t]
            else:
                yield s, r, t
                if t not in visited_nodes:
                    visited_nodes.add(t)
                    yield t, ':instance', amr.nodes[t]
    else:
        yield amr.root, ':instance', amr.nodes[amr.root]
        for s, r, t in edges(amr, ignore_attributes=False):
            if AMR_Notation.is_attribute(amr.nodes[t]):
                yield s, r, amr.nodes[t]
            else:
                yield s, r, t
                if amr.reentrancy_artifacts is not None and t in amr.reentrancy_artifacts:
                    if (s, r, t) == amr.reentrancy_artifacts[t]:
                        yield t, ':instance', amr.nodes[t]
                else:
                    yield t, ':instance', amr.nodes[t]


def edges(amr: AMR, depth_first: bool = False, breadth_first: bool = False, ignore_attributes: bool = False):
    '''
    Iterate AMR edges
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): whether to use depth first search
        breadth_first (bool): whether to use breadth first search
        ignore_attributes (bool): whether to not include attribute relations as edges

    Yields:
        tuple: edges, which are tuples of the form (source_id, relation, target_id)
    '''
    iter = depth_first_edges(amr) if depth_first \
        else breadth_first_edges(amr) if breadth_first \
        else enumerate(amr.edges)
    for _, e in iter:
        if not (ignore_attributes and AMR_Notation.is_attribute(amr.nodes[e[2]])):
            yield e


def nodes(amr: AMR, depth_first=False, breadth_first=False, ignore_attributes=False):
    '''
    Iterate AMR nodes
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): whether to use depth first search
        breadth_first (bool): whether to use breadth first search
        ignore_attributes (bool): whether to not include attribute value nodes

    Yields:
        str: node ids
    '''
    if depth_first or breadth_first:
        yield amr.root
        iter = depth_first_edges(amr, ignore_reentrancies=True) if depth_first \
            else breadth_first_edges(amr, ignore_reentrancies=True)
        for _, e in iter:
            s, r, t = e
            if not (ignore_attributes and AMR_Notation.is_attribute(amr.nodes[t])):
                yield t
    else:
        for n in amr.nodes:
            if not (ignore_attributes and AMR_Notation.is_attribute(amr.nodes[n])):
                yield n


def attributes(amr: AMR, depth_first=False, breadth_first=False):
    '''
    Iterate AMR attributes
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): whether to use depth first search
        breadth_first (bool): whether to use breadth first search

    Yields:
        tuple: tuples of the form (source_id, relation, value)
    '''
    iter = depth_first_edges(amr) if depth_first \
        else breadth_first_edges(amr) if breadth_first \
        else enumerate(amr.edges)
    for _, e in iter:
        s, r, t = e
        if AMR_Notation.is_attribute(amr.nodes[t]):
            yield s, r, amr.nodes[t]


def reentrancies(amr: AMR, depth_first: bool=False, breadth_first: bool=False):
    '''
    Iterate AMR reentrencies. A reentrancy occurs when a node has more than one parent edge.
    Reentrancies are what make AMRs graph-structured rather than tree-structured.
    Args:
        amr (AMR): the AMR to iterate
        depth_first (bool): whether to use depth first search
        breadth_first (bool): whether to use breadth first search
        ignore_attributes (bool): whether to not include attribute relations as edges

    Yields:
        tuple: (node, edge) pairs for each node with a reentrancy and each parent edge
    '''
    parents = {n: [] for n in amr.nodes}
    for s, r, t in edges(amr, depth_first=depth_first, breadth_first=breadth_first):
        if not depth_first \
                and not breadth_first \
                and amr.reentrancy_artifacts is not None \
                and t in amr.reentrancy_artifacts \
                and (s, r, t) == amr.reentrancy_artifacts[t]:
            parents[t].insert(0, (s, r, t))
        else:
            parents[t].append((s, r, t))
    for n in nodes(amr, depth_first=depth_first, breadth_first=breadth_first):
        if len(parents[n]) > 1:
            for e in parents[n]:
                yield n, e
        elif n == amr.root and len(parents[n]) > 0:
            for e in parents[n]:
                yield n, e
