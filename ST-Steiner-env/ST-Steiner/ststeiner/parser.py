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

import argparse
import configparser


def parse_commands(argv):
    """Command-Line Interface parser for intepreting command-line input for ST-Steiner
    Args:
        argv (list of str): arguments

    Returns:
        args (argparse.Namespace): holds parsed attributes

    """
    default_ini_file = 'config/default.ini'
    config = configparser.ConfigParser()
    config.read(default_ini_file)

    parser = argparse.ArgumentParser(prog='ST-Steiner - Spatio-Temporal Steiner',
                                     description='''Implementation for the
                                        ST-Steiner algorithm''',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     argument_default=argparse.SUPPRESS)
    required_args = parser.add_argument_group('required named arguments')

    # Define file/directory related arguments.
    required_args.add_argument('--network_file', type=str, required=True,
                       help='''network file to operate on''')
    required_args.add_argument('--prize_file', type=str, required=True,
                       help='''tab-separated node prize file''')
    required_args.add_argument('--msgsteiner_bin', type=str, required=True,
                       help='''msgsteiner binary file. Preferred version 1.3.''')

    parser.add_argument('--config_file', type=str, default=default_ini_file,
                       help='''configuration file for the experiment''')

    parser.add_argument('--stp_dir', type=str, default=config['Paths']['stp_dir'],
                       help='''output directory to to place intermediate files as input to msgsteiner''')
    parser.add_argument('--cluster_dir', type=str, default=config['Paths']['cluster_dir'],
                       help='''directory to place the results''')
    parser.add_argument('--log_dir', type=str, default=config['Paths']['log_dir'],
                       help='''output directory for a log file that describes the experiment''')
    parser.add_argument('--cluster_list_file', type=str, default=config['Paths']['cluster_list_file'],
                       help='''a file that contains a list of files that point to used to networks in F_c to calculate artificial prize''')
    parser.add_argument('--art_prizes_dir', type=str, default=config['Paths']['art_prizes_dir'],
                       help='''output directory for a prize file that contains the artificial prizes added to the original prizes''')

    # Define arguments for trade-off parameters.
    parser.add_argument('-b', '--beta', type=float, default=config['Parameters']['beta'],
                       help='''sets node prize and edge cost trade-off''')
    parser.add_argument('-l', '--lambda', type=float, dest='lambd', default=config['Parameters']['lambd'],
                       help='''sets the parameter that scales the effect of an artificial prize''')
    parser.add_argument('-a', '--alpha', type=float, default=config['Parameters']['alpha'],
                       help='''sets the parameter that adjusts the non-linearity for an artificial prize''')

    # Other arguments.
    parser.add_argument('--exp_id', type=str, default='None',
                       help='''sets an ID for the experiment. Generated in format <date>_<random number> by default.
                       Overriden if exists.''')
    # parser.add_argument('--fold', type=str, default=config['ST-Steiner']['fold'],
    #                    help='''fold number can be specified here.''')

    parser.add_argument('--prize_mode', type=str, default=config['ST-Steiner']['prize_mode'],
                       help='''sets the artificial prize mode: positive (default), or negative''')

    parser.add_argument('--cost_mode', type=str, default=config['ST-Steiner']['cost_mode'],
                       help='''sets the edge cost mode: "weight" (default), or "1-weightsqd" (1-weight^2)''')

    parser.add_argument('--retain_intermediate', default=config['ST-Steiner'].getboolean('retain_intermediate'),
                       help='''sets whether to remove ST-Steiner generated intermediate files''', action='store_true')

    parser.add_argument('--version', action='version',
                       version='%(prog)s ' + str(config['ST-Steiner']['version']))

    # Do the parsing and return the results.
    args = parser.parse_args(argv)

    return args