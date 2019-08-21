Installation
------------

Pypi
~~~~

- Create your virtual environment
- ``pip install ethpm-cli``


Docker
~~~~~~

- ``docker pull ethpm/ethpm:latest``
- ``docker run ethpm/ethpm:latest``

Homebrew (recommended)
~~~~~~~~~~~~~~~~~~~~~~
- ``brew update``
- ``brew upgrade``
- ``brew tap ethpm/ethpm-cli``
- ``brew install ethpm-cli``

Setting up your environment vars
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Before you can use ethPM CLI, you must provide an API key to interact with Infura. If you don't have an API key, you can sign up for one here. Then set your environment variable with 
``export WEB3_INFURA_PROJECT_ID="INSERT_KEY_HERE"``

If you plan to generate packages from Etherscan verified contracts, you must also provide an API key for Etherscan.
``export ETHPM_CLI_ETHERSCAN_API_KEY="INSERT_KEY_HERE"``

If you're using Docker to run ethPM CLI, you must pass Docker the environment variables and mount volumes, like so...

.. code-block:: bash

   docker run -i -e WEB3_INFURA_PROJECT_ID="INSERT_KEY_HERE" -v '/absolute/path/to/ethpm-cli/:/absolute/path/to/ethpm-cli/' -v '/$HOME/.local/share/ethpmcli/:/root/.local/share/ethpmcli/' ethpm/ethpm:latest list

Setting up your private key
~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you plan to use the CLI to send any transactions over an Ethereum network (eg. deploying a new registry, releasing a package to a registry), you must link a private key keyfile to sign these transactions. ethPM CLI uses `eth-keyfile <https://github.com/ethereum/eth-keyfile>`_ to handle private keys. Follow the steps in the README to generate your encrypted keyfile. Make sure you don't lose the password, as you'll need to provide for any tx-signing commands. Once you have your encrypted keyfile, you can link it to the ethPM CLI with the following command.

``ethpm auth --keyfile-path KEYFILE_PATH``
