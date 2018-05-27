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


import os
import subprocess
import time
import logging
import datetime
import uuid


# try:
#   from pathlib import Path
# except ImportError:
#   from pathlib2 import Path  # python 2 backport


# third party imports
import pathlib as pl
import networkx as nx

# local application imports
from ststeiner.utils import s_if_plural, is_none
import ststeiner.io as io

import configparser

def solve_st_steiner(network_file, prize_file, msgsteiner_bin,
                    config_file=None, cluster_list_file=None,
                    stp_dir='inputs', cluster_dir='results', log_dir='logs',
                    beta=1, lambd=0, alpha=2, prize_mode='positive',
                    cost_mode='weight',
                    log_name='ST-Steiner', rounder=6, # fold='1-1',
                    exp_id=None, art_prizes_dir=None,
                    retain_intermediate=True):

    dirs = [stp_dir, cluster_dir, log_dir, art_prizes_dir]
    stp_dir = pl.Path(stp_dir)
    cluster_dir = pl.Path(cluster_dir)
    log_dir = pl.Path(log_dir)
    art_prizes_dir = pl.Path(art_prizes_dir)

    # Type checks here.
    lambd = float(lambd)
    alpha = float(alpha)
    beta = float(beta)

    if config_file is not None:
        config = configparser.ConfigParser()
        config.read(config_file)
        msgsteiner_args = config['msgsteiner']
        if 'cost_mode' in config['ST-Steiner']:
            cost_mode = config['ST-Steiner']['cost_mode']
        # print(config)
    else:
        msgsteiner_args = {}

    exp_date = datetime.date.today().strftime("%Y%m%d")

    if is_none(exp_id):
        exp_id = '{}_{}'.format(exp_date, uuid.uuid4().hex[:5])

    stp_file = stp_dir.joinpath('{}.stp'.format(exp_id))
    result_file = stp_dir.joinpath('{}.json'.format(exp_id))
    result_details_file = cluster_dir.joinpath('{}.txt'.format(exp_id))
    log_file = log_dir.joinpath('{}.log'.format(exp_id))
    if not art_prizes_dir.exists():
        art_prizes_dir.mkdir()
    if not is_none(art_prizes_dir):
        art_prizes_file = art_prizes_dir.joinpath(
            '{}.txt'.format(exp_id))
    else:
        art_prizes_file = None

    if not pl.Path(log_dir).exists():
        pl.Path(log_dir).mkdir(parents=True) #, exist_ok=True)
    logger = create_logger(log_file=log_file, log_name=log_name,
                           stream_level=logging.DEBUG)
    logger.debug('Running {}, {} with ID {}'.format(log_name,
                                                    datetime.datetime.now(), exp_id))


    for d in dirs:
        if not pl.Path(d).exists():
            logger.debug('Creating directory {}'.format(d))
            d.mkdir(parents=True) #, exist_ok=True)

    # Get file list.
    const_results = list()
    const_files = list()
    if is_none(cluster_list_file):
        logger.debug('No constraint file list is provided.')
    else:
        cluster_list_file = pl.Path(cluster_list_file)
        if cluster_list_file.exists():
            const_files = [pl.Path(f.strip())
                           for f in cluster_list_file.open().read().strip().split('\n')]
            logger.debug('Read constraining file list from {}: {} file{}'.format(
                cluster_list_file, len(const_files), s_if_plural(len(const_files))))
            logger.debug('Files:')
            for f in const_files:
                logger.debug('\t{}'.format(f))
        else:
            logger.debug('Constraint file not found at {}'.format(
                cluster_list_file))

    # Read files.
    const_networks = list()
    if len(const_files) > 0:
        for file in const_files:
            if file.suffix == '.json':
                data = io.read_json(file)
                if data is None:
                    logger.debug('Unable to load constraining set from json {}'.format(
                        file))
                nodes = data['nodes']
            elif file.suffix == '.txt':
                nodes = set(file.open().read().strip().split())
            else:
                logger.debug('Unable to laod from {}'.format(file))
                continue
            const_results.append({'nodes':list(nodes)})
            logger.debug('Loaded contraining set from {}: {} nodes'.format(
                file, len(nodes)))
            G = nx.Graph()
            G.add_nodes_from(nodes)
            const_networks.append(G)

    prizes = dict(io.read_prizes(prize_file, logger=logger))

    network = io.read_network(network_file, logger=logger)

    if cost_mode == 'weight':
        cost_func = lambda weight: weight
    elif cost_mode == '1-weightsqd':
        cost_func = lambda weight: 1 - (weight ** 2)
    else:
        logger.error('Unsupported cost mode "{}"'.format(cost_mode))
    logger.debug('Edge cost mode selected: {}'.format(cost_mode))
    compute_edge_costs(network, cost_func=cost_func, 
                       logger=logger, inplace=True)

    resolve_node_prizes(network, prizes)

    scale_node_prizes(network, beta, to_attr_name='scaled_prize',
                      logger=logger, inplace=True)

    constrain_prizes(network, const_networks,
                     from_attr_name='scaled_prize',
                     to_attr_name='const_prize',
                     lambd=lambd, alpha=alpha,
                     inplace=True, prize_mode=prize_mode,
                     logger=logger, art_prizes_file=art_prizes_file)

    const_prizes = nx.get_node_attributes(network, 'const_prize')
    undir_edges = nx.get_edge_attributes(network, 'cost')

    G, run_data = find_steiner(stp_file, logger=logger,
                               undir_edges=undir_edges,
                               prizes=const_prizes,
                               msgsteiner_bin=msgsteiner_bin,
                               msgsteiner_args=msgsteiner_args)

    metadata = {
        'name': pl.Path(network_file).stem,
        'exp_id': exp_id,
        'exp_date': exp_date,
        'nodes': list(G.nodes()),
        'edges': list(tuple(e) for e in G.edges()),
        'beta': beta,
        'lambda': lambd,
        'alpha': alpha,
        'log': run_data,
        'log_name': log_name,
        'prize_mode': prize_mode,
        # 'fold': fold,
        'files': {
            'result': str(pl.Path(result_file).name),
            'log': str(pl.Path(log_file).name),
            'prize': str(pl.Path(prize_file).name),
            'network': str(pl.Path(network_file).name),
            'stp': str(pl.Path(stp_file).name),
        },
        'const_results': const_results,
    }
    io.write_json(result_file, metadata, logger=logger)

    file = result_details_file
    if logger is not None:
        logger.debug('Saving to {}'.format(file))
    nx.write_edgelist(G, str(file), data=False, delimiter='\t')
 
    if not retain_intermediate:
        stp_file.unlink()
        result_file.unlink()
        d = pl.Path(stp_file).parent
        if len(list(d.glob('*'))) == 0:
            d.rmdir()
        if not is_none(art_prizes_dir):
            if pl.Path(art_prizes_file).exists():
                pl.Path(art_prizes_file).unlink()
            if len(list(art_prizes_dir.glob('*'))) == 0:
                if art_prizes_dir.exists():
                    art_prizes_dir.rmdir()
        if logger is not None:
            logger.debug('Intermediate files and folder are removed')  
    logger.debug('{} {} with ID {} completed.'.format(log_name,
        datetime.datetime.now(), exp_id))

    return G, metadata


