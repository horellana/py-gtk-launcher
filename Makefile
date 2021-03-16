build:
	cp src/* build/
	pip install --target ./build/vendor -r requirements.txt

.PHONY: build
