#!/bin/bash

# Required Environment Variables:
  # $CONFIG, $VPC_NAME, $PROFILE, $AWS_DEFAULT_REGION

set -e

function pull_consul_config {
  local readonly consul_url="$1"
  local readonly profile="$2"
  local readonly environment="$3"
  local readonly service_name="$4"

  echo "$consul_url :: $profile :: $environment :: $service_name"



  keys=$(curl -s -k $consul_url/v1/kv/services/$profile/\?keys | \
    sed 's/[]["]//g' | \
    tr , '\n' | \
    grep -e "services/$profile/[^/]*$" -e "services/$profile/$environment/[^/]*$" -e "services/$profile/$environment/$service_name/[^/]*$" | \
    awk '{ print length($0), $0 }' | \
    sort -rn | \
    cut -d' ' -f2- | \
    awk -F/ '!_[$NF]++' -)

  while read -r line; do
      key=$(echo $line | awk -F/ '{ print toupper($NF) }' - | tr -d '[:space:]')
      # make sure the key is valid
      if [[ ! -z $key ]]; then
      value="$(curl -s -k "$consul_url/v1/kv/$line?raw")"
      echo "$key = $value"
      export "$key"=$value
      fi
  done <<< "$keys"
}

function decrypt_file {
  local readonly aws_region="$1"
  local readonly file_src="$2"
  local readonly file_dest="$3"

  # Use file_src as dest if file_dest not set.
  if [[ -z "$file_dest" ]]; then
    local readonly file_dest="$file_src"
  fi

  echo "Decrypting secrets in $file_src using gruntkms in region $aws_region"

  local readonly encrypted_config_contents=$(cat "$file_src")
  local readonly decrypted_config_contents=$(gruntkms decrypt --aws-region "$aws_region" --ciphertext "$encrypted_config_contents")
  echo "Writing decrypted file to $file_dest"
  echo -n "$decrypted_config_contents" > "$file_dest"
}

function start_app {

  echo "The service $SERVICE_NAME in environment $ENVIRONMENT_NAME with profile $PROFILE will start in 2 seconds..."
  sleep 2
  export DJANGO_SETTINGS_MODULE=settings-$PROFILE
  cd /opt/app
  echo "DB Migration/Initialization service"
  python /opt/app/manage.py migrate
  python /opt/app/manage.py flush --no-input
  echo "Server intialzation"
  gunicorn control_panel.wsgi:application --bind 0.0.0.0:3000 --certfile=certificate.pem --keyfile=key.pem &
  status=$?
  if [ $status -ne 0 ]; then
    echo "Failed to start $SERVICE_NAME webapp: $status"
    exit $status
  fi

  python /opt/app/kafka/entrypoint.py &
  status=$?
  if [ $status -ne 0 ]; then
    echo "Failed to start $SERVICE_NAME kafka listener: $status"
    exit $status
  fi

  while sleep 30; do
    pgrep gunicorn > /dev/null
    PROCESS_1_STATUS=$?
    pgrep python > /dev/null
    PROCESS_2_STATUS=$?
    # If the greps above find anything, they exit with 0 status
    # If they are not both 0, then something is wrong
    if [ $PROCESS_1_STATUS -ne 0 -o $PROCESS_2_STATUS -ne 0 ]; then
      exit 1
    fi
  done
}

function run_app {
  local readonly profile="$1"
  local readonly aws_region="$2"

  local readonly django_config="/opt/app/control_panel/settings-$profile.py"
  local readonly yaml_config="/opt/app/resources/env-$profile.yml"
  local readonly kafka_cert="/opt/app/resources/kafka.server.$profile.pem"

  echo "run_app for $SERVICE_NAME"

  if [[ "$profile" == "development" ]]; then
    echo "Profile is set to $profile, so no need to decrypt secrets"
    mv "$kafka_cert.decrypted" "$kafka_cert"
  else
    # decrypt the configs
    decrypt_file "$aws_region" "$django_config"
    decrypt_file "$aws_region" "$yaml_config"
    # decrypt the kafka cert
    decrypt_file "$aws_region" "$kafka_cert.encrypted" "$kafka_cert"
  fi

  openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out certificate.pem -batch -subj '/CN=control-panel-service' > /dev/null
  start_app
}

# Use vpc name as profile if profile isn't set.
if [[ -z "$PROFILE" ]]; then
  export PROFILE="$VPC_NAME"
fi

pull_consul_config "$CONSUL_URL" "$PROFILE" "$ENVIRONMENT_NAME" "$SERVICE_NAME"
run_app "$PROFILE" "$AWS_REGION"
