# Production deployment helper

## New deployment

- Pull new master if not done by gitlab pipeline

- Activate prod environnment
```bash
source /home/elbaladiya/smartup-backend/venv/bin/activate 
```

- Change directory to the backend
```bash
cd /home/elbaladiya/smartup-backend
```

- Run migration ( in case there is some changes)
```bash
python manage.py migrate
```

- Restart the backend service to apply changes
```bash
sudo systemctl restart elbaladeya_backend.service
```

## Debug celery worker

```bash
tail -n 500 /var/log/smartup-backend/celery-tasks.log
```

## Debug celery beat

```bash
tail -n 500 /var/log/smartup-backend/celery-beat-tasks.log
```

## Debug rabbitmq
- Check if rabbitmq service is up and running
```bash
sudo service rabbitmq-server status
```
- Otherwise (it will take some time to restart)
```bash
sudo service rabbitmq-server restart
```
## Debug storage

- Check free disk space
```bash
df -h
```

If disk is full, try to delete old backups from:

- /backup/backup_elbaladiya_hourly
- /backup/backup_elbaladiya_daily