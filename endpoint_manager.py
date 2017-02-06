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
Start an endpoint via the docker cloud API.

Expects the following environment variables to be set:

    DOCKERCLOUD_USER
    DOCKERCLOUD_APIKEY

or:

    DOCKERCLOUD_AUTH

and possibly:

    DOCKERCLOUD_NAMESPACE
"""

from __future__ import (absolute_import, print_function)

import os
import logging

from time import sleep
from math import ceil

import click
import dockercloud as dc

DOCKERCLOUD_TYPES = {
    "stack": dc.Stack,
    "service": dc.Service
}


def find_endpoint(dc_type, dc_id):
    """Find a docker cloud endpoint by its name or UUID."""
    units = dc_type.list(name=dc_id)  # make threaded?
    units += dc_type.list(uuid=dc_id)
    assert len(units) == 1, "%d objects found, expected 1" % (len(units),)
    return units[0]


def start(endpoint, grace_time=10.0, delay=0.5):
    """Start a docker cloud object, stopping it first if necessary."""
    LOGGER.info("object %r: %r", endpoint.name, endpoint.uuid)
    if endpoint.state != "Stopped":
        LOGGER.info("stopping %r: %r", endpoint.name, endpoint.uuid)
        endpoint.stop()
        for _ in range(ceil(grace_time / delay)):
            sleep(delay)
            endpoint.refresh()
            if endpoint.state == "Stopped":
                break
            LOGGER.info("waiting...")
    endpoint.start()


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("dc_type", type=click.Choice(["stack", "service"]))
@click.argument("dc_id")
@click.option("--log-level", "-l", default="WARN",
              type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]),
              help="Set the logging level.")
def main(dc_type, dc_id, log_level):
    """
    Start the docker cloud endpoint DC_ID of DC_TYPE via the API.

    Currently the endpoint DC_TYPE can be either 'stack' or 'service'.
    DC_ID is either the name or the uuid of the endpoint.
    """
    LOGGER.setLevel(log_level)
    assert ("DOCKERCLOUD_AUTH" in os.environ) or (
                ("DOCKERCLOUD_USER" in os.environ) and
                ("DOCKERCLOUD_APIKEY" in os.environ)
            ), "docker cloud authorization must be defined via environment"
    dc_type = DOCKERCLOUD_TYPES[dc_type]
    endpoint = find_endpoint(dc_type, dc_id)
    try:
        start(endpoint)
    except dc.ApiError as err:
        LOGGER.error(str(err))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARN,
        format="[%(asctime)s %(levelname)s] %(message)s"
    )
    LOGGER = logging.getLogger()
    main()
    logging.shutdown()
