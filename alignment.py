import re, sys
from amr import AMR
import nltk
from nltk.stem import WordNetLemmatizer
from collections import Counter
from rules import Align_Edge_RE, Align_Node_RE, Align_Triple_Rules, AMR_Triple_AddOns

print('#amr-utils Rule-based Aligner')
print('#Loading Rules:',len(Align_Node_RE)+len(Align_Edge_RE)+len(Align_Triple_Rules)+len(AMR_Triple_AddOns))
print()

# nltk.download('wordnet')
lemma = WordNetLemmatizer()

class Alignment:

    def __init__(self):
        self.amr_ids = []
        self.word_ids = []
        self.amr_elems = []
        self.words = []

    def readible(self):
        return ' '.join(self.amr_elems)+' ~ '+' '.join(self.words)

    def __str__(self):
        return ' '.join(str(i) for i in self.word_ids) + ' ~ ' + ' '.join(self.amr_ids)

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



class Match:

    @staticmethod
    def exact_lemma_or_fuzzy(elem, words, word_indices):
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



def align_amr(amr, words):
    alignments = []
    amr_unaligned = set(e for e in amr.element_ids())
    words_unaligned = [j for j,w in enumerate(words)]

    # null alignments
    for j, w in enumerate(words):
        if w.lower() in ['the', 'a', 'an', '.', '?', '!', ',', '-', '"', ';', ':']:
            align = Alignment()
            align.add_word(j, w)
            alignments.append(align)
            words_unaligned.remove(j)

    # named entities
    for ne in amr.named_entities():
        align = named_entity_align(ne, amr, words, words_unaligned)
        if align:
            alignments.append(align)
            for a in align.amr_ids:
                if a in amr_unaligned:
                    amr_unaligned.remove(a)
            for j in align.word_ids: words_unaligned.remove(j)

    # edge rules
    for edge, id in zip(amr.edges(), amr.edge_ids()):
        if edge in Align_Edge_RE:
            regex = Align_Edge_RE[edge]
            for j in words_unaligned:
                if regex.match(words[j]):
                    align = Alignment()
                    align.add_word(j, words[j])
                    align.add_amr(id, edge)
                    alignments.append(align)
                    for a in align.amr_ids:
                        if a in amr_unaligned:
                            amr_unaligned.remove(a)
                    for j in align.word_ids: words_unaligned.remove(j)
                    break

    # node rules
    for node, id in zip(amr.nodes(), amr.node_ids()):
        frame = node.split('/')[-1]
        if frame in Align_Node_RE:
            regex = Align_Node_RE[frame]
            for j in words_unaligned:
                if regex.match(words[j]):
                    align = Alignment()
                    align.add_word(j, words[j])
                    align.add_amr(id, node)
                    alignments.append(align)
                    for a in align.amr_ids:
                        if a in amr_unaligned:
                            amr_unaligned.remove(a)
                    for j in align.word_ids: words_unaligned.remove(j)
                    break

    # amr subgraph rules
    for rule in Align_Triple_Rules:
        ws = [w for j,w in enumerate(words) if j in words_unaligned]
        x = rule(amr, ws)
        if not x: continue
        amr_elems, word = x
        align = Alignment()
        align.add_word(words_unaligned[ws.index(word)], word)
        for id in amr_elems:
            align.add_amr(id, amr.get_name(id))
        alignments.append(align)
        for a in align.amr_ids:
            if a in amr_unaligned:
                 amr_unaligned.remove(a)
        for j in align.word_ids: words_unaligned.remove(j)

    # node matching
    for node, id in zip(amr.nodes(), amr.node_ids()):
        if not '/' in node: continue
        frame = re.sub('-[0-9]+$', '', node.split('/')[-1])
        match = Match.exact_lemma_or_fuzzy(frame, words, words_unaligned)
        if match < 0: continue
        align = Alignment()
        align.add_word(match, words[match])
        align.add_amr(id, node)
        alignments.append(align)
        for a in align.amr_ids:
            if a in amr_unaligned:
                amr_unaligned.remove(a)
        for j in align.word_ids: words_unaligned.remove(j)

    # amr subgraph addons
    for align in alignments:
        if not align.amr_ids: continue
        if not any('_' not in i for i in align.amr_ids): continue
        frame_id = [i for i in align.amr_ids if not '_' in i][0]
        for rule in AMR_Triple_AddOns:
            x = rule(amr, frame_id)
            if not x: continue
            amr_elems = x
            for id in reversed(amr_elems):
                align.amr_ids.insert(0, id)
                align.amr_elems.insert(0, amr.get_name(id))
            for a in amr_elems:
                if a in amr_unaligned:
                     amr_unaligned.remove(a)

    # attach :ARGX, :ARGX-of, :opX
    for align in alignments:
        if not align.amr_ids: continue
        if not any('_' not in i for i in align.amr_ids): continue
        frame_id = [i for i in align.amr_ids if not '_' in i][0]
        for tr, id in zip(amr.edge_triples(), amr.edge_ids()):
            source, rel, target = tr
            if source == frame_id and re.match('^:ARG[0-9]+$', rel):
                align.add_amr(id, rel)
            elif source == frame_id and re.match('^:op[0-9]+$', rel):
                align.add_amr(id, rel)
            elif target == frame_id and re.match('^:ARG[0-9]+-of$', rel):
                align.amr_ids.insert(0, id)
                align.amr_ids.insert(0, rel)
        for a in align.amr_ids:
            if a in amr_unaligned:
                amr_unaligned.remove(a)

    alignments = sorted(alignments, key = lambda a: a.word_ids[0] if a.word_ids else 1000)
    amr_unaligned = [amr.get_name(a) for a in amr_unaligned]
    words_unaligned = [words[j] for j in words_unaligned]
    return alignments, amr_unaligned, words_unaligned


def named_entity_align(named_entity, amr, words, word_indices):
    alignment = Alignment()
    for e, i in zip(named_entity.elements(), named_entity.element_ids()):
        alignment.add_amr(i, e)

    name = []
    for n,i in zip(named_entity.nodes(), named_entity.node_ids()):
        x = [x for x in named_entity.edge_ids()]
        if any(re.search(f'op[0-9]+_{i}$',e) for e in named_entity.edge_ids()):
            n = n.split('/')[-1].strip()
            n = n.replace('"','')
            name.append(n)
    if len(name) == 1:
        name = name[0]
        word_index = Match.exact_or_fuzzy(name, words, word_indices)
        if word_index > 0:
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
        elif len(possible_spans[-1])>0:
            possible_spans.append([])
            name_left = name
    match = max(possible_spans, key=lambda x: len(x))
    if not match:
        return None
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


def test_rules(amr, words):
    for source, rel, target in amr.edge_triples():
        if 'h/have-degree' in amr.get_name(target):
            print(amr.get_name(source), rel, amr.get_name(target), ':', ' '.join(words))


def output_failed_alignments(failed_amrs, failed_words):

    for a in failed_amrs.most_common():
        print(a)
    # for w in failed_words.most_common():
    #     print(w)

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
                print('#'+str(i+1))
                words = sentences[i].strip().split()
                amr = AMR(amr)
                # test_rules(amr, words)
                alignments, amr_unal, words_unal = align_amr(amr, words)
                print('# AMR:')
                print('\n'.join('# '+l for l in str(amr).split('\n')))
                print('# Sentence:')
                print('# '+' '.join(words))
                print('# Alignments:')
                for a in alignments:
                    print('#',a.readible())
                for a in alignments:
                    print(a)
                print()

if __name__ == "__main__":
    main()