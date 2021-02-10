
from amr_utils.amr import AMR
from amr_utils.smatch import get_best_match


def get_subgraph(amr, nodes: list, edges: list):
    if not nodes:
        return AMR()
    potential_root = nodes.copy()
    for x, r, y in amr.edges:
        if x in nodes and y in nodes:
            if y in potential_root:
                potential_root.remove(y)
    root = potential_root[0] if len(potential_root) > 0 else nodes[0]
    sub = AMR(root=root,
               edges=edges,
               nodes={n: amr.nodes[n] for n in nodes})
    for s,r,t in edges:
        if s not in nodes:
            sub.nodes[s] = '<var>'
        if t not in nodes:
            sub.nodes[t] = '<var>'
    return sub


def is_rooted_dag(amr, nodes):
    if not nodes:
        return False
    roots = nodes.copy()
    edges = [(s,r,t) for s,r,t in amr.edges if s in nodes and t in nodes]
    for s,r,t in edges:
        if t in roots:
            roots.remove(t)
    if len(roots)==1:
        return True
    return False


def get_connected_components(amr, nodes):

    if not nodes:
        return []
    descendants = {n:{n} for n in nodes}
    roots = [n for n in nodes]
    taken = set()
    edges = [(s, r, t) for s, r, t in breadth_first_edges(amr, ignore_reentrancies=True) if s in nodes and t in nodes]
    for s, r, t in edges:
        if t in taken: continue
        taken.add(t)
        if t in roots:
            roots.remove(t)
        for d in descendants:
            if s in descendants[d]:
                descendants[d].update(descendants[t])
    components = []
    for root in roots:
        edges = []
        for s,r,t in breadth_first_edges(amr, ignore_reentrancies=True):
            if s in descendants[root] and t in descendants[root]:
                edges.append((s,r,t))
        sub = AMR(nodes={n:amr.nodes[n] for n in descendants[root]}, root=root, edges=edges)
        components.append(sub)
    components = sorted(components, key=lambda x:len(x.nodes), reverse=True)
    return list(components)


def is_projective_node_(amr, n, descendants, positions, ignore=None):
    span = {positions[m] for m in descendants if m in positions}
    if not span:
        return True, []
    max_token = max(span)
    min_token = min(span)
    if max_token - min_token <= 1:
        return True, [i for i in range(min_token,max_token+1)]
    for tok in range(min_token + 1, max_token):
        if ignore and tok in ignore:
            continue
        if tok in span:
            continue
        align = amr.get_alignment(token_id=tok)
        if align and align.tokens[0] not in span:
            return False, [i for i in range(min_token,max_token+1)]
    return True, [i for i in range(min_token,max_token+1)]


def is_projective(amr):

    descendants = {n: {n} for n in amr.nodes.keys()}
    for s, r, t in breadth_first_edges(amr, ignore_reentrancies=True):
        for d in descendants:
            if s in descendants[d]:
                descendants[d].update(descendants[t])
    positions = {}
    alignments = {}
    for n in amr.nodes:
        align = amr.get_alignment(node_id=n)
        alignments[n] = align
        if align:
            positions[n] = align.tokens[0]

    nonprojective = {}
    used = set()
    for n in breadth_first_nodes(amr):
        if n in used:
            continue
        test, span = is_projective_node_(amr, n, descendants[n], positions)
        used.update(alignments[n].nodes)
        if not test:
            nonprojective[n] = span
    if not nonprojective:
        return True, []
    for n in list(nonprojective.keys()):
        for d in descendants[n]:
            if d!=n and d in nonprojective:
                del nonprojective[n]
                break

    used = set()
    culprits = []
    for n in nonprojective:
        for tok in nonprojective[n]:
            align = amr.get_alignment(token_id=tok)
            if not align or align in used:
                continue
            test, _ = is_projective_node_(amr, n, descendants[n], positions, ignore=align.tokens)
            used.add(align)
            if test:
                culprits.append(align)
    return False, culprits


def breadth_first_nodes(amr):
    if amr.root is None:
        return
    nodes = [amr.root]
    children = [(s,r,t) for s,r,t in amr.edges if s in nodes]
    children = sorted(children, key=lambda x: x[1].lower())
    edges = [e for e in amr.edges]
    yield amr.root
    while True:
        for s,r,t in children:
            if t not in nodes:
                nodes.append(t)
                yield t
            edges.remove((s,r,t))
        children = [(s, r, t) for s, r, t in edges if s in nodes and t not in nodes]
        children = list(sorted(children, key=lambda x: x[1].lower()))
        if not children:
            break


def breadth_first_edges(amr, ignore_reentrancies=False):
    if amr.root is None:
        return
    nodes = [amr.root]
    children = [(s,r,t) for s,r,t in amr.edges if s in nodes]
    children = sorted(children, key=lambda x: x[1].lower())
    edges = [e for e in amr.edges]
    while True:
        for s,r,t in children:
            edges.remove((s, r, t))
            if ignore_reentrancies and t in nodes:
                continue
            if t not in nodes:
                nodes.append(t)
            yield (s,r,t)
        children = [(s, r, t) for s, r, t in edges if s in nodes]
        children = list(sorted(children, key=lambda x: x[1].lower()))
        if not children:
            break


