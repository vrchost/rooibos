#!/bin/bash
set -x
source %(install_dir)s/venv/bin/activate
mdid $@
