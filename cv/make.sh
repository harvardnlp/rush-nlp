cat ../_data/papers.yaml ../_data/extra.yaml ../_data/code.yaml ../_data/projects.yaml > /tmp/all.yaml
jinja2 cv.tex /tmp/all.yaml --format yaml > cv.comp.tex
pdflatex cv.comp.tex
jinja2 cv_short.tex /tmp/all.yaml --format yaml > cv_short.comp.tex
pdflatex cv_short.comp.tex
jinja2 cv_tenure.tex /tmp/all.yaml --format yaml > cv_tenure.comp.tex
pdflatex cv_tenure.comp.tex
