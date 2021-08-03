FROM python:rc-alpine3.14
WORKDIR /app
COPY src/ /app/src/
COPY .env /app/.env
COPY workflows/ /app/workflows/

RUN pip3 install -r /app/src/requirements.txt

ENTRYPOINT ["python"]
CMD ["-m", "flask", "run","--host","0.0.0.0"]