def find_steiner(stp_file, msgsteiner_bin,
                 undir_edges=set(), dir_edges=set(), prizes=dict(),
                 terminals=set(), root=None,
                 msgsteiner_args={}, logger=None):
    '''Finds a Steiner tree.'''

    logger.debug('Writing msgsteiner stp file to {}'.format(stp_file))
    _write_input(stp_file, dir_edges=dir_edges, undir_edges=undir_edges,
                 prizes=prizes, terminals=terminals, root=root)

    logger.debug(
        'Executing msgsteiner binary at {}'.format(msgsteiner_bin))
    G, run_data = _execute_msgsteiner(msgsteiner_bin, stp_file,
                                      logger=logger, **msgsteiner_args)
    logger.debug('Tree found, {} nodes, {} edges'.format(
        G.number_of_nodes(), G.number_of_edges()))
    logger.debug('Nodes:')
    if len(G) < 100:
        for u in G:
            logger.debug(u)
        logger.debug('Edges:')
        for e in G.edges():
            logger.debug(e)

    run_data['terminals'] = list(terminals)

    logger.debug('Finding Steiner tree is completed.')

    return G, run_data


def _write_input(stp_file, undir_edges=set(),
                 dir_edges=set(), prizes=dict(),
                 terminals=set(), root=None, comments='#'):
    """Command for reading MSGSTEINER input file
    ## msgsteiner input file format
    #undirected edges
    E v1 v2 w12 (*)
    #directed edges
    D v1 v2 w12
    #node values:
    W v1 p1 (*)
    #terminals (implemented as a very large value, check value in the code)
    T v1 (*)
    #root (if no root specified, an rooting procedure is used)
    R v1
    """

    prizes = dict(prizes)
    # Create directories for the MSGSTEINER input file.
    stp_file = pl.Path(stp_file)
    if not stp_file.parent.exists():
        stp_file.parent.mkdir(parents=True)

    # Write data to the MSGSTEINER input file
    # with open(stp_file, 'w') as f:
    with open(str(stp_file), 'w') as f:

        # Write undirected edges in the format 'E v1 v2 w12'.
        if comments is not None:  # and len(undir_edges) > 0:
            print('{} undirected edges'.format(comments), file=f)
        for (u, v), a in undir_edges.items():  # G.edges(data=edge_cost_label):
            if u != v:
                print('E', u, v, a, file=f)

        # Write directed edges in the format 'D v1 v2 w12'
        if comments is not None:  # and len(dir_edges) > 0:
            print('{} directed edges'.format(comments), file=f)
        for u, v, a in dir_edges:
            if u != v:
                print('D', u, v, a, file=f)

        # Write node values  in the format 'W v1 p1'
        if comments is not None:  # and len(prizes) > 0:
            print('{} node prizes'.format(comments), file=f)
        for node, prize in prizes.items():  # G.nodes_iter():
            print('W', node, prize, file=f)  # G.node[n][node_prize_label]))

        # Write terminals  in the format 'T v1'
        if comments is not None:  # and len(terminals) > 0:
            print('{} terminals'.format(comments), file=f)
        for terminal in terminals:
            print('T', terminal, file=f)

        # Write the root in the format 'R <root>'. In MSGSTEINER,
        #   if no root specified, an rooting procedure is use
        # max_key = max(stats, key=lambda k: stats[k])
        # node_prizes = {n:G.node[n][node_prize_label] for n in G}
        # root = max(node_prizes, key=lambda k: node_prizes[k])
        if root is not None:
            if comments is not None:
                print(comments, 'root', file=f)
            print('R', root, file=f)


