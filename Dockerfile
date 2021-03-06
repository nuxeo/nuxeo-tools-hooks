FROM python:2.7-slim

ENV BUILD_DATE=201905271800

RUN apt-get update && \
    apt-get install -y gcc libffi-dev libssl-dev build-essential libssl-dev libffi-dev python2.7-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/

RUN pip install pathlib2==2.1.0 cryptography

COPY dist /opt/dist

RUN pip install --upgrade /opt/dist/nuxeo-tools-hooks-*.tar.gz

CMD ["python", "-m", "nxtools.hooks.app"]

EXPOSE 8888
