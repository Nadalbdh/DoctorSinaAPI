#!/bin/sh

#sudo systemctl daemon-reload
sudo systemctl $1 elbaladeya_backend.service
echo "elbaladeya_backend "$1"ed successfully"
sudo systemctl $1 supervisor
echo "supervisor "$1"ed successfully"
