###############################################
ST-Steiner: Spatio-Temporal Knowledge Discovery
###############################################


.. contents::

.. section-numbering::

ST-Steiner is a prize-collecting Steiner forest based algorithm for spatiotemporal knowledge discovery.

- **Source:** https://github.com/ciceklab/ST-Steiner


Installation
============

Prerequisites
-------------

+ Python version 2.7, 3.5 or 3.6
+ `Boost C++ Libraries <http://www.boost.org/>`_
+ Python packages listed in `requirements.txt`

Initialize the environment
--------------------------

Create a directory for ST-Steiner files, e.g. ``ST-Steiner-env``:

.. code-block:: bash

  $ mkdir ST-Steiner-env && cd ST-Steiner-env

Prepare solver
--------------

Download msgsteiner 1.3, a solver for the prize-collecting Steiner tree problem used in ST-Steiner:

.. code-block:: bash

  $ wget http://staff.polito.it/alfredo.braunstein/code/msgsteiner-1.3.tgz  && tar xzf msgsteiner-1.3.tgz && rm  msgsteiner-1.3.tgz

Compile the solver (requires `Boost C++ Libraries <http://www.boost.org/>`_):

.. code-block:: bash

  $ make --directory msgsteiner-1.3/


Download ST-Steiner source
--------------------------

Download ST-Steiner source code and change the working folder to ST-Steiner:

.. code-block:: bash

  $ git clone https://github.com/ciceklab/ST-Steiner.git && cd ST-Steiner




Install Python libraries
--------------------------


Install the required Python libraries, e.g. via `pip <https://pypi.org/project/pip/>`_:

.. code-block:: bash
  
  $ pip install --user -r requirements.txt

Updating
========

Update ST-Steiner source
------------------------

When in an ST-Steiner folder, you can download the newest source code from the remote repository by typing:

.. code-block:: bash

  $ git pull origin master


Simple example
==============

A motivating toy example for the method ST-Steiner and its decision making process is shown in the Figure. 
On the coexpression network of spatio-time window 1, known risk genes (black) are connected by selecting (red-bordered) genes after solving PCSF. 
This result affects which genes will be selected on the coexpression network of spatio-temporal window 2. 

Assume genes `x, y` and `z` are equally likely to be selected (equal prizes and edge costs) to connect the seed genes. The algorithm prefers gene `x` because it is selected in the earlier period and its prize is increased.


.. msgsteiner directory is referred as <MSGSTEINER_BIN_DIR> and the binary file <MSGSTEINER_BIN_DIR>/msgsteiner .
.. class:: no-web

  .. figure:: https://raw.githubusercontent.com/utku-norman/st-steiner/master/example.png
      :alt: ST-Steiner example
      :width: 50%
      :align: center

      A motivating toy example

      Figure shows 2 spatio-temporal windows (plates) and respective coexpression networks along with a parallel brain region and its plates (on right). Circles represent genes and black edges represent pairs of genes that are coexpressed. Red bordered nodes form the Steiner tree found on plate 1 (linked with red edges), which minimally connects black seed genes. In ST-Steiner, genes that are selected in plate 1 are more likely to be selected in plate 2. Curved lines between windows show the mapping of selected genes from plate 1 to plate 2. On the second plate ST-Steiner can pick `X, Y` or `Z` to connect the seed genes. Assuming that they all have identical priors and identical edge costs, the algorithm would pick `X`, because it is selected in the prior window and its prize is increased. If other brain regions in the first temporal window are also considered, then selected genes in those regions would also be used (from the plate on the right).

ST-Steiner solves this problem in two steps. 

First, we solve for Spatio-Temporal Window 1:

.. code-block:: bash

  $ python ./bin/st_steiner \
  --network_file=data/network_1.txt \
  --prize_file=data/prizes.txt \
  --msgsteiner_bin=../msgsteiner-1.3/msgsteiner \
  --exp_id=cluster_1

This generates a cluster ``cluster_1.txt`` in folder ``clusters/``.

Second, considering the solution for Spatio-Temporal Window 1, we solve ST-Steiner for Spatio-Temporal Window 2:

.. code-block:: bash

  $ echo "clusters/cluster_1.txt" > clusters/cluster_list.txt; # Produced by the previous step.

.. code-block:: bash

  $ python ./bin/st_steiner \
  --network_file=data/network_2.txt \
  --prize_file=data/prizes.txt \
  --msgsteiner_bin=../msgsteiner-1.3/msgsteiner \
  --exp_id=cluster_2 \
  --cluster_list_file=clusters/cluster_list.txt \
  --lambda=1


Usage
=====

.. code-block:: bash

  python ./bin/st_steiner [-h] --network_file NETWORK_FILE
                          --prize_file PRIZE_FILE
                          --msgsteiner_bin MSGSTEINER_BIN
                          [--config_file CONFIG_FILE]
                          [--stp_dir STP_DIR]
                          [--cluster_dir CLUSTER_DIR]
                          [--log_dir LOG_DIR]
                          [--cluster_list_file CLUSTER_LIST_FILE]
                          [--art_prizes_dir ART_PRIZES_DIR]
                          [-b BETA] [-l LAMBD] [-a ALPHA]
                          [--exp_id EXP_ID]
                          [--prize_mode PRIZE_MODE]
                          [--retain_intermediate]
                          [--version]

See also ``python ./bin/st_steiner --help``.

Reference
=========

Norman, U. and Cicek, A. E. (2018). Spatio-temporal gene discovery for autism spectrum disorder. bioRxiv.
Available at: https://www.biorxiv.org/content/early/2018/03/08/256693

License
=======

Released under the GNU General Public License version 3 (see `LICENSE.txt`)::

   Copyright (C) 2018 Utku Norman <utku.norman@bilkent.edu.tr>