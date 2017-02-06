# Docker Cloud API Cron

Generate cron jobs from environment variables suitable for docker cloud.

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

**N.B.:** The container currently uses Python 2.7 because the `dockercloud`
package does not work with 3+.

## Copyright

* Copyright 2017 Novo Nordisk Foundation Center for Biosustainability,
  Technical University of Denmark.

## License

* [Apache License Version 2.0](LICENSE)

