import re
from amr import AMR
from features import amr_reification_rules

Align_Edge_RE = {
    ':location': re.compile('^(in|at|on)$', flags=re.IGNORECASE),
    ':time': re.compile('^(in|at|when|during)$', flags=re.IGNORECASE),
    ':domain': re.compile('^(be|is|are|was|were|am)$', flags=re.IGNORECASE),
    ':poss': re.compile('^(\'s|of)$', flags=re.IGNORECASE),
    ':condition': re.compile('^if$', flags=re.IGNORECASE),
    ':purpose': re.compile('^for$', flags=re.IGNORECASE),
    ':beneficiary': re.compile('^(for|against)$', flags=re.IGNORECASE),
    ':source': re.compile('^(from|off)$', flags=re.IGNORECASE),
    ':destination': re.compile('^(into)$', flags=re.IGNORECASE),
    ':compared-to': re.compile('^(like|than)$', flags=re.IGNORECASE),
}

Align_Node_RE = {
    'amr-unknown': re.compile('^(wh\w+|how)$', flags=re.IGNORECASE),
    'i': re.compile('^(i|me|my|mine)$', flags=re.IGNORECASE),
    'we': re.compile('^(we|us|ours?)$', flags=re.IGNORECASE),
    'he': re.compile('^(he|him|his)$', flags=re.IGNORECASE),
    'she': re.compile('^(she|hers?)$', flags=re.IGNORECASE),
    'they': re.compile('^(they|them|theirs?)$', flags=re.IGNORECASE),
    # modals and conjunctions
    'cause-01': re.compile('^(caus(e|ed|es|ing)|because|thus|so|hence)$', flags=re.IGNORECASE),
    'contrast-01': re.compile('^(but|yet|while|however)$', flags=re.IGNORECASE),
    'obligate-01': re.compile('^(need(s|ed|ing)?|must|have)$', flags=re.IGNORECASE),
    'possible-01': re.compile('^(can|could|might|maybe|possibl[ey]|perhaps)$', flags=re.IGNORECASE),
    'possible': re.compile('^(can|could|might|maybe|possibl[ey]|perhaps)$', flags=re.IGNORECASE),
    'recommend-01': re.compile('^(recommend(s|ed|ing)?|should)$', flags=re.IGNORECASE),
    'expect-01': re.compile('^(expect(s|ed|ing)?|should)$', flags=re.IGNORECASE),
    'allow-01': re.compile('^(allow(s|ed|ing)?|let)$', flags=re.IGNORECASE),
    'oppose-01': re.compile('^(against|anti-)$', flags=re.IGNORECASE),
    # abbreviations
    'kilometer': re.compile('^(kilometers?|kms?)$', flags=re.IGNORECASE),
    # numbers
    '0': re.compile('^(0(th)?|zero)$', flags=re.IGNORECASE),
    '1': re.compile('^(1(st)?|one)$', flags=re.IGNORECASE),
    '2': re.compile('^(2(nd)?|two)$', flags=re.IGNORECASE),
    '3': re.compile('^(3(rd)?|three)$', flags=re.IGNORECASE),
    '4': re.compile('^(4(th)?|four)$', flags=re.IGNORECASE),
    '5': re.compile('^(5(th)?|five)$', flags=re.IGNORECASE),
    '6': re.compile('^(6(th)?|six)$', flags=re.IGNORECASE),
    '7': re.compile('^(7(th)?|seven)$', flags=re.IGNORECASE),
    '8': re.compile('^(8(th)?|eight)$', flags=re.IGNORECASE),
    '9': re.compile('^(9(th)?|nine)$', flags=re.IGNORECASE),
    '10': re.compile('^(10(th)?|ten)$', flags=re.IGNORECASE),
    '100': re.compile('^(100(th)?|hundred)$', flags=re.IGNORECASE),
    '1000': re.compile('^(1,?000(th)?|thousand)$', flags=re.IGNORECASE),
    '1000000': re.compile('^(1,?000,?000(th)?|million)$', flags=re.IGNORECASE),
    '1000000000': re.compile('^(1,?000,?000,?000(th)?|billion)$', flags=re.IGNORECASE),
}

# add all reifications to Align_Node_RE
for rel in Align_Edge_RE:
    if rel in amr_reification_rules:
        Align_Node_RE[amr_reification_rules[rel]] = Align_Edge_RE[rel]


