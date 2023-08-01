Configuration
=============

The configuration of |IT_l| is set in the idmtools.ini file. This file is normally located in the project directory but |IT_l| will search up through the directory hierarchy, and lastly the files *~/.idmtools.ini* on Linux and *%LOCALAPPDATA%\\idmtools_local\\idmtools.ini* on Windows.
If no configuration file is found, an error is displayed. To supress this error, you can use *IDMTOOLS_NO_CONFIG_WARNING=1*

.. toctree::
   :maxdepth: 3
   :titlesonly:
   :caption: Specific configuration items and idmtools.ini wizard

   common-parameters
   logging

Below is an example idmtools.ini configuration file:

.. literalinclude:: idmtools.ini
