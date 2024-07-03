FROM ubuntu:24.04
RUN apt-get update
RUN apt-get install -y software-properties-common # This is for add-apt-repository
RUN add-apt-repository ppa:deadsnakes/ppa  # This is for python3.9
RUN apt-get update \
    && apt-get install -y software-properties-common \
    libmpich-dev  \
    mpich \
    locales \
    nano # This is for text editor

RUN dpkg-reconfigure --frontend=noninteractive locales  # This is for setting up the locale

RUN ln -sf /usr/share/zoneinfo/America/Los_Angeles /etc/localtime # This is for setting up the timezone
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata  # This is for setting up the timezone
#RUN dpkg-reconfigure --frontend=noninteractive tzdata  # This is for setting up the timezone

RUN apt-get install -y python3-pip python3.9 python3.9-dev  # This is for python3.9 and python3.9-dev

RUN ln -s /usr/lib/x86_64-linux-gnu/libmpichcxx.so /usr/lib/x86_64-linux-gnu/libmpicxx.so.12  # This is for linking the mpichcxx library
#RUN ln -s /usr/lib/x86_64-linux-gnu/libmpich.so /usr/lib/x86_64-linux-gnu/libmpi.so.12

ENV PATH /usr/bin:${PATH}
ENV LD_LIBRARY_PATH /usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}