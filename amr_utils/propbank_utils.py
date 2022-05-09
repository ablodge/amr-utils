import json
import os
import sys

import pkg_resources

from amr_utils.utils import class_name

RESOURCE_FILE = 'resources/propbank_frames.json'


class PropBank:

    print(f'[PropBank] Loading PropBank resources')
    stream = pkg_resources.resource_stream(__name__, RESOURCE_FILE)
    frames = json.load(stream)

    ROLE_TO_AMR_ROLE = {
        'LOC': 'location',
        'TMP': 'time',
        'DIR': 'direction',
        'MNR': 'manner',
        'EXT': 'extent',
        'ADV': 'mod',
        'COM': 'accompanier',
        'GOL': 'destination',
        'PRP': 'purpose',
    }

    @staticmethod
    def _pb_frame_to_amr_frame(frame: str):
        return frame.replace('_','-').replace('.','-')

    @staticmethod
    def _pb_role_to_amr_role(role: str, non_core: str):
        if role.isdigit():
            return f'ARG{role}'
        else:
            if non_core in PropBank.ROLE_TO_AMR_ROLE:
                return PropBank.ROLE_TO_AMR_ROLE[non_core]
            return f'ARGM-{non_core}'

    @staticmethod
    def _create_propbank_resources(frame_directory: str):
        if os.path.isfile(RESOURCE_FILE):
            raise Exception('PropBank resource already exists!')

        import xml.etree.ElementTree as ET

        propbank_frames = {}

        # read PropBank frame files
        for filename in os.listdir(frame_directory):
            if not filename.endswith('.xml'):
                continue
            file = os.path.join(frame_directory, filename)
            tree = ET.parse(file)
            root = tree.getroot()
            # iterate rolesets
            for roleset in root.findall('predicate/roleset'):
                frame = roleset.attrib['id']
                frame = PropBank._pb_frame_to_amr_frame(frame)
                frame_def = roleset.attrib['name']
                frame_roles = {}
                frame_aliases = {}
                # check usage matches AMR
                amr_version = False
                for usage in roleset.findall('usagenotes/usage'):
                    if usage.attrib['resource'] == 'AMR' and usage.attrib['inuse'] == '+':
                        amr_version = True
                if not amr_version:
                    continue
                # find roles
                for role in roleset.findall('roles/role'):
                    desc = role.attrib['descr']
                    role_name = PropBank._pb_role_to_amr_role(role.attrib['n'], role.attrib['f'])
                    frame_roles[role_name] = desc
                # find frame aliases
                for link in roleset.findall('lexlinks/lexlink'):
                    resource = link.attrib['resource']
                    if resource in ['FrameNet', 'VerbNet', 'ERE']:
                        if resource not in frame_aliases:
                            frame_aliases[resource] = []
                        alias = link.attrib['class']
                        if alias not in frame_aliases[resource]:
                            frame_aliases[resource].append(alias)
                # add propbank frame
                print(f'[{class_name(PropBank)}]', 'Adding Frame', frame)
                propbank_frames[frame] = {}
                propbank_frames[frame]['definition'] = frame_def
                for role, desc in frame_roles.items():
                    propbank_frames[frame][role] = desc
                propbank_frames[frame]['aliases'] = frame_aliases

        with open(RESOURCE_FILE, 'w+') as fw:
            json.dump(propbank_frames, fw, indent=4)

    @staticmethod
    def get_frame_description(frame: str):
        if frame in PropBank.frames:
            desc = [PropBank.frames[frame]['definition']]
            for role in PropBank.frames[frame]:
                if role in ['definition', 'aliases']:
                    continue
                desc.append(role+': '+PropBank.frames[frame][role])
            return '\n'.join(desc)
        return ''

    @staticmethod
    def is_propbank_frame(frame: str):
        return frame in PropBank.frames

    @staticmethod
    def is_valid_role(frame: str, role: str):
        if frame in PropBank.frames:
            if role not in ['definition', 'aliases'] and role in PropBank.frames[frame]:
                return True
        return False


if __name__ == '__main__':
    PropBank._create_propbank_resources(sys.argv[1])



