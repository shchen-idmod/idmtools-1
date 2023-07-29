============
Installation
============

You can install |IT_l| in two different ways. If you intend to use |IT_l| as
|IDM_l| builds it, follow the instructions in :doc:`basic-installation`.
However, if you intend to modify the |IT_l| source code to add new
functionality, follow the instructions in :doc:`dev-installation`. Whichever
installation method you choose, the prerequisites are the same.

.. _idmtools-prereqs:

Prerequisites
=============

|IT_l| uses Docker to run |IT_l| within a container to keep the |IT_l| environment securely
isolated. You must also have |Python_IT| and Python virtual environments installed to isolate your
|IT_l| installation in a separate Python environment. If you do not already have these installed,
see the links below for instructions.

* Windows 10 Pro or Enterprise
* |Python_IT| (https://www.python.org/downloads/release)
* Python virtual environments

    Python virtual environments enable you to isolate your Python environments from one
    another and give you the option to run multiple versions of Python on the same computer. When using a
    virtual environment, you can indicate the version of Python you want to use and the packages you
    want to install, which will remain separate from other Python environments. You may use
    ``virtualenv``, which requires a separate installation, but ``venv`` is recommended and included with Python 3.3+.

* Docker (https://docs.docker.com/)

.. toctree::

    basic-installation
    dev-installation