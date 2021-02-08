# amr-utils
A python package of common operations for AMRs


I wrote amr-utils to store operations that I often need when doing research with AMRs. 
### Features:
- Load multiple AMRs from a text file
- iterate through nodes, edges, or alignments
- output AMRs to useful formats: html (AMR string) or latex (AMR graph)

### Requirements
Python 3.6 or higher
PENMAN library

### Input
Input should contain AMR strings separated by a blank line. Lines starting with `#` will be ignored.

# AMR Reader
The class `AMR_Reader` can be used to load AMRs or AMR alignments from a number of different formats including LDC, JAMR, and ISI. An `AMR_Reader` can be used as follows.

```
from amr_utils.amr_readers import AMR_Reader

reader = AMR_Reader()
amrs = reader.load(amr_file, remove_wiki=True)
```
or
```
from amr_utils.amr_readers import AMR_Reader

reader = AMR_Reader()
amrs, alignments = reader.load(amr_file, remove_wiki=True, output_alignments=True)
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

AMR Alignments can also be loaded from different formats:
LDC:
`# ::alignments 0-1.1 1-1 1-1.1.r 1-1.2.r 2-1.2`
JAMR:
`# ::alignments 0-1|0.0 1-2|0 2-3|0.1`
ISI:
`(c/chase-01~e.1 :ARG0~e.1 (d/dog~e.0) :ARG1~e.1 (c2/cat~e.2))`

Just set the parameter `output_alignments` to `True`. By default, `AMR_Reader` uses the LDC/ISI style of node ids where 1.n is the nth child of the root with indices starting at 1. 
Any alignments are automatically converted to this format for data consistency. 

# Versatile AMR Alignments JSON Format
The package includes tools for converting AMR alignemnts from and to JSON like the following.
```
[{'type':'isi', 'tokens':[0], 'nodes':['1.1'], 'edges':[]},
{'type':'isi', 'tokens':[1], 'nodes':['1'], 'edges':[['1',':ARG0','1.1'],['1',':ARG1','1.2']]},
{'type':'isi', 'tokens':[2], 'nodes':['1.2'], 'edges':[]},
]
```

The advantages of using JSON are:
- Easy to load and save (No need to write a special script for reading some esoteric format)
- Can store additional information in a `type` to distinguish different types of alignments
- Can easily store multiple sets of alignments seperately for comparison without needing to modify an AMR file. 


To read alignemnts from a JSON file do:
```
reader = AMR_Reader()
alignments = reader.load_alignemnts_from_json(alignments_file)
```
To save alignemnts to a JSON file do:
```
reader = AMR_Reader()
reader.save_alignemnts_to_json(alignments_file, alignments)
```

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
