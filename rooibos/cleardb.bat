mysqldump -u root --add-drop-table --no-data rooibos > _temp_rooibos_structure.mysql
mysql -u root rooibos < _temp_rooibos_structure.mysql
del _temp_rooibos_structure.mysql