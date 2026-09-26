.PHONY: all clean

all: main.pdf

main.pdf: main.tex $(wildcard sections/*.tex) refs.bib $(wildcard figures/fig[1-6]_*.pdf)
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	latexmk -c main.tex
