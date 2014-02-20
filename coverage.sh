coverage run ./manage.py test --settings=earwig.settings.dev && coverage report && coverage html && gnome-open htmlcov/index.html
