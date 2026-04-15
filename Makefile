#################################################################################
# GLOBALS                                                                       #
#################################################################################

SHELL := /bin/sh

#################################################################################
# COMMANDS                                                                      #
#################################################################################


.PHONY: requirements 
requirements:
	@uv sync


.PHONY: clean
clean:
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@find . -type d -name ".mypy_cache" -exec rm -r {} +
	@find . -type d -name ".pytest_cache" -exec rm -r {} +


.PHONY: lint
lint:
	@uv run mypy --strict src/
	@uv run mypy tests/
	@uv run pylint src/ tests/


.PHONY: format
format:
	@uv run black src/ tests/


.PHONY: test
test:
	@uv run python -m pytest tests/


## Soft diagnostics
.PHONY: precommit
precommit:
	@$(MAKE) --no-print-directory format || true
	@$(MAKE) --no-print-directory lint || true
	@$(MAKE) --no-print-directory test || true


.PHONY: git_precommit_hook
git_precommit_hook:
	@./scripts/git_enforce_staged.sh
	@uv run black --check src/
	@uv lock --check
	@$(MAKE) lint 
	@$(MAKE) test 
	@$(MAKE) clean
	@./scripts/git_enforce_staged.sh

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

.PHONY: help
help:
	@uv run python -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
