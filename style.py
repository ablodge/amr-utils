import html
import sys


def default_string(amr):
    '''
        # ::id sentence id
        # ::tok tokens...
        # ::node node_id node alignments
        # ::root root_id root
        # ::edge src label trg src_id trg_id alignments
    '''
    output = ''
    # id
    if amr.id:
        output += f'# ::id {amr.id}\n'
    # tokens
    output += '# ::tok ' + (' '.join(amr.tokens)) + '\n'
    # nodes
    for n in amr.nodes:
        alignment = amr.get_alignment(node_id=n)
        align_string = ''
        if alignment:
            align_string = f'\t{alignment.write_span()}'
        output += f'# ::node\t{n}\t{amr.nodes[n] if n in amr.nodes else "None"}' + align_string + '\n'
    # root
    root = amr.root
    alignment = amr.get_alignment(node_id=root)
    align_string = ''
    if alignment:
        align_string = f'\t{alignment.write_span()}'
    if amr.root:
        output += f'# ::root\t{root}\t{amr.nodes[root] if root in amr.nodes else "None"}' + align_string + '\n'
    # edges
    for i, e in enumerate(amr.edges):
        s, r, t = e
        r = r.replace(':', '')
        alignment = amr.get_alignment(edge=e)
        align_string = ''
        if alignment:
            align_string = f'\t{alignment.write_span()}'
        output += f'# ::edge\t{amr.nodes[s] if s in amr.nodes else "None"}\t{r}\t{amr.nodes[t] if t in amr.nodes else "None"}\t{s}\t{t}' \
                  + align_string + '\n'
    return output


def graph_string(amr):
    amr_string = f'[[{amr.root}]]'
    new_ids = {}
    for n in amr.nodes:
        new_id = amr.nodes[n][0] if amr.nodes[n] else 'x'
        if new_id.isalpha() and new_id.islower():
            if new_id in new_ids.values():
                j = 2
                while f'{new_id}{j}' in new_ids.values():
                    j += 1
                new_id = f'{new_id}{j}'
        else:
            j = 0
            while f'x{j}' in new_ids.values():
                j += 1
            new_id = f'x{j}'
        new_ids[n] = new_id
    depth = 1
    nodes = {amr.root}
    completed = set()
    while '[[' in amr_string:
        tab = '\t' * depth
        for n in nodes.copy():
            id = new_ids[n] if n in new_ids else 'x91'
            concept = amr.nodes[n] if n in new_ids and amr.nodes[n] else 'None'
            edges = sorted([e for e in amr.edges if e[0] == n], key=lambda x: x[1])
            targets = set(t for s, r, t in edges)
            edges = [f'{r} [[{t}]]' for s, r, t in edges]
            children = f'\n{tab}'.join(edges)
            if children:
                children = f'\n{tab}' + children
            if n not in completed:
                if (concept[0].isalpha() and concept not in ['imperative', 'expressive', 'interrogative']) or targets:
                    amr_string = amr_string.replace(f'[[{n}]]', f'({id}/{concept}{children})', 1)
                else:
                    amr_string = amr_string.replace(f'[[{n}]]', f'{concept}')
                completed.add(n)
            amr_string = amr_string.replace(f'[[{n}]]', f'{id}')
            nodes.remove(n)
            nodes.update(targets)
        depth += 1
    if len(completed) < len(amr.nodes):
        missing_nodes = [n for n in amr.nodes if n not in completed]
        missing_nodes= ', '.join(f'{n}/{amr.nodes[n]}' for n in missing_nodes)
        missing_edges= [(s,r,t) for s,r,t in amr.edges if s in missing_nodes or t in missing_nodes]
        missing_edges = ', '.join(f'{s}/{amr.nodes[s]} {r} {t}/{amr.nodes[t]}' for s,r,t in missing_edges)
        print('[amr]', 'Failed to print AMR, '
              + str(len(completed)) + ' of ' + str(len(amr.nodes)) + ' nodes printed:\n '
              + str(amr.id) +':\n'
              + amr_string + ':\n'
              + 'Missing nodes: ' + missing_nodes
              + 'Missing edges: ' + missing_edges,
              file=sys.stderr)
    if not amr_string.startswith('('):
        amr_string = '(' + amr_string + ')'
    if len(amr.nodes) == 0:
        amr_string = '(a/amr-empty)'

    return amr_string + '\n\n'


def jamr_string(amr):
    return default_string(amr) + graph_string(amr)


