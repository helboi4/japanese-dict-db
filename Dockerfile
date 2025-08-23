FROM python:3.11-slim

RUN apt-get update && apt-get install -y postgresql postgresql-contrib libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY convert_xml.py .
COPY requirements.txt .
COPY JMdict.xml .

RUN pip install -r requirements.txt

USER postgres
RUN service postgresql start && \
    psql -c "CREATE DATABASE dictionary;" && \
    psql -c "CREATE USER dictreader;" && \
    psql dictionary -c "GRANT CONNECT ON DATABASE dictionary TO dictreader;" && \
    cd /app && \
    python convert_xml.py && \
    psql dictionary -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO dictreader;" && \
    psql dictionary -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO dictreader;" && \
    psql -c "ALTER USER postgres WITH NOLOGIN;" && \
    echo "listen_addresses = '*'" >> /etc/postgresql/*/main/postgresql.conf && \
    echo "host dictionary dictreader 0.0.0.0/0 trust" >> /etc/postgresql/*/main/pg_hba.conf && \
    echo "local all postgres peer" >> /etc/postgresql/*/main/pg_hba.conf && \
    service postgresql stop

USER root

RUN rm JMdict.xml convert_xml.py requirements.txt

EXPOSE 5432

CMD service postgresql start && tail -f /dev/null