def depth_first_nodes(amr):
    visited, stack = {amr.root}, []
    children = [(s, r, t) for s, r, t in amr.edges if s == amr.root and t not in visited]
    children = list(sorted(children, key=lambda x: x[1].lower(), reverse=True))
    stack.extend(children)
    edges = [e for e in amr.edges]
    yield amr.root

    while stack:
        s, r, t = stack.pop()
        if t in visited:
            continue
        yield t
        edges.remove((s, r, t))
        visited.add(t)
        children = [(s2, r2, t2) for s2, r2, t2 in edges if s2 == t]
        children = list(sorted(children, key=lambda x: x[1].lower(), reverse=True))
        stack.extend(children)


def depth_first_edges(amr, ignore_reentrancies=False):
    visited, stack = {amr.root}, []
    children = [(s, r, t) for s, r, t in amr.edges if s == amr.root and t not in visited]
    children = list(sorted(children, key=lambda x: x[1].lower(), reverse=True))
    stack.extend(children)
    edges = [e for e in amr.edges]

    while stack:
        s,r,t = stack.pop()
        if ignore_reentrancies and t in visited:
            continue
        yield (s,r,t)
        edges.remove((s,r,t))
        visited.add(t)
        children = [(s2,r2,t2) for s2,r2,t2 in edges if s2==t]
        children = list(sorted(children, key=lambda x: x[1].lower(), reverse=True))
        stack.extend(children)


def get_shortest_path(amr, n1, n2, ignore_reentrancies=False):
    path = [n1]
    for s,r,t in depth_first_edges(amr, ignore_reentrancies):
        if s in path:
            while path[-1]!=s:
                path.pop()
            path.append(t)
            if t==n2:
                return path
    return None


# def is_cycle(amr, nodes):
#     descendants = {n: {n} for n in nodes}
#     for s, r, t in amr.edges:
#         if s in nodes and t in nodes:
#             for d in descendants:
#                 if s in descendants[d]:
#                     descendants[d].update(descendants[t])
#     for n in nodes:
#         for n2 in nodes:
#             if n==n2:
#                 continue
#             if n in descendants[n2] and n2 in descendants[n]:
#                 return True
#     return False


def get_node_alignment(amr1:AMR, amr2:AMR):
    prefix1 = "a"
    prefix2 = "b"
    node_map1 = {}
    node_map2 = {}
    idx = 0
    for n in amr1.nodes.copy():
        amr1._rename_node(n, prefix1+str(idx))
        node_map1[prefix1+str(idx)] = n
        idx+=1
    idx = 0
    for n in amr2.nodes.copy():
        amr2._rename_node(n, prefix2+str(idx))
        node_map2[prefix2 + str(idx)] = n
        idx += 1
    instance1 = []
    attributes1 = []
    relation1 = []
    for s,r,t in amr1.triples(normalize_inverse_edges=True):
        if r==':instance':
            instance1.append((r,s,t))
        elif t not in amr1.nodes:
            attributes1.append((r,s,t))
        else:
            relation1.append((r,s,t))
    instance2 = []
    attributes2 = []
    relation2 = []
    for s,r,t in amr2.triples(normalize_inverse_edges=True):
        if r==':instance':
            instance2.append((r,s,t))
        elif t not in amr2.nodes:
            attributes2.append((r,s,t))
        else:
            relation2.append((r,s,t))
    # optionally turn off some of the node comparison
    doinstance = doattribute = dorelation = True
    (best_mapping, best_match_num) = get_best_match(instance1, attributes1, relation1,
                                                    instance2, attributes2, relation2,
                                                    prefix1, prefix2, doinstance=doinstance,
                                                    doattribute=doattribute, dorelation=dorelation)
    test_triple_num = len(instance1) + len(attributes1) + len(relation1)
    gold_triple_num = len(instance2) + len(attributes2) + len(relation2)
    for n in amr1.nodes.copy():
        amr1._rename_node(n, node_map1[n])
    for n in amr2.nodes.copy():
        amr2._rename_node(n, node_map2[n])

    align_map = {}
    for i,j in enumerate(best_mapping):
        a = prefix1 + str(i)
        if j==-1:
            continue
        b = prefix2 + str(j)
        align_map[node_map1[a]] = node_map2[b]
    if amr1.root not in align_map:
        align_map[amr1.root] = amr2.root
    for s,r,t in breadth_first_edges(amr1, ignore_reentrancies=True):
        if t not in align_map:
            for s2,r2,t2 in amr2.edges:
                if align_map[s]==s2 and r==r2 and amr1.nodes[t]==amr2.nodes[t2]:
                    align_map[t] = t2
            if t not in align_map:
                align_map[t] = align_map[s]

    if not all(n in align_map for n in amr1.nodes):
        raise Exception('Failed to build node alignment:', amr1.id, amr2.id)
    prec = best_match_num / test_triple_num if test_triple_num>0 else 0
    rec = best_match_num / gold_triple_num if gold_triple_num>0 else 0
    f1 = 2*(prec*rec)/(prec+rec) if (prec+rec)>0 else 0
    return align_map, prec, rec, f1
