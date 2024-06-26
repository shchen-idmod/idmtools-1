=======
Install
=======

You can install |IT_s| in two different ways. If you intend to use |IT_s| as
|IDM_s| builds it, follow the instructions in :doc:`basic-installation`.
However, if you intend to modify the |IT_s| source code to add new
functionality, follow the instructions in :doc:`dev-installation`. Whichever
installation method you choose, the prerequisites are the same.

.. _idmtools-prereqs:

Prerequisites
=============

|IT_s| uses Docker to run |IT_s| within a container to keep the |IT_s| environment securely
isolated. You must also have |Python_IT| and Python virtual environments installed to isolate your
|IT_s| installation in a separate Python environment. If you do not already have these installed,
see the links below for instructions.

* Windows 10 Pro or Enterprise
* |Python_IT| (https://www.python.org/downloads/release)
* Python virtual environments

    Python virtual environments enable you to isolate your Python environments from one
    another and give you the option to run multiple versions of Python on the same computer. When using a
    virtual environment, you can indicate the version of Python you want to use and the packages you
    want to install, which will remain separate from other Python environments. You may use
    ``virtualenv``, which requires a separate installation, but ``venv`` is recommended and included with Python 3.7+.

* Docker (https://docs.docker.com/)

  Docker is optional for the basic installation of |IT_s|; it is needed only for running simulations
  or analysis locally. It is required for the developer installation.

.. toctree::

    basic-installation
    dev-installation