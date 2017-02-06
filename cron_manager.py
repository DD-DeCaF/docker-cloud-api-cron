#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017 Novo Nordisk Foundation Center for Biosustainability,
# Technical University of Denmark.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate cron jobs from environment variables suitable for docker cloud.

This is run as a service within a phusion/baseimage docker container. It needs
to be run after environment variables have been initialized but really only
needs to be run once. However, a docker container needs an on-going process or
it exits. An alternative would be a script that runs this Python script once and
then the cron daemon in the foreground. For the time being this just sleeps for
a very long time.

The environment variables should have the following format in order to be
correctly installed as cron jobs:

1. Their names begin with ``DC_CRON``.
2. Their content should be a string describing a cron schedule plus a docker
   cloud service or stack endpoint given by its name or UUID.
3. Optionally, a log level can be defined and logs of the script that manages
   the docker cloud API endpoint are stored in `/var/log/dc_cron*.log` inside of
   the container.

    * * * * * <service|stack> <name|uuid> [LEVEL]
    | | | | |
    | | | | |
    | | | | +---- Day of the Week   (range: 1-7, 1 standing for Monday)
    | | | +------ Month of the Year (range: 1-12)
    | | +-------- Day of the Month  (range: 1-31)
    | +---------- Hour              (range: 0-23)
    +------------ Minute            (range: 0-59)
"""

from __future__ import absolute_import

import os
import io
import logging

from subprocess import check_output
from glob import glob
from collections import Counter
from time import sleep

import click


def make_log_name(dc_type, dc_id, namespace):
    """Generate a unique name for the log file."""
    name = u"dc_cron_{}_{}".format(dc_type, dc_id)
    namespace[name] += 1
    count = namespace[name]
    if count > 1:
        name += u"_{0:d}.log".format(count)
    else:
        name += u".log"
    return name


def make_cron_line(job, namespace):
    """Generate the full crontab line from the environment variable."""
    with io.open(job, "r") as file_h:
        entries = file_h.read().strip().split()
    log_name = make_log_name(entries[5], entries[6], namespace)
    line = u"{schedule} /opt/dc_api_cron/manage.py".format(
        schedule=u" ".join(entries[:5])
    )
    if len(entries) > 7:
        line += u" --log-level={level}".format(level=entries[7])
    line += u" {type} {id} >> /var/log/{log_name} 2>&1\n".format(
        type=entries[5],
        id=entries[6],
        log_name=log_name
    )
    return line


def add_dockercloud_env(lines):
    if "DOCKERCLOUD_AUTH" in os.environ:
        lines.append(u"DOCKERCLOUD_AUTH={}\n".format(
            os.environ["DOCKERCLOUD_AUTH"]
        ))
    if "DOCKERCLOUD_USER" in os.environ and\
            "DOCKERCLOUD_APIKEY" in os.environ:
        lines.append(u"DOCKERCLOUD_USER={}\n".format(
            os.environ["DOCKERCLOUD_USER"]
        ))
        lines.append(u"DOCKERCLOUD_APIKEY={}\n".format(
            os.environ["DOCKERCLOUD_APIKEY"]
        ))
    if "DOCKERCLOUD_NAMESPACE" in os.environ:
        lines.append(u"DOCKERCLOUD_NAMESPACE={}\n".format(
            os.environ["DOCKERCLOUD_NAMESPACE"]
        ))


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option("--log-level", "-l", default="WARN",
              type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]),
              help="Set the logging level.")
def main(log_level):
    """
    Generate cron jobs from environment variables suitable for docker cloud.
    """
    LOGGER.setLevel(log_level)
    LOGGER.info("installing new crontab")
    jobs = sorted(glob("/etc/container_environment/DC_CRON*"))
    logs = Counter()
    lines = list()
    # cron jobs environment variables
    lines.append(u'MAILTO=""\n')  # disable MTA
    add_dockercloud_env(lines)
    for cron_job in jobs:
        cron_line = make_cron_line(cron_job, logs)
        LOGGER.info(cron_line.strip())
        lines.append(cron_line)
    with io.open("/tmp/crontab.tmp", "w") as crontab:
        crontab.writelines(lines)
    check_output(["crontab", "/tmp/crontab.tmp"])
    while True:
        # Environment variables of a running container cannot be updated but
        # since this runs as a service it would be restarted all the time.
        sleep(86400)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARN,
        format="[%(asctime)s %(levelname)s] %(message)s"
    )
    LOGGER = logging.getLogger()
    main()
    logging.shutdown()
