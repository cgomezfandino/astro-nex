FROM debian:stretch-slim
RUN echo 'deb http://archive.debian.org/debian stretch main' > /etc/apt/sources.list \
 && apt-get -o Acquire::Check-Valid-Until=false update \
 && apt-get install -y --no-install-recommends python2.7 python-tz \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# legacy/ provides pysw.py, _pysw.so (ephemeris). utils.py + directions.py are
# the ORIGINAL legacy source (copied in at build time, see gen_golden.sh / plan).
COPY legacy/ /app/
COPY gen_golden.py boss_stub.py datasets.json /app/
# 4th arg selects output: "ephemeris" (default) or "directions"
ENTRYPOINT ["python2.7", "gen_golden.py", "datasets.json", "/out/out.json", "ephemeris"]
