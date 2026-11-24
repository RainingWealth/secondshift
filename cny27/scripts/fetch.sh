#!/bin/bash
# usage: fetch.sh "<downloadUrl>" out_file  (links expire ~5 min) -> prints file size
curl -s -o "$2" "$1" && stat -c %s "$2"