'''a custumized rule for searching for source,rel,edge combinations and their word alignemnts'''
def build_rule(amr, words, search_triple, regex, include_source= True, include_rel=True, include_target=True):
    amr_elems = []
    triple = None
    for tr, id in zip(amr.edge_triples(), amr.edge_ids()):
        source, rel, target = tr
        source_name = amr.get_name(source).split('/')[-1]
        if search_triple[0] and source_name != search_triple[0]:
            continue
        if search_triple[1] and rel != search_triple[1]:
            continue
        target_name = amr.get_name(target).split('/')[-1]
        if search_triple[2] and target_name != search_triple[2]:
            continue
        triple = source, id, target
        break
    if not triple: return
    source, rel, target = triple
    if include_source: amr_elems.append(source)
    if include_rel: amr_elems.append(rel)
    if include_target: amr_elems.append(target)
    for w in words:
        if regex.match(w):
            return amr_elems, w
    return


Align_Triple_Rules = [
    # polarity
    lambda amr, words : build_rule(
                        amr, words,
                        search_triple = ('', ':polarity', '-'),
                        regex = re.compile('^(un[\w-]+|non[\w-]+|il[\w-]+)$', flags=re.IGNORECASE)),
    lambda amr, words : build_rule(
                        amr, words,
                        search_triple = ('', ':polarity', '-'),
                        regex = re.compile('^(not|no|n\'t)$', flags=re.IGNORECASE),
                        include_source=False),
    # months
    lambda amr, words : build_rule(
                        amr, words,
                        search_triple = ('',':month','1'),
                        regex = re.compile('^(0?1(st|-|/)?|jan([.]|uary)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : build_rule(
                        amr, words,
                        search_triple = ('',':month','2'),
                        regex = re.compile('^(0?2(nd|-|/)?|feb([.]|ruary)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : build_rule(
                        amr, words,
                        search_triple = ('',':month','3'),
                        regex = re.compile('^(0?3(rd|-|/)?|mar([.]|ch)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: build_rule(
                        amr, words,
                        search_triple=('', ':month', '4'),
                        regex=re.compile('^(0?4(th|-|/)?|apr([.]|il)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : build_rule(
                        amr, words,
                        search_triple = ('',':month','5'),
                        regex = re.compile('^(0?5(th|-|/)?|may)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : build_rule(
                        amr, words,
                        search_triple = ('',':month','6'),
                        regex = re.compile('^(0?6(th|-|/)?|jun([.]|e)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : build_rule(
                        amr, words,
                        search_triple = ('',':month','7'),
                        regex = re.compile('^(0?7(th|-|/)?|jul([.]|y)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : build_rule(
                        amr, words,
                        search_triple = ('',':month','8'),
                        regex = re.compile('^(0?8(th|-|/)?|aug([.]|ust)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: build_rule(
                        amr, words,
                        search_triple=('', ':month', '9'),
                        regex=re.compile('^(0?9(th|-|/)?|sep([.]|tember)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: build_rule(
                        amr, words,
                        search_triple=('', ':month', '10'),
                        regex=re.compile('^(10(th|-|/)?|oct([.]|ober)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: build_rule(
                        amr, words,
                        search_triple=('', ':month', '11'),
                        regex=re.compile('^(11(th|-|/)?|nov([.]|ember)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: build_rule(
                        amr, words,
                        search_triple=('', ':month', '12'),
                        regex=re.compile('^(12(th|-|/)?|dec([.]|ember)?)$', flags=re.IGNORECASE),
                        include_source=False),
    # prep-*
    lambda amr, words: special_rule_prep(amr, words),

    # never
    lambda amr, words: special_rule_never(amr, words),
]

def special_rule_prep(amr, words):
    search_rel = ':prep-'
    for e, i in zip(amr.edges(), amr.edge_ids()):
        if e.startswith(search_rel):
            prep = e.replace(search_rel, '')
            for w in words:
                if w.lower() == prep:
                    return [i], w
                if prep=='toward' and w.lower()=='towards':
                    return [i], w


Never_RE = re.compile('^never$', re.IGNORECASE)
def special_rule_never(amr, words):
    word = None
    for w in words:
        if Never_RE.match(w):
            word = w
            break
    if not word: return
    search_triple1 = ('', ':polarity','-')
    search_triple2 = ('', ':time', 'ever')
    amr_elems = []
    for tr, id in zip(amr.edge_triples(), amr.edge_ids()):
        source, rel, target = tr
        target_name = amr.get_name(target).split('/')[-1]
        if rel == search_triple1[1] and target_name==search_triple1[2]:
            source_id = source
            for tr2, id2 in zip(amr.edge_triples(), amr.edge_ids()):
                source2, rel2, target2 = tr2
                target2_name = amr.get_name(target2).split('/')[-1]
                if source2 == source_id and rel2 == search_triple2[1] and target2_name == search_triple2[2]:
                    amr_elems.append(id)
                    amr_elems.append(target)
                    amr_elems.append(id2)
                    amr_elems.append(target2)
                    break
    if word and amr_elems:
        return amr_elems, word
    return


def build_addon(amr, frame_id, search_triple, include_source= True, include_rel=True):
    amr_elems = []
    for tr, rel_id in zip(amr.edge_triples(), amr.edge_ids()):
        source, rel, target = tr
        source_name = amr.get_name(source).split('/')[-1]
        if target != frame_id:
            continue
        if search_triple[0] and source_name != search_triple[0]:
            continue
        if search_triple[1] and rel != search_triple[1]:
            continue
        target_name = amr.get_name(target).split('/')[-1]
        if search_triple[2] and target_name == search_triple[2]:
            continue
        if include_source:
            amr_elems.append(source)
        if include_rel:
            amr_elems.append(rel_id)
        return amr_elems
    return


AMR_Triple_AddOns = [
    # person sub-graphs
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('thing', '', '')
    ),
    # thing sub-graphs
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('person', '', '')
    ),
   # :mod
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('', ':mod', ''),
        include_source=False
    ),
    # :quant
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('', ':quant', ''),
        include_source=False
    ),
    # :degree
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('', ':degree', ''),
        include_source=False
    ),
    # :extent
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('', ':extent', ''),
        include_source=False
    ),
    # :manner
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('', ':manner', ''),
        include_source=False
    ),
   # (have-rel-role-91 :ARG0 John :ARG1 Mary :ARG2 *husband*)
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('have-rel-role-91', ':ARG2', ''),
    ),
   # date-entity :day :month :year
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('date-entity', ':day', ''),
    ),
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('date-entity', ':month', ''),
    ),
    lambda amr, frame_id: build_addon(
        amr, frame_id,
        search_triple=('date-entity', ':year', ''),
    ),

    # *-quantity :unit
    lambda amr, frame_id: special_rule_quantity(amr, frame_id),

    # (person :arg0 (have-org-role-91 :arg2 *president*) )
    lambda amr, frame_id: special_rule_have_org_role(amr, frame_id),

    # (government-organization :ARG0-of (govern-01 :ARG1 (*country* :name China)))
    lambda amr, frame_id: special_rule_government_organization(amr, frame_id),

]

def special_rule_quantity(amr, frame_id):
    search_source = '-quantity'
    search_rel = ':unit'
    amr_elems = []
    for x, id in zip(amr.edge_triples(), amr.edge_ids()):
        source, rel, target = x
        source_name = amr.get_name(source)
        if source_name.endswith(search_source) and rel == search_rel:
            if target == frame_id:
                amr_elems.append(source)
                amr_elems.append(id)
                return amr_elems
    return None


def special_rule_have_org_role(amr, frame_id):
    search_triple1 = ('have-org-role-91', ':ARG2', '')
    search_triple2 = ('person', ':ARG0-of', 'have-org-role-91')
    amr_elems = []
    for tr, id in zip(amr.edge_triples(), amr.edge_ids()):
        source, rel, target = tr
        if target!=frame_id:
            continue
        source_name = amr.get_name(source).split('/')[-1]
        if source_name in ['have-org-role-91','have-rel-role-91'] and rel == search_triple1[1]:
            source_id = source
            for tr2, id2 in zip(amr.edge_triples(), amr.edge_ids()):
                source2, rel2, target2 = tr2
                if target2 != source_id:
                    continue
                source2_name = amr.get_name(source2).split('/')[-1]
                if source2_name == search_triple2[0] and rel2 == search_triple2[1]:
                    amr_elems.append(source2)
                    amr_elems.append(id2)
                    amr_elems.append(source)
                    amr_elems.append(id)
                    return amr_elems
    return

def special_rule_government_organization(amr, frame_id):
    search_triple1 = ('govern-01', ':ARG1', '')
    search_triple2 = ('government-organization', ':ARG0-of', 'govern-01')
    amr_elems = []
    for tr, id in zip(amr.edge_triples(), amr.edge_ids()):
        source, rel, target = tr
        if target!=frame_id:
            continue
        source_name = amr.get_name(source).split('/')[-1]
        if source_name == search_triple1[0] and rel == search_triple1[1]:
            source_id = source
            for tr2, id2 in zip(amr.edge_triples(), amr.edge_ids()):
                source2, rel2, target2 = tr2
                if target2 != source_id:
                    continue
                source2_name = amr.get_name(source2).split('/')[-1]
                if source2_name == search_triple2[0] and rel2 == search_triple2[1]:
                    amr_elems.append(source2)
                    amr_elems.append(id2)
                    amr_elems.append(source)
                    amr_elems.append(id)
                    return amr_elems
    return