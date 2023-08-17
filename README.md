# edulint-web

[![Docker image](https://img.shields.io/docker/image-size/edulint/edulint-web/latest?label=Docker%20image%20size)](https://hub.docker.com/r/edulint/edulint-web)

This repository contains backend (API) of edulint-web and the docker-compose files for easy deployment of all components together.


### Quickstart

You can start your own instance of EduLint (including the [web interface](https://github.com/GiraffeReversed/edulint-web-frontend)) using Docker and docker-compose:

```sh
git clone https://github.com/GiraffeReversed/edulint-web.git
cd edulint-web

docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

- The web UI will be reachable on http://127.0.0.1:4999 only from your PC. If you want to change that, you can modify `docker-compose.local.yml` to use `0.0.0.0:4999:80` instead of `127.0.0.1:4999:80`.
