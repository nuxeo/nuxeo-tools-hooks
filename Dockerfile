FROM python:2.7-slim

ENV BUILD_DATE=201609011200

RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev && apt-get clean && rm -rf /var/lib/apt/lists/

RUN pip install pathlib2==2.1.0

COPY dist /opt/dist

RUN pip install --upgrade /opt/dist/nuxeo-tools-hooks-*.tar.gz

EXPOSE 8888