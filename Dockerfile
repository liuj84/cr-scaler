# build image to run scalign job
FROM devops-repo.isus.emc.com:8116/nautilus/nautilus-alpine:3.14.4

RUN apk add --no-cache python3-dev py3-pip

RUN mkdir -p /scaling
WORKDIR /
COPY scaling/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copying src code to Container
COPY . /

RUN addgroup -g 1000 scl
RUN adduser -u 1000 -G scl -h /scaling -D scl
USER scl

# Running Python Application
CMD ["python3", "scaling/scale.py"]
# CMD ["tail", "-f", "dev/null"]

