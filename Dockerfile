FROM python:3.9

RUN apt-get update && apt-get install -y wkhtmltopdf
ENV APP_HOME /app
RUN mkdir -p $APP_HOME && chown 1000:1000 $APP_HOME
WORKDIR $APP_HOME

COPY --chown=1000:1000 . /app

RUN pip install --no-cache-dir -r requirements.txt

USER 1000

CMD ["python", "app.py"]
