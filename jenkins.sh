#! /bin/bash
set -e

virtualenv django_rql_env
. django_rql_env/bin/activate

python setup.py test
deactivate

export PATH=$PATH:/opt/sonar-scanner-2.6.1/bin/
export VERSION=$(cat VERSION)
export PR_ID=`git branch -a --contains ${GIT_COMMIT} | grep 'remotes/origin/pr/[0-9]*/' | head -1 | sed 's/[^0-9]*//g'`

sonar-scanner \
    -Dsonar.analysis.mode=preview \
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
