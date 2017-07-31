FROM openjdk:8-jre-alpine

ADD https://archive.apache.org/dist/lucene/solr/4.10.4/solr-4.10.4.tgz /tmp/solr.tgz
RUN mkdir /opt \
    && cd /tmp \
    && tar -xf solr.tgz \
    && mv /tmp/solr-4.10.4/example /opt/solr \
    && rm -Rf /tmp/solr-4.10.4 \
    && rm -Rf /opt/solr/example-DIH /opt/solr/solr-webapp \
      /opt/solr/exampledocs \
      /opt/solr/example-schemaless /opt/solr/solr /opt/solr/multicore \
      /opt/solr/scripts /opt/solr/*.txt

COPY . /opt/solr/config
RUN mv /opt/solr/config/template /opt/solr/config/mdid

VOLUME ["/opt/solr/config/mdid/data"]

EXPOSE 8983
WORKDIR /opt/solr
CMD ["java", "-Dsolr.solr.home=/opt/solr/config", "-jar",  "/opt/solr/start.jar"]
