# Database Setup Instructions

## Quick Setup (Windows)

1. **Install PostgreSQL** (if not already installed):
   - Download from: https://www.postgresql.org/download/windows/
   - During installation, set password as: `password`
   - Default port: 5432

2. **Create Database**:
   Open PostgreSQL command line (psql) and run:
   ```sql
   CREATE DATABASE aquamonitor;
   ```

3. **Run Setup Script**:
   ```bash
   cd web-app
   setup-db.bat
   ```

## Manual Setup

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Setup Database**:
   ```bash
   node setup-database.js
   ```

3. **Test Connection**:
   ```bash
   node test-connection.js
   ```

4. **Start Server**:
   ```bash
   node server.js
   ```

## Troubleshooting

- **Connection Error**: Make sure PostgreSQL service is running
- **Authentication Error**: Check username/password in server.js
- **Database Not Found**: Create database manually: `CREATE DATABASE aquamonitor;`

## Default Configuration

- **Host**: localhost
- **Port**: 5432
- **Database**: aquamonitor
- **Username**: postgres
- **Password**: password

Update these in `server.js` if your PostgreSQL setup is different.