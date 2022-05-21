import csv
import glob
import warnings
from collections import defaultdict
from typing import List, Union, Callable, Iterable, Tuple, Iterator

import penman

from amr_utils import amr_normalizers
from amr_utils.amr import AMR, AMR_Notation, Metadata
from amr_utils.amr_alignments import AMR_Alignment, AMR_Alignment_Set
from amr_utils.utils import *


class AMR_Reader:
    """
    TODO
    """

    def __init__(self, id_style: Union[str, 'ID_Notation'] = None,
                 tokenizer: Union[Callable[[str], List[str]], None] = None,
                 normalizers: List[Callable[[AMR], None]] = None):
        """
        
        Args:
            id_style: 
            tokenizer (function: str -> List[str]):
            normalizers (List[function: AMR -> None]):
        """
        self.tokenizer = tokenizer
        self.normalizers = normalizers if normalizers else []
        if id_style is None:
            self.id_notation = None
        elif isinstance(id_style, ID_Notation):
            self.id_notation = id_style
        elif id_style.lower() == 'isi':
            self.id_notation = ISI_Notation()
        elif id_style.lower() == 'jamr':
            self.id_notation = JAMR_Notation()
        else:
            raise Exception(f'[{class_name(self)}] Unrecognized id_style, please use "jamr", "isi", or None.')

    def load(self, amr_file: str, return_alignments: bool = False, quiet: bool = True, encoding: str = 'utf8') -> \
            Union[List[AMR], Tuple[List[AMR], List[AMR_Alignment_Set]]]:
        """
        Load AMRs from a file
        Args:
            amr_file (str): file to load
            return_alignments (bool): whether to also load and return alignments
            quiet (bool): do not print progress to stdout
            encoding (str): file encoding (default: "utf8")

        Returns:
            List[AMR]: a list of AMRs (if return_alignments is False)
             or
            List[AMR], List[AMR_Alignment_Set]: a list of AMRs and a list of AMR alignments (if return_alignments is 
                True)
        """
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

    def load_dir(self, directory: str, return_alignments: bool = False, quiet: bool = True) -> \
            Union[List[AMR], Tuple[List[AMR], List[AMR_Alignment_Set]]]:
        """
        Load AMRs from a directory
        Args:
            directory (str): directory to load
            return_alignments (bool): whether to also load and return alignments
            quiet (bool): do not print progress to stdout

        Returns:
            List[AMR]: a list of AMRs (if return_alignments is False)
             or
            List[AMR], List[AMR_Alignment_Set]: a list of AMRs and a list of AMR alignments (if return_alignments is
                True)
        """
        files = [os.path.join(directory, filename) for filename in os.listdir(directory)]
        return self._load_files(files, return_alignments=return_alignments, quiet=quiet)

    def load_glob(self, glob_string: str, return_alignments: bool = False, quiet: bool = True) -> \
            Union[List[AMR], Tuple[List[AMR], List[AMR_Alignment_Set]]]:
        """
        Load AMRs from a glob of files
        Args:
            glob_string (str): glob description of files
            return_alignments (bool): whether to also load and return alignments
            quiet (bool): do not print progress to stdout

        Returns:
            List[AMR]: a list of AMRs (if return_alignments is False)
             or
            List[AMR], List[AMR_Alignment_Set]: a list of AMRs and a list of AMR alignments (if return_alignments is
                True)
        """
        return self._load_files(glob.glob(glob_string), return_alignments=return_alignments, quiet=quiet)

    def parse(self, amr_string: str, return_alignments: bool = False) -> Union[AMR, Tuple[AMR, AMR_Alignment_Set]]:
        """
        Parse an AMR string, with or without metadata
        Args:
            amr_string (str): amr string
            return_alignments (bool): whether to also load and return alignments

        Returns:
            AMR: an AMR (if return_alignments is False)
             or
            AMR, AMR_Alignment_Set: an AMR and list of AMR alignments (if return_alignments is True)
        """
        amr = AMR.from_string(amr_string)
        aligns = None
        if return_alignments:
            aligns = self._parse_graph_alignments(amr, amr_string)
        if self.id_notation is not None:
            self.id_notation.rename_nodes(amr, aligns)
        for normalize in self.normalizers:
            normalize(amr)
        if self.tokenizer is not None and 'snt' in amr.metadata:
            amr.tokens = self.tokenizer(amr.metadata['snt'])
        if return_alignments:
            if not aligns and 'alignments' in amr.metadata:
                if isinstance(self.id_notation, ISI_Notation) or isinstance(self.id_notation, JAMR_Notation):
                    aligns = self.id_notation.parse_alignments_from_line(amr, amr.metadata['alignments'])
                else:
                    raise Exception(f'[{class_name(self)}] Cannot read alignments from file. Please set the '
                                    'parameter `id_style` to "isi" or "jamr" to specify the alignments format.')
            return amr, aligns
        return amr

    def iterate_amr_strings(self, amr_file: str, separate_metadata: bool = False, encoding: str = 'utf8') -> \
            Union[Iterator[str], Iterator[Tuple[str, str]]]:
        """
        TODO
        Args:
            amr_file:
            separate_metadata:
            encoding:

        Returns:

        """
        buffer = []
        with open(amr_file, 'r', encoding=encoding) as fr:
            for line in fr:
                if not line.strip():
                    if not buffer:
                        continue
                    if Metadata.AMR_START_RE.search(''.join(buffer)):
                        if separate_metadata:
                            yield Metadata.separate_metadata(''.join(buffer))
                        else:
                            yield ''.join(buffer)
                    buffer = []
                else:
                    buffer.append(line)
            if buffer and Metadata.AMR_START_RE.search(''.join(buffer)):
                if separate_metadata:
                    yield Metadata.separate_metadata(''.join(buffer))
                else:
                    yield ''.join(buffer)

    def _parse_graph_alignments(self, amr, amr_string):
        with silence_warnings():
            penman_graph = penman.decode(amr_string, model=AMR._penman_model)

        aligns = AMR_Alignment_Set(amr)
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
                        elif AMR_Notation.is_constant(t):
                            new_t = amr.shape.attribute_nodes[i]
                            align = AMR_Alignment(type='isi', tokens=[tok], nodes=[new_t])
                        else:
                            align = AMR_Alignment(type='isi', tokens=[tok], nodes=[t])
                        aligns.add(align)
                    elif type(datum).__name__ == 'RoleAlignment':
                        if AMR_Notation.is_constant(t):
                            new_t = amr.shape.attribute_nodes[i]
                            align = AMR_Alignment(type='isi', tokens=[tok], edges=[(s, r, new_t)])
                        else:
                            align = AMR_Alignment(type='isi', tokens=[tok], edges=[(s, r, t)])
                        aligns.add(align)
            seen_triples.add(triple)
        return aligns

    def _load_files(self, files: Iterable[str], return_alignments: bool = False, quiet: bool = True) -> \
            Union[List[AMR], Tuple[List[AMR], List[AMR_Alignment_Set]]]:
        amrs = []
        alignments = []
        for file in files:
            try:
                output = self.load(file, return_alignments=return_alignments, quiet=quiet)
            except Exception as e:
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


