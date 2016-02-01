sudo -u postgres psql -c "DROP ROLE IF EXISTS admindemo_user"
sudo -u postgres psql -c "CREATE USER admindemo_user WITH PASSWORD 'admindemo_user';"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS admindemo_blog"
sudo -u postgres psql -c "CREATE DATABASE admindemo_blog ENCODING 'UTF8';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE admindemo_blog TO admindemo_user;"

cat sql/data.sql | sudo -u postgres psql -d admindemo_blog -a
