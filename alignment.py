import re, sys
from amr import AMR
import nltk
from nltk.stem import WordNetLemmatizer
from collections import Counter

# nltk.download('wordnet')
lemma = WordNetLemmatizer()

Align_Edge_Re = {
    ':location': re.compile('^(in|at|on)$',flags=re.IGNORECASE),
    ':time': re.compile('^(in|at|when|during)$',flags=re.IGNORECASE),
    ':domain': re.compile('^(be|is|are|was|were|am)$',flags=re.IGNORECASE),
    ':poss': re.compile('^(\'s|of)$',flags=re.IGNORECASE),
    ':condition': re.compile('^if$',flags=re.IGNORECASE),
    ':purpose': re.compile('^for$',flags=re.IGNORECASE),
    ':beneficiary': re.compile('^(for|against)$',flags=re.IGNORECASE),
}

Align_Node_RE = {
    'amr-unknown': re.compile('^(wh\w+|how)$',flags=re.IGNORECASE),
    # modals and conjunctions
    'cause-01': re.compile('^(caus(e|ed|es|ing)|because|thus|so|hence)$',flags=re.IGNORECASE),
    'contrast-01': re.compile('^(but|yet|while|however)$',flags=re.IGNORECASE),
    # 'ever': re.compile('^(ever|never)$',flags=re.IGNORECASE),
    'obligate-01': re.compile('^(need(s|ed|ing)?|must)$',flags=re.IGNORECASE),
    'possible-01': re.compile('^(can|could|might|maybe|possibl[ey]|perhaps)$',flags=re.IGNORECASE),
    'possible': re.compile('^(can|could|might|maybe|possibl[ey]|perhaps)$',flags=re.IGNORECASE),
    'recommend-01': re.compile('^(should)$',flags=re.IGNORECASE),
    'expect-01': re.compile('^(should)$',flags=re.IGNORECASE),
    'a/allow-01': re.compile('^(let)$',flags=re.IGNORECASE),
    'kilometer': re.compile('^(kilometers?|kms?)$',flags=re.IGNORECASE),

}

class Alignment:

    def __init__(self):
        self.amr_ids = []
        self.word_ids = []
        self.amr_elems = []
        self.words = []

    def readible(self):
        return ' '.join(self.amr_elems)+' ~ '+' '.join(self.words)

    def __str__(self):
        return ' '.join(self.amr_ids) + ' ~ ' + ' '.join(self.word_ids)

    def __bool__(self):
        return bool(self.amr_ids or self.word_ids)

    def __lt__(self, other):
        if not other.word_ids:
            return True
        if not self.word_ids:
            return False
        return self.word_ids[0]<other.word_ids[0]

    def add_amr(self, amr_id, amr_elem):
        self.amr_ids.append(amr_id)
        self.amr_elems.append(amr_elem)

    def add_word(self, word_id, word):
        self.word_ids.append(word_id)
        self.words.append(word)

    def remove_from_list(self, amr_list:list, word_list:list):
        for a in self.amr_elems:
            if a in amr_list:
                j = amr_list.index(a)
                amr_list.pop(j)
        for w in self.word_ids:
            if w in word_list:
                j = word_list.index(w)
                word_list.pop(j)
        return amr_list, word_list


def align_amr(amr, words):
    alignments = []
    amr_unaligned = [e for e in amr.elements() if not re.match('^[a-z][0-9]*$', e)]
    words_unaligned = [j for j,w in enumerate(words)]
    for j, w in enumerate(words):
        if w.lower() in ['the', 'a', 'an', '.', '?', '!', ',', '-', '"', ';', ':']:
            a = Alignment()
            a.add_word(j, w)
            alignments.append(a)
            words_unaligned.remove(j)
    for ne in amr.named_entities():
        a = named_entity_align(ne, amr, words, words_unaligned)
        if not a: continue
        amr_unaligned, words_unaligned = a.remove_from_list(amr_unaligned, words_unaligned)
        alignments.append(a)
    for frame in amr.nodes():
        if frame not in amr_unaligned: continue
        id, f = frame.split('/')
        a = frame_align(f, id, amr, words, words_unaligned)
        if not a: continue
        amr_unaligned, words_unaligned = a.remove_from_list(amr_unaligned, words_unaligned)
        alignments.append(a)
    for edge, id in zip(amr.edges(),amr.edge_ids()):
        a = edge_align(edge, id, amr, words, words_unaligned)
        if not a: continue
        amr_unaligned, words_unaligned = a.remove_from_list(amr_unaligned, words_unaligned)
        alignments.append(a)
    return sorted(alignments, key = lambda a: a.word_ids[0] if a.word_ids else 1000), amr_unaligned, [words[j] for j in words_unaligned]


