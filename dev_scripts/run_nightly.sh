#!/usr/bin/env bash

SRC_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
VIRTUALENV_DIR="$(mktemp -d)"

echo "env" $VIRTUALENV_DIR
trap 'rm -r "${VIRTUALENV_DIR}"' EXIT
virtualenv -p python3.7 "${VIRTUALENV_DIR}"
source "${VIRTUALENV_DIR}/bin/activate"

echo "install required libraries for packaging"
pip install py-make twine bump2version twine


echo "Setting up pypirc"
cp "${SRC_DIR}/.pypirc" ~/.pypirc
echo "Replacing <username> with ${bamboo_UserArtifactory@Q}"
sed -i "s|<username>|${bamboo_UserArtifactory}|" ~/.pypirc
# we could end up with characters in our password that conflict with our sed replacement
# instead of trying to escape, which bash is not good at, we just check for a series of characters
# presence and then use an appriote sed expression
if [[ "$bamboo_PasswordArtifactory" == *"|"* ]]; then
  sed -i "s/<password>/${bamboo_PasswordArtifactory@Q}/" ~/.pypirc
elif [[ "$bamboo_PasswordArtifactory" == *"/"* ]]; then
  sed -i "s|<password>|${bamboo_PasswordArtifactory@Q}|" ~/.pypirc
elif [[ "$bamboo_PasswordArtifactory" == *"#"* ]]; then
  sed -i "s#<password>#${bamboo_PasswordArtifactory@Q}#" ~/.pypirc
elif [[ "$bamboo_PasswordArtifactory" == *"^"* ]]; then
  sed -i "s^<password>^${bamboo_PasswordArtifactory@Q}^" ~/.pypirc
elif [[ "$bamboo_PasswordArtifactory" == *"@"* ]]; then
  sed -i "s@<password>@${bamboo_PasswordArtifactory@Q}@" ~/.pypirc
else
  echo "Could not find an appropriate expression to use for sed. Please add expression to setup_env.sh"
  exit -1
fi

echo "Login to docker"
docker login idm-docker-staging.packages.idmod.org -u "${bamboo_UserArtifactory@Q}" -p "${bamboo_PasswordArtifactory@Q}"

echo "Release to staging"
pymake release-staging

echo "deactivate..."
deactivate