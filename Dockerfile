FROM kriskbx/gitlab-time-tracker AS gtt

RUN apk add --no-cache --virtual=.build-dependencies git \
        autoconf automake freetype-dev g++ gcc jpeg-dev lcms2-dev libffi-dev libpng-dev \
        libwebp-dev linux-headers make openjpeg-dev openssl-dev zlib-dev && \
    apk add --no-cache openssl python3 bash && \
    ln -s -f /usr/bin/pip3 /usr/bin/pip && \
    pip install --no-cache-dir -U pip  setuptools

# Gitlab Auth
ENV GITLAB_URL "http://gitlab.example.com/api/v4/"
ENV GITLAB_TOKEN "PERSONAL_ACCESS_TOKEN"
ENV GITLAB_PROJECT "namespace/project/repository"

# OneDrive Auth
ENV GTT_CLIENT_SECRET "CLIENT_SECRET"
ENV GTT_CLIENT_ID "CLIENT_ID"

ENV ONEDRIVE_LOCATION "me"
ENV ONEDRIVE_PATH "Timetracking"
ENV ONEDRIVE_FILE "Timetracking.xlsx"

ENV CONFIG_ROOT "/root/"
ENV REPORT_FILE "/root/report.csv"
ENV USERS_FILE "/gtt-upload/users.csv"

WORKDIR /gtt-upload

ADD config/gtt.yml /gtt-upload/gtt.yml
ADD config/users.csv ${USERS_FILE}
ADD report.sh /gtt-upload/report.sh
ADD requirements.txt /gtt-upload/
ADD gtt-upload.py /gtt-upload/

RUN pip3 install -r requirements.txt

RUN apk del --purge .build-dependencies && rm -rf /root/.cache /tmp/*
RUN chmod +x /gtt-upload/report.sh

VOLUME ["/root"]
ENTRYPOINT ["/gtt-upload/report.sh"]