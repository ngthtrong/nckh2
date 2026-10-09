PYTHON ?= python3
BIBLIOGRAPHY ?= auto
TARGETS := content bulletin-vi bulletin-en summary-vi summary-en smoke
.PHONY: all $(TARGETS) content-twoside deliverables check doctor clean
all: content content-twoside deliverables
$(TARGETS):
	$(PYTHON) scripts/build.py $@ --bibliography $(BIBLIOGRAPHY)
content-twoside:
	$(PYTHON) scripts/build.py content --twoside --bibliography $(BIBLIOGRAPHY)
deliverables: bulletin-vi bulletin-en summary-vi summary-en
check:
	$(PYTHON) scripts/check_template.py
doctor:
	$(PYTHON) scripts/doctor.py
clean:
	$(PYTHON) -c 'import shutil; shutil.rmtree("build", ignore_errors=True)'
