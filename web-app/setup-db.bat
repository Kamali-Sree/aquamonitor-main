@echo off
echo Setting up AquaMonitor Database...
echo.

echo Step 1: Installing Node.js dependencies...
call npm install

echo.
echo Step 2: Setting up PostgreSQL database...
echo Make sure PostgreSQL is running on your system
echo Default connection: localhost:5432, user: postgres, password: password
echo.

echo Creating database and tables...
node setup-database.js

echo.
echo Step 3: Testing database connection...
node test-connection.js

echo.
echo Database setup completed!
echo You can now start the server with: node server.js
pause