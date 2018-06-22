#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Fix abbreviation, hesitation based on GLM provided Switchboard corpus."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re


class GLM(object):
    """docstring for GLM."""

    def __init__(self, glm_path, space='_'):
        super(GLM, self).__init__()

        self.space = space

        self.map_dict = {}
        with open(glm_path, 'r')as f:
            for line in f:
                line = line.strip()
                if len(line) == 0 or line[0] in [';', '*', '\'']:
                    continue
                before, after = line.split('=>')
                before = re.sub(r'[\[\]\s]+', '', before).lower()
                after = after.split('/')[0]
                # NOTE: use the first word from candidates
                after = after.split(';')[0]
                after = re.sub(r'[\[\]{}]+', '', after).lower()

                # Remove consecutive spaces
                after = re.sub(r'[\s]+', ' ', after)

                # Remove the first and last space
                if after[0] == ' ':
                    after = after[1:]
                if after[-1] == ' ':
                    after = after[:-1]

                self.map_dict[before] = after

                # For debug
                # print(before + ' => ' + after)

    def __call__(self, trans):
        """
        Args:
            trans (string):
        Returns:
            trans (string):
        """
        # Fix abbreviation, hesitation based on GLM
        word_list = trans.split(self.space)
        word_list_mapped = []
        for w in word_list:
            if w in self.map_dict.keys():
                word_fixed = self.map_dict[w]
                word_list_mapped.extend(word_fixed.split(' '))

                # For debug
                # print('fixed: %s => %s' % (w, word_fixed))
            else:
                word_list_mapped.append(w)
        trans = self.space.join(word_list_mapped)

        return trans
