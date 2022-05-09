from typing import Iterable, Tuple

from amr_utils import amr_iterators
from amr_utils.amr import AMR
from amr_utils.amr_alignments import AMR_Alignment_Set


def _get_reachable_nodes(amr: AMR, nodes: Iterable[str] = None, edges: Iterable[Tuple[str, str, str]] = None):
    if edges is None:
        edges = amr.edges
    if nodes is None:
        nodes = amr.nodes
    else:
        edges = [(s, r, t) for s, r, t in edges if (s in nodes and t in nodes)]
    descendants = {n: {n} for n in nodes}
    for s, r, t in edges:
        for n in descendants:
            if s in descendants[n] and (s in nodes and t in nodes):
                descendants[n].update(descendants[t])
    return descendants


def is_rooted_dag(amr: AMR, root: str = None, nodes: Iterable[str] = None,
                  edges: Iterable[Tuple[str, str, str]] = None):
    if nodes is None:
        nodes = amr.nodes
    if root is None:
        root = amr.root
    if not nodes:
        return False
    reachable_nodes = _get_reachable_nodes(amr, nodes, edges)
    # check for cycles
    for s, r, t in amr.edges:
        if s in reachable_nodes[t]:
            return False
    # check that all nodes are reachable
    if all(n in reachable_nodes[root] for n in nodes):
        return True
    return False


def has_cycles(amr: AMR):
    reachable_nodes = _get_reachable_nodes(amr)
    for s, r, t in amr.edges:
        if s in reachable_nodes[t]:
            return True
    return False


def find_cycles(amr: AMR):
    reachable_nodes = _get_reachable_nodes(amr)
    cycles = []
    equivalence_classes = []
    for s, r, t in amr.edges:
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


def get_subgraph(amr, root: str, nodes: Iterable[str], edges: Iterable[Tuple[str, str, str]]):
    sub = AMR(root=root,
              edges=[e for e in edges],
              nodes={n: amr.nodes[n] for n in nodes})
    for s, r, t in edges:
        if s not in nodes:
            sub.nodes[s] = '<var>'
        if t not in nodes:
            sub.nodes[t] = '<var>'
    return sub


def is_connected(amr: AMR, nodes: Iterable[str] = None, edges: Iterable[Tuple[str, str, str]] = None):
    if nodes is None:
        nodes = amr.nodes
    reachable_nodes = _get_reachable_nodes(amr, nodes, edges)
    for n in reachable_nodes:
        if all(m in reachable_nodes[n] for m in nodes):
            return True
    return False


def find_connected_components(amr):
    reachable_nodes = _get_reachable_nodes(amr)

    components = []
    taken = set()
    # component attached to root
    if amr.root is not None:
        component_nodes = [amr.root]
        taken.add(amr.root)
        component_nodes.extend(n for n in reachable_nodes[amr.root] if n not in taken)
        components.append(component_nodes)
        taken.update(component_nodes)
    # disconnected components
    if len(taken) < len(amr.nodes):
        roots = {n for n in amr.nodes}
        for n in reachable_nodes:
            for m in reachable_nodes[n]:
                if n != m and m in roots:
                    roots.remove(m)
        for root in roots:
            if root in taken:
                continue
            component_nodes = [root]
            taken.add(root)
            component_nodes.extend(n for n in reachable_nodes[root] if n not in taken)
            components.append(component_nodes)
            taken.update(component_nodes)
    # handle cycles
    if len(taken) < len(amr.nodes):
        cycles = find_cycles(amr)
        for cycle in cycles:
            for c in cycle:
                if c in taken:
                    continue
                component_nodes = [c]
                taken.add(c)
                component_nodes.extend(n for n in reachable_nodes[c] if n not in taken)
                components.append(component_nodes)
                taken.update(component_nodes)
                break
    components = sorted(components, key=lambda ns: len(ns), reverse=True)
    return components


def break_into_connected_components(amr: AMR):
    components = find_connected_components(amr)
    amrs = []
    for nodes in components:
        amr_ = amr.copy()
        amr_.nodes = {n: amr.nodes[n] for n in nodes}
        amr_.edges = [(s, r, t) for s, r, t in amr.edges if (s in nodes and t in nodes)]
        amr_.root = nodes[0]
        amr_.reentrancy_artifacts = None
        amrs.append(amr_)
    return amrs


def get_shortest_path(amr, n1, n2):
    paths = {n1: [n1]}
    for s, r, t in amr_iterators.edges(amr, breadth_first=True):
        if s in paths and t not in paths:
            paths[t] = paths[s] + [t]
            if t == n2:
                return paths[t]
    return None


def is_projective(amr: AMR, alignments: AMR_Alignment_Set):
    align = find_nonprojective_alignment(amr, alignments)
    if align is None:
        return True
    return False


def find_nonprojective_alignment(amr: AMR, alignments: AMR_Alignment_Set):
    reachable_nodes = _get_reachable_nodes(amr)
    nodes = [n for n in amr_iterators.nodes(amr, breadth_first=True)]
    for n in reversed(nodes):
        min_token_idx = float('inf')
        max_token_idx = float('-inf')
        for n2 in reachable_nodes[n]:
            for align in alignments.get_all(node=n2):
                for t in align.tokens:
                    if t < min_token_idx:
                        min_token_idx = t
                    if t > max_token_idx:
                        max_token_idx = t
        aligns = alignments.find_all(lambda a: any(min_token_idx <= t <= max_token_idx for t in a.tokens))
        for align in aligns:
            for n2 in align.nodes:
                if n2 not in reachable_nodes[n]:
                    return align
            for s,r,t in align.edges:
                if not (s in reachable_nodes[n] or t in reachable_nodes[n]):
                    return align
    return None
