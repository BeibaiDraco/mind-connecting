.PHONY: all clean arxiv

all: main.pdf

main.pdf: main.tex $(wildcard sections/*.tex) refs.bib $(wildcard figures/fig[1-6]_*.pdf)
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

# arXiv does not run BibTeX, so the upload carries main.bbl from the local build,
# plus every section that main.tex inputs and the six figures.
ARXIV_SECTIONS := $(shell grep -ho 'input{sections/[a-z_0-9]*}' main.tex sections/*.tex | sed 's/input{\(.*\)}/\1.tex/' | sort -u)
ARXIV_FIGURES := $(addprefix figures/,fig1_hook.pdf fig2_setup.pdf fig3_claim.pdf fig4_route.pdf fig5_moments.pdf fig6_twoway.pdf)

arxiv: main.pdf
	tar czf arxiv.tar.gz main.tex main.bbl $(ARXIV_SECTIONS) $(ARXIV_FIGURES)
	@echo "wrote paper/arxiv.tar.gz"

clean:
	latexmk -c main.tex
