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
Generate cron jobs on the docker cloud via their API.

Every hour, check the environment for variables beginning with DC_CRON and
install them to the crontab. The variables should contain a string with the
following format:

    * * * * * <service|stack> <name|uuid>
    | | | | |
    | | | | |
    | | | | +---- Day of the Week   (range: 1-7, 1 standing for Monday)
    | | | +------ Month of the Year (range: 1-12)
    | | +-------- Day of the Month  (range: 1-31)
    | +---------- Hour              (range: 0-23)
    +------------ Minute            (range: 0-59)

So a normal cron schedule followed by the docker cloud endpoint type and its
name or uuid.
"""

from __future__ import absolute_import

import io
import logging

from time import sleep
from subprocess import (check_output, CalledProcessError)
from glob import glob
from collections import Counter

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


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option("--snooze", "-s", type=float, default=20.0,
              help="time in seconds until the environment is checked again")
@click.option("--log-level", "-l", default="WARN",
              type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]),
              help="set the logging level")
def watcher(snooze, log_level):
    """Generate cron jobs for the docker cloud from environment variables."""
    LOGGER.setLevel(log_level)
    while True:
        LOGGER.info("installing new crontab")
        jobs = sorted(glob("/etc/container_environment/DC_CRON*"))
        logs = Counter()
        lines = list()
        lines.append(u'MAILTO=""\n')  # disable MTA
        for cron_job in jobs:
            cron_line = make_cron_line(cron_job, logs)
            LOGGER.info(cron_line.strip())
            lines.append(cron_line)
        dirty = True
        try:
            old_tab = check_output(["crontab", "-l"])
            dirty = ("".join(lines) != old_tab)
        except CalledProcessError as err:
            LOGGER.error(str(err))
        if dirty:
            with io.open("/tmp/crontab.tmp", "w") as crontab:
                crontab.writelines(lines)
            check_output(["crontab", "/tmp/crontab.tmp"])
        sleep(snooze)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARN,
        format="[%(asctime)s %(levelname)s] %(message)s"
    )
    LOGGER = logging.getLogger()
    watcher()
    logging.shutdown()
