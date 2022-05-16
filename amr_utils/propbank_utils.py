import json
import os
import sys
from typing import List, Dict

import pkg_resources

from amr_utils.utils import class_name

RESOURCE_FILE = 'resources/propbank_frames.json'


class PropBank:
    """
    This class contains static methods related to PropBank frames and roles such as methods for looking up the
    definition of a frame or getting a frame's semantic roles.

    PropBank (https://propbank.github.io/) is a lexical resource of 9,000 predicate senses with semantic roles.
    PropBank frames and roles can be found here: https://github.com/propbank/propbank-frames/
    """

    print(f'[PropBank] Loading PropBank resources')
    if os.path.isfile(RESOURCE_FILE):
        _stream = pkg_resources.resource_stream(__name__, RESOURCE_FILE)
        FRAMES = json.load(_stream)

    @staticmethod
    def is_propbank_frame(frame: str) -> bool:
        """
        Test whether a string is a PropBank frame. The string must be in the AMR format for frames,
        containing only letters, numbers, and hyphens (e.g., "aaa-aaa-01" instead of "aaa_aaa.01").
        Args:
            frame (str): string to test

        Returns:
            bool: True if and only if string is in the list of PropBank frames.
        """
        return frame in PropBank.FRAMES

    @staticmethod
    def is_valid_role(frame: str, role: str) -> bool:
        """
        Test whether a semantic role is a possible core role for this frame.
        Args:
            frame (str): frame to test
            role (str): role to test (e.g., ":ARG0")

        Returns:
            bool: True if and only if role is one of the frame's core roles
        """
        if role.startswith(':'):
            role = role[1:]
        if frame in PropBank.FRAMES:
            if role not in ['definition', 'aliases'] and role in PropBank.FRAMES[frame]:
                return True
        return False

    @staticmethod
    def frame_roles(frame: str) -> List[str]:
        """
        Get a list of valid core semantic roles for this frame.
        Args:
            frame (str): a frame

        Returns:
            List[str]: a list of relations
        """
        if frame in PropBank.FRAMES:
            roles = []
            for role in PropBank.FRAMES[frame]:
                if role.startswith('ARG'):
                    roles.append(':'+role)
            return roles
        return []

    @staticmethod
    def frame_description(frame: str) -> str:
        """
        Get a complete description of this frame's definition and roles.
        Args:
            frame (str): a frame

        Returns:
            str: a formatted description including the frame's definition and possible roles.
        """
        if frame in PropBank.FRAMES:
            desc = [PropBank.FRAMES[frame]['definition']]
            for role in PropBank.FRAMES[frame]:
                if role in ['definition', 'aliases']:
                    continue
                desc.append(role +': ' + PropBank.FRAMES[frame][role])
            return '\n'.join(desc)
        return ''

    @staticmethod
    def frame_def(frame: str) -> str:
        """
        Get this frame's definition
        Args:
            frame (str): a frame

        Returns:
            str: a definition
        """
        if frame in PropBank.FRAMES:
            return PropBank.FRAMES[frame]['definition']
        return ''

    @staticmethod
    def role_description(frame: str, role: str) -> str:
        """
        Get the description of a semantic role for this frame
        Args:
            frame (str): a frame
            role (str): a role (e.g., ":ARG0")

        Returns:
            str: a description of this role for this frame
        """
        if role.startswith(':'):
            role = role[1:]
        if frame in PropBank.FRAMES:
            if role in PropBank.FRAMES[frame] and role not in ['definition', 'aliases']:
                return PropBank.FRAMES[frame][role]
        return ''

    @staticmethod
    def frame_aliases(frame: str) -> Dict[str, List[str]]:
        """

        Args:
            frame (str): a frame
            role (str): a role (e.g., ":ARG0")

        Returns:
            str: a description of this role for this frame
        """
        if frame in PropBank.FRAMES:
            if 'aliases' in PropBank.FRAMES[frame]:
                return PropBank.FRAMES[frame]['aliases'].deepcopy()
        return {}

    @staticmethod
    def _pb_frame_to_amr_frame(frame: str):
        return frame.replace('_', '-').replace('.', '-')

    @staticmethod
    def _pb_role_to_amr_role(role: str, non_core: str):
        if role.isdigit():
            return f'ARG{role}'
        else:
            return f'Non-Core {non_core}'

    @staticmethod
    def _create_propbank_resources(frame_directory: str):
        if os.path.isfile(RESOURCE_FILE):
            raise Exception('PropBank resource already exists!')
        frame_directory = os.path.join(frame_directory, 'frames')

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


if __name__ == '__main__':
    PropBank._create_propbank_resources(sys.argv[1])



