#!/bin/bash

cleanup() {
  echo -e "\nService stopped"

  if [ -f local.env ]; then
    while IFS='=' read -r key value; do
      if [ -n "$key" ]; then
        unset "$key"
      fi
    done < local.env
  fi

  docker-compose -f docker-compose.service.yml down > /dev/null 2>&1
}

trap cleanup SIGINT SIGTERM

echo "Service started"
export $(grep -v '^#' local.env | xargs)
docker-compose -f docker-compose.service.yml down > /dev/null 2>&1
docker-compose -f docker-compose.service.yml up --build
cleanup
