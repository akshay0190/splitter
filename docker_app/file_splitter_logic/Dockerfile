#Use amazonlinux to avoid vulnerabilities
FROM amazonlinux:2.0.20210326.0

#Set WORKDIR
ARG WORKING_DIR=/execute/file_splitter_scripts/

#Installs/Updates to fix vulnerabilities
RUN yum -y install nghttp2
RUN yum -y install file
RUN yum -y update curl
RUN yum -y update python
RUN yum -y install python3


#Setup python environment
RUN mkdir -p $d .
WORKDIR $WORKING_DIR
COPY file_splitter_logic .

RUN pip3 install -r requirements.txt

#Run script
CMD ["python3","file_splitter_handler.py"]
#CMD ["/bin/bash"]