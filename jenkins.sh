#! /bin/bash
set -e

flake8

python2.7 -m virtualenv django_rql_env
. django_rql_env/bin/activate
python2.7 setup.py test
deactivate
rm -rf django_rql_env

virtualenv -p python3 django_rql_env
. django_rql_env/bin/activate
python3 setup.py test
python3 setup.py publish $@
deactivate

export PATH=$PATH:/opt/sonar-scanner-2.6.1/bin/
export VERSION=$(cat VERSION)
export PR_ID=`git branch -a --contains ${GIT_COMMIT} | grep 'remotes/origin/pr/[0-9]*/' | head -1 | sed 's/[^0-9]*//g'`

sonar-scanner \
    -Dsonar.projectVersion=$VERSION \
    -Dsonar.stash.project=SWFT \
    -Dsonar.stash.repository=django-rql \
    -Dsonar.stash.pullrequest.id=$PR_ID \
    -Dsonar.stash.notification=true \
    -Dsonar.stash.comments.reset=false \
    -Dsonar.stash.login=commit-blocker-bot \
    -Dsonar.stash.report.issues=true \
    -Dsonar.stash.report.line=false \
    -Dsonar.stash.report.coverage=true

rm -rf django_rql_env
