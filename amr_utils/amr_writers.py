import html
from typing import Callable, Iterable, Union, Tuple

from amr_utils import amr_iterators
from amr_utils.amr import AMR, AMR_Notation
from amr_utils.utils import class_name


class Metadata_Writer:

    def write(self, amr: AMR):
        raise NotImplemented()


class AMR_Writer:

    def write_metadata(self, amr):
        metadata = []
        metadata.append(f'# ::id {amr.id}')
        metadata.append(f'# ::tok {" ".join(amr.tokens)}')
        for tag in amr.metadata:
            metadata.append(f'# ::{tag} {amr.metadata[tag]}')
        return '\n'.join(metadata)

    def write_amr(self, amr):
        return amr.graph_string(pretty_print=True)

    def write_to_file(self, file, amrs):
        print('Writing AMRs to file:', file)
        with open(file, 'w+') as fw:
            for amr in amrs:
                fw.write(self.write_metadata(amr))
                fw.write('\n')
                fw.write(self.write_amr(amr))
                fw.write('\n\n')

class JAMR_Metadata_Writer(Default_Metadata_Writer):
    '''
    # ::id sentence id
    # ::tok tokens...
    # metadata...
    # ::node node_id node alignments
    # ::root root_id root
    # ::edge src label trg src_id trg_id alignments
    '''

    def write(self, amr: AMR, aligns=None):
        metadata_string = [super().write(amr)]
        for n in amr.nodes:
            metadata_string.append(f'# ::node\t{n}\t{amr.nodes[n]}\n')
        metadata_string.append(f'# ::root\t{amr.root}\t{amr.nodes[amr.root]}\n')
        for s, r, t in amr.edges:
            r = r[1:] if r.startswith(':') else r
            metadata_string.append(f'# ::edge\t{amr.nodes[s]}\t{r}\t{amr.nodes[t]}\t{s}\t{t}\n')
        return ''.join(metadata_string)


class Latex_AMR_Writer(AMR_Writer):
    '''
    \begin{tikzpicture}[
        red/.style={rectangle, draw=red!60, fill=red!5, very thick, minimum size=7mm},
        blue/.style={rectangle, draw=blue!60, fill=blue!5, very thick, minimum size=7mm},
        ]
        %Nodes
        \node[red]   (r) at (5,4) {read-01};
        \node[purple](p) at (3.33,2) {person};
        \node[green] (b) at (6.67,2) {book};
        \node[blue]  (j) at (5,0) {``John''};

        %Edges
        \draw[->] (r.south) -- (p.north) node[midway, above, sloped] {:ARG0};
        \draw[->] (r.south) -- (b.north) node[midway, above, sloped] {:ARG1};
        \draw[->] (p.south) -- (j.north) node[midway, above, sloped] {:name};
    \end{tikzpicture}
    '''

    def print(self, amr, assign_color: Union[str, Callable[[AMR, str], str]] = 'blue'):

        colors = set()

        node_rows = [[amr.root]]
        node_depth = {amr.root: 0}
        node_pos = {amr.root: 0}
        curent_depth = 1
        current_row = []
        for depth, edge in amr_iterators.breadth_first_edges(amr, alphabetical_edges=False):
            s, r, t = edge
            if t not in node_depth:
                node_depth[t] = depth
                node_pos[t] = len(current_row)
            if depth>curent_depth:
                node_rows.append(current_row)
            current_row.append(t)
            curent_depth = depth

        elems = ['\t% Nodes']
        max_depth = len(node_rows)
        for depth,node_row in enumerate(node_rows):
            for pos,n in enumerate(node_row):
                x = self._get_x(pos, len(node_row))
                y = self._get_y(depth, max_depth)
                if callable(assign_color):
                    color = assign_color(amr, n)
                else:
                    color = assign_color
                colors.add(color)
                if not amr.nodes[n][0].isalpha() or amr.nodes[n] in ['imperative', 'expressive', 'interrogative']:
                    concept = amr.nodes[n]
                else:
                    concept = f'{n}/{amr.nodes[n]}'
                elems.append(f'\t\\node[{color}]({n}) at ({x},{y}) {{{concept}}};')
        elems.append('\t% Edges')
        for s, r, t in amr.edges:
            if node_depth[s] > node_depth[t]:
                dir1 = 'north'
                dir2 = 'south'
            elif node_depth[s] < node_depth[t]:
                dir1 = 'south'
                dir2 = 'north'
            elif node_depth[s] == node_depth[t] and node_pos[s] < node_pos[t]:
                dir1 = 'east'
                dir2 = 'west'
            else:
                dir1 = 'west'
                dir2 = 'east'
            elems.append(f'\t\draw[->, thick] ({s}.{dir1}) -- ({t}.{dir2}) node[midway, above, sloped] {{{r}}};')
        latex = '\n\\begin{tikzpicture}[\n'
        for color in colors:
            latex += f'{color}/.style={{rectangle, draw={color}!60, fill={color}!5, very thick, minimum size=7mm}},\n'
        latex += ']\n'
        latex += '\n'.join(elems)
        latex += '\n\end{tikzpicture}\n'

        return latex

    def write_to_file(self, amrs, file, assign_color='blue'):
        with open(file, 'w+') as fw:
            fw.write(self._prefix())
            for amr in amrs:
                fw.write(self.print(amr, assign_color))

    @staticmethod
    def _prefix():
        return '\\usepackage{tikz}\n\\usetikzlibrary{shapes}\n\n'

    def _get_x(self, i, num_nodes):
        return (i + 1) * 20.0 / (num_nodes + 1)

    def _get_y(self, depth, max_depth):
        return 2.5 * (max_depth - depth)


