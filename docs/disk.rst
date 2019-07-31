Disk Format
===========

_ethpm_packages/
----------------

ethPM cli writes ethPM package assets to your disk using the following format. You can have multiple different ``_ethpm_packages/`` local directories. The ``--ethpm-dir`` flag is available on most ``ethpm-cli`` commands to target a specific ``_ethpm_packages/`` dir. You can also set the environment variable ``ETHPM_CLI_PACKAGES_DIR`` to your target ``_ethpm_packages/`` directory. Otherwise, the cli will automatically lookup any ``_ethpm_packages/`` directory available under the current working dirctory.


- CWD

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
