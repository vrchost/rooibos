For testing and development purposes, you may want to run some services using Docker.  
In the directory you initialized using `mdid init`, run the following commands:


Solr
----

```
docker run -d -p 8983:8983 --name mdid_solr -v $PWD/var/solr:/mdid solr:8.11.1 solr-precreate mdid /mdid
```

Please note that you want to use at least version 8.11.1 of Solr to avoid the Log4j vulnerability.


RabbitMQ
--------

```
docker run -d -p 5672:5672 --hostname my-rabbit --name mdid_rabbitmq rabbitmq:3
```
