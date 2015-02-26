CREATE DATABASE rooibos CHARACTER SET utf8;
GRANT ALL PRIVILEGES ON rooibos.* TO rooibos@localhost IDENTIFIED BY 'rooibos';
UPDATE mysql.user SET
    Select_priv='Y', Insert_priv='Y', Update_priv='Y', Delete_priv='Y',
    Create_priv='Y', Drop_priv='Y', Index_priv='Y', Alter_priv='y'
    WHERE Host='localhost' AND User='rooibos';
FLUSH PRIVILEGES;
