# edulint-web

### Quickstart

You can start your own instance of EduLint (including the web interface) using Docker and docker-compose:

```sh
git clone https://github.com/GiraffeReversed/edulint-web.git
cd edulint-web

docker-compose -f docker-compose.yml -f docker-compose.local.yml up --build -d
```

The web UI will be reachable on http://127.0.0.1:4999 only from your PC. If you want to change that, you can modify `docker-compose.local.yml` to use `0.0.0.0:4999:80` instad of `127.0.0.1:4999:80`.
