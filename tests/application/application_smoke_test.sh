#!/usr/bin/env bash

set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$TEST_DIR/../.." && pwd)"
ENV_FILE="${APP_ENV:-$ROOT_DIR/.env/development}"
FIXTURE_DIR="$TEST_DIR"
FULL_FIXTURE_SPEC="$FIXTURE_DIR/full-database-fixture.json"
FULL_FIXTURE_LOADER="$FIXTURE_DIR/load_full_fixture.mongodb.js"
BASE_URL="${BASE_URL:-http://localhost:8000}"
TEST_ADMIN_USERNAME="${TEST_ADMIN_USERNAME:-test-admin}"
TEST_ADMIN_PASSWORD="${TEST_ADMIN_PASSWORD:-test-admin-password}"
JOB_TIMEOUT_SECONDS="${JOB_TIMEOUT_SECONDS:-180}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-2}"
DATASET_ID="67017efbb2d2f30e9c5ecc54"
SPORT="basketball"
GENDER="mens"
LEVEL="high_school"
MODE="test"
TOKEN=""

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ENV_FILE"
  set +a
fi

case "${1:-}" in
  "") ;;
  --reset) MODE="reset" ;;
  --maintenance) MODE="maintenance" ;;
  --reset-admin) MODE="reset-admin" ;;
  *) echo "Usage: $0 [--reset|--maintenance|--reset-admin]" >&2; exit 2 ;;
esac

info() {
  printf '[application-test] %s\n' "$*"
}

