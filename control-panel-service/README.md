# Running Locally In Docker

1. Install docker
2. Substitute your db credentials into env-xxxxx.env
3. Start kakfa + the database run `docker-compose up zookeeper db kafka`
4. Run `docker-compose up kafka-consumer` to start the kafka listener
5. Get into kafka-consumer container:

- run `docker ps` find id of kafka-consumer container
- run `docker exec -it <id from above> /bin/bash` to get terminal in container

5. From terminal in kafka-consumer container, run `python manage migrate` this will intialize db
6. From same terminal, run `python test/test_kafka.py`. This will send kafka message that request.
   tradititonal plan analysis be run on data in `test/data/traditiona_plan_v0.json`. As the plans finish,
   the script listens for the kafka message with the ids.
7. Connect to local postgres db: username: postgres, db: postgres, password: blank, hostname: localhost
8. You can see the results of the plan analysis with this query: `select * from trad_plan_analysis_existingplan;`
   The results of the traditional plan analysis are stored as a json blob in the analysis_results column, and can
   easily be converted back into a pandas data frame

Note: 2 and 5 only have to be done once

Note: From within the kafka-consumer containers, you can run `python test/test_trad_plan_analysis.py` to just run the
traditional plan analysis script without going through kafka.

# Running locally without docker

1. Run `python3 -m venv venv3` to create a new virtual environment
2. Run `source venv3/bin/activate` to activate your new virtual env (note this might be slightly different on windows)
3. Run `pip install -r requirements.pip` to install python requirements
4. Since you aren't using docker to set environment variables, go into the settings.py file, and set variables in the `# Project specific settings`
   section appropriately
5. You should now be able to run `python test/test_trad_plan_analysis.py`

# Architecture

- currently 1 containers with two apps - bind_plan_analysis_api for rest api and trad_plan_analysis  for kafka consumer
- Locally, runs kafka, zookeeper, and postgres db containers

# For development
If you change the model and wants to create a new migrations script following these

1. Delete your migrations folder under each app

2. In the database: DELETE FROM django_migrations WHERE app = 'app_name'.
   You could alternatively just truncate this table.

3. python manage.py makemigrations app_name

4. python manage.py migrate

# Devops TODO
..
