From ubuntu:14.04
ADD requirements.txt /nfvacc-exhaustive-tester/requirements.txt

RUN rm -vf /var/lib/apt/lists/*
RUN apt-get update

RUN apt-get install -y python2.7 python-dev python-distribute python-pip curl openssh-client openssh-server
RUN pip install ipython==5.0
RUN python -m pip install --upgrade pip
RUN pip install --user numpy scipy ipython

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/
CMD python scrader_server.py
EXPOSE 8000
