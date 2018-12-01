import re, paren_utils, sys


class AMR:
    NODE_RE = re.compile('(?P<id>[a-z][0-9]*|none[0-9]+)( ?/ ?(?P<concept>[^\s()]+))?(?![a-z])')
    EDGE_RE = re.compile('(?P<rel>:[A-Za-z0-9-]+(-of)?)')
    ELEM_RE = re.compile(fr'({NODE_RE.pattern}|{EDGE_RE.pattern}|[()]|[^\s()]+|\s+)')

    def __init__(self, text):
        # remove comments
        self.text = '\n'.join([l for l in text.split('\n') if not l.strip().startswith('#')])
        self.text_elements = []
        i = 0
        for e in self.ELEM_RE.finditer(self.text):
            e = e.group()
            if self.NODE_RE.match(e):
                self.text_elements.append(e.replace(' / ', '/'))
            elif not self.EDGE_RE.match(e) and not re.match('[()]|\s+', e):
                self.text_elements.append(f'x{i}/' + e)
                i += 1
            elif re.match('x[0-9]+( ?/ ?[A-Za-z-]+[0-9]*)', e):
                self.text_elements.append(f'x{i}/' + e.split('/')[1].strip())
                i += 1
            else:
                self.text_elements.append(e)
        self.names = {}
        for e,i in zip(self.elements(),self.element_ids()):
            if not re.match('^[a-z][0-9]*$', e):
                self.names[i] = e

    def root(self):
        return self.NODE_RE.search(self.text).group().replace(' / ', '/')

    def elements(self):
        for e in self.text_elements:
            if e in ['(',')'] or not e.strip():
                continue
            yield e


    def nodes(self):
        for e in self.elements():
            if self.NODE_RE.match(e):
                yield e


    def edges(self):
        for e in self.elements():
            if self.EDGE_RE.match(e):
                yield e

    def node_indices(self):
        for i,e in enumerate(self.elements()):
            if self.NODE_RE.match(e):
                yield i

    def edge_indices(self):
        for i,e in enumerate(self.elements()):
            if self.EDGE_RE.match(e):
                yield i

    def element_ids(self):
        nodes = self.node_ids()
        edges = self.edge_ids()
        for e in self.elements():
            if self.EDGE_RE.match(e):
                yield next(edges, None)
            else:
                yield next(nodes, None)

    def node_ids(self):
        for n in self.nodes():
            yield n.split('/')[0].strip()

    def edge_ids(self):
        for source,rel,target in self.edge_triples():
            rel = rel.replace(':', '')
            yield source+'_'+rel+'_'+target

    def get_name(self, id):
        return self.names[id]

    def edge_triples(self):
        text = str(self)
        idx = [(e.start(), e.group()) for e in self.EDGE_RE.finditer(text)]

        for rel_position, rel in idx:
            Target_RE = re.compile(f'{rel}\s*[(]?\s*{self.NODE_RE.pattern}')
            for t in paren_utils.paren_iter(text):
                pos = rel_position - text.index(t)
                if t.startswith(rel, pos) and paren_utils.depth_at(t, pos) == 0:
                    root = self.NODE_RE.match(t)
                    source = root.group().split('/')[0].strip()
                    x = Target_RE.match(t, pos=pos)
                    if x:
                        target = x.group('id')
                        yield (source, rel, target)
                    else:
                        print('Missing target node! ', rel, re.sub('\s+', ' ', t))
                        yield (source, rel, '?')
                    break

    def named_entities(self):
        NE_RE = re.compile(f'(?P<root>{self.NODE_RE.pattern})\s.*:name\s+<1>(?P<name>.*?)</1>')
        for t in paren_utils.paren_iter(str(self)):
            t = paren_utils.mark_depth(t)
            x = NE_RE.match(t)
            if x:
                root = x.group('root')
                name = x.group('name')
                yield AMR(f'({root} :name ({name}) )')

    def sub_amrs(self):
        for t in paren_utils.paren_iter(self.text):
            yield AMR('('+t+')')


    @staticmethod
    def test(text):
        # ignore comments
        text = '\n'.join([l for l in text.split('\n') if not l.strip().startswith('#')])
        return text.strip().startswith('(') and paren_utils.test_parens(text)

    @staticmethod
    def amr_iter(text):
        Split_RE = re.compile('\n\s*\n')
        for text in Split_RE.split(text):
            text = text.strip()
            if text and AMR.test(text):
                yield text

    def __str__(self):
        return ''.join(e for e in self.text_elements)

def main():
    input_file = r'test-data/amrs.txt'
    if len(sys.argv)>1:
        input_file = sys.argv[1]

    with open(input_file, 'r', encoding='utf8') as f:
        for amr in AMR.amr_iter(f.read()):
            amr = AMR(amr)
            print(amr)
            print()

if __name__ == "__main__":
    main()