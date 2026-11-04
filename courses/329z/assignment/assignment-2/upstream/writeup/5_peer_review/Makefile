DOC := peer_review

.PHONY: all clean cleanall

all: $(DOC).pdf

$(DOC).pdf: $(DOC).tex cs329z.sty
	latexmk -pdf -halt-on-error -interaction=nonstopmode $(DOC).tex

clean:
	latexmk -c $(DOC).tex

cleanall: clean
	rm -f $(DOC).pdf
