#!/bin/bash

my_dir="$(dirname "$(realpath "$0")")"

if [[ "$1" == "build" ]] ; then
    podman build -t amaranth "${my_dir}"
else
    podman run --rm -it --userns keep-id --volume "${my_dir}:${my_dir}" --workdir "$(pwd)" amaranth "${my_dir}/build.sh"
fi
