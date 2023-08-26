# SmartUp Backend

Backend part of SmartUp App and http://elbaladiya.tn/

citizen/manager login (used by platform ambassadors don't change it):

```
phone_number : 99998888
password: Test999
```

## Getting Started

These instructions will get you a clone of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

```
python 3.8
```

### Installing and Initial Setup

**[Optional]**
Before the installation, a best practise would be setting a virtualenv for the project

```
https://virtualenv.pypa.io/
```

All the necessary libraries are in requirements.txt

```
pip install -r requirements.txt
```

### Environment variables

These are managed by [decouple](https://pypi.org/project/python-decouple/). For that, you need a `.env` file. You can create one running

```sh
cp .dev.env .env
```

### Note:

The project can be run directly on your machine, just setting the **ENV=TEST** in your env file, and it will use `LocMemCache` instead of redis and `SQlite` instead of postgres, tho running the project in docker is preferred:

```
docker-compose up --build
```

and just prefixing all django commands with:

```sh
docker-compose exec -T backend ./manage.py <do_something>
```

To test different parts of the project, like push notifications or emails, you need to setup more variables. Contact the team for that.

### Initiate Database

Execute the command below

```
python manage.py migrate
```

### Run the project

Execute the command below

```
python manage.py runserver
```

## Running the tests

The tests are in tests_database.py and tests_mobile_api.py under the app backend

```
 python manage.py test
```

## pre-commit :

run `pre-commit install` before committing your code for the first time

## Populating database

To populate the database with fake data, just run the command, for now we have one fixture municipalities, fixtures are found in the fixture directory under the app backend

```
python manage.py loaddata <fixturename>
```

## RUN AS A SERVICE

Create a service for the web application following the example in:

```
deploy/elbaladeya_backend.service
```

## celery worker/sheduler daemonisation

this documentation was followed https://docs.celeryproject.org/en/stable/userguide/daemonizing.html used generic init-scripts

```
to manage daemond: /etc/init.d/celeryd {start|stop|restart|status}
```

to change config (eg number of nodes/workers, daemond system user/group ect) of the daemon edit the file

```
/etc/default/celeryd
```

Second possible solution: https://gist.github.com/mau21mau/9371a95b7c14ddf7000c1827b7693801

## server service :

file location : /etc/systemd/system/\*.service
for management use systemctl

##Services Management
Services_management.sh is bash file that can start/stop/restart the web service/celery

```
./home/elbaladiya/smartup-backend/services_management.sh
```

## Useful resources

- API documentation: [Swagger-UI](https://dev-backend.elbaladiya.tn/api/schema/swagger-ui/)
- [Frontoffice Staging environment](https://dev-citizen.elbaladiya.tn)
- [Backoffice Staging environment](https://dev-idara.elbaladiya.tn)

- [Frontoffice Prod environment](https://elbaladiya.tn/login)
- [Backoffice Prod environment](https://idara.elbaladiya.tn/login)

## Built With

- [python 3.8](https://www.python.org/)
- [django 3.2](https://www.djangoproject.com/)
- [djangorestframework](https://www.djangoproject.com/)

## Contributors:

- **SmartUp TEAM**

## Acknowledgments

- Tounes Lina Association
