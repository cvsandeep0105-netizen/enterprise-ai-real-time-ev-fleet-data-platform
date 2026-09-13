FROM apache/spark:3.5.1

USER root

RUN apt-get update \
    && apt-get install -y curl \
    && curl -L https://jdbc.postgresql.org/download/postgresql-42.7.3.jar -o /opt/spark/jars/postgresql-42.7.3.jar \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/spark/app

COPY transform_vehicle_data.py /opt/spark/app/transform_vehicle_data.py

ENV PYTHONUNBUFFERED=1
