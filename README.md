# Packages Status
![Staging: idmtools-platform-local](https://github.com/InstituteforDiseaseModeling/idmtools_local/workflows/Staging:%20idmtools-platform-local/badge.svg?branch=dev)


# Other status
![Dev: Rebuild documentation](https://github.com/InstituteforDiseaseModeling/idmtools_local/workflows/Rebuild%20documentation/badge.svg?branch=dev)
![Lint](https://github.com/InstituteforDiseaseModeling/idmtools_local/workflows/Lint/badge.svg?branch=dev)

# IDM Modeling Tools

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [User Installation](#user-installation)
  - [Recommended install](#recommended-install)
  - [Advanced Install](#advanced-install)
  - [Installing Development/Early Release Versions](#installing-developmentearly-release-versions)
    - [PyPI](#pypi)
  - [Pre-requisites](#pre-requisites)
- [Reporting issues](#reporting-issues)
- [Requesting a feature](#requesting-a-feature)
- [Development Documentation](#development-documentation)
- [Run test](#run-test)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# User Installation

Documentation is located at https://docs.idmod.org/projects/idmtools-local. 

To build the documentation locally, do the following:

1. Create and activate a venv.
2. Navigate to the root directory of the repo and enter the following:

    ```
    pip install -r dev_scripts/package_requirements.txt
    pip install -r docs/requirements.txt
    python dev_scripts/bootstrap.py
    cd docs
    make html
    ```
3. (Optional) To automatically serve the built docs locally in your browser, enter the following from
   the root directory:

    ```
    python dev_scripts/serve_docs.py
    ```

## Recommended install

The recommended install is to use
```bash
pip install idmtools --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
pip install idmtools-cli --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
pip install idmtools-platform-local --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
```
This will install the core tools, the cli, and idmtools-platform-local from production artifactory


## Installing Development/Early Release Versions

Development versions are available through both IDM's pypi registry and through Github.

### PyPI

If you have your authentication defined in your pip.conf or pip.ini file, you can use the following commands to install from staging
- `pip install idmtools --index-url=https://<USERNAME>:<PASSWORD>@packages.idmod.org/api/pypi/pypi-staging/simple` - Core package
- `pip install idmtools-cli --index-url=https://<USERNAME>:<PASSWORD>@packages.idmod.org/api/pypi/pypi-staging/simple` - Adds the idmtools cli commands
- `pip install idmtools-platform-local --index-url=https://<USERNAME>:<PASSWORD>@packages.idmod.org/api/pypi/pypi-staging/simple` - Support for Local Platform

## Pre-requisites
- Python 3.7/3.8/3.9 x64
- Docker(Required for the local platform)
- Prefer run on linux

# Reporting issues

Include the following information in your post:

-   Describe what you expected to happen.
-   If possible, include a `minimal reproducible example` to help us
    identify the issue. This also helps check that the issue is not with
    your own code.
-   Describe what actually happened. Include the full traceback if there
    was an exception.

You can report an issue directly on GitHub or by emailing [idmtools-issue@idmod.org](mailto:idmtools-issue@idmod.org). Please include steps to reproduce the issue

# Requesting a feature 

You can request a feature but opening a ticket on the repo or by emailing [idmtools-feature@idmod.org](mailto:idmtools-feature@idmod.org)

# Development Documentation
```bash
pip install idmtools --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
pip install idmtools-cli --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
python dev_scripts/bootstrap.py
```

# Run Test
Before run all tests under idmtools_platform_local/tests folder, install additional packages:
```bash
pip install idmtools-models --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
pip install idmtools-test --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
pip install idmtools[test] --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
# login to staging artifactory
docker login idm-docker-staging.packages.idmod.org
```

Run test:
```bash
cd idmtools_platform_local
make test-all 

OR cd tests
pytest -sv
```
