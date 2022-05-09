import csv
import glob
import re
import warnings
from collections import defaultdict, Counter
from typing import List, Union, Callable, Iterable

import penman

from amr_utils import amr_normalizers
from amr_utils.amr import AMR, AMR_Notation
from amr_utils.amr_alignments import AMR_Alignment
from amr_utils.utils import *


class Metadata_Reader:
    def parse(self, lines: List[str]):
        raise NotImplemented()

    def write(self, amr: AMR):
        raise NotImplemented()


class ID_Notation:
    def rename_nodes(self, amr, aligns=None):
        raise NotImplemented()


class AMR_Reader:

    def __init__(self, id_style: Union[str, ID_Notation] = None,
                 tokenizer: Union[Callable[[str], List[str]], None] = None,
                 metadata_reader: Union[Metadata_Reader, None] = None,
                 normalizers: List[Callable[[AMR], None]] = None):
        self.tokenizer = tokenizer

        self.metadata_reader = metadata_reader
        if metadata_reader is None:
            self.metadata_reader = Default_Metadata_Reader()

        if id_style is None:
            self.id_notation = None
        elif isinstance(id_style, ID_Notation):
            self.id_notation = id_style
        elif id_style.lower() == 'isi':
            self.id_notation = ISI_Notation()
        elif id_style.lower() == 'jamr':
            self.id_notation = JAMR_Notation()

        self.normalizers = normalizers if normalizers else []

        self._penman_model = AMR_Reader.TreePenmanModel()

    class TreePenmanModel(penman.model.Model):
        def deinvert(self, triple):
            return triple

        def invert(self, triple):
            return triple

    def load(self, amr_file: str, return_alignments: bool = False, quiet: bool = True, encoding: str = 'utf8'):
        '''
        Load AMRs from a file
        Args:
            amr_file (str): file to load
            return_alignments (bool): whether to also load and return alignments
            quiet (bool): do not print progress to stdout
            encoding (str): file encoding (default: "utf8")

        Returns:
            List[AMR]: a list of AMRs (if return_alignments is False)
             or
            List[AMR], List[List[AMR_Alignment]]: a list of AMRs and a list of AMR alignments (if return_alignments is True)
        '''
        if not quiet:
            print(f'[{class_name(self)}] Loading AMRs from file:', amr_file)
        amrs = []
        alignments = []
        for amr_string in self.iterate_amr_strings(amr_file, encoding=encoding):
            if return_alignments:
                amr, aligns = self.parse(amr_string, return_alignments=return_alignments)
                alignments.append(aligns)
            else:
                amr = self.parse(amr_string, return_alignments=return_alignments)
            amrs.append(amr)
        if return_alignments:
            return amrs, alignments
        return amrs

    def load_dir(self, dir: str, return_alignments: bool = False, quiet: bool = True):
        '''
        Load AMRs from a directory
        Args:
            dir (str): directory to load
            return_alignments (bool): whether to also load and return alignments
            quiet (bool): do not print progress to stdout

        Returns:
            List[AMR]: a list of AMRs (if return_alignments is False)
             or
            List[AMR], List[List[AMR_Alignment]]: a list of AMRs and a list of AMR alignments (if return_alignments is True)
        '''
        files = [os.path.join(dir, filename) for filename in os.listdir(dir)]
        return self._load_files(files, return_alignments=return_alignments, quiet=quiet)

    def load_glob(self, glob_string: str, return_alignments: bool = False, quiet: bool = True):
        '''
        Load AMRs from a glob of files
        Args:
            glob_string (str): glob description of files
            return_alignments (bool): whether to also load and return alignments
            quiet (bool): do not print progress to stdout

        Returns:
            List[AMR]: a list of AMRs (if return_alignments is False)
             or
            List[AMR], List[List[AMR_Alignment]]: a list of AMRs and a list of AMR alignments (if return_alignments is True)
        '''
        return self._load_files(glob.glob(glob_string), return_alignments=return_alignments, quiet=quiet)

    def parse(self, amr_string: str, return_alignments: bool = False):
        '''
        Parse an AMR string, with or without metadata
        Args:
            amr_string (str): amr string
            return_alignments (bool): whether to also load and return alignments

        Returns:
            AMR: an AMR (if return_alignments is False)
             or
            AMR, List[AMR_Alignment]: an AMR and list of AMR alignments (if return_alignments is True)
        '''
        try:
            lines = amr_string.split('\n')
            amr_start = None
            for i, line in enumerate(lines):
                if line.strip().startswith('('):
                    amr_start = i
                    break
            metadata_string = '\n'.join(lines[:amr_start]).strip()
            id, tokens, metadata = self.metadata_reader.parse(metadata_string)
            amr = self.metadata_reader.parse_graph_metadata(metadata_string)
            aligns = None
            if amr is None:
                amr_string = '\n'.join(lines[amr_start:]).strip()
                amr, aligns = self._parse_amr_string(amr_string, return_alignments=return_alignments)
            amr.id = id
            amr.tokens = tokens
            amr.metadata = metadata
            if self.tokenizer is not None and 'snt' in metadata:
                amr.tokens = self.tokenizer(amr.metadata['snt'])
            elif not tokens and 'snt' in metadata:
                amr.tokens = amr.metadata['snt'].split()
            if return_alignments:
                if not aligns and 'alignments' in amr.metadata:
                    if isinstance(self.id_notation, ISI_Notation) or isinstance(self.id_notation, JAMR_Notation):
                        aligns = self.id_notation.parse_alignments_from_line(amr, amr.metadata['alignments'])
                return amr, aligns
            return amr
        except:
            raise Exception('Could not parse:', ''.join(amr_string))

    def iterate_amr_strings(self, amr_file: str, separate_metadata: bool=False, encoding: str = 'utf8'):
        buffer = []
        with open(amr_file, 'r', encoding=encoding) as fr:
            for line in fr:
                if not line.strip():
                    if not buffer:
                        continue
                    if self._test_is_amr_string(buffer):
                        if separate_metadata:
                            amr_start = [i for i,l in enumerate(buffer) if l.strip().startswith('(')][0]
                            yield ''.join(buffer[:amr_start]).strip(), ''.join(buffer[amr_start:]).strip()
                        else:
                            yield ''.join(buffer)
                    buffer = []
                else:
                    buffer.append(line)
            if buffer and self._test_is_amr_string(buffer):
                if separate_metadata:
                    amr_start = [i for i,l in enumerate(buffer) if l.strip().startswith('(')][0]
                    yield ''.join(buffer[:amr_start]).strip(), ''.join(buffer[amr_start:]).strip()
                else:
                    yield ''.join(buffer)

    def _test_is_amr_string(self, lines):
        if all(line.startswith('#') for line in lines):
            return False
        amr_starts = [l for l in lines if l.strip().startswith('(')]
        if not amr_starts:
            return False
        if len(amr_starts)>1:
            warnings.warn(f'[{class_name(self)}] Could not parse AMR:\n'+''.join(lines))
            return False
        return True

    def _parse_amr_string(self, amr_string: str, return_alignments: bool=False):

        with silence_warnings():
            penman_graph = penman.decode(amr_string, model=self._penman_model)

        root = penman_graph.top
        nodes = {s: t for s, r, t in penman_graph.triples if r == ':instance'}
        edges = []
        new_attribute_nodes = {}
        reentrancy_artifacts = {}
        num_parents = Counter()
        prev_edge = None
        for i, triple in enumerate(penman_graph.triples):
            s, r, t = triple
            if r == ':instance':
                # an amr node
                if prev_edge is not None:
                    reentrancy_artifacts[s] = prev_edge
            elif AMR_Notation.is_attribute(t):
                # attribute
                idx = 0
                while f'x{idx}' in nodes:
                    idx += 1
                new_n = f'x{idx}'
                new_attribute_nodes[i] = new_n
                nodes[new_n] = t
                edges.append((s, r, new_n))
            else:
                # edge
                edges.append((s, r, t))
                num_parents[t] += 1
                prev_edge = (s, r, t)

        aligns = []
        if return_alignments:
            aligns = self._parse_graph_alignments(penman_graph, new_attribute_nodes)

        amr = AMR(root=root, nodes=nodes, edges=edges)
        amr.reentrancy_artifacts = {n: reentrancy_artifacts[n] for n in reentrancy_artifacts
                                    if num_parents[n] > 1}
        if self.id_notation is not None:
            self.id_notation.rename_nodes(amr, aligns)
        for normalize in self.normalizers:
            normalize(amr)
        return amr, sorted(aligns)

    def _parse_graph_alignments(self, penman_graph, new_attribute_nodes):
        aligns = []
        seen_triples = set()
        for i, triple in enumerate(penman_graph.triples):
            if triple in seen_triples:
                # ignore duplicate triples
                continue
            epidata = penman_graph.epidata[triple]
            for datum in epidata:
                if 'Alignment' not in type(datum).__name__:
                    continue
                s, r, t = triple
                for tok in datum.indices:
                    if type(datum).__name__ == 'Alignment':
                        if r == ':instance':
                            align = AMR_Alignment(type='isi', tokens=[tok], nodes=[s])
                        elif AMR_Notation.is_attribute(t):
                            new_t = new_attribute_nodes[i]
                            align = AMR_Alignment(type='isi', tokens=[tok], nodes=[new_t])
                        else:
                            align = AMR_Alignment(type='isi', tokens=[tok], nodes=[t])
                        aligns.append(align)
                    elif type(datum).__name__ == 'RoleAlignment':
                        if AMR_Notation.is_attribute(t):
                            new_t = new_attribute_nodes[i]
                            align = AMR_Alignment(type='isi', tokens=[tok], edges=[(s, r, new_t)])
                        else:
                            align = AMR_Alignment(type='isi', tokens=[tok], edges=[(s, r, t)])
                        aligns.append(align)
            seen_triples.add(triple)
        return aligns

    def _load_files(self, files: Iterable[str], return_alignments: bool = False, quiet: bool = True):
        amrs = []
        alignments = []
        for file in files:
            try:
                output = self.load(file, return_alignments=return_alignments, quiet=quiet)
            except:
                warnings.warn(f'Could not load file: {file}')
                continue
            if return_alignments:
                amrs.extend(output[0])
                alignments.extend(output[1])
            else:
                amrs.extend(output)
        if return_alignments:
            return amrs, alignments
        return amrs


