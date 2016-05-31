FROM ubuntu:latest

RUN apt-get update && apt-get install -y python python-pip apache2 libapache2-mod-wsgi

RUN a2dissite 000-default
RUN ln -nsf /proc/self/fd/1 /var/log/apache2/access.log
RUN ln -nsf /proc/self/fd/1 /var/log/apache2/other_vhosts_access.log
RUN ln -nsf /proc/self/fd/2 /var/log/apache2/error.log

COPY ./entrypoint.sh /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