class HTML_AMR_Writer(AMR_Writer):
    '''
    <div class="amr-container">
    <pre>
    (<span class="amr-node" tok-id="c" title="{description}>c / chase-01</span> <span class="amr-edge" tok-id="0">:ARG0</span> (<span class="amr-node" tok-id="d">d / dog</span>)
        <span class="amr-edge" tok-id="1">:ARG1</span> (<span class="amr-node" tok-id="c2">c2 / cat</span>))
    </pre>
    </div>
    '''

    def node_color(self, amr: AMR, node: str):
        return ''

    def node_desc(self, amr: AMR, node: str):
        return ''

    def edge_color(self, amr: AMR, edge: Tuple[str, str, str]):
        return ''

    def edge_desc(self, amr: AMR, edge: Tuple[str, str, str]):
        return ''

    def token_color(self, amr: AMR, token_id: int):
        return ''

    def token_desc(self, amr: AMR, token_id: int):
        return ''

    def print(self, amr: AMR, indent: str = '\t'):
        completed_nodes = set()
        completed_concepts = set()
        node_map = None
        if not all(n[0].isalpha() for n in amr.nodes):
            node_map = amr._default_node_ids()
        # add root node
        node_id = amr.root if node_map is None else node_map[amr.root]
        concept = amr.nodes[amr.root]
        css_class = 'amr-frame' if AMR_Notation.is_frame(concept) else 'amr-node'
        root_span = self.span(f'{node_id} / {concept}', css_class, node_id, desc=self.node_desc(amr, amr.root),
                              color=self.node_color(amr, amr.root))
        amr_string = [f'({root_span}']
        completed_concepts.add(amr.root)
        completed_nodes.add(amr.root)
        prev_depth = 1
        start_parens = 1
        end_parens = 0

        for depth, next_edge in amr._depth_first_edges(alphabetical_edges=False, ignore_reentrancies=False):
            s, r, t = next_edge
            if depth < prev_depth:
                for _ in range(prev_depth - depth):
                    amr_string.append(')')
                    end_parens += 1
            whitespace = '\n' + (indent * depth)
            s_node_id = s if (node_map is None) else node_map[s]
            t_node_id = t if (node_map is None) else node_map[t]
            concept = amr.nodes[t]
            # relation
            r_id = f'{s_node_id}-{r[1:]}-{t_node_id}'
            r_span = self.span(r, css_class='amr-rel', element_id=r_id, desc=self.edge_desc(amr, next_edge),
                               color=self.edge_color(amr, next_edge))
            if AMR_Notation.is_attribute(concept) and not (concept[0].isalpha() and r != ':mode'):
                # attribute
                attr_span = self.span(concept, css_class='amr-attr', element_id=node_id, desc=self.node_desc(amr, t),
                                      color=self.node_color(amr, t))
                amr_string.append(f'{whitespace}{r_span} {attr_span}')
                completed_nodes.add(t)
            elif t not in completed_concepts and amr._is_valid_instance_location(next_edge):
                # new concept
                css_class = 'amr-frame' if AMR_Notation.is_frame(concept) else 'amr-node'
                node_span = self.span(f'{node_id} / {concept}', css_class=css_class, element_id=node_id,
                                      desc=self.node_desc(amr, t), color=self.node_color(amr, t))
                amr_string.extend([f'{whitespace}{r_span} ', f'({node_span}'])
                completed_concepts.add(t)
                start_parens += 1
                depth += 1
            else:
                # reentrancy
                node_span = self.span(node_id, 'amr-node', node_id, desc=self.node_desc(amr, t),
                                      color=self.node_color(amr, t))
                amr_string.append(f'{whitespace}{r_span} {node_span}')
            completed_nodes.add(t)
            if start_parens - end_parens != depth:
                raise Exception(f'[{class_name(self)}] Failed to print AMR, Mismatched Parentheses:',
                                amr.id, ''.join(amr_string))
            prev_depth = depth
        for _ in range(prev_depth):
            amr_string.append(')')
            end_parens += 1
        if start_parens != end_parens:
            raise Exception(f'[{class_name(self)}] Failed to print AMR, Mismatched Parentheses:',
                            amr.id, ''.join(amr_string))
        amr_string = ''.join(amr_string)
        # tokens
        toks = [t for t in amr.tokens]
        for i, tok in enumerate(amr.tokens):
            toks[i] = self.span(tok, f'tok{i}', desc=self.token_desc(amr, i), color=self.token_color(amr, i))
        token_spans = " ".join(toks)
        output = f'<div class="amr-container">\n<pre>\n{token_spans}\n\n{amr_string}</pre>\n</div>\n\n'
        return output

    def write_to_file(self, amrs: Iterable[AMR], file: str, quiet: bool = False):
        with open(file, 'w+') as fw:
            fw.write(self._prefix())
            for amr in amrs:
                fw.write(self.print(amr))
                fw.write(self._separator())
            fw.write(self._suffix())

    @staticmethod
    def span(text: str, css_class, element_id: str, desc: str = None, color: str = None):
        type_and_color = type if not color else f'{css_class} {color}'
        desc = html.escape(desc)
        text = html.escape(text)
        if desc:
            return f'<span class="{type_and_color}" tok-id="{element_id}" title="{desc}">{text}</span>'
        else:
            return f'<span class="{type_and_color}" tok-id="{element_id}">{text}</span>'

    @staticmethod
    def _style_sheet():
        return '''
            div.amr-container {
                font-family: "Cambria Math", sans-serif;
                font-size: 14px;
            }

            .amr-node {
                color : black;
            }
            
            .amr-frame {
                color : purple;
                text-decoration: underline;
            }
            
            .amr-rel {
                color : grey;
            }
            
            .amr-attr {
                color : grey;
            }
            
            .blue {
                background: deepskyblue; 
                color : white;
            }
            
            .red {
                background: crimson; 
                color : white;
            }
            
            .grey {
                background: gainsboro; 
                color : black;
            }
            
            .green {
                background: yellowgreen; 
                color : black;
            }'''

    @staticmethod
    def _prefix():
        output = '<!DOCTYPE html>\n<html>\n<style>\n' + \
                 HTML_AMR_Writer._style_sheet() + \
                 '</style>\n\n<body>\n'
        return output

    @staticmethod
    def _separator():
        return '<hr>\n'

    @staticmethod
    def _suffix():
        return '</body>\n</html>\n'
