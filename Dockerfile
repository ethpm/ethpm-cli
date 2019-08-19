FROM python:3.7

# Set up code directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip install -e .[dev]

RUN echo "Welcome, to ethPM's CLI tool."

ENTRYPOINT ["ethpm"]
