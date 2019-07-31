Disk Format
===========

_ethpm_packages/
----------------

A user can have one or many different ``_ethpm_packages/`` local directories. Think of it like the ``node_modules/`` directory in Node or a virtual environment in Python.

   - By default, ``ethpm-cli`` will target the ``./_ethpm_packages/`` directory available under the current working directory.
   - If ``--ethpm-dir`` flag is specified on a cli command, the cli will target the provided directory.
   - If the environmnet variable ``ETHPM_CLI_PACKAGES_DIR`` is set, the cli will use this directory if one is not specified using the ``--ethpm-dir`` flag.


ethPM cli writes ethPM package assets to your disk using the following format. 

- ``.cwd/`` (current working directory)

  - ``_ethpm_packages/``

    - ``ethpm.lock``

    - ``package_name/``

      - ``manifest.json`` 
      
      - ``_ethpm_packages/`` (build dependencies if present in manifest)

      - ``_src/``
         
         - Resolved source tree


ethpm.lock
----------

A root-level JSON lockfile that manages what packages are currently installed. Everytime a package is installed or uninstalled, ``ethpm.lock`` must be updated with the corresponding package information.
   
   - ``installed_package_name``

     - ``alias``

       - Package alias, if one is used to install pacakge, else package name.

     - ``registry_address``

       - If package is installed with a registry URI, else ``null``.

     - ``resolved_content_hash``

       - Validation hash of fetched contents. If re-generated, **MUST** match hash of given URI.

     - ``resolved_package_name``

       - ``"package_name"`` resolved from target manifest.

     - ``resolved_uri``

       - Content-addressed URI of manifest.

     - ``resolved_version``

       - ``"version"`` resolved from target manifest.

     - ``install_uri``

       - Content addressed / etherscan / registry URI used to install package.


ethPM XDG
---------

For storing IPFS assets and the registry config file, ethPM-CLI uses the XDG Base Directory Specification `<https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html>`_. These files are written to ``$XDG_DATA_HOME / 'ethpmcli'``.  A user will only have one local ethPM XDG directory.
