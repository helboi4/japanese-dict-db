FROM postgres:16.10

COPY dictionary_dump.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
