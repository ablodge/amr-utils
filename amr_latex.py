
from amr import AMR
import re, paren_utils, sys

class AMR_Latex:

    '''
    \begin{tikzpicture}[
    red/.style={rectangle, draw=red!60, fill=red!5, very thick, minimum size=7mm},
    blue/.style={rectangle, draw=blue!60, fill=blue!5, very thick, minimum size=7mm},
    green/.style={rectangle, draw=green!60, fill=green!5, very thick, minimum size=7mm},
    purple/.style={rectangle, draw=purple!60, fill=purple!5, very thick, minimum size=7mm},
    orange/.style={rectangle, draw=orange!60, fill=orange!5, very thick, minimum size=7mm},
    ]
        %Nodes
        \node[red]   (r)       at (5,4) {read-01};
        \node[purple](p)       at (3.33,2) {person};
        \node[green] (b)       at (6.67,2) {book};
        \node[blue]  (j)       at (5,0) {``John''};

        %Edges
        \draw[->] (r.south) -- (p.north) node[midway, above, sloped] {:ARG0};
        \draw[->] (r.south) -- (b.north) node[midway, above, sloped] {:ARG1};
        \draw[->] (p.south) -- (j.north) node[midway, above, sloped] {:name};
    \end{tikzpicture}
    '''

    @staticmethod
    def get_x(i, num_nodes):
        return (i+1)*20.0/(num_nodes+1)

    @staticmethod
    def get_y(depth, max_depth):
        return 2.5*(max_depth - depth)

    @staticmethod
    def get_color(i):
        colors = ['red','orange','blue','green','purple']
        return colors[i%len(colors)]

    @staticmethod
    def latex(text):
        amr = AMR(text)
        text = str(amr)
        for x in re.findall('x[0-9]+ ?/ ?[^()\s]+', text):
            text = text.replace(x, '('+x+')')
        edges = [(e,id) for e,id in zip(amr.edges(),amr.edge_ids())]
        elems = []
        max_depth = paren_utils.max_depth(text)
        prev_depth = 0
        depth = 0

        i = 0
        node_depth = {}
        for t in paren_utils.paren_iter(text):
            node = amr.NODE_RE.match(t).group()
            id = node.split('/')[0].strip()
            # clean node
            if re.match('x[0-9]+/',node):
                node = node.split('/')[1]
            node = node.replace('"','``',1).replace('"',"''",1)
            prev_depth = depth
            depth = paren_utils.depth_at(text, text.index(t))
            if depth > prev_depth:
                i = 0
            node_depth[id] = depth
            num_nodes = paren_utils.mark_depth(text).count(f'<{depth}>')
            x = AMR_Latex.get_x(i, num_nodes)
            y = AMR_Latex.get_y(depth, max_depth)
            color = AMR_Latex.get_color(i)
            elems.append(f'\t\\node[{color}]({id}) at ({x},{y}) {{{node}}};')
            i+=1
        for edge, id in edges:
            source = id.split('_')[0]
            target = id.split('_')[2]
            dir1 = 'south'
            dir2 = 'north'
            if node_depth[source] > node_depth[target]:
                dir1 = 'north'
                dir2 = 'south'
            if node_depth[source] == node_depth[target]:
                dir1 = 'north'
                dir2 = 'north'
            elems.append(f'\t\draw[->, thick] ({source}.{dir1}) -- ({target}.{dir2}) node[midway, above, sloped] {{{edge}}};')
        latex = '\n\\begin{tikzpicture}[\n'
        latex += 'red/.style={rectangle, draw=red!60, fill=red!5, very thick, minimum size=7mm},\n'
        latex += 'blue/.style={rectangle, draw=blue!60, fill=blue!5, very thick, minimum size=7mm},\n'
        latex += 'green/.style={rectangle, draw=green!60, fill=green!5, very thick, minimum size=7mm},\n'
        latex += 'purple/.style={rectangle, draw=purple!60, fill=purple!5, very thick, minimum size=7mm},\n'
        latex += 'orange/.style={rectangle, draw=orange!60, fill=orange!5, very thick, minimum size=7mm},\n'
        latex += ']\n'
        latex += '\n'.join(elems)
        latex += '\n\end{tikzpicture}\n'

        return latex

def main():
    input_file = r'test-data/amrs.txt'
    if len(sys.argv) > 1:
        input_file = sys.argv[1]

    with open(input_file, 'r', encoding='utf8') as f:
        for amr in AMR.amr_iter(f.read()):
            amr = AMR_Latex.latex(amr)
            print(amr)
            print()


if __name__ == "__main__":
    main()
