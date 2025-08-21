FROM python:3.11-slim

RUN apt-get update && apt install mysql-server

WORKDIR /app

COPY convert_xml.py .

COPY JMdict.xml ./

RUN mkdir -p /output

RUN python convert_xml.py your_massive_file.xml /output/search.db

#TODO: work out how to make this actually work (this is just a brainstorm of the idea)

