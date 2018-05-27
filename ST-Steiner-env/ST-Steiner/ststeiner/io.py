'''
Copyright (C) 2018 Utku Norman

This file is part of ST-Steiner

ST-Steiner is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ST-Steiner is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from __future__ import print_function



# standard library imports
import json
import sys
if sys.version_info[0] > 2:
    # py3k
    pass
else:
    # py2
    import codecs
    import warnings
    def open(file, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None, closefd=True, opener=None):
        if newline is not None:
            warnings.warn('newline is not supported in py2')
        if not closefd:
            warnings.warn('closefd is not supported in py2')
        if opener is not None:
            warnings.warn('opener is not supported in py2')
        return codecs.open(filename=file, mode=mode, encoding=encoding,
                    errors=errors, buffering=buffering)


# third party imports
import pathlib as pl
import networkx as nx

# local application imports
from ststeiner.utils import s_if_plural, is_none

def read_prizes(file, logger=None, upper=False):
    '''Read node prize data from file.'''

    prizes = dict()

    if logger is not None:
        logger.debug('Prizes read from {}'.format(file))

    with open(str(file)) as f:
        for line in f:
            line = line.strip().split()
            if upper:
                prizes[line[0].upper()] = float(line[1])
            else: 
                prizes[line[0]] = float(line[1])
    return prizes


def read_network(file, logger=None, upper_nodes=False):

    if logger is not None:
        logger.debug('Reading network from {}'.format(file))

    G = nx.read_edgelist(str(file), data=(('weight', float), ))

    if logger is not None:
        n = G.number_of_nodes()
        m = G.number_of_edges()
        logger.debug('Network has {:,} node{}, {:,} edge{}.'.format(
            n, s_if_plural(n), m, s_if_plural(m)))

    if upper_nodes:
        G_upper = nx.Graph()
        for u, v, a in G.edges(data='weight'):
            G_upper.add_edge(u.upper(), v.upper(), weight=a)
        return G_upper
    else:
        return G


def read_json(file, logger=None):

    file = pl.Path(file)

    if not file.exists():
        if logger is not None:
            logger.debug('{} does not exist'.format(file))
        return None

    with open(str(file)) as f:
        data = json.load(f)

    return data


def write_dict(file, dictionary, sep='\t'):

    file = pl.Path(file)

    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)

    with open(str(file), 'w') as f:
        for k, v in dictionary.items():
            print('{}{}{}'.format(k, sep, v), file=f)


def write_json(file, data, logger=None):

    file = pl.Path(file)

    if logger is not None:
        logger.debug('Saving to {}'.format(file))

    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)

    with open(str(file), 'w') as f:
        json.dump(data, f, sort_keys=True, indent=4)


def write_result(G, logger=None):

    result = dict(**G.graph)
    result['beta'] = beta
    # result = {**G.graph,
    #           'beta': beta,
    #           }

    write_json(result_file, result, logger)