$env:PYTHONPATH = "$PSScriptRoot\.." + ";" + $env:PYTHONPATH
alembic -c "$PSScriptRoot\..\alembic.ini" upgrade head