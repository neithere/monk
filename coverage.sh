py.test --cov monk --cov-report term --cov-report html "$@" \
    && uzbl-browser htmlcov/index.html
