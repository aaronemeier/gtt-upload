#!/bin/bash

cp -f gtt.yml .gtt.yml
printf "\nurl: ${GITLAB_URL}\ntoken: ${GITLAB_TOKEN}\nproject: ${GITLAB_PROJECT}" >> .gtt.yml
rm -f "${REPORT_FILE}"
gtt report --file "${REPORT_FILE}"
python3 gtt-upload.py