fail() {
  printf '[application-test] ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

compose() {
  docker compose --env-file "$ENV_FILE" "$@"
}

api() {
  curl --silent --show-error --fail-with-body "$@"
}

authenticated_api() {
  api -H "Authorization: Bearer $TOKEN" "$@"
}

mongo_eval() {
  compose exec -T db mongosh \
    --quiet \
    --username "$MONGO_USER" \
    --password "$MONGO_PASS" \
    --authenticationDatabase admin \
    --eval "$1"
}

mongo_script() {
  compose exec -T db mongosh \
    --quiet \
    --username "$MONGO_USER" \
    --password "$MONGO_PASS" \
    --authenticationDatabase admin
}

wait_for_backend() {
  info "Waiting for FastAPI at $BASE_URL"
  for _ in $(seq 1 60); do
    if curl --silent --fail "$BASE_URL/docs" >/dev/null 2>&1; then
      info "FastAPI is ready"
      return
    fi
    sleep 2
  done
  fail "FastAPI did not become ready within 120 seconds"
}

ensure_dataset_documents() {
  local javascript
  # The quoted segments deliberately interpolate Bash values into MongoDB JavaScript.
  # shellcheck disable=SC2016
  javascript='const app = db.getSiblingDB("sports_data");
app.temp2.updateOne(
  {_id: ObjectId("'"$DATASET_ID"'")},
  {$setOnInsert: {sport_type: "'"$SPORT"'", gender: "'"$GENDER"'", level: "'"$LEVEL"'", teams: []}},
  {upsert: true}
);
app.flagged_games.updateOne(
  {sport_type: "'"$SPORT"'", gender: "'"$GENDER"'", level: "'"$LEVEL"'"},
  {$setOnInsert: {flagged_games: []}},
  {upsert: true}
);'
  mongo_eval "$javascript" >/dev/null
}

reset_fixture_data() {
  [[ "${CONFIRM_TEST_RESET:-}" == "1" ]] || fail \
    "Reset refused. Re-run with: make test-app-reset CONFIRM_TEST_RESET=1"

  local fixture_json
  fixture_json="$(jq -c . "$FULL_FIXTURE_SPEC")"

  info "Replacing all local sports collections with the full fixture dataset"
  {
    printf 'const fixtureSpec = %s;\n' "$fixture_json"
    cat "$FULL_FIXTURE_LOADER"
  } | mongo_script

  compose exec -T backend sh -c \
    'find "$UPLOAD_DIR" -type f ! -name .gitkeep -delete'
  while IFS=$'\t' read -r storage_path encoded_content; do
    printf '%s' "$encoded_content" | compose exec -T backend sh -c \
      'target="$UPLOAD_DIR/$1"; mkdir -p "$(dirname "$target")"; base64 -d >"$target"' \
      sh "$storage_path"
  done < <(jq -r '
    .datasets[] as $dataset
    | $dataset.team_names as $teams
    | ($dataset.sport_type + "-" + $dataset.gender + "-" + $dataset.level) as $slug
    | ($dataset.games
      | map(. as $game | [
          $game[0],
          $teams[$game[1] - 1],
          $teams[$game[2] - 1],
          $game[3],
          $game[4],
          $game[5]
        ] | @csv)
      | join("\n") + "\n") as $content
    | [
        ($dataset.sport_type + "/" + $dataset.gender + "/" + $dataset.level
          + "/fixture-" + $slug + "-" + $slug + "-fixture.csv"),
        ($content | @base64)
      ]
    | @tsv
  ' "$FULL_FIXTURE_SPEC")

  replace_test_admin
}

verify_full_fixture_data() {
  local javascript state response flagged label
  javascript='const app = db.getSiblingDB("sports_data");
const adminDb = db.getSiblingDB("admin_details");
const summarize = (document) => ({
  sport_type: document.sport_type,
  gender: document.gender,
  level: document.level,
  teams: (document.teams || []).length,
  game_refs: (document.teams || []).reduce(
    (total, team) => total + (team.season_opp || []).length,
    0
  )
});
const current = app.temp2.find({}).toArray().map(summarize);
const previous = app.previous_season.find({}).toArray().map(summarize);
const csv = app.csv_files.find({}).toArray();
const games = app.games.find({}).toArray();
const flagged = app.flagged_games.find({}).toArray();
const account = adminDb.admin.findOne({}, {_id: 0, username: 1});
print(JSON.stringify({
  current,
  previous,
  csv_documents: csv.length,
  csv_files: csv.reduce((total, document) => total + (document.csv_files || []).length, 0),
  canonical_games: games.length,
  csv_blobs: app.csv_files.countDocuments({"csv_files.filedata": {$exists: true}}),
  flagged_documents: flagged.length,
  flagged_games: flagged.reduce(
    (total, document) => total + (document.flagged_games || []).length,
    0
  ),
  admin_documents: adminDb.admin.countDocuments({}),
  admin: account
}));'
  state="$(mongo_eval "$javascript")"

  jq -e --arg username "$TEST_ADMIN_USERNAME" '
    (.current | length == 6) and
    (.current | all(.teams == 10 and .game_refs == 20)) and
    (.previous | length == 6) and
    (.previous | all(.teams == 10 and .game_refs == 20)) and
    .csv_documents == 6 and
    .csv_files == 6 and
    .canonical_games == 60 and
    .csv_blobs == 0 and
    .flagged_documents == 6 and
    .flagged_games == 6 and
    .admin_documents == 1 and
    .admin.username == $username
  ' <<<"$state" >/dev/null || fail "Full fixture database verification failed: $state"

  while IFS=$'\t' read -r sport gender level; do
    label="$level $gender $sport"
    response="$(api "$BASE_URL/teams?sport_type=$sport&gender=$gender&level=$level")"
    jq -e '.status == 200 and (.data.teams | length == 10)' \
      <<<"$response" >/dev/null || fail "Public API did not return ten teams for $label"

    flagged="$(authenticated_api \
      "$BASE_URL/retrieve-flagged?sport_type=$sport&gender=$gender&level=$level")"
    jq -e '.flagged_games | length == 1' \
      <<<"$flagged" >/dev/null || fail "Protected API did not return one flagged game for $label"
  done < <(jq -r '.datasets[] | [.sport_type, .gender, .level] | @tsv' "$FULL_FIXTURE_SPEC")

  info "Verified 6 datasets, 60 teams, 60 games, 6 CSV files, 6 flags, and previous-season data"
  info "PASS: full fixture reset and application verification"
}

assert_fixture_dataset_is_empty() {
  local javascript state team_count csv_count game_count
  javascript='const app = db.getSiblingDB("sports_data");
const dataset = app.temp2.findOne({_id: ObjectId("'"$DATASET_ID"'")});
const csv = app.csv_files.findOne({sport_type: "'"$SPORT"'", gender: "'"$GENDER"'", level: "'"$LEVEL"'"});
const games = app.games.countDocuments({sport_type: "'"$SPORT"'", gender: "'"$GENDER"'", level: "'"$LEVEL"'"});
print(JSON.stringify({teams: dataset && dataset.teams ? dataset.teams.length : 0, csvFiles: csv && csv.csv_files ? csv.csv_files.length : 0, games}));'
  state="$(mongo_eval "$javascript")"
  team_count="$(jq -r '.teams' <<<"$state")"
  csv_count="$(jq -r '.csvFiles' <<<"$state")"
  game_count="$(jq -r '.games' <<<"$state")"

  if [[ "$team_count" != "0" || "$csv_count" != "0" || "$game_count" != "0" ]]; then
    fail "Fixture dataset is not empty ($team_count teams, $game_count games, $csv_count upload records). Use: make test-app-reset CONFIRM_TEST_RESET=1"
  fi
}

login() {
  local setup_payload login_response existing_admin
  [[ -n "${SETUP_TOKEN:-}" ]] || fail "SETUP_TOKEN is missing. Add it to $ENV_FILE or export it before running the test."

  setup_payload="$(jq -nc \
    --arg username "$TEST_ADMIN_USERNAME" \
    --arg password "$TEST_ADMIN_PASSWORD" \
    '{username: $username, password: $password}')"

  # Setup is intentionally best-effort because an installation can have an admin already.
  curl --silent --show-error \
    -X POST "$BASE_URL/setup/admin/" \
    -H "X-Setup-Token: $SETUP_TOKEN" \
    -H 'Content-Type: application/json' \
    --data "$setup_payload" >/dev/null

  if ! login_response="$(api \
      -X POST "$BASE_URL/token/" \
      -H 'Content-Type: application/x-www-form-urlencoded' \
      --data-urlencode "username=$TEST_ADMIN_USERNAME" \
      --data-urlencode "password=$TEST_ADMIN_PASSWORD")"; then
    existing_admin="$(mongo_eval \
      'const account=db.getSiblingDB("admin_details").admin.findOne({}, {_id:0, username:1}); print(account ? account.username : "none");')"
    fail "Login failed for '$TEST_ADMIN_USERNAME'; existing local admin is '$existing_admin'. Supply its credentials with TEST_ADMIN_USERNAME/TEST_ADMIN_PASSWORD, or run: make test-admin-reset CONFIRM_ADMIN_RESET=1"
  fi

  TOKEN="$(jq -er '.access_token' <<<"$login_response")" || fail "Login response did not contain an access token"
  authenticated_api "$BASE_URL/validate-token/" | jq -e '.status == "valid"' >/dev/null
  info "Authenticated as $TEST_ADMIN_USERNAME"
}

replace_test_admin() {
  local password_hash username_json password_json javascript
  password_hash="$(printf '%s' "$TEST_ADMIN_PASSWORD" | \
    compose exec -T backend python -c \
      'import sys, bcrypt; value = sys.stdin.read().encode("utf-8"); print(bcrypt.hashpw(value, bcrypt.gensalt()).decode("utf-8"))')"
  [[ -n "$password_hash" ]] || fail "Could not generate the test admin password hash"

  username_json="$(jq -Rn --arg value "$TEST_ADMIN_USERNAME" '$value')"
  password_json="$(jq -Rn --arg value "$password_hash" '$value')"
  javascript='const app = db.getSiblingDB("admin_details");
app.admin.deleteMany({});
app.admin.insertOne({username: '"$username_json"', password: '"$password_json"'});'

  mongo_eval "$javascript" >/dev/null
  info "Replaced the local admin account with '$TEST_ADMIN_USERNAME'"
}

reset_test_admin() {
  [[ "${CONFIRM_ADMIN_RESET:-}" == "1" ]] || fail \
    "Admin reset refused. Re-run with: make test-admin-reset CONFIRM_ADMIN_RESET=1"

  replace_test_admin
  info "Run 'make test-app' to start the smoke test"
}

dataset_query() {
  printf 'sport_type=%s&gender=%s&level=%s' "$SPORT" "$GENDER" "$LEVEL"
}

add_teams() {
  local names missing response remaining
  names="$(jq -c '[.[].team_name]' "$FIXTURE_DIR/teams.json")"
  missing="$(authenticated_api \
    -X POST "$BASE_URL/check-teams/?$(dataset_query)" \
    -H 'Content-Type: application/json' \
    --data "$names")"
  jq -e '.missing_teams | length == 7' <<<"$missing" >/dev/null || fail \
    "Expected all seven fixture teams to be missing before setup"

  response="$(authenticated_api \
    -X POST "$BASE_URL/add_teams/?$(dataset_query)" \
    -H 'Content-Type: application/json' \
    --data-binary "@$FIXTURE_DIR/teams.json")"
  jq -e '.added | length == 7' <<<"$response" >/dev/null || fail "The API did not add all seven fixture teams"

  remaining="$(authenticated_api \
    -X POST "$BASE_URL/check-teams/?$(dataset_query)" \
    -H 'Content-Type: application/json' \
    --data "$names")"
  jq -e '.missing_teams | length == 0' <<<"$remaining" >/dev/null || fail "Some fixture teams are still missing"
  info "Added and verified seven teams"
}

upload_game_files() {
  local file
  for file in "$FIXTURE_DIR"/week-0{1,2,3,4}.csv; do
    authenticated_api \
      -X POST "$BASE_URL/games/upload/?$(dataset_query)" \
      -F "csv_file=@$file;type=text/csv" >/dev/null
    info "Uploaded $(basename "$file")"
  done
}

verify_ingestion_storage() {
  local javascript state
  javascript='const app = db.getSiblingDB("sports_data");
const query = {sport_type: "'"$SPORT"'", gender: "'"$GENDER"'", level: "'"$LEVEL"'"};
const uploads = app.csv_files.findOne(query);
print(JSON.stringify({
  games: app.games.countDocuments(query),
  uploads: uploads ? uploads.csv_files.length : 0,
  uploads_with_paths: uploads ? uploads.csv_files.filter((item) => item.storage_path).length : 0,
  blobs: app.csv_files.countDocuments({...query, "csv_files.filedata": {$exists: true}})
}));'
  state="$(mongo_eval "$javascript")"
  jq -e '
    .games == 13 and
    .uploads == 4 and
    .uploads_with_paths == 4 and
    .blobs == 0
  ' <<<"$state" >/dev/null || fail "Normalized ingestion storage verification failed: $state"
  info "Verified 13 canonical games, 4 filesystem references, and no MongoDB blobs"
}

poll_job() {
  local job_id="$1" label="$2" deadline response status success
  deadline=$((SECONDS + JOB_TIMEOUT_SECONDS))

  while (( SECONDS < deadline )); do
    response="$(authenticated_api "$BASE_URL/task-status/$job_id")"
    status="$(jq -r '.status // "unknown"' <<<"$response")"
    case "$status" in
      complete)
        success="$(jq -r 'if .info.success == null then true else .info.success end' <<<"$response")"
        [[ "$success" == "true" ]] || fail "$label job completed unsuccessfully: $response"
        info "$label job completed"
        return
        ;;
      queued|in_progress|deferred)
        sleep "$POLL_INTERVAL_SECONDS"
        ;;
      *) fail "$label job entered unexpected state '$status': $response" ;;
    esac
  done
  fail "$label job did not complete within $JOB_TIMEOUT_SECONDS seconds"
}