def _execute_msgsteiner(msgsteiner_path, stp_file,
                        logger=None,
                        threads=None, depth=30, maxit=None, tolerance=None,  # maxit=1000000
                        noise=0, rein=1e-3, decision=None, term_prize=None):  # noise=1e-5
    """Command for running MSGSTEINER.

    Output of MSGSTEINER is retrieved and parsed to form Steiner Network.

    Args:
        msgsteiner_path (str or pl.Path): path for a msgsteiner binary.
        stp_file (str or pl.Path): path for msgsteiner input file.
            The file should be created beforehand.
        params (dict of str): msgsteiner specific parameters of choice. 

    Returns:
        bool: True if successful, False otherwise.

    """
    # Prepare command-line string.
    args = [
        '-o',                   # outputs final tree to std output
        # '-M',                   # output messages on convergence
                                # cannot yet parse
    ]
    if threads is not None:     # Set number of threads
        args += ['-j', '{:d}'.format(int(threads))]
    if depth is not None:       # Set maximum depth
        args += ['-d', '{:d}'.format(int(depth))]
    if maxit is not None:       # Set maximum number of iterations
        args += ['-t', '{:d}'.format(int(maxit))]
    if tolerance is not None:   # Set convergence tolerance
        args += ['-e', '{}'.format(tolerance)]
    if noise is not None:       # Set random factor
        args += ['-r', '{}'.format(noise)]
    if rein is not None:        # Set reinforcement parameter rein
        args += ['-g', '{}'.format(rein)]
    if decision is not None:    # Set convergence # repeats
        args += ['-y', '{:d}'.format(int(decision))]
    if term_prize is not None:  # Set terminal infinity
        args += ['-p', '{}'.format(term_prize)]
    # Input file redirection
    # inhandle = stp_file
    # args += ['<', '{}'.format(stp_file)]
    # args = ['{}'.format(stp_file), '>'] + args

    out, err = _execute_script(
        msgsteiner_path, args, logger=logger, inhandle=stp_file)

    # Parse the root name.
    key = 'root:'
    a = list(filter(lambda line: key in line, err))
    if len(a) != 0:
        root = a[0].split(key)[-1].strip()
    else:
        root = 'n/a'
    logger.debug('Root: {}'.format(root))

    # Generate the steiner network from edgelist.
    edges = []
    for l in out:
        e = tuple(l.split()[0:2])
        if len(e) < 2:
            continue
        edges.append(e)

    # Make a graph from the edgelists.
    G = nx.Graph(edges)

    metadata = {
        'args': args,
        'output': out,
        'error': err,
        'root': root,
    }

    # Done. Return the graph handler and auxiliary data.
    return G, metadata


