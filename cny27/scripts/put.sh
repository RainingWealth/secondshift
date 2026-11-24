#!/bin/bash
# usage: put.sh file "<uploadUrl>" -> prints HTTP code (Photoroom signed PUT; headers fixed to those the API returns for jpeg/png)
ct=$(case "$1" in *.png) echo image/png;; *) echo image/jpeg;; esac)
curl -s -o /dev/null -w "%{http_code}\n" -X PUT -H "content-type: $ct" -H "x-goog-if-generation-match: 0" --data-binary @"$1" "$2"
