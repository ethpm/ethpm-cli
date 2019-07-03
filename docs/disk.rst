Disk Format
===========

ethPM cli writes package assets to your disk using the following format.


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
