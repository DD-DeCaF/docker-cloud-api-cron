# Docker Cloud API Cron

Implements a docker cloud stack that:

Every hour, checks the environment for variables beginning with `DC_CRON` and
installs them to the crontab. The variables should contain a string with the
following format:

```
* * * * * * <service|stack> <name|uuid>
| | | | | |
| | | | | +-- Year              (range: 1900-3000)
| | | | +---- Day of the Week   (range: 1-7, 1 standing for Monday)
| | | +------ Month of the Year (range: 1-12)
| | +-------- Day of the Month  (range: 1-31)
| +---------- Hour              (range: 0-23)
+------------ Minute            (range: 0-59)
```

So a normal cron schedule followed by the docker cloud object type and its name
or uuid.

## Copyright

* Copyright 2017 Novo Nordisk Foundation Center for Biosustainability,
  Technical University of Denmark.

## License

* [Apache License Version 2.0](LICENSE)

