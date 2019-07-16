cat ../_data/papers.yaml ../_data/code.yaml > /tmp/all.yaml
jinja2 cv.tex /tmp/all.yaml --format yaml > cv.comp.tex
pdflatex cv.tex
jinja2 cv_short.tex /tmp/all.yaml --format yaml > cv_short.comp.tex
pdflatex cv_short.tex
