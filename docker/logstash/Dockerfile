FROM java:8-jre

RUN mkdir /opt/logstash
RUN wget -O /tmp/logstash.zip https://download.elastic.co/logstash/logstash/logstash-2.3.4.zip && \
    unzip -d /opt/logstash /tmp/logstash.zip && \
    ln -s /opt/logstash/logstash-2.3.4 /opt/logstash/logstash && \
    rm /tmp/logstash.zip

RUN /opt/logstash/logstash/bin/logstash-plugin install logstash-output-logmatic

ADD logstash.conf /opt/logstash/logstash.conf

ENTRYPOINT ["/opt/logstash/logstash/bin/logstash"]

CMD ["-f", "/opt/logstash/logstash.conf", "-v"]

