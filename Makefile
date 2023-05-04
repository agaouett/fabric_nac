SOURCES := $(wildcard *.md)
NBS := $(patsubst %.md,%.ipynb,$(SOURCES))

%.ipynb: %.md
	pandoc  --self-contained  $^ -o $@

all: $(NBS)

notebooks: $(NBS)

pdfs: $(PDFS)