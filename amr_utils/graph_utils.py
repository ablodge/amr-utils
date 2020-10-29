
from amr_utils.amr import AMR

def is_rooted_dag(amr):
    if not amr.nodes:
        return False
    roots = [n for n in amr.nodes.keys()]
    for s,r,t in amr.edges:
        if t in roots:
            roots.remove(t)
    if len(roots)==1 and roots[0]==amr.root:
        return True
    return False


def get_rooted_components(amr):

    if not amr.nodes:
        return []
    descendants = {n:{n} for n in amr.nodes.keys()}
    roots = [n for n in amr.nodes.keys()]
    taken = set()
    for s, r, t in amr.edges:
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

def simple_node_map(amr1, amr2):
    parents1 = {n:set() for n in amr1.nodes}
    parents2 = {n: set() for n in amr2.nodes}
    children1 = {n:set() for n in amr1.nodes}
    children2 = {n: set() for n in amr2.nodes}
    edges1 = {n: set() for n in amr1.nodes}
    edges2 = {n: set() for n in amr2.nodes}

    for s,r,t in amr1.edges:
        if r.endswith('-of'):
            s,r,t = t,r.replace('-of',''),s
        parents1[t].add(amr1.nodes[s].lower())
        children1[s].add(amr1.nodes[t].lower())
        edges1[t].add(f'in {r}')
        edges1[s].add(f'out {r}')
    for s, r, t in amr2.edges:
        if r.endswith('-of'):
            s,r,t = t,r.replace('-of',''),s
        parents2[t].add(amr2.nodes[s].lower())
        children2[s].add(amr2.nodes[t].lower())
        edges2[t].add(f'in {r}')
        edges2[s].add(f'out {r}')

    test1 = lambda x,y: amr1.nodes[x].lower()==amr2.nodes[y].lower()
    test2 = lambda x,y: parents1[x]==parents2[y]
    test3 = lambda x,y: children1[x] == children2[y]
    test4 = lambda x, y: edges1[x] == edges2[y]

    node_map = {n:amr2.root for n in amr1.nodes}
    taken = {}
    scores = {}
    replaced = set()
    for n in amr1.nodes:
        max_score = 0
        best = amr2.root
        for n2 in amr2.nodes:
            score = 0
            for test in [test1,test2,test3,test4]:
                if test(n,n2):
                    score+=1
            if score > max_score:
                if n2 in taken:
                    other_score = scores[n2]
                    if score<=other_score:
                        continue
                best = n2
                max_score = score
        if best in taken:
            other = taken[best]
            node_map[n] = best
            node_map[other] = amr2.root
            replaced.add(other)
        else:
            node_map[n] = best
        if max_score>0:
            taken[node_map[n]] = n
            scores[node_map[n]] = max_score
    # for n in amr1.nodes:
    #     max_score = 0
    #     if n in replaced:
    #         for n2 in amr2.nodes:
    #             if n2 in taken:
    #                 continue
    #             score = 0
    #             for test in [test1, test2, test3, test4]:
    #                 if test(n, n2):
    #                     score += 1
    #             if score > max_score:
    #                 node_map[n]  = n2
    #                 max_score = score
    return node_map


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