class Default_Metadata_Reader(Metadata_Reader):
    SPLIT_METADATA_RE = re.compile(r'(?<=[^#]) ::(?=\S+)')
    METADATA_RE = re.compile(r'# ::(?P<tag>\S+)(?P<value>.*)')

    def parse(self, metadata_string: str):
        lines = self.SPLIT_METADATA_RE.sub('\n# ::', metadata_string).split('\n')
        id = None
        tokens = []
        metadata = {}
        for line in lines:
            tag, val = self._parse_line(line)
            if tag == 'id':
                id = val
            elif tag == 'tok':
                tokens = val
            elif tag in ['root', 'node', 'edge']:
                continue
            else:
                metadata[tag] = val
        return id, tokens, metadata

    def parse_graph_metadata(self, metadata_string: str):
        graph_metadata_lines = []
        for line in metadata_string.split('\n'):
            if any(line.startswith(f'# ::{tag}\t') for tag in ['root', 'node', 'edge']):
                graph_metadata_lines.append(line)
        if not graph_metadata_lines:
            return None
        root = None
        nodes = {}
        edges = []
        for row in csv.reader(graph_metadata_lines, delimiter='\t', quotechar='"'):
            if row[0] == '# ::root':
                root = row[1]
            elif row[0] == '# ::node':
                nodes[row[1]] = row[2]
            elif row[0] == '# ::edge':
                r = ':'+row[2] if not row[2].startswith(':') else row[2]
                edges.append((row[4], r, row[5]))
            else:
                raise Exception('Failed to read metadata:', graph_metadata_lines)
        amr = AMR(root=root, nodes=nodes, edges=edges)
        normalize_order = False
        seen_nodes = {amr.root}
        for s, r, t in amr.edges:
            if s not in seen_nodes:
                normalize_order = True
                break
            seen_nodes.add(t)
        if normalize_order:
            amr_normalizers.normalize_shape(amr)
        return amr

    def _parse_line(self, line: str):
        if not line.startswith('# ::'):
            tag = 'snt'
            val = line[1:].strip() if line.startswith('#') else line.strip()
            return tag, val

        match = self.METADATA_RE.match(line)
        if not match:
            raise Exception('Failed to parse metadata:', line)
        tag = match.group('tag')
        val = match.group('value').strip()
        return tag, val


