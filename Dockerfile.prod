FROM python:3.11.14-slim

ENV TZ="America/Sao_Paulo"
RUN ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && echo ${TZ} > /etc/timezone

WORKDIR /app

RUN apt-get update && \
    apt-get install -y netcat-traditional && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000

CMD [ "/start.sh" ]