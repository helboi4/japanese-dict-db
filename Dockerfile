FROM postgres:17.6

COPY dictionary_dump.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