class Graph_Metadata_AMR_Reader(AMR_Reader):
    """
        TODO
    """

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
                r = ':' + row[2] if not row[2].startswith(':') else row[2]
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


class ID_Notation:
    """
        TODO
    """
    def rename_nodes(self, amr, aligns=None):
        raise NotImplemented()


class Tree_ID_Notation(ID_Notation):
    """
        TODO
    """

    def get_ids(self, amr: AMR, start_idx: int = 0, ignore_reentrancies: bool = True, ignore_dupl_edges: bool = True):

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
            triple = (s, r, amr.nodes[t]) if AMR_Notation.is_constant(amr.nodes[t]) else e
            if ignore_dupl_edges and triple in seen_triples:
                # ignore duplicate
                dupl_triples.append(path_label)
            seen_triples.add(triple)

        new_ids = {}
        for old_id in path_labels:
            new_ids[old_id] = path_labels[old_id]

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
    """
        TODO
    """

    def rename_nodes(self, amr: AMR, aligns: AMR_Alignment_Set = None) -> None:
        new_ids, _ = super().get_ids(amr, start_idx=1, ignore_reentrancies=False, ignore_dupl_edges=True)
        amr_normalizers.rename_nodes(amr, new_ids)
        if aligns:
            for align in aligns:
                align.nodes = [new_ids[n] for n in align.nodes]
                align.edges = [(new_ids[s], r, new_ids[t]) for s, r, t in align.edges]

    def parse_alignments_from_line(self, amr: AMR, line: str) -> AMR_Alignment_Set:
        _, align_ids = super().get_ids(amr, start_idx=1,  ignore_reentrancies=False, ignore_dupl_edges=True)
        aligns = []
        for align in line.split():
            if '-' in align:
                token_idx = int(align.split('-')[0])
                element_id = align.split('-')[-1]
                aligns.append((token_idx, element_id))

        alignments = AMR_Alignment_Set(amr)
        for tok, element_id in aligns:
            nodes = []
            edges = []
            if element_id == '1.r':
                continue
            elif element_id in align_ids and align_ids[element_id] == 'ignore':
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
            alignments.add(new_align)
        return alignments

    def get_element_from_id(self, amr: AMR, element_id: str) -> str:
        path = element_id.split('.')
        children = {n: [] for n in amr.nodes}
        for e in amr.edges:
            s, r, t = e
            children[s].append(e)
        current_node = amr.root
        current_edge = None
        for i in path[1:]:
            if i == 'r':
                return current_edge
            i = int(i) - 1
            if len(children[current_node]) > i:
                current_edge = children[current_node][i]
                current_node = current_edge[-1]
            else:
                raise Exception(f'[{class_name(self)}] Could not parse path:', amr.id, element_id)
        return current_node