class Latex_AMR:
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

    @staticmethod
    def prefix():
        return '\\usepackage{tikz}\n\\usetikzlibrary{shapes}\n\n'


    @staticmethod
    def latex(amr, assign_color='blue'):

        colors = set()
        node_depth = {amr.root:0}
        nodes = [amr.root]
        done = {amr.root}
        depth = 1
        while True:
            new_nodes = set()
            for s,r,t in amr.edges:
                if s in done and t not in nodes:
                    node_depth[t] = depth
                    new_nodes.add(t)
                    nodes.append(t)
            if not new_nodes:
                break
            depth += 1
            done.update(new_nodes)
        if len(nodes) < len(amr.nodes):
            print('[amr]', 'Failed to print AMR, '
                  + str(len(nodes)) + ' of ' + str(len(amr.nodes)) + ' nodes printed:\n '
                  + ' '.join(amr.tokens) + '\n' + str(amr), file=sys.stderr)

        max_depth = depth
        elems = ['\t% Nodes']
        for n in nodes:
            depth = node_depth[n]
            row = [n for n in nodes if node_depth[n]==depth]
            pos = row.index(n)
            x = Latex_AMR.get_x_(pos, len(row))
            y = Latex_AMR.get_y_(depth, max_depth)
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
        for s,r,t in amr.edges:
            if node_depth[s] > node_depth[t]:
                dir1 = 'north'
                dir2 = 'south'
            elif node_depth[s] < node_depth[t]:
                dir1 = 'south'
                dir2 = 'north'
            elif node_depth[s] == node_depth[t] and nodes.index(s)<nodes.index(t):
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

    @staticmethod
    def get_x_(i, num_nodes):
        return (i+1)*20.0/(num_nodes+1)

    @staticmethod
    def get_y_(depth, max_depth):
        return 2.5*(max_depth - depth)

    @staticmethod
    def style(amrs, assign_color='blue'):
        output = Latex_AMR.prefix()
        for amr in amrs:
            output += Latex_AMR.latex(amr, assign_color)
        return output


class HTML_AMR:
    '''
    <div class="amr-container">
    <pre>
    (<span class="amr-node" tok-id="c" title="{description}>c / chase-01</span> <span class="amr-edge" tok-id="0">:ARG0</span> (<span class="amr-node" tok-id="d">d / dog</span>)
        <span class="amr-edge" tok-id="1">:ARG1</span> (<span class="amr-node" tok-id="c2">c2 / cat</span>))
    </pre>
    </div>
    '''
    @staticmethod
    def get_description_(frame, propbank_frames_dictionary):
        if frame in propbank_frames_dictionary:
            return propbank_frames_dictionary[frame].replace('\t', '\n')
        return ''

    @staticmethod
    def span(text, type, id, desc=''):
        desc = html.escape(desc)
        return f'<span class="{type}" tok-id="{id}"' + (f' title="{desc}"' if desc else '') +f'>{text}</span>'

    @staticmethod
    def style_sheet():
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
            
            .amr-edge {
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
            }
