.PHONY: clean lint test coverage dist release-staging release-staging-release-commit release-staging-minor changelog start-allure docs
MKDIR ?= mkdir
MV ?= mv
RM ?= rm
IPY=python3 -c
PY=python
PDS=$(PY) dev_scripts/
MAKEALL=$(PDS)run_pymake_on_all.py
PDR=$(PDS)run.py
CLDIR=$(PDS)clean_dir.py
COVERAGE_PATH=tests/.coverage

help:
	help-from-makefile -f ./Makefile

clean: stop-allure ## Clean most common outputs(Logs, Test Results, etc)
	-$(MAKEALL) --parallel clean
	-$(CLDIR) --file-patterns "**/*.log,*.pyi" --dir-patterns "./dev_scripts/.allure_*,./.*_reports"
	-$(PDR) -wd "docs" -ex "make clean"
	-$(RM) -rf **/$(COVERAGE_PATH) *.log *.pyi  dev_scripts/.allure_reports dev_scripts/.allure_results

clean-all: ## Clean most common outputs(Logs, Test Results, etc) as well as local install information. Running this requires a new call to setup-dev or setup-dev-no-docker
	$(IPY) "import os, glob; [os.remove(i) for i in glob.glob('**/$(COVERAGE_PATH)', recursive=True)]"
	$(MAKEALL) --parallel clean-all
	$(CLDIR) --file-patterns "**/*.buildlog"

setup-dev: ## Setup packages in dev mode
	python dev_scripts/bootstrap.py
	$(MAKE) -C idmtools_platform_local docker

lint: ## check style with flake8
	flake8

test: ## Run default set of tests which exclude comps and docker tests
	$(MAKEALL) --parallel test

test-all: ## Run all our tests
	$(MAKEALL) test-all

test-failed: ## Run only previously failed tests
	$(MAKEALL) test-failed

test-no-long: ## Run any tests that takes less than 30s on average
	$(MAKEALL) test-no-long

test-docker: ## Run our docker tests
	$(MAKEALL) test-docker

test-smoke: ## Run our smoke tests
	$(MAKEALL) test-smoke

aggregate-html-reports: ## Aggregate html test reports into one directory
	$(PDS)aggregate_reports.py
	-echo Serving documentation @ server at http://localhost:8001 . Ctrl + C Will Stop Server
	$(PDR) -wd '.html_reports' -ex 'python -m http.server 8001'

stop-allure: ## Stop Allure
	$(PDR) -wd dev_scripts -ex "docker-compose -f allure.yml down -v"

start-allure: ## start the allue docker report server
	-$(MKDIR) ./dev_scripts/.allure_results
	-$(MKDIR) ./dev_scripts/.allure_reports
ifeq ($(OS),Windows_NT)
	$(PDR) -wd dev_scripts -ex "docker-compose -f allure.yml up -d allure"
else
	cd ./dev_scripts/; MY_USER=$(shell id -u):$(shell id -g)  docker-compose -f allure.yml up -d allure
endif
	$(IPY) "print('Once tests have finished, your test report will be available at http://localhost:5050/allure-docker-service/latest-report. To clean results, use http://localhost:5050/allure-docker-service/clean-results')"

allure-report: ## Download report as zip
	$(IPY) "from urllib.request import urlretrieve; urlretrieve('http://localhost:5050/allure-docker-service/report/export', 'allure_report.zip')"

## Run smoke tests with reports to Allure server(Comment moved until https://github.com/tqdm/py-make/issues/11 is resolves)
test-smoke-allure: start-allure ## Run smoke tests and enable allure
	$(PDS)run_pymake_on_all.py --env "TEST_EXTRA_OPTS=--alluredir=../../dev_scripts/.allure_results" test-smoke
	$(PDS)launch_dir_in_browser.py http://localhost:5050/allure-docker-service/latest-report

 ## Run smoke tests with reports to Allure server(Comment moved until https://github.com/tqdm/py-make/issues/11 is resolves)
test-all-allure: start-allure ## Run all tests and enable allure
	$(PDS)run_pymake_on_all.py --env "TEST_EXTRA_OPTS=--alluredir=../../dev_scripts/.allure_results" test-all
	$(PDS)launch_dir_in_browser.py http://localhost:5050/allure-docker-service/latest-report

coverage-report: ## Generate coverage report for tests already ran
	coverage report -m
	coverage html -i
	$(PDS)launch_dir_in_browser.py htmlcov/index.html

