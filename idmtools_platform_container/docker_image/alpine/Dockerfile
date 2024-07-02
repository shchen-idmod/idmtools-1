FROM alpine:latest

ARG REQUIRE="sudo build-base"
RUN apk update && apk upgrade \
      && apk add --no-cache ${REQUIRE}
RUN apk update\
      && apk add ca-certificates wget && update-ca-certificates \
      && apk add openssl \
      && apk add perl \
      && apk add python3 \
      && apk add linux-headers \
      && apk add nano \
      && apk add bash

# Install Python and pip
RUN apk add --no-cache python3 py3-pip
# Create a virtual environment
RUN python3 -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip in the virtual environment
RUN python3 -m pip install --upgrade pip

# Make a directory for pip configurations (though this might not be necessary)
RUN mkdir -p /root/.pip

#### INSTALL MPICH ####
# Source is available at http://www.mpich.org/static/downloads/

# Build Options:
# See installation guide of target MPICH version
# Ex: http://www.mpich.org/static/downloads/4.2.0/mpich-4.2.0-installguide.pdf
# These options are passed to the steps below
ARG MPICH_VERSION="4.2.0"
ARG MPICH_CONFIGURE_OPTIONS="--disable-fortran --disable-f77 --disable-fc"
ARG MPICH_MAKE_OPTIONS

# Download, build, and install MPICH
RUN mkdir /tmp/mpich-src
WORKDIR /tmp/mpich-src
RUN wget http://www.mpich.org/static/downloads/${MPICH_VERSION}/mpich-${MPICH_VERSION}.tar.gz \
      && tar xfz mpich-${MPICH_VERSION}.tar.gz  \
      && cd mpich-${MPICH_VERSION}  \
      && ./configure ${MPICH_CONFIGURE_OPTIONS}  \
      && make ${MPICH_MAKE_OPTIONS} && make install \
      && rm -rf /tmp/mpich-src

ENV PATH ${PATH}:/usr/local/bin
ENV LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/usr/local/lib

COPY pip.conf /root/.pip
# Add the requirements file
ADD requirements.txt /tmp/
ARG CONTAINER_VERSION

# pip install pyproj --no-binary pyproj
RUN apk add proj-util proj-dev pkgconfig python3-dev geos-dev findutils
RUN python3 -m pip install -r /tmp/requirements.txt
# Set the default command to bash
CMD ["/bin/bash"]
