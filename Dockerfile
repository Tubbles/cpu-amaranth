# syntax=docker/dockerfile:1

FROM ubuntu:23.04

RUN apt update
RUN apt install -y bsdmainutils
RUN apt install -y python3
RUN apt install -y python3-pip
RUN apt install -y gtkwave
RUN apt install -y python-is-python3
RUN apt install -y python3-venv
RUN apt install -y python3-full
RUN apt install -y git
RUN python -m venv /var/venv
RUN /var/venv/bin/python -m pip install 'amaranth[builtin-yosys] @ git+https://github.com/amaranth-lang/amaranth.git'
ENV PATH=/var/venv/bin/:$PATH
RUN apt install -y make
