Commands
========

A command-line tool to help manage EthPM packages and registries.


.. warning::

   ``EthPM CLI`` is currently in public Alpha:

   - It is expected to have bugs and is not meant to be used in production 
   - Things may be ridiculously slow or not work at all


ethpm install
-------------

Install an ethPM package to a local ``_ethpm_packages`` directory.

.. argparse::
   :ref: ethpm_cli.parser.parser
   :prog: ethpm
   :path: install


ethpm list
----------

List all installed ethPM packages in a local ``_ethpm_packages`` directory.

.. argparse::
   :ref: ethpm_cli.parser.parser
   :prog: ethpm
   :path: list


ethpm uninstall
---------------

Uninstall an ethPM package from a local ``_ethpm_packages`` directory.

.. argparse::
   :ref: ethpm_cli.parser.parser
   :prog: ethpm
   :path: uninstall


ethpm auth
----------

Link a keyfile to authorize on-chain transactions (i.e. deploying a registry / releasing a package). To generate a keyfile, use `eth-keyfile <https://github.com/ethereum/eth-keyfile>`_.

.. argparse::
   :ref: ethpm_cli.parser.parser
   :prog: ethpm
   :path: auth


ethpm scrape
------------

Scrape a blockchain for all IPFS data associated with any package release. This command will scrape for all ``VersionRelease`` events (as specified in `ERC 1319 <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1319.md>`_). It will lookup all associated IPFS assets with that package, and write them to your ethPM XDG directory.

.. argparse::
   :ref: ethpm_cli.parser.parser
   :prog: ethpm
   :path: scrape
