
all: language-tool

language-tool: source/app.d source/languages.d source/stats.d dub.json
	dub build -b release

clean:
	rm -f language-tool
	rm -rf tmp


# get started here for more URLs: https://dict.wortschatz-leipzig.de/de?corpusId=eng-simple_wikipedia_2021
langs: lang-bul lang-ces lang-dan lang-deu lang-ell lang-eng lang-ekk lang-fin lang-fra lang-gle lang-hrv lang-hun lang-hye lang-isl lang-ita lang-lav lang-lit lang-ltz lang-mlt lang-nld lang-nor lang-pol lang-por lang-ron lang-slk lang-slv lang-spa lang-sqi lang-srp lang-swe lang-ukr lang-slop

lang-%: language-tool
	./build-language.sh $* "https://downloads.wortschatz-leipzig.de/corpora/$*_wikipedia_2021_30K.tar.gz"

lang-eng: language-tool
	./build-language.sh eng "https://downloads.wortschatz-leipzig.de/corpora/eng-simple_wikipedia_2021_30K.tar.gz"

lang-lav: language-tool
	./build-language.sh lav "https://downloads.wortschatz-leipzig.de/corpora/lav_wikipedia_2014_30K.tar.gz"

lang-slop: language-tool
	cp "res/slop.tar.gz" "tmp/slop.tar.gz"
	./build-language.sh slop "---"

checker: langs
	cp -r languages languages-additional ../../checker/res/