coverage: ## Run all tests and then generate a coverage report
	$(MAKEALL) "coverage-all"
	coverage combine idmtools_cli/$(COVERAGE_PATH) idmtools_core/$(COVERAGE_PATH) idmtools_models/$(COVERAGE_PATH) idmtools_platform_comps/$(COVERAGE_PATH) idmtools_platform_local/$(COVERAGE_PATH)
	$(MAKE) coverage-report

coverage-smoke: ## Generate a code-coverage report
	$(MAKEALL) "coverage-smoke"
	coverage combine idmtools_cli/$(COVERAGE_PATH) idmtools_core/$(COVERAGE_PATH) idmtools_models/$(COVERAGE_PATH) idmtools_platform_comps/$(COVERAGE_PATH) idmtools_platform_local/$(COVERAGE_PATH)
	$(MAKE) coverage-report

dist: ## build our package
	$(MAKEALL) --parallel dist

release-staging: clean-all ## perform a release to staging
	$(MAKEALL) release-staging

packages-changes-since-last-verison: ## Get list of versions since last release that have changes
	git diff --name-only $(shell git tag -l --sort=-v:refname | grep -w '[0-9]\.[0-9]\.[0-9]' | head -n 1) HEAD | grep idmtools | cut -d "/" -f 1  | sort | uniq | grep -v ini | grep -v examples | grep -v dev_scripts

linux-dev-env: ## Runs docker dev env
	$(PDR) -w 'dev_scripts/linux-test-env' -ex 'docker-compose build linuxtst'
	$(PDR) -w 'dev_scripts/linux-test-env' -ex 'docker-compose run --rm linuxtst'

changelog: ## Generate partial changelog
	$(PDS)changelog.py

bump-release: #bump the release version.
	$(MAKEALL) bump-release

# Use before release-staging-release-commit to confirm next version.
bump-release-dry-run: ## perform a release to staging and bump the minor version.
	$(MAKEALL) bump-release-dry-run

bump-patch: ## bump the patch version
	$(MAKEALL) bump-patch

bump-minor: ## bump the minor version
	$(MAKEALL) bump-minor

bump-major: ## bump the major version
	$(MAKEALL) bump-major

bump-patch-dry-run: ## bump the patch version(dry run)
	$(MAKEALL) bump-patch-dry-run

bump-minor-dry-run: ## bump the minor version(dry run)
	$(MAKEALL) bump-minor-dry-run

bump-major-dry-run: ## bump the major version(dry run)
	$(MAKEALL) bump-major-dry-run

build-docs: ## build docs
	$(PDR) -wd 'docs' -ex 'make html'

docs: build-docs ## Alias for build docs

build-docs-server: build-docs ## builds docs and launch a webserver and watches for changes to documentation
	$(PDS)serve_docs.py

dev-watch: ## Run lint on any python code changes
	$(PDS)run_commands_and_wait.py --command 'watchmedo shell-command --drop --wait --interval 10 --patterns="*.py" --ignore-pattern="*/tests/.test_platform/*" --recursive --command="$(MAKE) --ignore-errors lint"' \
        --command 'watchmedo shell-command --patterns="*.py" --ignore-pattern="*/tests/.test_platform/*" --drop --interval 10 --recursive --command="$(MAKE) test-smoke";;;idmtools_platform_local'

generate-stubs: ## Generate python interfaces. Useful to identify what the next version should be by comparing to previous runs
	$(PDS)make_stub_files.py  -c dev_scripts/stub.cfg
	$(PDS)process_interfaces.py
=======
# Makefile for Sphinx docs
#

# You can set these variables from the command line.
SPHINXOPTS    = -t idmtools -W
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = _build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  dirhtml    to make HTML files named index.html in directories"
	@echo "  singlehtml to make a single large HTML file"
	@echo "  pickle     to make pickle files"
	@echo "  json       to make JSON files"
	@echo "  htmlhelp   to make HTML files and a HTML help project"
	@echo "  qthelp     to make HTML files and a qthelp project"
	@echo "  applehelp  to make an Apple Help Book"
	@echo "  devhelp    to make HTML files and a Devhelp project"
	@echo "  epub       to make an epub"
	@echo "  epub3      to make an epub3"
	@echo "  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf   to make LaTeX files and run them through pdflatex"
	@echo "  latexpdfja to make LaTeX files and run them through platex/dvipdfmx"
	@echo "  text       to make text files"
	@echo "  man        to make manual pages"
	@echo "  texinfo    to make Texinfo files"
	@echo "  info       to make Texinfo files and run them through makeinfo"
	@echo "  gettext    to make PO message catalogs"
	@echo "  changes    to make an overview of all changed/added/deprecated items"
	@echo "  xml        to make Docutils-native XML files"
	@echo "  pseudoxml  to make pseudoxml-XML files for display purposes"
	@echo "  linkcheck  to check all external links for integrity"
	@echo "  doctest    to run all doctests embedded in the documentation (if enabled)"
	@echo "  coverage   to run coverage check of the documentation (if enabled)"
	@echo "  dummy      to check syntax errors of document sources"

