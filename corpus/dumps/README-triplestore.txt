This archive contains the dump of the OpenCitations Corpus (OCC, http://opencitations.net) triplestore (Blazegraph, https://www.blazegraph.com/, licensed in GPLv2) containing all the data of the corpus, and created regularly every month.

After unzipping the archive, Disk ARchive (DAR, http://dar.linux.free.fr/, a multi-platform archive tool for managing huge amount of data) is needed for recreating the whole structure. For extracting the DAR archive, please run the command

dar -x [archive-name]

Where "[archive-name"] is the name of the DAR file without final package number and extension. E.g.:

dar -x 2016-09-23-triplestore

Please execute "run.sh" for running the triplestore, and use "stop.sh" for stopping it.

For further questions, comments, and suggestions please don't hesitate to contact Silvio Peroni at essepuntato@opencitations.net.