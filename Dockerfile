FROM postgres:16.10

ENV POSTGRES_DB=dictionary

COPY dictionary_dump.sql /docker-entrypoint-initdb.d/00-dictionary_dump.sql

EXPOSE 5432
