# docker build -t noisyagent:0.1 .
# docker run -it --rm --hostname noisyagent noisyagent:0.1 /bin/sh
# docker run -d --rm --name noisyagent -v /home/rmarin/repos/noisyagent/noisyagent.yaml:/root/noisyagent.yaml -v /tmp/noisyagent:/tmp/noisyagent noisyagent:0.1

FROM debian:buster-slim
RUN apt-get update && \
    apt-get -y install python3.7 python3-pip build-essential libssl-dev libffi-dev python3-dev && \
    apt-get clean
RUN python3 -m pip install --no-cache-dir --no-input --upgrade pip
ADD requirements.txt /root/requirements.txt
RUN python3 -m pip install --no-cache-dir --no-input -r /root/requirements.txt
ADD noisyagent.py /root/noisyagent.py
ENTRYPOINT ["/usr/bin/python3", "/root/noisyagent.py", "/root/noisyagent.yaml"]
