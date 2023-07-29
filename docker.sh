#!/bin/bash

my_dir="$(dirname "$(realpath "$0")")"

if [[ "$1" == "image" ]] ; then
    podman build -t amaranth "${my_dir}"
elif [[ "$1" == "run" ]] ; then
    shift
    podman run --rm -it --userns keep-id --volume "${my_dir}:${my_dir}" --workdir "$(pwd)" amaranth "$@"
else
    podman run --rm -it --userns keep-id --volume "${my_dir}:${my_dir}" --workdir "$(pwd)" amaranth make
fi
