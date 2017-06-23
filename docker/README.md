mdid-docker
===========

Docker can be used to run MDID and its dependencies (e.g. rabbitmq, memcached,
etc.).

Images are published on the docker hub as
[wmit/mdid](https://hub.docker.com/r/wmit/mdid/) and
[wmit/solr4/mdid](https://hub.docker.com/r/wmit/solr4-mdid/)

## MDID Configuration

Settings outside of database connection information can be provided by
creating a new image, or by using the `docker config` tool introduced in Docker
17.06.

A simple overlay Dockerfile will look like
```
FROM wmit/mdid

COPY local_settings.py /opt/mdid/rooibos_settings/local_settings.py
```

In a perfect world, images are built automatically from version control, without
passwords or other secrets inside the image. To help make that a reality, MDID
supports providing database secrets in a few different ways.

### Environment Variables

MDID in Docker will check for environment variables named `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, and `DB_HOST` for the information. The method is discouraged as
environment information is rarely treated as secret by applications, but is
supported because it's often easier to use during development.

If `DB_PASSWORD` is set to a valid file path, the contents of that file will
be used as the database password.

### Docker Secrets (swarm mode)

If the environment variable `DB_PASSWORD` or the PASSWORD setting in
`config.ini` is set to a valid file path, the contents of that file will be used
as the database password.

## Building Images

The only images that are built from source are MDID and solr. They can
be build using [docker-compose](https://docs.docker.com/compose/). To build the
images using your code run `docker-compose build` from inside this directory.

## Running

To run MDID in a test environment, run the `docker-start.sh` script. Startup
can take around 40 seconds or so, 35 of which is waiting for MySQL to become
available.

## Swarm Mode

In addition to supporting docker secrets, the `stack.yml` file contains a file
ready to be used in conjunction with `docker stack deploy...` to get a system
ready for production. The stack ready compose file doesn't include a database
since persistent data in Swarm can still be challenging.

## Known Issues

cron jobs aren't run automatically in Docker and aren't accounted for in any of
the examples.