'''

    @staticmethod
    def html(amr, assign_node_color=None, assign_node_desc=None, assign_edge_color=None, assign_edge_desc=None,
             assign_token_color=None, assign_token_desc=None):
        from propbank_frames import propbank_frames_dictionary
        amr_string = f'[[{amr.root}]]'
        new_ids = {}
        for n in amr.nodes:
            new_id = amr.nodes[n][0] if amr.nodes[n] else 'x'
            if new_id.isalpha() and new_id.islower():
                if new_id in new_ids.values():
                    j = 2
                    while f'{new_id}{j}' in new_ids.values():
                        j += 1
                    new_id = f'{new_id}{j}'
            else:
                j = 0
                while f'x{j}' in new_ids.values():
                    j += 1
                new_id = f'x{j}'
            new_ids[n] = new_id
        depth = 1
        nodes = {amr.root}
        completed = set()
        while '[[' in amr_string:
            tab = '    ' * depth
            for n in nodes.copy():
                id = new_ids[n] if n in new_ids else 'x91'
                concept = amr.nodes[n] if n in new_ids and amr.nodes[n] else 'None'
                edges = sorted([e for e in amr.edges if e[0] == n], key=lambda x: x[1])
                targets = set(t for s, r, t in edges)
                edge_spans = []
                for s, r, t in edges:
                    if assign_edge_color:
                        color = assign_edge_color(amr, (s,r,t))
                    else:
                        color = False
                    type = 'amr-edge' + (f' {color}' if color else '')
                    desc = assign_edge_desc(amr, (s,r,t)) if assign_edge_desc else ''
                    edge_spans.append(f'{HTML_AMR.span(r, type, f"{s}-{t}", desc)} [[{t}]]')
                children = f'\n{tab}'.join(edge_spans)
                if children:
                    children = f'\n{tab}' + children
                if assign_node_color:
                    color = assign_node_color(amr, n)
                else:
                    color = False

                if n not in completed:
                    if (concept[0].isalpha() and concept not in ['imperative', 'expressive',
                                                                 'interrogative']) or targets or depth==1:
                        desc = HTML_AMR.get_description_(concept, propbank_frames_dictionary)
                        type = 'amr-frame' if desc else "amr-node"
                        if assign_node_desc:
                            desc = assign_node_desc(amr, n)
                        if color:
                            type += f' {color}'
                        span = HTML_AMR.span(f'{id}/{concept}', type, id, desc)
                        amr_string = amr_string.replace(f'[[{n}]]', f'({span}{children})', 1)
                    else:
                        type = 'amr-node' + (f' {color}' if color else '')
                        desc = assign_node_desc(amr, n) if assign_node_desc else ''
                        span = HTML_AMR.span(f'{concept}', type, id, desc)
                        amr_string = amr_string.replace(f'[[{n}]]', f'{span}')
                    completed.add(n)
                type = 'amr-node' + (f' {color}' if color else '')
                desc = assign_node_desc(amr, n) if assign_node_desc else ''
                span = HTML_AMR.span(f'{id}', type, id, desc)
                amr_string = amr_string.replace(f'[[{n}]]', f'{span}')
                nodes.remove(n)
                nodes.update(targets)
            depth += 1
        if len(completed) < len(amr.nodes):
            print('[amr]', 'Failed to print AMR, '
                  + str(len(completed)) + ' of ' + str(len(amr.nodes)) + ' nodes printed:\n '
                  + ' '.join(amr.tokens) + '\n'
                  + amr_string, file=sys.stderr)
        if not amr_string.startswith('('):
            amr_string = '(' + amr_string + ')'
        if len(amr.nodes) == 0:
            span = HTML_AMR.span('a/amr-empty', "amr-node", 'a')
            amr_string = f'({span})'
        toks = [t for t in amr.tokens]
        if assign_token_color:
            for i,t in enumerate(toks):
                color = assign_token_color(amr,i)
                desc = assign_token_desc(amr, i) if assign_token_desc else ''
                if color or desc:
                    toks[i] = HTML_AMR.span(t, color, f'tok{i}', desc)
        output = f'<div class="amr-container">\n<pre>\n{" ".join(toks)}\n\n{amr_string}</pre>\n</div>\n\n'
        return output

    @staticmethod
    def style(amrs, assign_node_color=None, assign_node_desc=None, assign_edge_color=None, assign_edge_desc=None,
             assign_token_color=None, assign_token_desc=None):
        output = '<!DOCTYPE html>\n'
        output += '<html>\n'
        output += '<style>\n'
        output += HTML_AMR.style_sheet()
        output += '</style>\n\n'
        output += '<body>\n'
        for amr in amrs:
            output += HTML_AMR.html(amr,
                                    assign_node_color, assign_node_desc,
                                    assign_edge_color, assign_edge_desc,
                                    assign_token_color, assign_token_desc)
        output += '</body>\n'
        output += '</html>\n'
        return output
#
# def is_aligned_node(amr, n):
#     align = amr.get_alignment(node_id=n)
#     return '' if align else 'red'
#
# def is_aligned_edge(amr, e):
#     align = amr.get_alignment(edge=e)
#     return 'grey' if align else ''
#
# def is_aligned_token(amr, t):
#     align = amr.get_alignment(token_id=t)
#     return '' if align else 'red'

def main():
    from amr import JAMR_AMR_Reader
    file = sys.argv[-2] if len(sys.argv) > 1 else "data/test.txt"
    outfile = sys.argv[-1]

    cr = JAMR_AMR_Reader()
    amrs = cr.load(file, verbose=False, remove_wiki=True)

    if '--latex' in sys.argv or len(sys.argv)==3:
        output = Latex_AMR.style(amrs)
        with open(outfile, 'w+', encoding='utf8') as f:
            f.write(output)
    elif '--html' in sys.argv:
        output = HTML_AMR.style(amrs)
        with open(outfile, 'w+', encoding='utf8') as f:
            f.write(output)


if __name__=='__main__':
    main()
