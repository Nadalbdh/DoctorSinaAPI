#!/bin/sh

env_vars="
BUGSNAG_API_KEY
ENV 
SECRET_KEY 
URL_PREFIX 
METABASE_SECRET_KEY 
BACKEND_PORT
BROKER_URL 
CACHE_URL 
DB_USER 
DB_NAME 
DB_PASSWORD 
DB_HOST 
DB_PORT
SMS_GATEWAY_URL 
SMS_GATEWAY_API_KEY
EMAIL_HOST_USER 
EMAIL_HOST_PASSWORD 
EMAIL_HOST_CONFIG_NOTIFICATIONS 
EMAIL_HOST_CONFIG_STATISTICS
EMAIL_HOST EMAIL_BCC FCM_API_KEY
"

for var in $env_vars
do
    if [ -z $(eval echo \$$var) ]; then
        echo -e "\033[31mError: $var is not set.\033[0m"
        exit 1
    else
        echo -e "\033[32m$var is set.\033[0m"
    fi
done

echo -e "\033[32mAll environment variables are set.\033[0m"

python3 manage.py createcachetable

gunicorn settings.wsgi:application --bind 0.0.0.0:${BACKEND_PORT} --timeout 90 --workers=4 --threads=4 --worker-class=gthread
