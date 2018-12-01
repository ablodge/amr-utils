import re
from amr import AMR

Align_Edge_Re = {
    ':location': re.compile('^(in|at|on)$', flags=re.IGNORECASE),
    ':time': re.compile('^(in|at|when|during)$', flags=re.IGNORECASE),
    ':domain': re.compile('^(be|is|are|was|were|am)$', flags=re.IGNORECASE),
    ':poss': re.compile('^(\'s|of)$', flags=re.IGNORECASE),
    ':condition': re.compile('^if$', flags=re.IGNORECASE),
    ':purpose': re.compile('^for$', flags=re.IGNORECASE),
    ':beneficiary': re.compile('^(for|against)$', flags=re.IGNORECASE),
}

Align_Node_RE = {
    'amr-unknown': re.compile('^(wh\w+|how)$', flags=re.IGNORECASE),
    # modals and conjunctions
    'cause-01': re.compile('^(caus(e|ed|es|ing)|because|thus|so|hence)$', flags=re.IGNORECASE),
    'contrast-01': re.compile('^(but|yet|while|however)$', flags=re.IGNORECASE),
    'obligate-01': re.compile('^(need(s|ed|ing)?|must)$', flags=re.IGNORECASE),
    'possible-01': re.compile('^(can|could|might|maybe|possibl[ey]|perhaps)$', flags=re.IGNORECASE),
    'possible': re.compile('^(can|could|might|maybe|possibl[ey]|perhaps)$', flags=re.IGNORECASE),
    'recommend-01': re.compile('^(recommend(s|ed|ing)?|should)$', flags=re.IGNORECASE),
    'expect-01': re.compile('^(expect(s|ed|ing)?|should)$', flags=re.IGNORECASE),
    'a/allow-01': re.compile('^(allow(s|ed|ing)?|let)$', flags=re.IGNORECASE),
    # abbreviations
    'kilometer': re.compile('^(kilometers?|kms?)$', flags=re.IGNORECASE),
    # numbers
    '0': re.compile('^(0|zero)$', flags=re.IGNORECASE),
    '1': re.compile('^(1|one)$', flags=re.IGNORECASE),
    '2': re.compile('^(2|two)$', flags=re.IGNORECASE),
    '3': re.compile('^(3|three)$', flags=re.IGNORECASE),
    '4': re.compile('^(4|four)$', flags=re.IGNORECASE),
    '5': re.compile('^(5|five)$', flags=re.IGNORECASE),
    '6': re.compile('^(6|six)$', flags=re.IGNORECASE),
    '7': re.compile('^(7|seven)$', flags=re.IGNORECASE),
    '8': re.compile('^(8|eight)$', flags=re.IGNORECASE),
    '9': re.compile('^(9|nine)$', flags=re.IGNORECASE),
    '10': re.compile('^(10|ten)$', flags=re.IGNORECASE),
    '100': re.compile('^(100|hundred)$', flags=re.IGNORECASE),
    '1000': re.compile('^(1,?000|thousand)$', flags=re.IGNORECASE),
    '1000000': re.compile('^(1,?000,?000|million)$', flags=re.IGNORECASE),
    '1000000000': re.compile('^(1,?000,?000,?000|billion)$', flags=re.IGNORECASE),
}

