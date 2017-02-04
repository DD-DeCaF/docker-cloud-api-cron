FROM phusion/baseimage:0.9.19

RUN apt-get update -q && apt-get upgrade -qy \
    && apt-get install -qy python-pip \
    && apt-get clean

RUN pip install -U pip setuptools wheel

RUN pip install python-dockercloud

ENV DOCKERCLOUD_USER DOCKERCLOUD_APIKEY

RUN mkdir -p /etc/service/dc_api_cron/run
COPY env_watcher.py /etc/service/dc_api_cron/run
RUN chmod u=rx /etc/service/dc_api_cron/run

RUN mkdir -p /opt/dc_api_cron
COPY manage.py /opt/dc_api_cron/
RUN chmod u=rx /opt/dc_api_cron/manage.py

RUN touch /var/log/cron.log
