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

So a normal cron schedule followed by the docker cloud object type and its name
or uuid.
"""

from __future__ import absolute_import

import sys
import os
import io
import logging

from time import sleep
from subprocess import check_output

LOGGER = logging.getLogger(__name__)


def main(wait_time=3600):
    while True:
        LOGGER.info("installing new crontab")
        with io.open("/tmp/crontab.tmp", "w") as file_h:
            for cron in (var for var in os.environ if var.startswith("DC_CRON")):
                entries = os.environ[cron].split()
                line = u"{schedule} /opt/dc_api_cron/manage.py {object} {id}\n".format(
                    schedule=" ".join(entries[:5]),
                    object=entries[5],
                    id=entries[6]
                )
                LOGGER.info(line.strip())
                file_h.write(line)
            check_output(["crontab", "/tmp/crontab.tmp"])
        sleep(wait_time)

if __name__ == "__main__":
    root = logging.getLogger()
    for handler in root.handlers:
        root.removeHandler(handler)
    logging.basicConfig(
        level="INFO",
        format="[%(asctime)s %(levelname)s] %(message)s"
    )
    try:
        main()
        rc = 0
    except StandardError as err:
        LOGGER.critical(str(err))
        rc = 1
    finally:
        logging.shutdown()
        sys.exit(rc)

