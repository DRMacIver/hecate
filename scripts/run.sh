#!/bin/bash

set -e
set -x

export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
pyenv local 3.4.3
PYTHONPATH=src python -c '
    from hecate.tmux import TMUX
    print("tmux=", TMUX)
'
tox
