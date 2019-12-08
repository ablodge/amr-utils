

def is_rooted_dag(amr):
    roots = [n for n in amr.nodes.keys()]
    for s,r,t in amr.edges:
        if t in roots:
            roots.remove(t)
    if len(roots)==1 and roots[0]==amr.root:
        return True
    return False


def get_rooted_components(amr):
    descendents = {n:{n} for n in amr.nodes.keys()}
    roots = [n for n in amr.nodes.keys()]
    for s, r, t in amr.edges:
        if t in roots:
            roots.remove(t)
        for d in descendents:
            if s in descendents[d]:
                descendents[d].update(descendents[t])
    components = [(r,list(descendents[r])) for r in roots]
    components = sorted(components, key=lambda x:len(x[1]), reverse=True)
    return list(components)


def iterate_nodes_breadth_first(amr):
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


def simple_node_map(amr1, amr2):
    parents1 = {n:set() for n in amr1.nodes}
    children1 = {n:set() for n in amr1.nodes}
    parents2 = {n: set() for n in amr2.nodes}
    children2 = {n: set() for n in amr2.nodes}
    for s,r,t in amr1.nodes:
        parents1[t].add(amr1.nodes[s].lower())
        children1[s].add(amr1.nodes[t].lower())
    for s, r, t in amr2.nodes:
        parents2[t].add(amr2.nodes[s].lower())
        children2[s].add(amr2.nodes[t].lower())

    test1 = lambda x,y: amr1.nodes[x].lower()==amr2.nodes[y].lower()
    test2 = lambda x,y: parents1[x]==parents2[y]
    test3 = lambda x,y: children1[x] == children2[y]

    node_map = {n:amr2.root for n in amr1.nodes}
    taken = []
    for n in amr1.nodes:
        max_score = 0
        for n2 in amr2.nodes:
            if n2 in taken:
                continue
            score = 0
            for test in [test1,test2,test3]:
                if test(n,n2):
                    score+=1
            if score > max_score:
                node_map[n] = n2
                max_score = score
        taken.append(node_map[n])
    return node_map

