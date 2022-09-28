FROM python:3.8.14

WORKDIR api

COPY app ./app
COPY config ./config
COPY databases ./databases
COPY app/requirements.txt ./requirements.txt

#RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install -r requirements.txt
RUN apt update
RUN apt install -y ghostscript python3-tk ffmpeg libsm6 libxext6

RUN mkdir -p app/schedule
RUN chmod +rw app/schedule

RUN mkdir logs
RUN chmod +rw logs


RUN chmod +x app/start.sh

EXPOSE 3000
CMD ["app/start.sh"]