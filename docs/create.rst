Creating an ethPM manifest
--------------------------

ethPM CLI offers a couple options for creating your own ethPM manifest for local smart contracts. All options expect a project directory in the following format. 

   - project_name/
       - ``solc_input.json``
       - ``solc_output.json``
       - contracts/
           - ``ContractA.sol``
           - ``ContractB.sol``

In order to create a manifest, the CLI starts with your project's solidity compiler output. Use the following steps to generate ``solc_output.json`` for your project.

Generate the solidity compiler input
====================================

To generate your project's solidity compiler output, the solidity compiler needs `a JSON input <https://solidity.readthedocs.io/en/v0.5.3/using-the-compiler.html#compiler-input-and-output-json-description>`_ to know which contracts to compile. If you don't want to create your own ``solc_input.json``, you can use the following command which will automatically generate the ``solc_input.json`` for all contracts found in your project's ``contracts/`` directory. However, if any of your contracts require special behavior, such as remappings, you will have to manually edit the generated ``solc_input.json`` as necessary.

.. code-block:: shell

   ethpm create solc-input --project-dir

Generate the solidity compiler output
=====================================

To generate the solidity compiler output for your project, you must have the appropriate solidity compiler version installed locally, or you can use the docker image. For more information on how to use the solidity compiler, `read this <https://solidity.readthedocs.io/en/v0.5.3/installing-solidity.html>`_.

Example..

.. code-block:: shell

   solc --standard-json --allow-paths [path/to/project_dir] < [path/to/project_dir/solc_input.json] > [path/to/project_dir/solc_output.json]

Creating your ethPM manifest
============================

Now that you have the solidity compiler output for your project, there are two options for creating an ethPM manifest.

Manifest Wizard
~~~~~~~~~~~~~~~

The most comprehensive option for generating a manifest is the manifest wizard. The wizard will walk you through the steps and the available options to customize your manifest. Finally, it will write the generated manifest to your project's directory in the format ``[package_version].json``.

.. code-block:: shell

   ethpm create wizard --project-dir

Basic Manifest
~~~~~~~~~~~~~~

If you want a quick and easy option to generate a valid manifest for your project, you can use the ``basic-manifest`` command. This will automatically package up all available sources and contract types found in your project's ``solc_output.json``, and create a manifest with the provided ``--package-name`` and ``--package-version``. Finally, it will write the generated manifest to your project's directory in the format ``[package_version].json``.

.. code-block:: shell

   ethpm create basic-manifest --project-dir /my_project --package-name my-package --package-version 1.0.0
