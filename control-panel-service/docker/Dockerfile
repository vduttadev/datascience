ARG BASE_IMAGE='python:3.7'
FROM $BASE_IMAGE AS control-panel-service

RUN mkdir -p /opt/pkgs

# TODO pull from a repo
#COPY ./pyco /opt/pkgs/pyco
#COPY ./pymei /opt/pkgs/pymei


RUN mkdir /opt/app

WORKDIR /opt/app

COPY ./bin/requirements.pip /opt
COPY ./bin/run-app.sh /opt/app
COPY ./bin/gruntkms_linux_amd64_v0.0.6 /usr/local/bin/gruntkms
RUN pip install -r /opt/requirements.pip

COPY ./bin/control_panel /opt/app

ENV PYTHONPATH /opt/pkgs:/opt/app:/opt/app/control_panel \
    PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1

RUN chmod u+x /usr/local/bin/gruntkms && \
    chmod u+x /opt/app/run-app.sh

EXPOSE 3000
CMD ["/opt/app/run-app.sh"]
