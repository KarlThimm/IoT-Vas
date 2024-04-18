# iot-vas

## TODO

|To Do|Doing|Done|
|-|-|-|
|Overview page|Admin page for managing gvm and psql backend|Replace sqlite with postgresql|
|             |                                            |Replace ORM with psycopg      |
|             |                                            |Make API require auth         |
|             |                                            |Database schema               |
|             |                                            |Use htmx for frontend         |
|             |                                            |Devices page                  |
|             |                                            |Reports page                  |

## Creating updated requirements.txt

If you want to update requirements.txt, make a new virtual environment and then install the required packages using pip. It may be necessary to put quotes around the psycopg[binary] package like so:

```shell
pip install 'Flask' 'Flask-Login' 'psycopg[binary]' 'python-gvm'
```

Then you can use pip freeze to update requirements.txt like so:

```shell
pip freeze > requirements.txt
```


## Working with the database

Recreate the db container like so:

```shell
docker compose up --build -d --force-recreate -V db
```

You can omit the `-V` flag if you want to keep the data from the old database, although this will prevent any updates to db.sql from running.

You can also omit the `--build` flag or the `--force-recreate` flag or both flags depending no what you are trying to achieve.
