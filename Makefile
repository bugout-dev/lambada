build:
	python setup.py sdist bdist_wheel

clean:
	mkdir -p build/ dist/ lambada.egg-info/
	rm -r build/ dist/ lambada.egg-info/

release: build
	twine upload dist/*
