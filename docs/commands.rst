Commands
========

A command-line tool to help manage ethPM packages and registries.


.. warning::

   ``ethPM CLI`` is currently in public Alpha:

   - It is expected to have bugs and is not meant to be used in production 
   - Things may be ridiculously slow or not work at all


ethpm create
------------

Commands to help generate manifests for local smart contracts.

.. argparse::
   :ref: ethpm_cli.parser.parser
   :prog: ethpm
   :path: create


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


ethpm release
-------------

Release a package on the currently active registry. Requires an active registry set via ``ethpm registry`` and authentication for tx signing set via ``ethpm auth``.

.. argparse::
   :ref: ethpm_cli.parser.parser
   :prog: ethpm
   :path: release


ethpm registry
--------------

Commands to help manage your local registry store.

.. argparse::
   :ref: ethpm_cli.parser.parser
   :prog: ethpm
   :path: registry


ethpm auth
----------

Link a keyfile to authorize on-chain transactions (i.e. deploying a registry / releasing a package). To generate a keyfile, use `eth-keyfile <https://github.com/ethereum/eth-keyfile>`_.

.. code-block:: python

   # Example script to generate your own keyfile
   import json
   from pathlib import Path
   from eth_keyfile import create_keyfile_json

   keyfile_json = create_keyfile_json(
      private_key = b"11111111111111111111111111111111",  # A bytestring of length 32
      password = b"foo"  # A bytestring which will be the password that can be used to decrypt the resulting keyfile.
   )
   keyfile_path = Path.cwd() / 'keyfile.json'
   keyfile_path.touch()
   keyfile_path.write_text(json.dumps(keyfile_json))

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