def named_entity_align(named_entity, amr, words, word_indices):
    alignment = Alignment()
    for e, i in zip(named_entity.elements(), named_entity.element_ids()):
        alignment.add_amr(i, e)

    name = []
    for n,i in zip(named_entity.nodes(), named_entity.node_ids()):
        if any(re.search(f'op[0-9]+_{i}$',e) for e in named_entity.edge_ids()):
            n = n.split('/')[-1].strip()
            n = n.replace('"','')
            name.append(n)
    if len(name) == 1:
        name = name[0]
        word_index = Match.exact_or_fuzzy(name,words, word_indices)
        if word_index:
            alignment.add_word(word_index, words[word_index])
            return alignment
    name = ''.join(name)
    possible_spans = [[]]
    name_left = name
    for i in word_indices:
        w = words[i].rstrip('-')
        if w[0:3] in name_left:
            possible_spans[-1].append(i)
            if w in name_left:
                name_left = name_left.replace(w,'',1)
            else:
                prefix = [j for j, ch in enumerate(w) if w[:j] in name_left]
                prefix = w[:prefix[-1]]
                name_left = name_left.replace(prefix, '', 1)
        else:
            possible_spans.append([])
            name_left = name
    match = max(possible_spans, key=lambda x: len(x))
    for w in match:
        alignment.add_word(w, words[w])
    for tr, id in zip(amr.edge_triples(),amr.edge_ids()):
        source, rel, target = tr
        source_frame = amr.get_name(source).split('/')[-1]
        target_frame = amr.get_name(target).split('/')[-1]
        # (government-organization :ARG0-of (govern-01 :ARG1 (*country* :name China)))
        if target == named_entity.root().split('/')[0] and rel==':ARG1' and source_frame=='govern-01':
            alignment.amr_ids.insert(0, id)
            alignment.amr_elems.insert(0, rel)
            alignment.amr_ids.insert(0, source)
            alignment.amr_elems.insert(0, amr.get_name(source))
            for tr2, id2 in zip(amr.edge_triples(), amr.edge_ids()):
                source2, rel2, target2 = tr2
                source_frame2 = amr.get_name(source2).split('/')[-1]
                if target2 == source and rel2 == ':ARG0-of' and source_frame2 == 'government-organization':
                    alignment.amr_ids.insert(0, id2)
                    alignment.amr_elems.insert(0, rel2)
                    alignment.amr_ids.insert(0, source2)
                    alignment.amr_elems.insert(0, amr.get_name(source2))
                    break
        # (person :mod (*country* :name China) )
        if target == named_entity.root().split('/')[0] and rel==':mod' and source_frame=='person':
            alignment.amr_ids.insert(0, id)
            alignment.amr_elems.insert(0, rel)
            alignment.amr_ids.insert(0, source)
            alignment.amr_elems.insert(0, amr.get_name(source))

    return alignment


def frame_align(frame, frame_id, amr, words, word_indices):
    alignment = Alignment()
    alignment.add_amr(frame_id,frame_id+'/'+frame)
    word_index = -1
    # check rules
    if frame in Align_Node_RE:
        regex = Align_Node_RE[frame]
        ws = [j for j in word_indices if regex.match(words[j])]
        if len(ws) > 0:
            word_index = ws[0]
            alignment.add_word(word_index, words[word_index])
    # look for matches
    frame = re.sub('-[0-9]+$', '', frame)
    if word_index < 0:
        word_index = Match.any(frame, words, word_indices)
        if word_index < 0:
            return None
        alignment.add_word(word_index, words[word_index])
    for tr, id in zip(amr.edge_triples(), amr.edge_ids()):
        source, rel, target = tr
        if source==frame_id and re.match('^:ARG[0-9]+$',rel):
            alignment.add_amr(id, rel)
        elif source==frame_id and re.match('^:op[0-9]+$',rel):
            alignment.add_amr(id, rel)
        elif target==frame_id and re.match('^:ARG[0-9]+-of$',rel):
            alignment.amr_ids.insert(0, id)
            alignment.amr_elems.insert(0, rel)
        elif target==frame_id and rel in [':mod', ':quant']:
            alignment.amr_ids.insert(0, id)
            alignment.amr_elems.insert(0, rel)
        # polarity
        elif source==frame_id and rel == ':polarity' and amr.get_name(target).endswith('-'):
            if re.match('^(non[\w-]+|un[\w-]+|il[\w-]+)$', frame, flags=re.IGNORECASE):
                alignment.add_amr(id, rel)
                alignment.add_amr(target, amr.get_name(target))
        # *-quantity
        elif target == frame_id and amr.get_name(source).endswith('-quantity') and rel == ':unit':
            alignment.amr_ids.insert(0, id)
            alignment.amr_elems.insert(0, rel)
            alignment.amr_ids.insert(0, source)
            alignment.amr_elems.insert(0, amr.get_name(source))

    return alignment


