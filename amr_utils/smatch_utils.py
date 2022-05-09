import random
import sys
from collections import defaultdict

from amr_utils import amr_normalizers
from amr_utils.amr import AMR
from amr_utils.amr_iterators import breadth_first_edges


def smatch_score(amr1: AMR, amr2: AMR):
    raise NotImplemented()


def smatch_amr2amr_alignment(amr1: AMR, amr2: AMR):
    smatch = SMATCH()

    prefix1 = "a"
    prefix2 = "b"
    node_map1 = {}
    node_map2 = {}
    idx = 0
    for n in amr1.nodes.copy():
        node_map1[n] = prefix1+str(idx)
        idx+=1
    amr_normalizers.rename_nodes(amr1, node_map1)
    idx = 0
    for n in amr2.nodes.copy():
        node_map2[n] = prefix2 + str(idx)
        idx += 1
    amr_normalizers.rename_nodes(amr2, node_map2)
    node_map1 = {v:k for k,v in node_map1.items()}
    node_map2 = {v: k for k, v in node_map2.items()}
    instance1 = []
    attributes1 = []
    relation1 = []
    for s,r,t in amr1.triples(normalize_inverse_relations=True):
        if r==':instance':
            instance1.append((r,s,t))
        elif t not in amr1.nodes:
            attributes1.append((r,s,t))
        else:
            relation1.append((r,s,t))
    instance2 = []
    attributes2 = []
    relation2 = []
    for s,r,t in amr2.triples(normalize_inverse_relations=True):
        if r==':instance':
            instance2.append((r,s,t))
        elif t not in amr2.nodes:
            attributes2.append((r,s,t))
        else:
            relation2.append((r,s,t))
    # optionally turn off some of the node comparison
    doinstance = doattribute = dorelation = True
    (best_mapping, best_match_num) = smatch.get_best_match(instance1, attributes1, relation1,
                                                    instance2, attributes2, relation2,
                                                    prefix1, prefix2, doinstance=doinstance,
                                                    doattribute=doattribute, dorelation=dorelation)
    test_triple_num = len(instance1) + len(attributes1) + len(relation1)
    gold_triple_num = len(instance2) + len(attributes2) + len(relation2)
    amr_normalizers.rename_nodes(amr1, node_map1)
    amr_normalizers.rename_nodes(amr2, node_map2)

    align_map = {}
    for i,j in enumerate(best_mapping):
        a = prefix1 + str(i)
        if j==-1:
            continue
        b = prefix2 + str(j)
        align_map[node_map1[a]] = node_map2[b]
    if amr1.root not in align_map:
        align_map[amr1.root] = amr2.root
    for depth, e in breadth_first_edges(amr1, ignore_reentrancies=True):
        s, r, t = e
        if t not in align_map:
            for s2,r2,t2 in amr2.edges:
                if align_map[s]==s2 and r==r2 and amr1.nodes[t]==amr2.nodes[t2]:
                    align_map[t] = t2
            if t not in align_map:
                align_map[t] = align_map[s]

    if not all(n in align_map for n in amr1.nodes):
        raise Exception('Failed to build node alignment:', amr1.id, amr2.id)
    prec = best_match_num / test_triple_num if test_triple_num>0 else 0
    rec = best_match_num / gold_triple_num if gold_triple_num>0 else 0
    f1 = 2*(prec*rec)/(prec+rec) if (prec+rec)>0 else 0
    return align_map, prec, rec, f1


