set apps=
if "%1"=="" set apps=-a
python manage.py graph_models -g %apps% %1 %2 %3 %4 %5 %6 %7 %8 %9 | dot -ograph.svg -Tsvg