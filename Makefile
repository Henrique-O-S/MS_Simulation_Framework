SCENARIO ?= baseline

# detect OS
ifeq ($(OS),Windows_NT)
    # Windows settings
    PYTHON = python
    PIP = pip
    SEP = \\
    RM = - rd /s /q
	RMF = del
    SCRIPTS = Scripts
	COPY = copy
else
    # Linux settings
    PYTHON = python3
    PIP = pip3
    SEP = /
    RM = rm -rf
	RMF = $(RM)
    SCRIPTS = bin
	COPY = cp
endif

all: install

# create a virtual environment
venv:
	$(PYTHON) -m venv .venv
	.venv$(SEP)$(SCRIPTS)$(SEP)activate

# install project dependencies
install: venv
	.venv$(SEP)$(SCRIPTS)$(SEP)pip install -r requirements.txt

help:
	@echo Usage: make [target]
	@echo Targets:
	@echo    all: install project dependencies
	@echo    venv: create a virtual environment
	@echo    install: install project dependencies
	@echo    run: run the project
	@echo    clean: clean up generated files and virtual environment
	@echo Run modes:
	@echo    "make run [SCENARIO=baseline|future|inner|outer|balanced]"

load_env:
ifeq ($(SCENARIO), baseline)
	$(COPY) config$(SEP).env.baseline .env
else ifeq ($(SCENARIO), future)
	$(COPY) config$(SEP).env.future .env
else ifeq ($(SCENARIO), inner)
	$(COPY) config$(SEP).env.inner .env
else ifeq ($(SCENARIO), outer)
	$(COPY) config$(SEP).env.outer .env
else ifeq ($(SCENARIO), balanced)
	$(COPY) config$(SEP).env.balanced .env
endif

# run the project
run: load_env
	$(PYTHON) main.py

# clean up generated files and virtual environment
clean:
	$(RM) .venv
	$(RM) __pycache__
	$(RM) entities$(SEP)__pycache__
	$(RM) logs$(SEP)__pycache__

.PHONY: all venv install clean