# docker build -t noisyagent:0.3 .
# docker run -it --rm --hostname noisyagent noisyagent:0.1 /bin/sh
# docker run -d --rm --name noisyagent -p 8080:8080/tcp -v /home/rmarin/repos/noisyagent/noisyagent.yaml:/etc/noisyagent/noisyagent.yaml -v /tmp/noisyagent:/tmp/noisyagent noisyagent:0.3

FROM debian:buster-slim
RUN apt-get update && \
    apt-get -y install python3.7 python3-pip build-essential libssl-dev libffi-dev python3-dev && \
    apt-get clean
RUN python3 -m pip install --no-cache-dir --no-input --upgrade pip
ADD requirements.txt /root/requirements.txt
ADD news.xml /root/news.xml
RUN python3 -m pip install --no-cache-dir --no-input -r /root/requirements.txt
RUN mkdir /etc/noisyagent
ADD noisyagent.py /root/noisyagent.py
ENTRYPOINT ["/usr/bin/python3", "/root/noisyagent.py", "/etc/noisyagent/noisyagent.yaml"]
