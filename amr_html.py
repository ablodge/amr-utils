
from amr import AMR
from features import propbank_frames_dictionary
import re, sys


amr_dictionary_url = 'https://www.isi.edu/~ulf/amr/lib/amr-dict.html'
prop_frames_url = 'https://verbs.colorado.edu/propbank/framesets-english-aliases/'


class AMR_HTML:

    @staticmethod
    def html(text, delete_x_ids=True):
        amr = AMR(text)
        elems = [e for e in amr.text_elements]
        nodes = [id for id in amr.node_ids()]
        edges = [id for id in amr.edge_ids()]
        node_indices = [i for i,e in enumerate(amr.text_elements) if amr.NODE_RE.match(e)]
        edge_indices = [i for i,e in enumerate(amr.text_elements) if amr.EDGE_RE.match(e)]
        Named_Entity_RE = re.compile('x[0-9]+/".*?"')
        for i,e in enumerate(elems):
            if i in node_indices:
                id = nodes.pop(0)
                frame = e.split('/')[-1] if '/' in e else '_'
                node = e
                if delete_x_ids:
                    node = re.sub('^x[0-9]+/', '', e, 1)
                if frame in propbank_frames_dictionary:
                    description = propbank_frames_dictionary[frame].replace('\t','\n')
                    elems[i] = f'<span class="amr-frame" tok-id="{id}" title="{description}">{node}</span>'
                elif Named_Entity_RE.match(e):
                    elems[i] = f'<span class="amr-entity" tok-id="{id}">{node}</span>'
                else:
                    elems[i] = f'<span class="amr-node" tok-id="{id}">{node}</span>'
            elif i in edge_indices:
                id = edges.pop(0)
                elems[i] = f'<span class="amr-edge" tok-id="{id}">{e}</span>'
        text = ''.join(elems)
        return '\n<div class="amr-container">\n<pre>\n'+text+'\n</pre>\n</div>\n'


def main():
    input_file = r'test-data/amrs.txt'
    ids = True if '-x' in sys.argv else False
    if len(sys.argv) > 1:
        input_file = sys.argv[-1]

    with open(input_file, 'r', encoding='utf8') as f:
        for amr in AMR.amr_iter(f.read()):
            amr = AMR_HTML.html(amr, ids)
            print(amr)
            print()

if __name__ == "__main__":
    main()


