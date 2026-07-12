#!/bin/sh

command_exists () {
    command -v "$1" >/dev/null 2>&1
    echo "$?"
}

####################
### Check for uv ###
####################

if [ $(command_exists uv) != "0" ]; then
    echo "'uv' could not be found. The setup cannot be completed."
    exit 1
fi

#######################
### Check for .venv ###
#######################

venv_path="$(pwd)/.venv"
if [ ! -f "$venv_path" ]; then

    # If the script was accidentally called from some other directory,
    # we want to make sure that no venv is initialized in a random location.
    # We check for the presence of the 'pyproject.toml'.
    # If it is missing, we are likely in a location where no .venv belongs.
    pyproject_path="$(pwd)/pyproject.toml"
    if [ -f "$pyproject_path" ]; then
        echo "'.venv' directory missing. Creating it."
        uv venv
        if [ "$VIRTUAL_ENV" != "" ]; then
            echo "Another virtual environment is currently active."
            echo "Deactivating it before activating the new one."
            deactivate
        fi
        . .venv/bin/activate
        uv sync
    else
        echo "'.venv' directory and 'pyproject.toml' are missing."
        echo "Are you in the projects root?"
        exit 1
    fi
fi

