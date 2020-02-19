FROM python:3.6-alpine as builder

RUN apk --no-cache add g++ zeromq-dev libffi-dev
COPY . /src
WORKDIR /src
RUN pip install .
RUN pip install -r requirements.txt

FROM python:3.6-alpine

RUN apk --no-cache add zeromq git openssh && adduser -s /bin/false -D locust
COPY --from=builder /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/site-packages
COPY --from=builder /usr/local/bin/locust-aws /usr/local/bin/locust-aws
#COPY docker_start.sh docker_start.sh
#RUN chmod +x docker_start.sh

EXPOSE 5557 5558

USER locust
ENTRYPOINT ["locust-aws"]