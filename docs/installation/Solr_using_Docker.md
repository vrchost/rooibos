For testing and development purposes, you may want to run Solr using Docker.  In the directory you initialized
using `mdid init`, run:

```
docker run -d -p 8983:8983 --name mdid_solr -v $PWD/var/solr:/mdid solr:7.7.3 solr-precreate mdid /mdid
```
