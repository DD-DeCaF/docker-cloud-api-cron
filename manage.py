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
Expect input in the following format:

./manage.py <stack|service> <name|uuid>

Expects the following environment variables to be set:

    DOCKERCLOUD_USER
    DOCKERCLOUD_APIKEY

and possibly:

    DOCKERCLOUD_NAMESPACE
"""

from __future__ import (absolute_import, print_function)

import sys
import os
import logging

from time import sleep
from math import ceil

import dockercloud as dc

LOGGER = logging.getLogger(__name__)
DOCKERCLOUD_OBJECTS = {
    "stack": dc.Stack,
    "service": dc.Service
}


def start(unit, grace_time=10.0, delay=0.5):
    LOGGER.info("object %r: %r" % (unit.name, unit.uuid))
    if unit.state != "Stopped":
        LOGGER.info("stopping %r: %r" % (unit.name, unit.uuid))
        unit.stop()
        for _ in range(ceil(grace_time / delay)):
            sleep(delay)
            unit.refresh()
            if unit.state == "Stopped":
                break
            LOGGER.info("waiting...")
    unit.start()

def main(argv):
    LOGGER.debug("start main with %r" % (argv,))
    assert ("DOCKERCLOUD_USER" in os.environ), "DOCKERCLOUD_USER must be defined"
    assert ("DOCKERCLOUD_APIKEY" in os.environ), "DOCKERCLOUD_APIKEY must be defined"
    dc_object = DOCKERCLOUD_OBJECTS.get(argv[0].lower())
    if dc_object is None:
        raise ValueError("unknown docker cloud API object %r" % (argv[0],))
    # find service/stack by name/uuid
    units = dc_object.list(name=argv[1]) # make threaded?
    units += dc_object.list(uuid=argv[1])
    assert len(units) == 1, "%d objects found, expected 1" % (len(units),)
    try:
        start(units[0])
    except dc.ApiError as err:
        LOGGER.error(str(err))


if __name__ == "__main__":
    root = logging.getLogger()
    for handler in root.handlers:
        root.removeHandler(handler)
    logging.basicConfig(
        level="WARN",
        format="[%(asctime)s %(levelname)s] %(message)s"
    )
    try:
        if len(sys.argv) != 3:
            print("Usage:\n%s <stack|service> <name|uuid>" % (sys.argv[0],))
            rc = 2
        else:
            main(sys.argv[1:])
            rc = 0
    except StandardError as err:
        LOGGER.critical(str(err))
        rc = 1
    finally:
        logging.shutdown()
        sys.exit(rc)