class SMATCH:
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    """
    This code is taken from https://github.com/snowblink14/smatch
    """


    """
    This script computes smatch score between two AMRs.
    For detailed description of smatch, see http://www.isi.edu/natural-language/amr/smatch-13.pdf
    
    """

    # total number of iteration in smatch computation
    iteration_num = 5

    # verbose output switch.
    # Default false (no verbose output)
    verbose = False
    veryVerbose = False

    # single score output switch.
    # Default true (compute a single score for all AMRs in two files)
    single_score = True

    # precision and recall output switch.
    # Default false (do not output precision and recall, just output F score)
    pr_flag = False

    # Error log location
    ERROR_LOG = sys.stderr

    # Debug log location
    DEBUG_LOG = sys.stderr

    # dictionary to save pre-computed node mapping and its resulting triple match count
    # key: tuples of node mapping
    # value: the matching triple count
    match_triple_dict = {}


    def get_best_match(self, instance1, attribute1, relation1,
                       instance2, attribute2, relation2,
                       prefix1, prefix2, doinstance=True, doattribute=True, dorelation=True):
        """
        Get the highest triple match number between two sets of triples via hill-climbing.
        Arguments:
            instance1: instance triples of AMR 1 ("instance", node name, node value)
            attribute1: attribute triples of AMR 1 (attribute name, node name, attribute value)
            relation1: relation triples of AMR 1 (relation name, node 1 name, node 2 name)
            instance2: instance triples of AMR 2 ("instance", node name, node value)
            attribute2: attribute triples of AMR 2 (attribute name, node name, attribute value)
            relation2: relation triples of AMR 2 (relation name, node 1 name, node 2 name)
            prefix1: prefix label for AMR 1
            prefix2: prefix label for AMR 2
        Returns:
            best_match: the node mapping that results in the highest triple matching number
            best_match_num: the highest triple matching number

        """
        # Compute candidate pool - all possible node match candidates.
        # In the hill-climbing, we only consider candidate in this pool to save computing time.
        # weight_dict is a dictionary that maps a pair of node
        (candidate_mappings, weight_dict) = self.compute_pool(instance1, attribute1, relation1,
                                                         instance2, attribute2, relation2,
                                                         prefix1, prefix2, doinstance=doinstance, doattribute=doattribute,
                                                         dorelation=dorelation)
        if self.veryVerbose:
            print("Candidate mappings:", file=self.DEBUG_LOG)
            print(candidate_mappings, file=self.DEBUG_LOG)
            print("Weight dictionary", file=self.DEBUG_LOG)
            print(weight_dict, file=self.DEBUG_LOG)

        best_match_num = 0
        # initialize best match mapping
        # the ith entry is the node index in AMR 2 which maps to the ith node in AMR 1
        best_mapping = [-1] * len(instance1)
        for i in range(self.iteration_num):
            if self.veryVerbose:
                print("Iteration", i, file=self.DEBUG_LOG)
            if i == 0:
                # smart initialization used for the first round
                cur_mapping = self.smart_init_mapping(candidate_mappings, instance1, instance2)
            else:
                # random initialization for the other round
                cur_mapping = self.random_init_mapping(candidate_mappings)
            # compute current triple match number
            match_num = self.compute_match(cur_mapping, weight_dict)
            if self.veryVerbose:
                print("Node mapping at start", cur_mapping, file=self.DEBUG_LOG)
                print("Triple match number at start:", match_num, file=self.DEBUG_LOG)
            while True:
                # get best gain
                (gain, new_mapping) = self.get_best_gain(cur_mapping, candidate_mappings, weight_dict,
                                                    len(instance2), match_num)
                if self.veryVerbose:
                    print("Gain after the hill-climbing", gain, file=self.DEBUG_LOG)
                # hill-climbing until there will be no gain for new node mapping
                if gain <= 0:
                    break
                # otherwise update match_num and mapping
                match_num += gain
                cur_mapping = new_mapping[:]
                if self.veryVerbose:
                    print("Update triple match number to:", match_num, file=self.DEBUG_LOG)
                    print("Current mapping:", cur_mapping, file=self.DEBUG_LOG)
            if match_num > best_match_num:
                best_mapping = cur_mapping[:]
                best_match_num = match_num
        return best_mapping, best_match_num


    def normalize(self, item):
        """
        lowercase and remove quote signifiers from items that are about to be compared
        """
        return item.lower().rstrip('_')


    def compute_pool(self, instance1, attribute1, relation1,
                     instance2, attribute2, relation2,
                     prefix1, prefix2, doinstance=True, doattribute=True, dorelation=True):
        """
        compute all possible node mapping candidates and their weights (the triple matching number gain resulting from
        mapping one node in AMR 1 to another node in AMR2)

        Arguments:
            instance1: instance triples of AMR 1
            attribute1: attribute triples of AMR 1 (attribute name, node name, attribute value)
            relation1: relation triples of AMR 1 (relation name, node 1 name, node 2 name)
            instance2: instance triples of AMR 2
            attribute2: attribute triples of AMR 2 (attribute name, node name, attribute value)
            relation2: relation triples of AMR 2 (relation name, node 1 name, node 2 name
            prefix1: prefix label for AMR 1
            prefix2: prefix label for AMR 2
        Returns:
          candidate_mapping: a list of candidate nodes.
                           The ith element contains the node indices (in AMR 2) the ith node (in AMR 1) can map to.
                           (resulting in non-zero triple match)
          weight_dict: a dictionary which contains the matching triple number for every pair of node mapping. The key
                       is a node pair. The value is another dictionary. key {-1} is triple match resulting from this node
                       pair alone (instance triples and attribute triples), and other keys are node pairs that can result
                       in relation triple match together with the first node pair.


        """
        candidate_mapping = []
        weight_dict = {}
        for instance1_item in instance1:
            # each candidate mapping is a set of node indices
            candidate_mapping.append(set())
            if doinstance:
                for instance2_item in instance2:
                    # if both triples are instance triples and have the same value
                    if self.normalize(instance1_item[0]) == self.normalize(instance2_item[0]) and \
                            self.normalize(instance1_item[2]) == self.normalize(instance2_item[2]):
                        # get node index by stripping the prefix
                        node1_index = int(instance1_item[1][len(prefix1):])
                        node2_index = int(instance2_item[1][len(prefix2):])
                        candidate_mapping[node1_index].add(node2_index)
                        node_pair = (node1_index, node2_index)
                        # use -1 as key in weight_dict for instance triples and attribute triples
                        if node_pair in weight_dict:
                            weight_dict[node_pair][-1] += 1
                        else:
                            weight_dict[node_pair] = {}
                            weight_dict[node_pair][-1] = 1
        if doattribute:
            for attribute1_item in attribute1:
                for attribute2_item in attribute2:
                    # if both attribute relation triple have the same relation name and value
                    if self.normalize(attribute1_item[0]) == self.normalize(attribute2_item[0]) \
                            and self.normalize(attribute1_item[2]) == self.normalize(attribute2_item[2]):
                        node1_index = int(attribute1_item[1][len(prefix1):])
                        node2_index = int(attribute2_item[1][len(prefix2):])
                        candidate_mapping[node1_index].add(node2_index)
                        node_pair = (node1_index, node2_index)
                        # use -1 as key in weight_dict for instance triples and attribute triples
                        if node_pair in weight_dict:
                            weight_dict[node_pair][-1] += 1
                        else:
                            weight_dict[node_pair] = {}
                            weight_dict[node_pair][-1] = 1
        if dorelation:
            for relation1_item in relation1:
                for relation2_item in relation2:
                    # if both relation share the same name
                    if self.normalize(relation1_item[0]) == self.normalize(relation2_item[0]):
                        node1_index_amr1 = int(relation1_item[1][len(prefix1):])
                        node1_index_amr2 = int(relation2_item[1][len(prefix2):])
                        node2_index_amr1 = int(relation1_item[2][len(prefix1):])
                        node2_index_amr2 = int(relation2_item[2][len(prefix2):])
                        # add mapping between two nodes
                        candidate_mapping[node1_index_amr1].add(node1_index_amr2)
                        candidate_mapping[node2_index_amr1].add(node2_index_amr2)
                        node_pair1 = (node1_index_amr1, node1_index_amr2)
                        node_pair2 = (node2_index_amr1, node2_index_amr2)
                        if node_pair2 != node_pair1:
                            # update weight_dict weight. Note that we need to update both entries for future search
                            # i.e weight_dict[node_pair1][node_pair2]
                            #     weight_dict[node_pair2][node_pair1]
                            if node1_index_amr1 > node2_index_amr1:
                                # swap node_pair1 and node_pair2
                                node_pair1 = (node2_index_amr1, node2_index_amr2)
                                node_pair2 = (node1_index_amr1, node1_index_amr2)
                            if node_pair1 in weight_dict:
                                if node_pair2 in weight_dict[node_pair1]:
                                    weight_dict[node_pair1][node_pair2] += 1
                                else:
                                    weight_dict[node_pair1][node_pair2] = 1
                            else:
                                weight_dict[node_pair1] = {-1: 0, node_pair2: 1}
                            if node_pair2 in weight_dict:
                                if node_pair1 in weight_dict[node_pair2]:
                                    weight_dict[node_pair2][node_pair1] += 1
                                else:
                                    weight_dict[node_pair2][node_pair1] = 1
                            else:
                                weight_dict[node_pair2] = {-1: 0, node_pair1: 1}
                        else:
                            # two node pairs are the same. So we only update weight_dict once.
                            # this generally should not happen.
                            if node_pair1 in weight_dict:
                                weight_dict[node_pair1][-1] += 1
                            else:
                                weight_dict[node_pair1] = {-1: 1}
        return candidate_mapping, weight_dict


    def smart_init_mapping(self, candidate_mapping, instance1, instance2):
        """
        Initialize mapping based on the concept mapping (smart initialization)
        Arguments:
            candidate_mapping: candidate node match list
            instance1: instance triples of AMR 1
            instance2: instance triples of AMR 2
        Returns:
            initialized node mapping between two AMRs

        """
        random.seed()
        matched_dict = {}
        result = []
        # list to store node indices that have no concept match
        no_word_match = []
        for i, candidates in enumerate(candidate_mapping):
            if not candidates:
                # no possible mapping
                result.append(-1)
                continue
            # node value in instance triples of AMR 1
            value1 = instance1[i][2]
            for node_index in candidates:
                value2 = instance2[node_index][2]
                # find the first instance triple match in the candidates
                # instance triple match is having the same concept value
                if value1 == value2:
                    if node_index not in matched_dict:
                        result.append(node_index)
                        matched_dict[node_index] = 1
                        break
            if len(result) == i:
                no_word_match.append(i)
                result.append(-1)
        # if no concept match, generate a random mapping
        for i in no_word_match:
            candidates = list(candidate_mapping[i])
            while candidates:
                # get a random node index from candidates
                rid = random.randint(0, len(candidates) - 1)
                candidate = candidates[rid]
                if candidate in matched_dict:
                    candidates.pop(rid)
                else:
                    matched_dict[candidate] = 1
                    result[i] = candidate
                    break
        return result


    def random_init_mapping(self, candidate_mapping):
        """
        Generate a random node mapping.
        Args:
            candidate_mapping: candidate_mapping: candidate node match list
        Returns:
            randomly-generated node mapping between two AMRs

        """
        # if needed, a fixed seed could be passed here to generate same random (to help debugging)
        random.seed()
        matched_dict = {}
        result = []
        for c in candidate_mapping:
            candidates = list(c)
            if not candidates:
                # -1 indicates no possible mapping
                result.append(-1)
                continue
            found = False
            while candidates:
                # randomly generate an index in [0, length of candidates)
                rid = random.randint(0, len(candidates) - 1)
                candidate = candidates[rid]
                # check if it has already been matched
                if candidate in matched_dict:
                    candidates.pop(rid)
                else:
                    matched_dict[candidate] = 1
                    result.append(candidate)
                    found = True
                    break
            if not found:
                result.append(-1)
        return result


    def compute_match(self, mapping, weight_dict):
        """
        Given a node mapping, compute match number based on weight_dict.
        Args:
        mappings: a list of node index in AMR 2. The ith element (value j) means node i in AMR 1 maps to node j in AMR 2.
        Returns:
        matching triple number
        Complexity: O(m*n) , m is the node number of AMR 1, n is the node number of AMR 2

        """
        # If this mapping has been investigated before, retrieve the value instead of re-computing.
        if self.veryVerbose:
            print("Computing match for mapping", file=self.DEBUG_LOG)
            print(mapping, file=self.DEBUG_LOG)
        if tuple(mapping) in self.match_triple_dict:
            if self.veryVerbose:
                print("saved value", self.match_triple_dict[tuple(mapping)], file=self.DEBUG_LOG)
            return self.match_triple_dict[tuple(mapping)]
        match_num = 0
        # i is node index in AMR 1, m is node index in AMR 2
        for i, m in enumerate(mapping):
            if m == -1:
                # no node maps to this node
                continue
            # node i in AMR 1 maps to node m in AMR 2
            current_node_pair = (i, m)
            if current_node_pair not in weight_dict:
                continue
            if self.veryVerbose:
                print("node_pair", current_node_pair, file=self.DEBUG_LOG)
            for key in weight_dict[current_node_pair]:
                if key == -1:
                    # matching triple resulting from instance/attribute triples
                    match_num += weight_dict[current_node_pair][key]
                    if self.veryVerbose:
                        print("instance/attribute match", weight_dict[current_node_pair][key], file=self.DEBUG_LOG)
                # only consider node index larger than i to avoid duplicates
                # as we store both weight_dict[node_pair1][node_pair2] and
                #     weight_dict[node_pair2][node_pair1] for a relation
                elif key[0] < i:
                    continue
                elif mapping[key[0]] == key[1]:
                    match_num += weight_dict[current_node_pair][key]
                    if self.veryVerbose:
                        print("relation match with", key, weight_dict[current_node_pair][key], file=self.DEBUG_LOG)
        if self.veryVerbose:
            print("match computing complete, result:", match_num, file=self.DEBUG_LOG)
        # update match_triple_dict
        self.match_triple_dict[tuple(mapping)] = match_num
        return match_num


    def move_gain(self, mapping, node_id, old_id, new_id, weight_dict, match_num):
        """
        Compute the triple match number gain from the move operation
        Arguments:
            mapping: current node mapping
            node_id: remapped node in AMR 1
            old_id: original node id in AMR 2 to which node_id is mapped
            new_id: new node in to which node_id is mapped
            weight_dict: weight dictionary
            match_num: the original triple matching number
        Returns:
            the triple match gain number (might be negative)

        """
        # new node mapping after moving
        new_mapping = (node_id, new_id)
        # node mapping before moving
        old_mapping = (node_id, old_id)
        # new nodes mapping list (all node pairs)
        new_mapping_list = mapping[:]
        new_mapping_list[node_id] = new_id
        # if this mapping is already been investigated, use saved one to avoid duplicate computing
        if tuple(new_mapping_list) in self.match_triple_dict:
            return self.match_triple_dict[tuple(new_mapping_list)] - match_num
        gain = 0
        # add the triple match incurred by new_mapping to gain
        if new_mapping in weight_dict:
            for key in weight_dict[new_mapping]:
                if key == -1:
                    # instance/attribute triple match
                    gain += weight_dict[new_mapping][-1]
                elif new_mapping_list[key[0]] == key[1]:
                    # relation gain incurred by new_mapping and another node pair in new_mapping_list
                    gain += weight_dict[new_mapping][key]
        # deduct the triple match incurred by old_mapping from gain
        if old_mapping in weight_dict:
            for k in weight_dict[old_mapping]:
                if k == -1:
                    gain -= weight_dict[old_mapping][-1]
                elif mapping[k[0]] == k[1]:
                    gain -= weight_dict[old_mapping][k]
        # update match number dictionary
        self.match_triple_dict[tuple(new_mapping_list)] = match_num + gain
        return gain


    def swap_gain(self, mapping, node_id1, mapping_id1, node_id2, mapping_id2, weight_dict, match_num):
        """
        Compute the triple match number gain from the swapping
        Arguments:
        mapping: current node mapping list
        node_id1: node 1 index in AMR 1
        mapping_id1: the node index in AMR 2 node 1 maps to (in the current mapping)
        node_id2: node 2 index in AMR 1
        mapping_id2: the node index in AMR 2 node 2 maps to (in the current mapping)
        weight_dict: weight dictionary
        match_num: the original matching triple number
        Returns:
        the gain number (might be negative)

        """
        new_mapping_list = mapping[:]
        # Before swapping, node_id1 maps to mapping_id1, and node_id2 maps to mapping_id2
        # After swapping, node_id1 maps to mapping_id2 and node_id2 maps to mapping_id1
        new_mapping_list[node_id1] = mapping_id2
        new_mapping_list[node_id2] = mapping_id1
        if tuple(new_mapping_list) in self.match_triple_dict:
            return self.match_triple_dict[tuple(new_mapping_list)] - match_num
        gain = 0
        new_mapping1 = (node_id1, mapping_id2)
        new_mapping2 = (node_id2, mapping_id1)
        old_mapping1 = (node_id1, mapping_id1)
        old_mapping2 = (node_id2, mapping_id2)
        if node_id1 > node_id2:
            new_mapping2 = (node_id1, mapping_id2)
            new_mapping1 = (node_id2, mapping_id1)
            old_mapping1 = (node_id2, mapping_id2)
            old_mapping2 = (node_id1, mapping_id1)
        if new_mapping1 in weight_dict:
            for key in weight_dict[new_mapping1]:
                if key == -1:
                    gain += weight_dict[new_mapping1][-1]
                elif new_mapping_list[key[0]] == key[1]:
                    gain += weight_dict[new_mapping1][key]
        if new_mapping2 in weight_dict:
            for key in weight_dict[new_mapping2]:
                if key == -1:
                    gain += weight_dict[new_mapping2][-1]
                # to avoid duplicate
                elif key[0] == node_id1:
                    continue
                elif new_mapping_list[key[0]] == key[1]:
                    gain += weight_dict[new_mapping2][key]
        if old_mapping1 in weight_dict:
            for key in weight_dict[old_mapping1]:
                if key == -1:
                    gain -= weight_dict[old_mapping1][-1]
                elif mapping[key[0]] == key[1]:
                    gain -= weight_dict[old_mapping1][key]
        if old_mapping2 in weight_dict:
            for key in weight_dict[old_mapping2]:
                if key == -1:
                    gain -= weight_dict[old_mapping2][-1]
                # to avoid duplicate
                elif key[0] == node_id1:
                    continue
                elif mapping[key[0]] == key[1]:
                    gain -= weight_dict[old_mapping2][key]
        self.match_triple_dict[tuple(new_mapping_list)] = match_num + gain
        return gain


    def get_best_gain(self, mapping, candidate_mappings, weight_dict, instance_len, cur_match_num):
        """
        Hill-climbing method to return the best gain swap/move can get
        Arguments:
        mapping: current node mapping
        candidate_mappings: the candidates mapping list
        weight_dict: the weight dictionary
        instance_len: the number of the nodes in AMR 2
        cur_match_num: current triple match number
        Returns:
        the best gain we can get via swap/move operation

        """
        largest_gain = 0
        # True: using swap; False: using move
        use_swap = True
        # the node to be moved/swapped
        node1 = None
        # store the other node affected. In swap, this other node is the node swapping with node1. In move, this other
        # node is the node node1 will move to.
        node2 = None
        # unmatched nodes in AMR 2
        unmatched = set(range(instance_len))
        # exclude nodes in current mapping
        # get unmatched nodes
        for nid in mapping:
            if nid in unmatched:
                unmatched.remove(nid)
        for i, nid in enumerate(mapping):
            # current node i in AMR 1 maps to node nid in AMR 2
            for nm in unmatched:
                if nm in candidate_mappings[i]:
                    # remap i to another unmatched node (move)
                    # (i, m) -> (i, nm)
                    if self.veryVerbose:
                        print("Remap node", i, "from ", nid, "to", nm, file=self.DEBUG_LOG)
                    mv_gain = self.move_gain(mapping, i, nid, nm, weight_dict, cur_match_num)
                    if self.veryVerbose:
                        print("Move gain:", mv_gain, file=self.DEBUG_LOG)
                        new_mapping = mapping[:]
                        new_mapping[i] = nm
                        new_match_num = self.compute_match(new_mapping, weight_dict)
                        if new_match_num != cur_match_num + mv_gain:
                            print(mapping, new_mapping, file=self.ERROR_LOG)
                            print("Inconsistency in computing: move gain", cur_match_num, mv_gain, new_match_num,
                                  file=self.ERROR_LOG)
                    if mv_gain > largest_gain:
                        largest_gain = mv_gain
                        node1 = i
                        node2 = nm
                        use_swap = False
        # compute swap gain
        for i, m in enumerate(mapping):
            for j in range(i + 1, len(mapping)):
                m2 = mapping[j]
                # swap operation (i, m) (j, m2) -> (i, m2) (j, m)
                # j starts from i+1, to avoid duplicate swap
                if self.veryVerbose:
                    print("Swap node", i, "and", j, file=self.DEBUG_LOG)
                    print("Before swapping:", i, "-", m, ",", j, "-", m2, file=self.DEBUG_LOG)
                    print(mapping, file=self.DEBUG_LOG)
                    print("After swapping:", i, "-", m2, ",", j, "-", m, file=self.DEBUG_LOG)
                sw_gain = self.swap_gain(mapping, i, m, j, m2, weight_dict, cur_match_num)
                if self.veryVerbose:
                    print("Swap gain:", sw_gain, file=self.DEBUG_LOG)
                    new_mapping = mapping[:]
                    new_mapping[i] = m2
                    new_mapping[j] = m
                    print(new_mapping, file=self.DEBUG_LOG)
                    new_match_num = self.compute_match(new_mapping, weight_dict)
                    if new_match_num != cur_match_num + sw_gain:
                        print(mapping, new_mapping, file=self.ERROR_LOG)
                        print("Inconsistency in computing: swap gain", cur_match_num, sw_gain, new_match_num,
                              file=self.ERROR_LOG)
                if sw_gain > largest_gain:
                    largest_gain = sw_gain
                    node1 = i
                    node2 = j
                    use_swap = True
        # generate a new mapping based on swap/move
        cur_mapping = mapping[:]
        if node1 is not None:
            if use_swap:
                if self.veryVerbose:
                    print("Use swap gain", file=self.DEBUG_LOG)
                temp = cur_mapping[node1]
                cur_mapping[node1] = cur_mapping[node2]
                cur_mapping[node2] = temp
            else:
                if self.veryVerbose:
                    print("Use move gain", file=self.DEBUG_LOG)
                cur_mapping[node1] = node2
        else:
            if self.veryVerbose:
                print("no move/swap gain found", file=self.DEBUG_LOG)
        if self.veryVerbose:
            print("Original mapping", mapping, file=self.DEBUG_LOG)
            print("Current mapping", cur_mapping, file=self.DEBUG_LOG)
        return largest_gain, cur_mapping


    def print_alignment(self, mapping, instance1, instance2):
        """
        print the alignment based on a node mapping
        Args:
            mapping: current node mapping list
            instance1: nodes of AMR 1
            instance2: nodes of AMR 2

        """
        result = []
        for instance1_item, m in zip(instance1, mapping):
            r = instance1_item[1] + "(" + instance1_item[2] + ")"
            if m == -1:
                r += "-Null"
            else:
                instance2_item = instance2[m]
                r += "-" + instance2_item[1] + "(" + instance2_item[2] + ")"
            result.append(r)
        return " ".join(result)


    def compute_f(self, match_num, test_num, gold_num):
        """
        Compute the f-score based on the matching triple number,
                                     triple number of AMR set 1,
                                     triple number of AMR set 2
        Args:
            match_num: matching triple number
            test_num:  triple number of AMR 1 (test file)
            gold_num:  triple number of AMR 2 (gold file)
        Returns:
            precision: match_num/test_num
            recall: match_num/gold_num
            f_score: 2*precision*recall/(precision+recall)
        """
        if test_num == 0 or gold_num == 0:
            return 0.00, 0.00, 0.00
        precision = float(match_num) / float(test_num)
        recall = float(match_num) / float(gold_num)
        if (precision + recall) != 0:
            f_score = 2 * precision * recall / (precision + recall)
            if self.veryVerbose:
                print("F-score:", f_score, file=self.DEBUG_LOG)
            return precision, recall, f_score
        else:
            if self.veryVerbose:
                print("F-score:", "0.0", file=self.DEBUG_LOG)
            return precision, recall, 0.00


    def generate_amr_lines(self, f1, f2):
        """
        Read one AMR line at a time from each file handle
        :param f1: file handle (or any iterable of strings) to read AMR 1 lines from
        :param f2: file handle (or any iterable of strings) to read AMR 2 lines from
        :return: generator of cur_amr1, cur_amr2 pairs: one-line AMR strings
        """
        while True:
            cur_amr1 = SMATCH_AMR.get_amr_line(f1)
            cur_amr2 = SMATCH_AMR.get_amr_line(f2)
            if not cur_amr1 and not cur_amr2:
                pass
            elif not cur_amr1:
                print("Error: File 1 has less AMRs than file 2", file=self.ERROR_LOG)
                print("Ignoring remaining AMRs", file=self.ERROR_LOG)
            elif not cur_amr2:
                print("Error: File 2 has less AMRs than file 1", file=self.ERROR_LOG)
                print("Ignoring remaining AMRs", file=self.ERROR_LOG)
            else:
                yield cur_amr1, cur_amr2
                continue
            break


    def get_amr_match(self, cur_amr1, cur_amr2, sent_num=1, justinstance=False, justattribute=False, justrelation=False):
        amr_pair = []
        for i, cur_amr in (1, cur_amr1), (2, cur_amr2):
            try:
                amr_pair.append(SMATCH_AMR.parse_AMR_line(cur_amr))
            except Exception as e:
                print("Error in parsing amr %d: %s" % (i, cur_amr), file=self.ERROR_LOG)
                print("Please check if the AMR is ill-formatted. Ignoring remaining AMRs", file=self.ERROR_LOG)
                print("Error message: %s" % e, file=self.ERROR_LOG)
        amr1, amr2 = amr_pair
        prefix1 = "a"
        prefix2 = "b"
        # Rename node to "a1", "a2", .etc
        amr1.rename_node(prefix1)
        # Renaming node to "b1", "b2", .etc
        amr2.rename_node(prefix2)
        (instance1, attributes1, relation1) = amr1.get_triples()
        (instance2, attributes2, relation2) = amr2.get_triples()
        if self.verbose:
            print("AMR pair", sent_num, file=self.DEBUG_LOG)
            print("============================================", file=self.DEBUG_LOG)
            print("AMR 1 (one-line):", cur_amr1, file=self.DEBUG_LOG)
            print("AMR 2 (one-line):", cur_amr2, file=self.DEBUG_LOG)
            print("Instance triples of AMR 1:", len(instance1), file=self.DEBUG_LOG)
            print(instance1, file=self.DEBUG_LOG)
            print("Attribute triples of AMR 1:", len(attributes1), file=self.DEBUG_LOG)
            print(attributes1, file=self.DEBUG_LOG)
            print("Relation triples of AMR 1:", len(relation1), file=self.DEBUG_LOG)
            print(relation1, file=self.DEBUG_LOG)
            print("Instance triples of AMR 2:", len(instance2), file=self.DEBUG_LOG)
            print(instance2, file=self.DEBUG_LOG)
            print("Attribute triples of AMR 2:", len(attributes2), file=self.DEBUG_LOG)
            print(attributes2, file=self.DEBUG_LOG)
            print("Relation triples of AMR 2:", len(relation2), file=self.DEBUG_LOG)
            print(relation2, file=self.DEBUG_LOG)
        # optionally turn off some of the node comparison
        doinstance = doattribute = dorelation = True
        if justinstance:
            doattribute = dorelation = False
        if justattribute:
            doinstance = dorelation = False
        if justrelation:
            doinstance = doattribute = False
        (best_mapping, best_match_num) = self.get_best_match(instance1, attributes1, relation1,
                                                        instance2, attributes2, relation2,
                                                        prefix1, prefix2, doinstance=doinstance,
                                                        doattribute=doattribute, dorelation=dorelation)
        if self.verbose:
            print("best match number", best_match_num, file=self.DEBUG_LOG)
            print("best node mapping", best_mapping, file=self.DEBUG_LOG)
            print("Best node mapping alignment:", self.print_alignment(best_mapping, instance1, instance2), file=self.DEBUG_LOG)
        if justinstance:
            test_triple_num = len(instance1)
            gold_triple_num = len(instance2)
        elif justattribute:
            test_triple_num = len(attributes1)
            gold_triple_num = len(attributes2)
        elif justrelation:
            test_triple_num = len(relation1)
            gold_triple_num = len(relation2)
        else:
            test_triple_num = len(instance1) + len(attributes1) + len(relation1)
            gold_triple_num = len(instance2) + len(attributes2) + len(relation2)
        return best_match_num, test_triple_num, gold_triple_num


    def score_amr_pairs(self, f1, f2, justinstance=False, justattribute=False, justrelation=False):
        """
        Score one pair of AMR lines at a time from each file handle
        :param f1: file handle (or any iterable of strings) to read AMR 1 lines from
        :param f2: file handle (or any iterable of strings) to read AMR 2 lines from
        :param justinstance: just pay attention to matching instances
        :param justattribute: just pay attention to matching attributes
        :param justrelation: just pay attention to matching relations
        :return: generator of cur_amr1, cur_amr2 pairs: one-line AMR strings
        """
        # matching triple number, triple number in test file, triple number in gold file
        total_match_num = total_test_num = total_gold_num = 0
        # Read amr pairs from two files
        for sent_num, (cur_amr1, cur_amr2) in enumerate(self.generate_amr_lines(f1, f2), start=1):
            best_match_num, test_triple_num, gold_triple_num = self.get_amr_match(cur_amr1, cur_amr2,
                                                                             sent_num=sent_num,  # sentence number
                                                                             justinstance=justinstance,
                                                                             justattribute=justattribute,
                                                                             justrelation=justrelation)
            total_match_num += best_match_num
            total_test_num += test_triple_num
            total_gold_num += gold_triple_num
            # clear the matching triple dictionary for the next AMR pair
            self.match_triple_dict.clear()
            if not self.single_score:  # if each AMR pair should have a score, compute and output it here
                yield self.compute_f(best_match_num, test_triple_num, gold_triple_num)
        if self.verbose:
            print("Total match number, total triple number in AMR 1, and total triple number in AMR 2:", file=self.DEBUG_LOG)
            print(total_match_num, total_test_num, total_gold_num, file=self.DEBUG_LOG)
            print("---------------------------------------------------------------------------------", file=self.DEBUG_LOG)
        if self.single_score:  # output document-level smatch score (a single f-score for all AMR pairs in two files)
            yield self.compute_f(total_match_num, total_test_num, total_gold_num)


