FROM python:3.8.14

WORKDIR app

COPY start_tg.py bots/requirements.txt ./
COPY bots ./bots
COPY databases ./databases
COPY config ./config

RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN mkdir logs
RUN chmod -R 777 *

CMD ["python", "start_tg.py"]