class Tree_ID_Notation(ID_Notation):

    def get_ids(self, amr: AMR, start_idx: int = 0, use_annotator_artifacts: bool = False,
                ignore_reentrancies: bool = True, ignore_dupl_edges: bool = True):

        path_edge_idx = defaultdict(lambda: start_idx)
        path_labels = {amr.root: str(start_idx)}
        edge_path_labels = {}

        seen_triples = set()
        dupl_triples = []
        for i, e in enumerate(amr.edges):
            s, r, t = e
            path_label = path_labels[s] + '.' + str(path_edge_idx[s])
            edge_path_labels[i] = path_label
            is_reentrancy = (t in path_labels)
            if not is_reentrancy:
                path_labels[t] = path_label
            # edge
            if not (ignore_reentrancies and is_reentrancy):
                # ignore reentrancies
                path_edge_idx[s] += 1
            triple = (s, r, amr.nodes[t]) if AMR_Notation.is_attribute(amr.nodes[t]) else e
            if ignore_dupl_edges and triple in seen_triples:
                # ignore duplicate
                dupl_triples.append(path_label)
            seen_triples.add(triple)

        new_ids = {}
        for old_id in path_labels:
            new_ids[old_id] = path_labels[old_id]

        if use_annotator_artifacts and amr.reentrancy_artifacts is not None:
            for n, parent in amr.reentrancy_artifacts.items():
                new_ids[n] = edge_path_labels[amr.edges.index(parent)]

        align_ids = {}
        align_ids[new_ids[amr.root]] = new_ids[amr.root]
        for i, e in enumerate(amr.edges):
            s, r, t = e
            path = edge_path_labels[i]
            align_ids[path + '.r'] = (new_ids[s], r, new_ids[t])
            align_ids[path] = new_ids[t]
            if path in dupl_triples:
                align_ids[path + '.r'] = 'ignore'
                align_ids[path] = 'ignore'

        # if len(set(new_ids.values())) < len(new_ids):
        #     raise Exception('Failed to assign unique IDs:', amr.id)
        return new_ids, align_ids


