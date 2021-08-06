FROM python:rc-alpine3.14 AS compile-image
RUN apk add curl gcc build-base python3-dev unixodbc-dev
COPY src/requirements.txt /app/src/requirements.txt
RUN pip3 install -r /app/src/requirements.txt
RUN curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.8.1.1-1_amd64.apk
RUN apk add --allow-untrusted msodbcsql17_17.8.1.1-1_amd64.apk

FROM compile-image AS build-image
# COPY --from=compile-image ~/.local ~/.local
RUN mkdir -p /app/workflows/
COPY src/ /app/src/
COPY .env /app/.env
WORKDIR /app

ENV WORKFLOWS_PATH=/app/workflows

ENTRYPOINT ["python"]
CMD ["-m", "flask", "run","--host","0.0.0.0"]
