# amr-utils
A python package of common operations for AMRs


I wrote amr-utils to store operations that I often need when doing research with AMRs. 
### Features:
- Load multiple AMRs from a text file
- iterate through nodes, edges, or alignments
- output AMRs to useful formats: html (AMR string) or latex (AMR graph)

### Requirements
Python 3.6 or higher

### Input
Input should contain AMR strings separated by a blank line. Lines starting with `#` will be ignored.

# Latex
Amr-utils allows you to read AMRs from a text file and output them as latex diagrams, such as the following.
![latex example](https://github.com/ablodge/amr-utils/blob/master/latex_ex.PNG)

### Colors
The default coloring assigns blue to each node, but the parameter `assign_color` can be used to assign colors using a function. To change a color by hand, just rewrite `\node[red]` as `\node[purple]`, etc.

### Instructions
Run as follows:

`python style.py --latex [input file] [output file]`

Add these lines to your latex file:

```
\usepackage{tikz}
\usetikzlibrary{shapes}
```


# HTML
Amr-utils allows you to read AMRs from a text file and output them as html. You can look in `style.css` for an example of styling. 
![html example](https://github.com/ablodge/amr-utils/blob/master/html_ex.png)
### Instructions
Run as follows:

`python style.py --html [input file] [output file]`
