PYTHON ?= python3
BIBLIOGRAPHY ?= auto
TARGETS := content full smoke bulletin-vi bulletin-en summary-vi summary-en
.PHONY: all $(TARGETS) deliverables content-twoside full-twoside check check-release doctor clean
all: content
$(TARGETS):
	$(PYTHON) scripts/build.py $@ --bibliography $(BIBLIOGRAPHY)
deliverables: bulletin-vi bulletin-en summary-vi summary-en
content-twoside:
	$(PYTHON) scripts/build.py content --twoside --bibliography $(BIBLIOGRAPHY)
full-twoside:
	$(PYTHON) scripts/build.py full --twoside --bibliography $(BIBLIOGRAPHY)
check:
	$(PYTHON) scripts/check_report.py
check-release:
	$(PYTHON) scripts/check_report.py --release
doctor:
	$(PYTHON) scripts/doctor.py
clean:
	$(PYTHON) -c 'import shutil; shutil.rmtree("build", ignore_errors=True)'
