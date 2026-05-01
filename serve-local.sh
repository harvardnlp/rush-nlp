#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"
docker run --rm -it \
  -p 4000:4000 \
  -v "$(pwd):/site" \
  -w /site \
  ruby:3.3-alpine \
  sh -c "apk add --no-cache build-base >/dev/null && bundle install --quiet && bundle exec jekyll serve --host 0.0.0.0 --livereload"
