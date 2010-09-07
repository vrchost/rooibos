pause This will set all user passwords in the database to 'admin'.
mysql -u root rooibos -e "UPDATE auth_user SET password='sha1$bc241$8bc918c29c4d1e313ca858bb1218b6c268b53961'"