class JAMR_Notation(Tree_ID_Notation):
    """
    TODO
    """

    def rename_nodes(self, amr: AMR, aligns: AMR_Alignment_Set = None) -> None:
        new_ids, _ = super().get_ids(amr, start_idx=0, ignore_reentrancies=True, ignore_dupl_edges=False)
        amr_normalizers.rename_nodes(amr, new_ids, alignments=aligns)

    def parse_alignments_from_line(self, amr: AMR, line: str) -> AMR_Alignment_Set:
        _, align_ids = super().get_ids(amr, start_idx=0, ignore_reentrancies=True, ignore_dupl_edges=True)
        align_pairs = []
        for align in line.split():
            if '|' in align:
                token_string = align.split('|')[0].split('-')
                nodes_string = align.split('|')[1]
                start, stop = int(token_string[0]), int(token_string[1])
                tokens = [i for i in range(start, stop)]
                ns = nodes_string.split('+') if '+' in nodes_string else [nodes_string]
                align_pairs.append((tokens, ns))

        alignments = AMR_Alignment_Set(amr)
        for tokens, ns in align_pairs:
            if not all(t < len(amr.tokens) for t in tokens):
                raise Exception(f'[{class_name(self)}] Could not parse alignment:', amr.id, tokens, ns)
            nodes = []
            for n in ns:
                if n not in align_ids:
                    align_ids[n] = self.get_element_from_id(amr, n)
                nodes.append(align_ids[n])
            new_align = AMR_Alignment(type='jamr', tokens=tokens, nodes=nodes)
            alignments.add(new_align)
        return alignments

    def get_element_from_id(self, amr: AMR, element_id: str) -> str:
        path = element_id.split('.')
        children = {n: [] for n in amr.nodes}
        seen_nodes = {amr.root}
        for e in amr.edges:
            s, r, t = e
            if t not in seen_nodes:
                children[s].append(e)
            seen_nodes.add(t)
        current_node = amr.root
        for i in path[1:]:
            i = int(i)
            if len(children[current_node]) > i:
                s, r, t = children[current_node][i]
                current_node = t
            else:
                raise Exception(f'[{class_name(self)}] Could not parse path:', amr.id, element_id)
        return current_node


class JSON_Alignment_Reader:
    """
    TODO
    """

    @staticmethod
    def _check_ids_match(amr: AMR, json_alignment_list):
        # check ids
        node_ids = set()
        for align in json_alignment_list:
            nodes = align['nodes'] if ('nodes' in align) else []
            edges = align['edges'] if ('edges' in align) else []
            for node in nodes:
                node_ids.add(node)
            for edge in edges:
                node_ids.add(edge[0])
                node_ids.add(edge[2])
        if any(n not in amr.nodes for n in node_ids):
            raise Exception(f'Failed to anonymize alignments for {amr.id}. '
                            'This typically means the alignment ids do not match the AMR ids.'
                            f'\nAMR node IDs: {set(amr.nodes.keys())}'
                            f'\nAMR_Alignment node IDs: {node_ids}')

    @staticmethod
    def _unanonymize_edges(amr, json_alignment_list):
        map_unlabeled_edges = defaultdict(list)
        for s, r, t in amr.edges:
            map_unlabeled_edges[(s, t)].append((s, r, t))
        for json_align in json_alignment_list:
            if 'edges' in json_align:
                for i, e in enumerate(json_align['edges']):
                    s, r, t = e[0], e[1], e[2]
                    if r == ':_':
                        s, r, t = map_unlabeled_edges[(s, t)]
                    json_align['edges'][i] = (s, r, t)

    def load_from_json(self, json_file: str, unanonymize: bool = False, amrs: Iterable[AMR] = None):
        """
        TODO
        Args:
            json_file:
            unanonymize:
            amrs:

        Returns:

        """
        alignment_sets = []
        if unanonymize and not amrs:
            raise Exception('To un-anonymize alignments, the parameter "amrs" is required.')
        with open(json_file, 'r', encoding='utf8') as f:
            json_alignments = json.load(f)
        amrs_from_id = {}
        for amr in amrs:
            amrs_from_id[amr.id] = amr
        for amr_id in json_alignments:
            amr = amrs_from_id[amr_id]
            self._check_ids_match(amr, json_alignments[amr_id])
            if unanonymize:
                self._unanonymize_edges(amr, json_alignments[amr_id])
            alignment_list = []
            for json_align in json_alignments[amr_id]:
                nodes = json_align['nodes'] if ('nodes' in json_align) else []
                edges = [(e[0], e[1], e[2]) for e in json_align['edges']] if ('edges' in json_align) else []
                alignment = AMR_Alignment(type=json_align['type'], tokens=json_align['tokens'],
                                          nodes=nodes, edges=edges)
                alignment_list.append(alignment)
            alignment_sets.append(AMR_Alignment_Set(amr, alignment_list))
        return alignment_sets
