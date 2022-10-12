FROM python:3.10

ADD . /app
WORKDIR /app

# Install requirements
RUN pip install -r requirements.txt

# migrate db, so we have the latest db schema
RUN python manage.py migrate

EXPOSE 5000

# start development server on public ip interface, on port 5000
CMD python manage.py runserver 0.0.0.0:5000
