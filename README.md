AMR-utils is a python package for working with AMR data, working with AMR alignments, and visualizing AMRs. This code is maintained by Austin Blodgett. I wrote amr-utils to store operations that I often need when doing research with AMRs. 
### Features:
- Load AMRs from a file or directory, with support for multiple formats
- Load AMR alignments, with support for LDC, JAMR, and ISI alignment formats
- A simple class for accessing AMR nodes, edges, tokens, etc.
- Tools for AMR Visualization
	- Convert AMR graphs to Latex (using the tikz library)
	- Display AMR strings as HTML, with overridable display settings for nodes, tokens, and edges
	- AMR Diff, Display differnces between AMRs as HTML
	- Display AMR Alignments as HTML

### Requirements
- Python 3.6 or higher
- [PENMAN library](https://github.com/goodmami/penman)

### Input
Input should contain AMR strings separated by a blank line. Lines starting with `#` will be treated as metadata.

# AMR Reader
The class `AMR_Reader` can be used to load AMRs or AMR alignments from a number of different formats including LDC, JAMR, and ISI. An `AMR_Reader` can be used as follows.

```
from amr_utils.amr_readers import AMR_Reader

reader = AMR_Reader()
amrs = reader.load(amr_file, remove_wiki=True)
```

AMRs must be separated by empty lines, but otherwise can take various formats.
Simplified:
```
# Dogs chase cats.
(c/chase-01 :ARG0 (d/dog)
	:ARG1 (c2/cat))
```

JAMR-style tab seperated metdata format:

```
# ::id 1
# ::tok Dogs chase cats.
# ::node	c	chase-01
# ::node	d	dog
# ::node	c2	cat
# ::root	c	chase-01
# ::edge	chase-01	ARG0	dog	c	d
# ::edge	chase-01	ARG1	cat	c	c2
(c/chase-01 :ARG0 (d/dog)
	:ARG1 (c2/cat))
```

### Loading Alignments from LDC, JAMR, or ISI
AMR Alignments can also be loaded from different formats:
- LDC:
`# ::alignments 0-1.1 1-1 1-1.1.r 1-1.2.r 2-1.2`
- JAMR:
`# ::alignments 0-1|0.0 1-2|0 2-3|0.1`
- ISI:
`(c/chase-01~e.1 :ARG0~e.1 (d/dog~e.0) :ARG1~e.1 (c2/cat~e.2))`

Just set the parameter `output_alignments` to `True`. 

```
from amr_utils.amr_readers import AMR_Reader

reader = AMR_Reader()
amrs, alignments = reader.load(amr_file, remove_wiki=True, output_alignments=True)
```

By default, `AMR_Reader` uses the LDC/ISI style of node ids where 1.n is the nth child of the root with indices starting at 1. 
Any alignments are automatically converted to this format for data consistency. 

# AMR Alignments JSON Format
The package includes tools for converting AMR alignments from and to JSON like the following.
```
[{'type':'isi', 'tokens':[0], 'nodes':['1.1'], 'edges':[]},
{'type':'isi', 'tokens':[1], 'nodes':['1'], 'edges':[['1',':ARG0','1.1'],['1',':ARG1','1.2']]},
{'type':'isi', 'tokens':[2], 'nodes':['1.2'], 'edges':[]},
]
```

The advantages of using JSON are:
- Easy to load and save (No need to write a special script for reading some esoteric format)
- Can store additional information in a `type` to distinguish different types of alignments
- Can easily store multiple sets of alignments separately for comparison without needing to modify an AMR file. 


To read alignments from a JSON file do:
```
reader = AMR_Reader()
alignments = reader.load_alignments_from_json(alignments_file)
```
To save alignments to a JSON file do:
```
reader = AMR_Reader()
reader.save_alignments_to_json(alignments_file, alignments)
```
# AMR Visualization
AMR-utils includes tools for visualizing AMRs and AMR aligments. See the wiki for more detail.

## Latex
Amr-utils allows you to read AMRs from a text file and output them as latex diagrams, such as the following.
![latex example](https://github.com/ablodge/amr-utils/blob/master/latex_ex.PNG)

### Colors
The default coloring assigns blue to each node, but the parameter `assign_color` can be used to assign colors using a function. To change a color by hand, just rewrite `\node[red]` as `\node[purple]`, etc.

### Instructions
Run as follows:

`python style.py --latex -f [input file] [output file]`

Add these lines to your latex file:

```
\usepackage{tikz}
\usetikzlibrary{shapes}
```


## HTML
Amr-utils allows you to read AMRs from a text file and output them as html. You can look in `style.css` for an example of styling. 
![html example](https://github.com/ablodge/amr-utils/blob/master/html_ex.PNG)
### Instructions
Run as follows:

`python style.py --html -f [input file] [output file]`



## AMR Diff

![amr diff example](https://github.com/ablodge/amr-utils/blob/master/amr_diff_ex.PNG)
### Instructions
Run as follows:

`python amr_diff.py [amr file1] [amr file2] [output file]`


## Display Alignments

![display alignments example](https://github.com/ablodge/amr-utils/blob/master/display_align_ex.PNG)
### Instructions
Run as follows:

`python display_alignments.py [amr file] [alignment file] [output file]`
