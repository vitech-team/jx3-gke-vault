#!/usr/bin/env bash

function sendMessageToSlack() {
  cat .execution.info
  export DETAILS=$(cat cat .execution.info)
  export GIT_SHA=$(git rev-parse master)
  cat /workspace/source/.env_to_test | while read ENV || [[ -n $line ]]; do
    export REPORT_URL="$REPORTS_URL/${ENV}_${GIT_SHA}/"
    if [ -f /large-test-reports/${ENV}_${GIT_SHA}/.failed ]; then
      export STATUS="failed"
      eval "cat <<EOF
          $SLACK_LARGE_TEST_FAILED_MSG
          EOF
          " >rpl.json
      export MESSAGE=$(cat rpl.json)
    else
      export STATUS="passed"
      eval "cat <<EOF
          $SLACK_LARGE_TEST_SUCCESS_MSG
          EOF
          " >rpl.json
      export MESSAGE=$(cat rpl.json)
    fi

    curl -X POST -H 'Content-type: application/json' -H "Authorization: Bearer $SLACK_TOKEN" --data "$MESSAGE" https://slack.com/api/chat.postMessage

  done
}

function storeTestResults() {
  export GIT_SHA=$(git rev-parse master)
  export REPORT_FOLDER=/large-test-reports
  pip install pyyaml
  echo "Environments to check: $(cat /workspace/source/.env_to_test)"

  cat /workspace/source/.env_to_test | while read ENV || [[ -n $line ]]; do
    export ENV=${ENV}
    if [ -f /large-test-reports/${ENV}_${GIT_SHA}/.failed ]; then
      export TEST_STATUS=failed
    else
      export TEST_STATUS=success
    fi
    echo "Status is: ${TEST_STATUS} for ${ENV}"
    python -m script.large_test_utils
    python -c 'from script.large_test_utils import store_versions; store_versions()'
  done
}

function executeLargeTests() {
  export GIT_SHA=$(cat /workspace/source/.git_sha)
  cat /workspace/source/.env_to_test | while read ENV || [[ -n $line ]]; do
    export RESULT_FOLDER="/large-test-reports/${ENV}_${GIT_SHA}"
    export BASE_URL=$(eval "echo" "$"{BASE_URL_${ENV}})

    if [ -d "$RESULT_FOLDER" ]; then
      rm -rf "$RESULT_FOLDER"
    fi
    mkdir -p "$RESULT_FOLDER"

    echo "Performing test run for ${ENV} and URL: ${BASE_URL}"

    if npm run test; then
      echo success >>"$RESULT_FOLDER/.success"
    else
      echo failed >>"$RESULT_FOLDER/.failed"
    fi

    ls -la reports/html-reports/
    cp -aR reports/html-reports/. "$RESULT_FOLDER"
    ls -la "$RESULT_FOLDER"
  done
}

function prepareData() {
  jx get applications -p -u >.deployed_apps
  git rev-parse master >.git_sha
  cat .deployed_apps
}

function checkPromotion() {
  pip install pyyaml
  python -m script.large_test_utils
  python -c 'from script.large_test_utils import check_promotion; check_promotion()'
  echo Large test will be executed for next environments:
  cat .env_to_test
}
