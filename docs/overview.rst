Overview
========

A command-line tool to help manage EthPM packages and registries.


.. warning::

   ``EthPM CLI`` is currently in public Alpha:

   - It is expected to have bugs and is not meant to be used in production 
   - Things may be ridiculously slow or not work at all


Installing EthPM Packages
-------------------------

.. argparse::
   :ref: ethpm_cli.parser.parser
   :prog: ethpm


URIs
----

ethPM Cli supports the following URI schemes.

- IPFS

  - ``ipfs://[IPFS_HASH]``

- Etherscan

  - ``etherscan://[CONTRACT_ADDRESS]/[CHAIN_ID]``
  - ``CONTRACT_ADDRESS`` and ``CHAIN_ID`` must represent a `Verified Contract <https://etherscan.io/contractsVerified>`_ on Etherscan.
  - Supported values for ``CHAIN_ID``

      ========  ===== 
      CHAIN_ID  CHAIN
      1         Mainnet
      3         Ropsten
      4         Rinkeby
      5         Goerli
      42        Kovan
      ========  =====

- Github Blob 

  - ``https://api.github.com/repos/[OWNER]/[REPO]/git/blobs/[FILE_SHA]``
