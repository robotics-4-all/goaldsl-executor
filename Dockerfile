FROM python:3.10

WORKDIR /goalexecutor

RUN apt-get update && apt upgrade  -y

COPY ./requirements.txt /requirements.txt

RUN pip install --no-cache-dir --upgrade -r /requirements.txt

COPY ./setup_deps.sh /setup_deps.sh

RUN bash /setup_deps.sh

COPY ./ /goalexecutor

ENV LOCAL_REDIS=True
ENV BROKER_TYPE=MQTT
ENV BROKER_HOST=localhost
ENV BROKER_PORT=1883
ENV BROKER_SSL=True
ENV BROKER_USERNAME=guest
ENV BROKER_PASSWORD=guest
ENV UID=123

CMD ["python", "executor.py"]