Align_Triple_Rules = [
    # polarity
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('', ':polarity', '-'),
                        regex = re.compile('^(un[\w-]+|non[\w-]+|il[\w-]+)$', flags=re.IGNORECASE)),
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('', ':polarity', '-'),
                        regex = re.compile('^(not|no|never)$', flags=re.IGNORECASE),
                        include_source=False),
    # never
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('', ':time', 'ever'),
                        regex = re.compile('^(ever|never)$', flags=re.IGNORECASE),
                        include_source=False),
    # months
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('',':month','1'),
                        regex = re.compile('^(0?1|jan([.]|uary)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('',':month','2'),
                        regex = re.compile('^(0?2|feb([.]|ruary)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('',':month','3'),
                        regex = re.compile('^(0?3|mar([.]|ch)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: match_triple(
                        amr, words,
                        triple=('', ':month', '4'),
                        regex=re.compile('^(0?4|apr([.]|il)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('',':month','5'),
                        regex = re.compile('^(0?5|may)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('',':month','6'),
                        regex = re.compile('^(0?6|jun([.]|e)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('',':month','7'),
                        regex = re.compile('^(0?7|jul([.]|y)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words : match_triple(
                        amr, words,
                        triple = ('',':month','8'),
                        regex = re.compile('^(0?8|aug([.]|ust)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: match_triple(
                        amr, words,
                        triple=('', ':month', '9'),
                        regex=re.compile('^(0?9|sep([.]|tember)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: match_triple(
                        amr, words,
                        triple=('', ':month', '10'),
                        regex=re.compile('^(10|oct([.]|ober)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: match_triple(
                        amr, words,
                        triple=('', ':month', '11'),
                        regex=re.compile('^(11|nov([.]|ember)?)$', flags=re.IGNORECASE),
                        include_source=False),
    lambda amr, words: match_triple(
                        amr, words,
                        triple=('', ':month', '12'),
                        regex=re.compile('^(12|dec([.]|ember)?)$', flags=re.IGNORECASE),
                        include_source=False),
    # prep-*
    lambda amr, words: special_rule_prep(amr, words),
]

def special_rule_prep(amr, words):
    for e, i in zip(amr.edges(), amr.edge_ids()):
        if e.startswith('prep-'):
            prep = e.replace('prep-', '')
            for w in words:
                if w.lower() == prep:
                    return [i], w


AMR_Triple_AddOns = [
    # person of country
    lambda amr, id: match_addon(
        amr, id,
        triple=('person', ':mod', 'country')
    ),
   # :mod
    lambda amr, id: match_addon(
        amr, id,
        triple=('', ':mod', ''),
    ),
   # (person :arg0 (have-org-role-91 :arg2 *president*) )
    lambda amr, id: match_addon(
        amr, id,
        triple=[('have-org-role-91', ':ARG2', ''),
                ('person', ':ARG0', 'have-org-role-91'),]
    ),
   # (have-rel-role-91 :ARG0 John :ARG1 Mary :ARG2 *husband*)
    lambda amr, id: match_addon(
        amr, id,
        triple=('have-rel-role-91', ':ARG2', ''),
    ),
   # date-entity :day :month :year
    lambda amr, id: match_addon(
        amr, id,
        triple=('date-entity', ':day', ''),
    ),
    lambda amr, id: match_addon(
        amr, id,
        triple=('date-entity', ':month', ''),
    ),
    lambda amr, id: match_addon(
        amr, id,
        triple=('date-entity', ':year', ''),
    ),
   # :quant
    lambda amr, id: match_addon(
        amr, id,
        triple=('', ':quant', ''),
    ),
   # (government-organization :ARG0-of (govern-01 :ARG1 (*country* :name China)))
    lambda amr, id: match_addon(
        amr, id,
        triple=[('govern-01', ':ARG1', ''),
                ('government-organization', ':ARG0-of', 'govern-01'), ]
    ),
    # :ARGX, :ARGX-of, :opX
    lambda amr, id: special_arg_rule(amr, id)
]

def special_arg_rule(amr, id):
    amr_elems = []
    for tr, id in zip(amr.edge_triples(), amr.edge_ids()):
        source, rel, target = tr
        if source==frame_id and re.match('^:ARG[0-9]+$',rel):
            amr_elems.append(id)
        elif source==frame_id and re.match('^:op[0-9]+$',rel):
            amr_elems.append(id)
        elif target==frame_id and re.match('^:ARG[0-9]+-of$',rel):
            amr_elems.insert(0, id)
            amr_elems.insert(0, rel)



def match_triple(amr, words, triple, regex, include_source= True, include_rel=True, include_target=True):
    amr_elems = []
    source, rel, target = triple
    for x, id in zip(amr.edge_triples(),amr.edge_ids()):
        s, r, t = x
        if (not source or s.split('/')[-1]==source) and (not rel or r==rel) and (not target or t.split('/')[-1]==target):
            triple = s.split('/')[0], id, t.split('/')[0]
    s, r, t = triple
    if include_source: amr_elems.append(s)
    if include_rel: amr_elems.append(r)
    if include_target: amr_elems.append(t)
    for w in words:
        if regex.match(w):
            return amr_elems, w
    return None


def match_addon(amr, id, triple, attach_to_source=False):
    if isinstance(triple, list):
        amr_elems = []
        x = match_addon(amr, id, triple[0], attach_to_source)
        amr_elems.extend(x)
        for tr in triple[1:]:
            x = match_addon(amr, x[0 if not attach_to_source else -1], tr, attach_to_source)
            if attach_to_source:
                amr_elems.extend(x)
            else:
                amr_elems = x + amr_elems
        return amr_elems

    amr_elems = []
    source, rel, target = triple
    for x, id in zip(amr.edge_triples(), amr.edge_ids()):
        s, r, t = x
        if (not source or s.split('/')[-1] == source) and (not rel or r.split('/')[-1] == rel) and (
                not target or t.split('/')[-1] == target):
            if attach_to_source and s.split('/')[0] == id:
                amr_elems.append(id)
                amr_elems.append(t.split('/')[0])
                return amr_elems
            elif not attach_to_source and t.split('/')[0] == id:
                amr_elems.append(s.split('/')[0])
                amr_elems.append(id)
                return amr_elems
    return None