.PHONY: all develop test lint clean doc format


# The package name
PKG=ldif


all: test lint

#
# Setup
#
develop: install-deps activate-pre-commit configure-git

install-deps:
	@echo "--> Installing dependencies"
	uv sync

activate-pre-commit:
	@echo "--> Activating pre-commit hook"
	pre-commit install

configure-git:
	@echo "--> Configuring git"
	git config branch.autosetuprebase always

#
# testing & checking
#
test-all: test

test:
	@echo "--> Running Python tests"
	pytest --ff -x -p no:randomly
	@echo ""

test-randomly:
	@echo "--> Running Python tests in random order"
	pytest
	@echo ""

test-with-coverage:
	@echo "--> Running Python tests"
	py.test --cov $(PKG)
	@echo ""

test-with-typeguard:
	@echo "--> Running Python tests with typeguard"
	pytest --typeguard-packages=${PKG}
	@echo ""

#
# Various Checkers
#
lint: lint-py lint-rst lint-doc

lint-ci: lint

lint-py:
	@echo "--> Linting Python files /w various tools"
	ruff check src tests
	pyrefly check src
	@echo ""

lint-rst:
	@echo "--> Linting .rst files"
	rst-lint *.rst
	@echo ""

lint-doc:
	@echo "--> Linting doc"
	@echo "TODO"
	#sphinx-build -W -b dummy docs/ docs/_build/
	#sphinx-build -b dummy docs/ docs/_build/
	@echo ""

#
# Formatting
#
format: format-py

format-py:
	docformatter -i -r src tests
	black src tests
	isort src tests

#
# Everything else
#
install:
	uv sync

doc: doc-html doc-pdf

doc-html:
	sphinx-build -W -b html docs/ docs/_build/html

doc-pdf:
	sphinx-build -W -b latex docs/ docs/_build/latex
	make -C docs/_build/latex all-pdf

clean:
	adt clean
	rm -f **/*.pyc
	find . -type d -empty -delete
	rm -rf *.egg-info *.egg .coverage .eggs .cache .mypy_cache .pyre \
		.pytest_cache .pytest .DS_Store  docs/_build docs/cache docs/tmp \
		dist build pip-wheel-metadata junit-*.xml htmlcov coverage.xml

tidy: clean
	rm -rf .tox

update-deps:
	uv sync -U
	uv pip list --outdated
	pre-commit autoupdate

publish: clean
	git push --tags
	uv build
	twine upload dist/*
