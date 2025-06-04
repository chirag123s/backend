#!/bin/bash

# URL to request
URL="http://192.168.50.10:8002/scraper/ddg/dl/cars/"

# Optional headers
HEADERS=(-H "User-Agent: Mozilla/5.0")

# Delay between retries (initial, in seconds)
DELAY=60

# Max number of retries
MAX_RETRIES=100

# Retry counter
attempt=1

# Retry on these status codes
RETRY_STATUSES=("403" "429" "500" "502" "503" "504")

should_retry() {
  for code in "${RETRY_STATUSES[@]}"; do
    if [ "$1" == "$code" ]; then
      return 0
    fi
  done
  return 1
}

while true; do
  echo "🌐 Attempt $attempt: Requesting $URL..."

  # Capture only the HTTP status code
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${HEADERS[@]}" "$URL")
  echo "📡 Response status: $STATUS"

  if should_retry "$STATUS"; then
    if [ "$attempt" -ge "$MAX_RETRIES" ]; then
      echo "🛑 Max retries ($MAX_RETRIES) reached. Exiting."
      exit 1
    fi

    echo "🔁 Retrying after $DELAY seconds (retryable status: $STATUS)..."
    sleep "$DELAY"

    # ⏱️ Exponential backoff: double the delay each time
    DELAY=$((DELAY * 2))
    attempt=$((attempt + 1))
  else
    echo "✅ Request succeeded or failed with non-retryable status. Exiting."
    break
  fi
done
