#!/bin/bash

java -classpath /usr/share/marvin/bin/marvin.jar:/usr/share/java/v4l4j.jar org.cbase.marvin.Marvin -Xmx 32m 2>&1 > /var/log/marvin.log

