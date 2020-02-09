-- creating database
CREATE DATABASE fedspend;

-- creating users
CREATE USER sanoke WITH PASSWORD '<your-password>';
CREATE USER migrater WITH PASSWORD '<your-password>';

-- granting permissions
GRANT ALL ON DATABASE fedspend TO sanoke;
GRANT ALL ON DATABASE fedspend TO migrater;