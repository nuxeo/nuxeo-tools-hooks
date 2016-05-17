FROM ubuntu:latest

RUN apt-get update && apt-get install -y python python-pip apache2 libapache2-mod-wsgi

RUN a2dissite 000-default

COPY ./entrypoint.sh /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
