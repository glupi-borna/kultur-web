#!/bin/bash

localserver &

echo "Watching $PWD for changes..."
while true; do
    mod="$(inotifywait -rq -e modify .)"
    file="$(echo "$mod" | cut -d" " -f3)"

    if [[ "$file" =~ .*src.html$ ]] || \
        [[ "$file" =~ .*post ]] || \
        [[ "$file" =~ .*part.html ]] || \
        [[ "$file" =~ .*generate.py ]] || \
        [[ "$file" =~ .*inject.py ]] || \
        [[ "$file" =~ .*newsgen.py ]] || \
        [[ "$file" =~ .*news.links ]]
    then
        echo "$file modified, rebuilding..."
        ./build.sh
        echo "Build finished."
    fi
done
