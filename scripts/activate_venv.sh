#!/bin/sh

dotvenv_path="$(pwd)/.venv"

if [ ! -d "$dotvenv_path" ]; then
    echo "Did not detect the .venv directory."
    echo "Running 'scripts/setup.sh' to initialize the project."
    scripts/setup.sh
    setup_success="$?"
else
    setup_success="0"
fi

# We do not want to call exit in this script, since it is likely called
# via 'source'. This would exit the session.
# --> Have explicit success check.
if [ "$setup_success" = "0" ]; then
    if [ "$VIRTUAL_ENV" = "" ]; then
        echo "Activating virtual environment."
        . $dotvenv_path/bin/activate
    elif [ "$VIRTUAL_ENV" = "$dotvenv_path" ]; then
        echo "The virtual environment is already activated. Skipping."
    else
        echo "Virtual venv '${VIRTUAL_ENV}' is currently activated."
        echo "Deactivating it and activating the projects .venv."

        deactivate
        . $dotvenv_path/bin/activate
    fi
fi