.PHONY: clean
clean:
	rm -rf $(BUILDDIR)/*
	rm -rf api/idmtools*.rst

.PHONY: generate-api

generate-api:
	-rm ./api/modules.rst
	-rm ./api/idmtools_index.rst
	sphinx-apidoc -f -e -M -o ./api --templatedir api_templates ../idmtools_core/idmtools
	mv ./api/modules.rst ./api/idmtools_index.rst

	-rm ./api/idmtools_models_index.rst
	sphinx-apidoc -f -e -M -o ./api --templatedir api_templates ../idmtools_models/idmtools_models
	mv ./api/modules.rst ./api/idmtools_models_index.rst

	-rm ./api/idmtools_platform_comps_index.rst
	sphinx-apidoc -f -e -M -o ./api --templatedir api_templates ../idmtools_platform_comps/idmtools_platform_comps
	mv ./api/modules.rst ./api/idmtools_platform_comps_index.rst

	-rm ./api/idmtools_platform_slurm_index.rst
	sphinx-apidoc -f -e -M -o ./api --templatedir api_templates ../idmtools_platform_slurm/idmtools_platform_slurm
	mv ./api/modules.rst ./api/idmtools_platform_slurm_index.rst

	-rm ./api/idmtools_slurm_utils_index.rst
	sphinx-apidoc -f -e -M -o ./api --templatedir api_templates ../idmtools_slurm_utils/idmtools_slurm_utils
	mv ./api/modules.rst ./api/idmtools_slurm_utils_index.rst

	-rm ./api/idmtools_platform_local_index.rst
	SPHINX_APIDOC_OPTIONS=members,undoc-members,show-inheritance,ignore-module-all sphinx-apidoc -f -e -M -o ./api --templatedir api_templates  ../idmtools_platform_local/idmtools_platform_local '../idmtools_platform_local/idmtools_platform_local/internals//*'
	mv ./api/modules.rst ./api/idmtools_platform_local_index.rst

.PHONY: html
html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

.PHONY: dirhtml
dirhtml:
	$(SPHINXBUILD) -b dirhtml $(ALLSPHINXOPTS) $(BUILDDIR)/dirhtml
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/dirhtml."

.PHONY: singlehtml
singlehtml:
	$(SPHINXBUILD) -b singlehtml $(ALLSPHINXOPTS) $(BUILDDIR)/singlehtml
	@echo
	@echo "Build finished. The HTML page is in $(BUILDDIR)/singlehtml."

.PHONY: pickle
pickle:
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) $(BUILDDIR)/pickle
	@echo
	@echo "Build finished; now you can process the pickle files."

.PHONY: json
json:
	$(SPHINXBUILD) -b json $(ALLSPHINXOPTS) $(BUILDDIR)/json
	@echo
	@echo "Build finished; now you can process the JSON files."

.PHONY: htmlhelp
htmlhelp:
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) $(BUILDDIR)/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in $(BUILDDIR)/htmlhelp."

.PHONY: qthelp
qthelp:
	$(SPHINXBUILD) -b qthelp $(ALLSPHINXOPTS) $(BUILDDIR)/qthelp
	@echo
	@echo "Build finished; now you can run "qcollectiongenerator" with the" \
	      ".qhcp project file in $(BUILDDIR)/qthelp, like this:"
	@echo "# qcollectiongenerator $(BUILDDIR)/qthelp/IDMDocumentation.qhcp"
	@echo "To view the help file:"
	@echo "# assistant -collectionFile $(BUILDDIR)/qthelp/IDMDocumentation.qhc"

.PHONY: applehelp
applehelp:
	$(SPHINXBUILD) -b applehelp $(ALLSPHINXOPTS) $(BUILDDIR)/applehelp
	@echo
	@echo "Build finished. The help book is in $(BUILDDIR)/applehelp."
	@echo "N.B. You won't be able to view it unless you put it in" \
	      "~/Library/Documentation/Help or install it in your application" \
	      "bundle."

.PHONY: devhelp
devhelp:
	$(SPHINXBUILD) -b devhelp $(ALLSPHINXOPTS) $(BUILDDIR)/devhelp
	@echo
	@echo "Build finished."
	@echo "To view the help file:"
	@echo "# mkdir -p $$HOME/.local/share/devhelp/IDMDocumentation"
	@echo "# ln -s $(BUILDDIR)/devhelp $$HOME/.local/share/devhelp/IDMDocumentation"
	@echo "# devhelp"

.PHONY: epub
epub:
	$(SPHINXBUILD) -b epub $(ALLSPHINXOPTS) $(BUILDDIR)/epub
	@echo
	@echo "Build finished. The epub file is in $(BUILDDIR)/epub."

.PHONY: epub3
epub3:
	$(SPHINXBUILD) -b epub3 $(ALLSPHINXOPTS) $(BUILDDIR)/epub3
	@echo
	@echo "Build finished. The epub3 file is in $(BUILDDIR)/epub3."

.PHONY: latex
latex:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo
	@echo "Build finished; the LaTeX files are in $(BUILDDIR)/latex."
	@echo "Run \`make' in that directory to run these through (pdf)latex" \
	      "(use \`make latexpdf' here to do that automatically)."

.PHONY: latexpdf
latexpdf:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

.PHONY: latexpdfja
latexpdfja:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo "Running LaTeX files through platex and dvipdfmx..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf-ja
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

.PHONY: text
text:
	$(SPHINXBUILD) -b text $(ALLSPHINXOPTS) $(BUILDDIR)/text
	@echo
	@echo "Build finished. The text files are in $(BUILDDIR)/text."

.PHONY: man
man:
	$(SPHINXBUILD) -b man $(ALLSPHINXOPTS) $(BUILDDIR)/man
	@echo
	@echo "Build finished. The manual pages are in $(BUILDDIR)/man."

.PHONY: texinfo
texinfo:
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) $(BUILDDIR)/texinfo
	@echo
	@echo "Build finished. The Texinfo files are in $(BUILDDIR)/texinfo."
	@echo "Run \`make' in that directory to run these through makeinfo" \
	      "(use \`make info' here to do that automatically)."

.PHONY: info
info:
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) $(BUILDDIR)/texinfo
	@echo "Running Texinfo files through makeinfo..."
	make -C $(BUILDDIR)/texinfo info
	@echo "makeinfo finished; the Info files are in $(BUILDDIR)/texinfo."

.PHONY: gettext
gettext:
	$(SPHINXBUILD) -b gettext $(I18NSPHINXOPTS) $(BUILDDIR)/locale
	@echo
	@echo "Build finished. The message catalogs are in $(BUILDDIR)/locale."

.PHONY: changes
changes:
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) $(BUILDDIR)/changes
	@echo
	@echo "The overview file is in $(BUILDDIR)/changes."

.PHONY: linkcheck
linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

.PHONY: doctest
doctest:
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) $(BUILDDIR)/doctest
	@echo "Testing of doctests in the sources finished, look at the " \
	      "results in $(BUILDDIR)/doctest/output.txt."

.PHONY: coverage
coverage:
	$(SPHINXBUILD) -b coverage $(ALLSPHINXOPTS) $(BUILDDIR)/coverage
	@echo "Testing of coverage in the sources finished, look at the " \
	      "results in $(BUILDDIR)/coverage/python.txt."

.PHONY: xml
xml:
	$(SPHINXBUILD) -b xml $(ALLSPHINXOPTS) $(BUILDDIR)/xml
	@echo
	@echo "Build finished. The XML files are in $(BUILDDIR)/xml."

.PHONY: pseudoxml
pseudoxml:
	$(SPHINXBUILD) -b pseudoxml $(ALLSPHINXOPTS) $(BUILDDIR)/pseudoxml
	@echo
	@echo "Build finished. The pseudo-XML files are in $(BUILDDIR)/pseudoxml."

.PHONY: dummy
dummy:
	$(SPHINXBUILD) -b dummy $(ALLSPHINXOPTS) $(BUILDDIR)/dummy
	@echo
	@echo "Build finished. Dummy builder generates no files."

