.PHONY: test check preview verify serve clean wheel

test:
	python -m unittest discover -s tests -v

check:
	python -m spek check

preview:
	python -m spek build --out dist --formats html,pdf,tex

verify:
	python -m spek verify-site dist

serve:
	python -m http.server 8000 --directory dist

clean:
	rm -rf dist build *.egg-info
