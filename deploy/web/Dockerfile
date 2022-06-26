FROM python:3.10

COPY mega_market/ .

RUN pip install --upgrade pip \
    pip install -r requirements.txt --no-cache-dir

ADD deploy/web/entrypoint.sh .
RUN chmod +x /entrypoint.sh
ADD .env .

ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:80"]