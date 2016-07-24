default: build

.PHONY:build
build: 
	  python ./setup.py build develop


.PHONY: test
test: 
	python -m unittest discover -v test

.PHONY: doc
doc: build $(wildcard doc/*.rst)
	$(MAKE) -C doc html

.PHONY: doczip
doczip: doc
	T=$$PWD; (cd doc/_build/html; zip -r $$T/Swoop-$$(cat $$T/VERSION.txt)-docs.zip *)

.PHONY: diff
diff: 
	diff Swoop/eagle-7.2.0.dtd Swoop/eagle-swoop.dtd > Swoop/eagle.dtd.diff

.PHONY: release
release: clean
	touch VERSION.txt
	git commit -m "Commit before release $$(cat VERSION.txt)" -a
	git push
	git checkout release
	git merge --no-ff master
	git tag -a $$(cat VERSION.txt) -m "Tag version $$(cat VERSION.txt)"
	git push --follow-tags
	$(MAKE) test_dist
	python setup.py sdist upload
	$(MAKE) doczip

.PHONY: test_dist
test_dist:
	@echo Building source distribution
	@python setup.py sdist > sdist.log 2>&1 || (tail -10 sdist.log; echo FAILED; false)
	rm -rf test_dist
	mkdir test_dist
	virtualenv test_dist/venv
	@echo Installing distribution in clean venv.  This will take a while...
	@(. test_dist/venv/bin/activate; pip install dist/Swoop-$$(cat VERSION.txt).tar.gz ); grep -q 'Failed.*Swoop' < build_test.log || (tail -10 build_test.log; echo FAILED; false)
	@echo SUCCESS!
	@echo Running tests
	@(cd test_dist; python -m unittest discover -v ../test)	

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
