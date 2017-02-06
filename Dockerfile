FROM phusion/baseimage:0.9.19

RUN apt-get update -q && apt-get upgrade -qy \
    && apt-get install -qy python-setuptools python-pip \
    && apt-get clean

RUN pip install -U pip setuptools wheel

RUN pip install click python-dockercloud

RUN mkdir -p /etc/service/dc_api_cron
COPY cron_manager.py /etc/service/dc_api_cron/run
RUN chmod 0755 /etc/service/dc_api_cron/run

RUN mkdir -p /opt/dc_api_cron
COPY endpoint_manager.py /opt/dc_api_cron/manage.py
RUN chmod 0755 /opt/dc_api_cron/manage.py

RUN touch /var/log/cron.log
