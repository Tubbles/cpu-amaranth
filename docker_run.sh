#!/bin/bash

my_dir="$(dirname "$(realpath "$0")")"

podman run --rm -it --userns keep-id --volume "${my_dir}:${my_dir}" --workdir "$(pwd)" amaranth "$@"
