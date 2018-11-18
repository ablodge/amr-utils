# amr-utils
A python package of common operations for AMRs


I wrote amr-utils to store operations that I often need when doing research with AMRs. 
### Features:
- Load multiple AMRs from a text file
- iterate through nodes, edges, or named entities
- output AMRs to useful formats: html (AMR string) or latex (AMR graph)
- associates a unique id to each node or edge (can be used for styling a particular element in a webpage or web app)

### Requirements
Python 3.6 or higher

### Input
Input should contain AMR strings separated by a blank line. Lines starting with `#` will be ignored.

# HTML
Amr-utils allows you to read AMRs from a text file and output them as html. You can look in `style.css` for an example of styling. 
### Instructions
Run as follows:

`python amr_html.py [input file] > [output file]`

# Latex
Amr-utils allows you to read AMRs from a text file and output them as latex diagrams, such as the following.
![latex example](https://github.com/ablodge/amr-utils/blob/master/latex_ex.PNG)

### Colors
The default coloring assigns a different color to each node in a given row. To change a color by hand, just rewrite `\node[red]` as `\node[purple]`, etc.

### Instructions
Run as follows:

`python amr_latex.py [input file] > [output file]`