def _execute_script(executable_path, args=[], inhandle=None,
                    verbose=True, timer=True, logger=None):
    cmd = [str(executable_path)] + args
    cmd_txt = ' '.join(cmd)
    # cmd = ' '.join(cmd)
    inhandle = pl.Path(inhandle)
    if verbose:
        logger.debug('Executing command: {}'.format(cmd_txt))
        if inhandle is not None:
            logger.debug('(With inhandle {})'.format(inhandle))
        if timer:
            start = time.time()

    if inhandle is not None:
        with inhandle.open() as in_h:
            p_in = subprocess.Popen(cmd, stdin=in_h,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out_data, err_data = p_in.communicate()
    else:
        # proc = subprocess.Popen(cmd,
        #     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # out_data, err_data = proc.communicate()

        completed_proc = subprocess.run(cmd,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out_data = completed_proc.stdout
        err_data = completed_proc.stderr

    out = out_data.decode('utf8').strip().split('\n')
    err = err_data.decode('utf8').strip().split('\n')

    if timer:
        duration = round(time.time() - start, 3)

    if verbose:
        if timer:
            logger.debug('Done. Duration: {} seconds.'.format(duration))

    # if logger is not None:
    #     if verbose:
    #         print('Logged to {}'.format(logger))
    #     write_channels(logger, out, err, duration)

    return out, err

#_IO_related_methods___________________________________________________________



#_Helper_methods_______________________________________________________________


def create_logger(log_name, log_file,
                  file_level=logging.DEBUG,
                  stream_level=logging.ERROR):

    # Create logger.
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs debug messages.
    fh = logging.FileHandler(str(log_file))
    fh.setLevel(file_level)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(stream_level)

    # Create formatter and add it to the handlers.
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger.
    # if (logger.hasHandlers()):
        # logger.handlers.clear()
    if len(logger.handlers) > 0:
        logger.handlers = []

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def compute_edge_costs(G, attr_name='weight',
                       cost_func=lambda weight: weight,
                       logger=None, inplace=False):

    if logger is not None:
        logger.debug('Computing edge costs')
    if not inplace:
        G = G.copy()
    for u, v, a in G.edges(data=attr_name):
        G[u][v]['cost'] = cost_func(a)
    return G



def resolve_node_prizes(network, prizes, label='prize', logger=None):

    if logger is not None:
        logger.debug('Resolving node prizes')

    network_prizes = dict()
    for node in network:

        prize = None

        if '_' in node:
            node2 = node.split('_')[0]
            if node2 in prizes:
                prize = prizes[node2]
        elif node in prizes:
            prize = prizes[node]

        if prize is not None:
            network_prizes[node] = prize

    nx.set_node_attributes(network, name=label, values=network_prizes)

# network_prizes = {node: prize for node, prize in prizes.items()
#                   if node in network}



def scale_node_prizes(network, beta,
                      from_attr_name='prize', to_attr_name='prize',
                      logger=None, inplace=False):

    if not inplace:
        network = network.copy()

    if logger is not None:
        logger.debug('Scaling node prizes by {}'.format(beta))

    prizes = nx.get_node_attributes(network, from_attr_name)

    prizes = {node: beta * prize for node, prize in prizes.items()}

    nx.set_node_attributes(network, name=to_attr_name, values=prizes)

    return network


def constrain_prizes(network, const_networks,
                     lambd=0, alpha=2, inplace=False,
                     prize_mode='positive',
                     from_attr_name='scaled_prize', to_attr_name='const_prize',
                     logger=None, art_prizes_file=None):
    '''Constrains the node prizes of a network using info. from other networks.'''

    if logger is not None:
        logger.debug('Begin computing new node prizes.')

    if not inplace:
        network = network.copy()

    art_prizes = _compute_art_prizes(network, const_networks, lambd=lambd,
                                     alpha=alpha, prize_mode=prize_mode,
                                     savefile=art_prizes_file, logger=logger)

    _update_org_prizes(network, art_prizes, from_attr_name=from_attr_name,
                       to_attr_name=to_attr_name,
                       logger=logger, inplace=True)

    if logger is not None:
        logger.debug('New prizes computed.')

    return network


def _compute_art_prizes(network, const_networks, lambd, alpha=2,
                        prize_mode='negative', savefile=None, logger=None,
                        indent=2):
    '''Computes artificial prizes for a network.'''

    if logger is not None:
        logger.debug((' ' * indent + 'Finding node frequencies '
                      'in constraining networks'))
    node_freqs = find_frequency(const_networks)

    if logger is not None:
        logger.debug(' ' * indent + 'Computing artifical prizes')
        logger.debug(' ' * indent + '  lambda = {}'.format(lambd))
        logger.debug(' ' * indent + '  alpha  = {}'.format(alpha))
        logger.debug(' ' * indent + '  mode   = {}'.format(prize_mode))
    art_prizes = dict()
    if 'negative' in prize_mode:
        for node in network.nodes():
            if node in node_freqs:
                freq = node_freqs[node]
            else:
                freq = 0
            art_prizes[node] = - lambd * ((1 - freq) ** alpha)
    elif 'positive' in prize_mode:
        for node in node_freqs.keys():
            freq = node_freqs[node]
            art_prizes[node] = lambd * (freq ** alpha)

    if 'proportional' in prize_mode:
        prizes = nx.get_node_attributes(network, 'prize')
        min_prize = min(prizes.values())
        for k, v in art_prizes.items():
            if k in prizes:
                art_prizes[k] = prizes[k] * v
            else:
                art_prizes[k] = min_prize * v

    if not is_none(savefile):
        if logger is not None:
            logger.debug((' ' * indent + 'Saving artificial prizes, '
                          'to {}').format(savefile))
        io.write_dict(savefile, art_prizes)

    return art_prizes


def _update_org_prizes(network, art_prizes,
                       from_attr_name='prize',
                       to_attr_name='prize',
                       logger=None,
                       inplace=False, indent=2):
    '''Add artificial prizes to the original prizes.'''

    if logger is not None:
        logger.debug(' ' * indent + 'Updating the original prizes')

    if not inplace:
        network = network.copy()

    prizes = nx.get_node_attributes(network, from_attr_name)

    for k, v in art_prizes.items():
        if k in prizes:
            prizes[k] = prizes[k] + v
        else:
            prizes[k] = v

    nx.set_node_attributes(network, name=to_attr_name, values=prizes)

    return network


def find_frequency(set_list):
    # Take a list of sets and return a dict that maps elements in the sets
    # to the fraction of sets they appear in.  This is not written for
    # maximum efficiency but rather readability.

    if set_list is None:
        return dict()

    n = float(len(set_list))  # Want floating point division
    count_dict = find_counts(set_list)

    # Transform the counts into frequencies
    freq_dict = {}
    for key in list(count_dict.keys()):
        freq_dict[key] = count_dict[key] / n

    return freq_dict


def find_counts(set_list):
    # Take a list of sets and return a dict that maps elements in the sets
    # to the number of sets they appear in as ints.  This is not written for
    # maximum efficiency but rather readability.
    keys = set()
    for cur_set in set_list:
        keys.update(cur_set)
    # Initialize the dictionary that will be used to store the counts of each element
    count_dict = dict.fromkeys(keys, 0)
    # Populate the counts
    for cur_set in set_list:
        for element in cur_set:
            count_dict[element] += 1
    return count_dict

# if __name__ == '__main__':

#     main(sys.argv[1:])