class ISI_Notation(Tree_ID_Notation):

    def rename_nodes(self, amr, aligns=None):
        new_ids, _ = super().get_ids(amr, start_idx=1, use_annotator_artifacts=False,
                                     ignore_reentrancies=False, ignore_dupl_edges=True)
        amr_normalizers.rename_nodes(amr, new_ids)
        if aligns:
            for align in aligns:
                align.nodes = [new_ids[n] for n in align.nodes]
                align.edges = [(new_ids[s], r, new_ids[t]) for s, r, t in align.edges]

    def parse_alignments_from_line(self, amr, line):
        _, align_ids = super().get_ids(amr, start_idx=1, use_annotator_artifacts=False,
                                     ignore_reentrancies=False, ignore_dupl_edges=True)
        aligns = []
        for align in line.split():
            if '-' in align:
                token_idx = int(align.split('-')[0])
                element_id = align.split('-')[-1]
                aligns.append((token_idx, element_id))

        alignments = []
        for tok, element_id in aligns:
            nodes = []
            edges = []
            if element_id == '1.r':
                continue
            elif element_id in align_ids and align_ids[element_id]=='ignore':
                # ignore duplicate edges
                continue
            elif element_id.endswith('.r'):
                # edge
                if element_id not in align_ids or align_ids[element_id] not in amr.edges:
                    align_ids[element_id] = self.get_element_from_id(amr, element_id)
                e = align_ids[element_id]
                edges.append(e)
            else:
                # node
                if element_id not in align_ids or align_ids[element_id] not in amr.nodes:
                    align_ids[element_id] = self.get_element_from_id(amr, element_id)
                nodes.append(align_ids[element_id])
            if tok >= len(amr.tokens):
                raise Exception('Could not parse alignment:', amr.id, tok, element_id)
            new_align = AMR_Alignment(type='isi', tokens=[tok], nodes=nodes, edges=edges)
            alignments.append(new_align)
        return sorted(alignments)

    def get_element_from_id(self, amr, element_id):
        path = element_id.split('.')
        children = {n:[] for n in amr.nodes}
        for e in amr.edges:
            s,r,t = e
            children[s].append(e)
        current_node = amr.root
        current_edge = None
        for i in path[1:]:
            if i=='r':
                return current_edge
            i = int(i) - 1
            if len(children[current_node])>i:
                current_edge = children[current_node][i]
                current_node = current_edge[-1]
            else:
                raise Exception('Could not parse path:', amr.id, element_id)
        return current_node