class SMATCH_AMR:
    """
        AMR is a rooted, labeled graph to represent semantics.
        This class has the following members:
        nodes: list of node in the graph. Its ith element is the name of the ith node. For example, a node name
               could be "a1", "b", "g2", .etc
        node_values: list of node labels (values) of the graph. Its ith element is the value associated with node i in
                     nodes list. In AMR, such value is usually a semantic concept (e.g. "boy", "want-01")
        root: root node name
        relations: list of edges connecting two nodes in the graph. Each entry is a link between two nodes, i.e. a triple
                   <relation name, node1 name, node 2 name>. In AMR, such link denotes the relation between two semantic
                   concepts. For example, "arg0" means that one of the concepts is the 0th argument of the other.
        attributes: list of edges connecting a node to an attribute name and its value. For example, if the polarity of
                   some node is negative, there should be an edge connecting this node and "-". A triple < attribute name,
                   node name, attribute value> is used to represent such attribute. It can also be viewed as a relation.
        """

    ERROR_LOG = sys.stderr
    DEBUG_LOG = sys.stderr

    def __init__(self, node_list=None, node_value_list=None, relation_list=None, attribute_list=None):
        """
        node_list: names of nodes in AMR graph, e.g. "a11", "n"
        node_value_list: values of nodes in AMR graph, e.g. "group" for a node named "g"
        relation_list: list of relations between two nodes
        attribute_list: list of attributes (links between one node and one constant value)
        """
        # initialize AMR graph nodes using list of nodes name
        # root, by default, is the first in var_list

        if node_list is None:
            self.nodes = []
            self.root = None
        else:
            self.nodes = node_list[:]
            if len(node_list) != 0:
                self.root = node_list[0]
            else:
                self.root = None
        if node_value_list is None:
            self.node_values = []
        else:
            self.node_values = node_value_list[:]
        if relation_list is None:
            self.relations = []
        else:
            self.relations = relation_list[:]
        if attribute_list is None:
            self.attributes = []
        else:
            self.attributes = attribute_list[:]

    def rename_node(self, prefix):
        """
        Rename AMR graph nodes to prefix + node_index to avoid nodes with the same name in two different AMRs.
        """
        node_map_dict = {}
        # map each node to its new name (e.g. "a1")
        for i in range(0, len(self.nodes)):
            node_map_dict[self.nodes[i]] = prefix + str(i)
        # update node name
        for i, v in enumerate(self.nodes):
            self.nodes[i] = node_map_dict[v]
        # update node name in relations
        for node_relations in self.relations:
            for i, l in enumerate(node_relations):
                node_relations[i][1] = node_map_dict[l[1]]

    def get_triples(self):
        """
        Get the triples in three lists.
        instance_triple: a triple representing an instance. E.g. instance(w, want-01)
        attribute triple: relation of attributes, e.g. polarity(w, - )
        and relation triple, e.g. arg0 (w, b)
        """
        instance_triple = []
        relation_triple = []
        attribute_triple = []
        for i in range(len(self.nodes)):
            instance_triple.append(("instance", self.nodes[i], self.node_values[i]))
            # l[0] is relation name
            # l[1] is the other node this node has relation with
            for l in self.relations[i]:
                relation_triple.append((l[0], self.nodes[i], l[1]))
            # l[0] is the attribute name
            # l[1] is the attribute value
            for l in self.attributes[i]:
                attribute_triple.append((l[0], self.nodes[i], l[1]))
        return instance_triple, attribute_triple, relation_triple

    def get_triples2(self):
        """
        Get the triples in two lists:
        instance_triple: a triple representing an instance. E.g. instance(w, want-01)
        relation_triple: a triple representing all relations. E.g arg0 (w, b) or E.g. polarity(w, - )
        Note that we do not differentiate between attribute triple and relation triple. Both are considered as relation
        triples.
        All triples are represented by (triple_type, argument 1 of the triple, argument 2 of the triple)
        """
        instance_triple = []
        relation_triple = []
        for i in range(len(self.nodes)):
            # an instance triple is instance(node name, node value).
            # For example, instance(b, boy).
            instance_triple.append(("instance", self.nodes[i], self.node_values[i]))
            # l[0] is relation name
            # l[1] is the other node this node has relation with
            for l in self.relations[i]:
                relation_triple.append((l[0], self.nodes[i], l[1]))
            # l[0] is the attribute name
            # l[1] is the attribute value
            for l in self.attributes[i]:
                relation_triple.append((l[0], self.nodes[i], l[1]))
        return instance_triple, relation_triple

    def __str__(self):
        """
        Generate AMR string for better readability
        """
        lines = []
        for i in range(len(self.nodes)):
            lines.append("Node " + str(i) + " " + self.nodes[i])
            lines.append("Value: " + self.node_values[i])
            lines.append("Relations:")
            for relation in self.relations[i]:
                lines.append("Node " + relation[1] + " via " + relation[0])
            for attribute in self.attributes[i]:
                lines.append("Attribute: " + attribute[0] + " value " + attribute[1])
        return "\n".join(lines)

    def __repr__(self):
        return self.__str__()

    def output_amr(self):
        """
        Output AMR string
        """
        print(self.__str__(), file=self.DEBUG_LOG)

    @staticmethod
    def get_amr_line(input_f):
        """
        Read the file containing AMRs. AMRs are separated by a blank line.
        Each call of get_amr_line() returns the next available AMR (in one-line form).
        Note: this function does not verify if the AMR is valid
        """
        cur_amr = []
        has_content = False
        for line in input_f:
            line = line.strip()
            if line == "":
                if not has_content:
                    # empty lines before current AMR
                    continue
                else:
                    # end of current AMR
                    break
            if line.strip().startswith("#"):
                # ignore the comment line (starting with "#") in the AMR file
                continue
            else:
                has_content = True
                cur_amr.append(line.strip())
        return "".join(cur_amr)

    @staticmethod
    def parse_AMR_line(line):
        """
        Parse a AMR from line representation to an AMR object.
        This parsing algorithm scans the line once and process each character, in a shift-reduce style.
        """
        # Current state. It denotes the last significant symbol encountered. 1 for (, 2 for :, 3 for /,
        # and 0 for start state or ')'
        # Last significant symbol is ( --- start processing node name
        # Last significant symbol is : --- start processing relation name
        # Last significant symbol is / --- start processing node value (concept name)
        # Last significant symbol is ) --- current node processing is complete
        # Note that if these symbols are inside parenthesis, they are not significant symbols.

        exceptions = set(["prep-on-behalf-of", "prep-out-of", "consist-of"])

        def update_triple(node_relation_dict, u, r, v):
            # we detect a relation (r) between u and v, with direction u to v.
            # in most cases, if relation name ends with "-of", e.g."arg0-of",
            # it is reverse of some relation. For example, if a is "arg0-of" b,
            # we can also say b is "arg0" a.
            # If the relation name ends with "-of", we store the reverse relation.
            # but note some exceptions like "prep-on-behalf-of" and "prep-out-of"
            # also note relation "mod" is the reverse of "domain"
            if r.endswith("-of") and not r in exceptions:
                node_relation_dict[v].append((r[:-3], u))
            elif r == "mod":
                node_relation_dict[v].append(("domain", u))
            else:
                node_relation_dict[u].append((r, v))

        state = 0
        # node stack for parsing
        stack = []
        # current not-yet-reduced character sequence
        cur_charseq = []
        # key: node name value: node value
        node_dict = {}
        # node name list (order: occurrence of the node)
        node_name_list = []
        # key: node name:  value: list of (relation name, the other node name)
        node_relation_dict1 = defaultdict(list)
        # key: node name, value: list of (attribute name, const value) or (relation name, unseen node name)
        node_relation_dict2 = defaultdict(list)
        # current relation name
        cur_relation_name = ""
        # having unmatched quote string
        in_quote = False
        for i, c in enumerate(line.strip()):
            if c == " ":
                # allow space in relation name
                if state == 2:
                    cur_charseq.append(c)
                continue
            if c == "\"":
                # flip in_quote value when a quote symbol is encountered
                # insert placeholder if in_quote from last symbol
                if in_quote:
                    cur_charseq.append('_')
                in_quote = not in_quote
            elif c == "(":
                # not significant symbol if inside quote
                if in_quote:
                    cur_charseq.append(c)
                    continue
                # get the attribute name
                # e.g :arg0 (x ...
                # at this point we get "arg0"
                if state == 2:
                    # in this state, current relation name should be empty
                    if cur_relation_name != "":
                        print("Format error when processing ", line[0:i + 1], file=SMATCH_AMR.ERROR_LOG)
                        return None
                    # update current relation name for future use
                    cur_relation_name = "".join(cur_charseq).strip()
                    cur_charseq[:] = []
                state = 1
            elif c == ":":
                # not significant symbol if inside quote
                if in_quote:
                    cur_charseq.append(c)
                    continue
                # Last significant symbol is "/". Now we encounter ":"
                # Example:
                # :OR (o2 / *OR*
                #    :mod (o3 / official)
                #  gets node value "*OR*" at this point
                if state == 3:
                    node_value = "".join(cur_charseq)
                    # clear current char sequence
                    cur_charseq[:] = []
                    # pop node name ("o2" in the above example)
                    cur_node_name = stack[-1]
                    # update node name/value map
                    node_dict[cur_node_name] = node_value
                # Last significant symbol is ":". Now we encounter ":"
                # Example:
                # :op1 w :quant 30
                # or :day 14 :month 3
                # the problem is that we cannot decide if node value is attribute value (constant)
                # or node value (variable) at this moment
                elif state == 2:
                    temp_attr_value = "".join(cur_charseq)
                    cur_charseq[:] = []
                    parts = temp_attr_value.split()
                    if len(parts) < 2:
                        print("Error in processing; part len < 2", line[0:i + 1], file=SMATCH_AMR.ERROR_LOG)
                        return None
                    # For the above example, node name is "op1", and node value is "w"
                    # Note that this node name might not be encountered before
                    relation_name = parts[0].strip()
                    relation_value = parts[1].strip()
                    # We need to link upper level node to the current
                    # top of stack is upper level node
                    if len(stack) == 0:
                        print("Error in processing", line[:i], relation_name, relation_value, file=SMATCH_AMR.ERROR_LOG)
                        return None
                    # if we have not seen this node name before
                    if relation_value not in node_dict:
                        update_triple(node_relation_dict2, stack[-1], relation_name, relation_value)
                    else:
                        update_triple(node_relation_dict1, stack[-1], relation_name, relation_value)
                state = 2
            elif c == "/":
                if in_quote:
                    cur_charseq.append(c)
                    continue
                # Last significant symbol is "(". Now we encounter "/"
                # Example:
                # (d / default-01
                # get "d" here
                if state == 1:
                    node_name = "".join(cur_charseq)
                    cur_charseq[:] = []
                    # if this node name is already in node_dict, it is duplicate
                    if node_name in node_dict:
                        print("Duplicate node name ", node_name, " in parsing AMR", file=SMATCH_AMR.ERROR_LOG)
                        return None
                    # push the node name to stack
                    stack.append(node_name)
                    # add it to node name list
                    node_name_list.append(node_name)
                    # if this node is part of the relation
                    # Example:
                    # :arg1 (n / nation)
                    # cur_relation_name is arg1
                    # node name is n
                    # we have a relation arg1(upper level node, n)
                    if cur_relation_name != "":
                        update_triple(node_relation_dict1, stack[-2], cur_relation_name, node_name)
                        cur_relation_name = ""
                else:
                    # error if in other state
                    print("Error in parsing AMR", line[0:i + 1], file=SMATCH_AMR.ERROR_LOG)
                    return None
                state = 3
            elif c == ")":
                if in_quote:
                    cur_charseq.append(c)
                    continue
                # stack should be non-empty to find upper level node
                if len(stack) == 0:
                    print("Unmatched parenthesis at position", i, "in processing", line[0:i + 1], file=SMATCH_AMR.ERROR_LOG)
                    return None
                # Last significant symbol is ":". Now we encounter ")"
                # Example:
                # :op2 "Brown") or :op2 w)
                # get \"Brown\" or w here
                if state == 2:
                    temp_attr_value = "".join(cur_charseq)
                    cur_charseq[:] = []
                    parts = temp_attr_value.split()
                    if len(parts) < 2:
                        print("Error processing", line[:i + 1], temp_attr_value, file=SMATCH_AMR.ERROR_LOG)
                        return None
                    relation_name = parts[0].strip()
                    relation_value = parts[1].strip()
                    # attribute value not seen before
                    # Note that it might be a constant attribute value, or an unseen node
                    # process this after we have seen all the node names
                    if relation_value not in node_dict:
                        update_triple(node_relation_dict2, stack[-1], relation_name, relation_value)
                    else:
                        update_triple(node_relation_dict1, stack[-1], relation_name, relation_value)
                # Last significant symbol is "/". Now we encounter ")"
                # Example:
                # :arg1 (n / nation)
                # we get "nation" here
                elif state == 3:
                    node_value = "".join(cur_charseq)
                    cur_charseq[:] = []
                    cur_node_name = stack[-1]
                    # map node name to its value
                    node_dict[cur_node_name] = node_value
                # pop from stack, as the current node has been processed
                stack.pop()
                cur_relation_name = ""
                state = 0
            else:
                # not significant symbols, so we just shift.
                cur_charseq.append(c)
        # create data structures to initialize an AMR
        node_value_list = []
        relation_list = []
        attribute_list = []
        for v in node_name_list:
            if v not in node_dict:
                print("Error: Node name not found", v, file=SMATCH_AMR.ERROR_LOG)
                return None
            else:
                node_value_list.append(node_dict[v])
            # build relation list and attribute list for this node
            node_rel_list = []
            node_attr_list = []
            if v in node_relation_dict1:
                for v1 in node_relation_dict1[v]:
                    node_rel_list.append([v1[0], v1[1]])
            if v in node_relation_dict2:
                for v2 in node_relation_dict2[v]:
                    # if value is in quote, it is a constant value
                    # strip the quote and put it in attribute map
                    if v2[1][0] == "\"" and v2[1][-1] == "\"":
                        node_attr_list.append([[v2[0]], v2[1][1:-1]])
                    # if value is a node name
                    elif v2[1] in node_dict:
                        node_rel_list.append([v2[0], v2[1]])
                    else:
                        node_attr_list.append([v2[0], v2[1]])
            # each node has a relation list and attribute list
            relation_list.append(node_rel_list)
            attribute_list.append(node_attr_list)
        # add TOP as an attribute. The attribute value just needs to be constant
        attribute_list[0].append(["TOP", 'top'])
        result_amr = SMATCH_AMR(node_name_list, node_value_list, relation_list, attribute_list)
        return result_amr

    # def main(arguments):
    #     """
    #     Main function of smatch score calculation
    #     """
    #     global verbose
    #     global veryVerbose
    #     global self.iteration_num
    #     global single_score
    #     global pr_flag
    #     global match_triple_dict
    #     # set the iteration number
    #     # total iteration number = restart number + 1
    #     iteration_num = arguments.r + 1
    #     if arguments.ms:
    #         single_score = False
    #     if arguments.v:
    #         verbose = True
    #     if arguments.vv:
    #         veryVerbose = True
    #     if arguments.pr:
    #         pr_flag = True
    #     # significant digits to print out
    #     floatdisplay = "%%.%df" % arguments.significant
    #     for (precision, recall, best_f_score) in score_amr_pairs(args.f[0], args.f[1],
    #                                                              justinstance=arguments.justinstance,
    #                                                              justattribute=arguments.justattribute,
    #                                                              justrelation=arguments.justrelation):
    #         # print("Sentence", sent_num)
    #         if pr_flag:
    #             print("Precision: " + floatdisplay % precision)
    #             print("Recall: " + floatdisplay % recall)
    #         print("F-score: " + floatdisplay % best_f_score)
    #     args.f[0].close()
    #     args.f[1].close()
    #
    #
    # if __name__ == "__main__":
    #     import argparse
    #
    #     parser = argparse.ArgumentParser(description="Smatch calculator")
    #     parser.add_argument(
    #         '-f',
    #         nargs=2,
    #         required=True,
    #         type=argparse.FileType('r'),
    #         help=('Two files containing AMR pairs. '
    #               'AMRs in each file are separated by a single blank line'))
    #     parser.add_argument(
    #         '-r',
    #         type=int,
    #         default=4,
    #         help='Restart number (Default:4)')
    #     parser.add_argument(
    #         '--significant',
    #         type=int,
    #         default=2,
    #         help='significant digits to output (default: 2)')
    #     parser.add_argument(
    #         '-v',
    #         action='store_true',
    #         help='Verbose output (Default:false)')
    #     parser.add_argument(
    #         '--vv',
    #         action='store_true',
    #         help='Very Verbose output (Default:false)')
    #     parser.add_argument(
    #         '--ms',
    #         action='store_true',
    #         default=False,
    #         help=('Output multiple scores (one AMR pair a score) '
    #               'instead of a single document-level smatch score '
    #               '(Default: false)'))
    #     parser.add_argument(
    #         '--pr',
    #         action='store_true',
    #         default=False,
    #         help=('Output precision and recall as well as the f-score. '
    #               'Default: false'))
    #     parser.add_argument(
    #         '--justinstance',
    #         action='store_true',
    #         default=False,
    #         help="just pay attention to matching instances")
    #     parser.add_argument(
    #         '--justattribute',
    #         action='store_true',
    #         default=False,
    #         help="just pay attention to matching attributes")
    #     parser.add_argument(
    #         '--justrelation',
    #         action='store_true',
    #         default=False,
    #         help="just pay attention to matching relations")
    #
    #     args = parser.parse_args()
    #     main(args)