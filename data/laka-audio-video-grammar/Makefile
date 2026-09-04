.PHONY: install test demo render-demo serve clean

install:
	pip install -e ".[dev]"

# Unit and integration checks
test:
	PYTHONPATH=src pytest -q

# Compile deterministic sample to JSON + browser preview
demo:
	PYTHONPATH=src python -m laka_video compile examples/demo/project.yml --strict

render-demo:
	PYTHONPATH=src python -m laka_video render examples/demo/project.yml --quality draft

serve:
	PYTHONPATH=src python -m laka_video serve

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