run_background_jobs() {
  local response job_id
  response="$(authenticated_api -X POST "$BASE_URL/run_algorithm/1/?$(dataset_query)")"
  job_id="$(jq -er '.task_id' <<<"$response")"
  info "Queued ranking job $job_id"
  poll_job "$job_id" "Ranking"

  response="$(authenticated_api -X POST "$BASE_URL/calc_z_scores/?$(dataset_query)")"
  job_id="$(jq -er '.task_id' <<<"$response")"
  info "Queued z-score job $job_id"
  poll_job "$job_id" "Z-score"
}

team_id() {
  local teams_response="$1" name="$2"
  jq -er --arg name "$name" '.data.teams[] | select(.team_name == $name) | .team_id' <<<"$teams_response"
}

verify_public_workflows() {
  local response actual expected detail prediction ids northstar_id cedar_id game_id payload flagged
  response="$(api "$BASE_URL/teams?$(dataset_query)")"
  actual="$(jq -c '[.data.teams[] | {team_name, wins, losses}] | sort_by(.team_name)' <<<"$response")"
  expected="$(jq -c 'sort_by(.team_name)' "$FIXTURE_DIR/expected-records.json")"
  if [[ "$actual" != "$expected" ]]; then
    printf 'Expected records: %s\nActual records:   %s\n' "$expected" "$actual" >&2
    fail "Team records did not match expected-records.json"
  fi
  jq -e '[.data.teams[].power_ranking[0] | keys[0] | select(. != "initial")] | length == 7' \
    <<<"$response" >/dev/null || fail "Not every team received an updated power ranking"

  detail="$(api "$BASE_URL/teams/Northstar%20Academy?$(dataset_query)")"
  jq -e '.data.teams.season_opp | length == 5' <<<"$detail" >/dev/null || fail \
    "Northstar Academy should have five game records"

  prediction="$(api "$BASE_URL/predictions/Northstar%20Academy/Mesa%20Vista/true/?$(dataset_query)")"
  jq -e '(."Northstar Academy" | type == "number") and (."Mesa Vista" | type == "number")' \
    <<<"$prediction" >/dev/null || fail "Prediction response did not contain two numeric scores"

  ids="$(api "$BASE_URL/teams-ids/?$(dataset_query)")"
  northstar_id="$(team_id "$ids" "Northstar Academy")"
  cedar_id="$(team_id "$ids" "Cedar Valley")"
  game_id="${northstar_id}_${cedar_id}_2026-01-09"
  payload="$(jq -nc \
    --arg game_id "$game_id" \
    --argjson team1_id "$northstar_id" \
    --argjson team2_id "$cedar_id" \
    '{game_id: $game_id, team1_id: $team1_id, team1_name: "Northstar Academy", team2_id: $team2_id, team2_name: "Cedar Valley"}')"

  api \
    -X POST "$BASE_URL/flagged-game/?$(dataset_query)" \
    -H 'Content-Type: application/json' \
    --data "$payload" | jq -e '.game_flagged == 1' >/dev/null
  flagged="$(authenticated_api "$BASE_URL/retrieve-flagged?$(dataset_query)")"
  jq -e --arg game_id "$game_id" '.flagged_games | any(.game_id == $game_id)' <<<"$flagged" >/dev/null || fail \
    "The flagged game was not returned"
  authenticated_api -X DELETE "$BASE_URL/clear-flagged?$(dataset_query)" >/dev/null

  info "Verified records, ranking updates, team detail, prediction, and flag lifecycle"
}

