========
Glossary
========


The following terms describe both the features and functionality of the |IT_s| software, as well
as information relevant to using |IT_s|.

.. glossary::
    :sorted:

    analyzer
        Functionality that uses the MapReduce framework to process large data sets in parallel, typically on a :term:`high-performance computing (HPC)` cluster. For example, if you would like to focus on specific data points from all simulations in one or more experiments then you can do this using analyzers with |IT_s| and plot the final output.

    assets
        See :term:`asset collection`.

    builder
        A function and list of values with which to call that function that is used to sweep through parameter values in a simulation.

    calibration
        The process of adjusting the parameters of a simulation to better match the data from a particular time and place. 

    entity
        Each of the interfaces or classes that are well-defined models, types, and validations for |IT_s| items, such as simulations, analyzers, or tasks.

    experiment
        Logical grouping of simulations. This allows for managing numerous simulations as a single unit or grouping.

    high-performance computing (HPC)
        The use of parallel processing for running advanced applications efficiently, reliably,
        and quickly.

    parameter sweep
        An iterative process in which simulations are run repeatedly using different values of the parameter(s) of choice. This process enables the modeler to determine what a parameter’s “best” value or range of values.

    platform
        The computing resource on which the simulation runs. See :doc:`platforms/platforms` for
        more information on those that are currently supported. 

    simulation
        An individual run of a model. Generally, multiple simulations are run as part
        of an experiement. 

    suite
        Logical grouping of experiments. This allows for managing multiple experiments as a single unit or grouping.
        
    task
        The individual actions that are processed for each simulation.

        .. Is this correct?

