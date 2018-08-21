init:
	pip install -r requirements.txt

init-dev:
	pip install -r requirements_dev.txt

test:
	python setup.py test

install:
	python setup.py install

install-mecab:
	git clone https://github.com/taku910/mecab.git; \
	cd mecab/mecab; \
	./configure  --enable-utf8-only; \
	make; \
	make check; \
	sudo make install; \
	sudo ldconfig; \
	cd ../mecab-ipadic; \
	./configure --with-charset=utf8; \
	make; \
	sudo make install; \
	mecab --version; \
	pip install mecab-python3

doc:
	make init-dev; \
	sphinx-apidoc -F -o docs/ budou/; \
	sphinx-build -b html docs/ docs/_build/
