rm -r dist
python -m build
python -m twine upload dist/*
