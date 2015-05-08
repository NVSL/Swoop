default: build

.PHONY:build
build: 
	@if [ "$$USE_VENV." = "yes." ]; then\
	  echo python ./setup.py build develop;\
	  python ./setup.py build develop;\
	else\
	  echo python ./setup.py build;\
	  python ./setup.py build;\
	fi

.PHONY: test
test: 
	python -m unittest discover test

.PHONY: doc
doc: build $(wildcard doc/*.rst)
	$(MAKE) -C doc html

.PHONY: diff
diff: 
	diff Swoop/eagle-7.2.0.dtd Swoop/eagle-swoop.dtd > Swoop/eagle.dtd.diff

.PHONY: release
release: clean
	svn commit -m "Commit before release $$(cat VERSION.txt)"
	python setup.py sdist upload

clean:
	rm -rf Swoop/eagleDTD.py
	rm -rf test/inputs/*.broken.xml
	rm -rf Swoop/Swoop.py
	if [ -d doc ]; then $(MAKE) -C doc clean; fi
	rm -rf *~
	rm -rf .eggs
	rm -rf Swoop.egg-info
	rm -rf build 
	find . -name '*.pyc' | xargs rm -rf
