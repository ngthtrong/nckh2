Remind for Camera-ready version:

For Springer CCIS papers, instruction is as following:

Deadline for final version: September 16, 2026

1. FINAL PAPER: Please submit the files belonging to your camera-ready paper using your EasyChair author account. Follow the instructions after the login for uploading two files:
2. either a zipped file containing all your LaTeX sources or a Word file, and
3. the PDF version of your camera-ready paper

The page limit is 12-15 and is strict. Please follow strictly the author instructions of Springer-Verlag (https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines) when preparing the final version. (./Lecture Notes in Computer Science _ Information for authors and editors.html)

2. COPYRIGHT: Please upload a signed and completed copyright form to us as soon as possible. The Springer copyright forms can be found at https://docs.google.com/document/d/1x7c0Gdny8aJ_VTgsC5grsCYiQj-GePrt/edit?usp=drive_link&ouid=100340418774707422809&rtpof=true&sd=true (./SNCS_ProceedingsPaper_LTP_ST_SN_Singapore.docx)

It is sufficient for one of the authors to sign the copyright form. You can scan the form into PDF.

You should also submit a signed copyright form. The copyright form can be submitted either together with the paper or separately.

Paper Prepared Using LaTeX
To submit your paper, you should upload a zip archive (with the extension .zip) and a PDF file. The archive must contain the LaTeX source required to produce your paper. Both EasyChair and Springer Verlag should be up to date and contain CTAN LaTeX packages. However, you should include in the archive all non-standard or locally used LaTeX packages.

The main LaTeX file must be in the top directory of the archive. Other files may be put in either the top directory or subdirectories of the archive. If you use LaTeX, before you put the files in the archive please check that running pdflatex (or latex) on your main file produces no errors. On Unix-like systems you can create the archive using the following procedure. Assume that the main LaTeX file is main.tex and it is placed in the directory papers/conf.

Then use the following sequence of actions

cd papers/conf
latex main
... check that the are no error messages ...
zip -r mypaper.zip *
It will produce the zip file mypaper.zip that can be uploaded. Your paper will be produced again from the LaTeX source. We will then use your pdf file to compare it with the files obtained from the source.

The main file name may not contain whitespace characters or any of the following symbols: \ / > < , ; ' " |.

Zip file:	No file chosen
PDF file:	No file chosen
Signed copyright form:	No file chosen
Name of the main LaTeX file:
Program to process the main file:
pdflatex,
xelatex,
latex,
lualatex
Program to process the bibliography:
bibtex,
biber,
(none)