def edge_align(edge, edge_id, amr, words, word_indices):
    alignment = Alignment()
    alignment.add_amr(edge_id, edge)
    source = amr.get_name(edge_id.split('_')[0])
    target = amr.get_name(edge_id.split('_')[-1])
    if edge in Align_Edge_Re:
        regex = Align_Edge_Re[edge]
        ws = [j for j in word_indices if regex.match(words[j])]
        if len(ws) > 0:
            word_index = ws[0]
            alignment.add_word(word_index, words[word_index])
            return alignment
        else:
            return None
    if edge == ':polarity' and target.split('/')[-1] == '-':
        Pol_RE = re.compile('^(no|not|never)$')
        word_index = -1
        ws = [j for j in word_indices if Pol_RE.match(words[j])]
        if len(ws) > 0:
            word_index = ws[0]
            alignment.add_word(word_index, words[word_index])
        else:
            return None
        alignment.add_word(word_index, words[word_index])
        alignment.add_amr(edge_id.split('_')[-1], target)
    # prep-*
    if edge.startswith(':prep-'):
        prep = edge.replace(':prep-','',1)
        word_index = Match.exact(prep, words, word_indices)
        if word_index < 0:
            return None
        alignment.add_word(word_index, words[word_index])
        return alignment


def modify_align(align, amr, amr_unaligned, words, word_indices):
    for tr, id in zip(amr.edge_triples(),amr.edge_ids()):
        source, rel, target = tr
        source_frame = amr.get_name(source).split('/')[-1]
        target_frame = amr.get_name(target).split('/')[-1]
        # (person :arg0 (have-org-role-91 :arg2 *president*) )
        # (have-rel-role-91 :ARG0 John :ARG1 Mary :ARG2 *husband*)


class Match:

    @staticmethod
    def any(elem, words, word_indices):
        if not word_indices: return -1
        word_index = Match.exact(elem, words, word_indices)
        if word_index < 0:
            word_index = Match.lemma(elem, words, word_indices)
        if word_index < 0:
            word_index = Match.fuzzy(elem, words, word_indices)
        return word_index

    @staticmethod
    def exact_or_fuzzy(elem, words, word_indices):
        if not word_indices : return -1
        word_index = Match.exact(elem, words, word_indices)
        if word_index < 0:
            word_index = Match.fuzzy(elem, words, word_indices)
        return word_index

    @staticmethod
    def exact(elem, words, word_indices):
        if not word_indices : return -1
        for j in word_indices:
            if words[j].lower() == elem.lower():
                return j
        return -1

    @staticmethod
    def lemma(elem, words, word_indices):
        if not word_indices : return -1
        for j in word_indices:
            w = words[j]
            if not w[0].lower() == elem[0].lower():
                continue
            lemmas = [lemma.lemmatize(w, 'v'), lemma.lemmatize(w, 'n'), lemma.lemmatize(w, 'a')]
            lemmas = [l.lower() for l in lemmas]
            if elem.lower() in lemmas:
                return j
        return -1

    @staticmethod
    def fuzzy(elem, words, word_indices):
        if not word_indices: return -1

        matches = {j: Match._largest_prefix(words[j].lower(), elem.lower()) for j in word_indices}
        ws = [j for j in word_indices if matches[j] >= 4]
        if not ws:
            return -1
        w = max(ws, key=lambda x: matches[x])
        if w >= 0:
            return w
        return -1

    @staticmethod
    def _largest_prefix(a, b):
        prefix = 0
        for c, d in zip(a, b):
            if c == d:
                prefix += 1
            else:
                break
        return prefix


def main():
    amr_file = r'test-data/amrs.txt'
    sentence_file = r'test-data/sentences.txt'
    if len(sys.argv)>2:
        amr_file = sys.argv[1]
        sentence_file = sys.argv[2]

    failed_amrs = Counter()
    failed_words = Counter()
    with open(sentence_file, 'r', encoding='utf8') as f1:
        sentences = [s for s in re.split('\n\s*\n',f1.read()) if s]
        with open(amr_file, 'r', encoding='utf8') as f2:
            for i,amr in enumerate(AMR.amr_iter(f2.read())):
                # print(i)
                words = sentences[i].strip().split()
                amr = AMR(amr)
                alignments, amr_unal, words_unal = align_amr(amr, words)
                a = '\n'.join(a.readible() for a in alignments)
                # for source, rel, target in amr.edge_triples():
                #     if amr.get_name(source).endswith('expect-01'):
                #         print(amr.get_name(source), rel, amr.get_name(target), ':', ' '.join(words))
                # print(amr)
                print(words)
                print(a)
                print('unaligned', amr_unal)
                print('unaligned', words_unal)
                print()
                # for a in amr_unal:
                #     failed_amrs[a]+=1
    #             for w in words_unal:
    #                 failed_words[w]+=1
    # for a in failed_amrs.most_common():
    #     print(a)
    # for w in failed_words.most_common():
    #     print(w)
if __name__ == "__main__":
    main()