class JAMR_Notation(Tree_ID_Notation):

    def rename_nodes(self, amr, aligns=None):
        new_ids, _ = super().get_ids(amr, start_idx=0, use_annotator_artifacts=False,
                                     ignore_reentrancies=True, ignore_dupl_edges=False)
        amr_normalizers.rename_nodes(amr, new_ids)
        if aligns:
            for align in aligns:
                align.nodes = [new_ids[n] for n in align.nodes]
                align.edges = [(new_ids[s], r, new_ids[t]) for s, r, t in align.edges]

    def parse_alignments_from_line(self, amr, line):
        _, align_ids = super().get_ids(amr, start_idx=0, use_annotator_artifacts=False,
                                       ignore_reentrancies=True, ignore_dupl_edges=True)
        align_pairs = []
        for align in line.split():
            if '|' in align:
                token_string = align.split('|')[0].split('-')
                nodes_string = align.split('|')[1]
                start, stop = int(token_string[0]), int(token_string[1])
                tokens = [i for i in range(start, stop)]
                ns = nodes_string.split('+') if '+' in nodes_string else [nodes_string]
                align_pairs.append((tokens, ns))

        alignments = []
        for tokens, ns in align_pairs:
            if not all(t < len(amr.tokens) for t in tokens):
                raise Exception('Could not parse alignment:', amr.id, tokens, ns)
            nodes = []
            for n in ns:
                if n not in align_ids:
                    align_ids[n] = self.get_element_from_id(amr, n)
                nodes.append(align_ids[n])
            new_align = AMR_Alignment(type='jamr', tokens=tokens, nodes=nodes)
            alignments.append(new_align)
        return sorted(alignments)

    def get_element_from_id(self, amr, element_id):
        path = element_id.split('.')
        children = {n:[] for n in amr.nodes}
        seen_nodes = {amr.root}
        for e in amr.edges:
            s,r,t = e
            if t not in seen_nodes:
                children[s].append(e)
            seen_nodes.add(t)
        current_node = amr.root
        for i in path[1:]:
            i = int(i)
            if len(children[current_node])>i:
                s, r, t = children[current_node][i]
                current_node = t
            else:
                raise Exception('Could not parse path:', amr.id, element_id)
        return current_node