run_happy_path() {
  ensure_dataset_documents
  assert_fixture_dataset_is_empty
  login
  add_teams
  upload_game_files
  verify_ingestion_storage
  run_background_jobs
  verify_public_workflows
  info "PASS: application happy-path smoke test"
}

run_maintenance_checks() {
  [[ "${CONFIRM_DESTRUCTIVE:-}" == "1" ]] || fail \
    "Maintenance checks refused. Re-run with: make test-app-maintenance CONFIRM_DESTRUCTIVE=1"

  local ids northstar_id cedar_id qa_id response detail archive_year
  login
  ids="$(api "$BASE_URL/teams-ids/?$(dataset_query)")"
  northstar_id="$(team_id "$ids" "Northstar Academy")"
  cedar_id="$(team_id "$ids" "Cedar Valley")"
  qa_id="$(team_id "$ids" "QA Reserve")"

  info "Updating the Northstar/Cedar score"
  authenticated_api \
    -X PUT --get "$BASE_URL/update-game/" \
    --data-urlencode 'date=2026-01-09' \
    --data-urlencode 'home_team=Northstar Academy' \
    --data-urlencode 'away_team=Cedar Valley' \
    --data-urlencode 'home_score=73' \
    --data-urlencode 'away_score=61' \
    --data-urlencode "sport_type=$SPORT" \
    --data-urlencode "gender=$GENDER" \
    --data-urlencode "level=$LEVEL" >/dev/null
  detail="$(api "$BASE_URL/teams/Northstar%20Academy?$(dataset_query)")"
  jq -e '.data.teams.season_opp | any(.game_date == "2026-01-09" and .home_score == 73 and .away_score == 61)' \
    <<<"$detail" >/dev/null || fail "Updated score was not reflected in Northstar's game history"

  info "Renaming and restoring the QA team"
  authenticated_api -X PUT \
    "$BASE_URL/update-name/$qa_id/QA%20Reserve%20Renamed?$(dataset_query)" >/dev/null
  response="$(api "$BASE_URL/teams?$(dataset_query)")"
  jq -e '.data.teams | any(.team_name == "QA Reserve Renamed")' <<<"$response" >/dev/null || fail \
    "Renamed QA team was not returned by the public team list"
  authenticated_api -X PUT \
    "$BASE_URL/update-name/$qa_id/QA%20Reserve?$(dataset_query)" >/dev/null

  info "Deleting the Northstar/Cedar game"
  authenticated_api -X DELETE \
    "$BASE_URL/delete-game/$northstar_id/$cedar_id/${northstar_id}_${cedar_id}_2026-01-09/2026-01-09?$(dataset_query)" >/dev/null
  detail="$(api "$BASE_URL/teams/Northstar%20Academy?$(dataset_query)")"
  jq -e --arg game_id "${northstar_id}_${cedar_id}_2026-01-09" \
    '.data.teams.season_opp | all(.game_id != $game_id)' <<<"$detail" >/dev/null || fail \
    "Deleted game is still present in Northstar's game history"

  info "Deleting QA Reserve"
  authenticated_api -X DELETE \
    "$BASE_URL/delete-team/QA%20Reserve/$qa_id/?$(dataset_query)" >/dev/null
  response="$(api "$BASE_URL/teams?$(dataset_query)")"
  jq -e '.data.teams | all(.team_name != "QA Reserve")' <<<"$response" >/dev/null || fail \
    "Deleted QA team is still present in the public team list"

  info "Archiving the current season before resetting the sample dataset"
  response="$(authenticated_api "$BASE_URL/archive-season/status")"
  archive_year="$(jq -r '.year' <<<"$response")"
  authenticated_api -X POST \
    "$BASE_URL/archive-season/?year=$archive_year&overwrite=true" >/dev/null
  response="$(authenticated_api -X DELETE "$BASE_URL/clear-season/?$(dataset_query)")"
  jq -e '.archive_unchanged == true and .teams_reset == true' <<<"$response" >/dev/null || fail \
    "Season reset did not preserve the existing archive"
  response="$(api "$BASE_URL/teams?$(dataset_query)")"
  jq -e '.data.teams | all(.wins == 0 and .losses == 0 and (.season_opp | length == 0))' \
    <<<"$response" >/dev/null || fail "Season data was not fully cleared"
  info "PASS: destructive maintenance requests completed"
}

main() {
  cd "$ROOT_DIR"
  require_command docker
  require_command curl
  require_command jq
  [[ -f "$FULL_FIXTURE_SPEC" && -f "$FULL_FIXTURE_LOADER" ]] || fail \
    "Full fixture specification or MongoDB loader is missing"
  [[ -n "${MONGO_USER:-}" && -n "${MONGO_PASS:-}" ]] || fail \
    "MONGO_USER and MONGO_PASS must be available in $ENV_FILE or the environment"
  wait_for_backend

  case "$MODE" in
    reset)
      reset_fixture_data
      login
      verify_full_fixture_data
      ;;
    maintenance)
      run_maintenance_checks
      ;;
    reset-admin)
      reset_test_admin
      ;;
    test)
      run_happy_path
      ;;
  esac
}

main "$@"
