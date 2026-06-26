FROM debian:stretch-slim
RUN echo 'deb http://archive.debian.org/debian stretch main' > /etc/apt/sources.list \
 && apt-get -o Acquire::Check-Valid-Until=false update \
 && apt-get install -y --no-install-recommends python2.7 python-tz \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY legacy/ /app/
COPY gen_golden.py datasets.json /app/
ENTRYPOINT ["python2.7", "gen_golden.py", "datasets.json", "/out/ephemeris.json"]
