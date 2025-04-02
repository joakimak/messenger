FROM python:3.11.4

WORKDIR /app

COPY Pipfile Pipfile.lock /app/

RUN pip install pipenv

RUN pipenv --python 3.11.4

RUN pipenv install --deploy --ignore-pipfile

COPY . /app/

EXPOSE 80

CMD ["pipenv", "run", "uvicorn", "source.api:app", "--host", "0.0.0.0", "--port", "80"]
