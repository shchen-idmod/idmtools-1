==================
Basic installation
==================

Follow the steps below if you will use |IT_l| to run and analyze simulations, but will not make
source code changes.

#.  Open a command prompt and create a virtual environment in any directory you choose. The
    command below names the environment "idmtools_local", but you may use any desired name::

        python -m venv idmtools_local

#.  Activate the virtual environment:

    .. container:: os-code-block

        .. container:: choices

            * Windows
            * Linux

        .. container:: windows

            Enter the following::

                idmtools_local\Scripts\activate

        .. container:: linux

            Enter the following::

                source idmtools_local/bin/activate

#.  Install |IT_l| packages::

        pip install idmtools_platform_local --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple

    .. note::

        When reinstalling |IT_l| you should use the ``--no-cache-dir`` and ``--force-reinstall`` options, such as: ``pip install idmtools_platform_local --index-url=https://packages.idmod.org/api/pypi/pipi-production/simple --no-cache-dir --force-reinstall``. Otherwise, you may see the error, **idmtools_platform_local not found**, when attempting to open and run one of the example Python scripts.

#.  Verify installation by pip list, you should see idmtools_platform_local package::

        pip list

#.  When you are finished, deactivate the virtual environment by entering the following at a command prompt::

        deactivate

