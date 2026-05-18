@echo off
echo Checking PostgreSQL Service Status...
echo ====================================
echo.

:: Check if PostgreSQL service is running
sc query postgresql-x64-14 >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ PostgreSQL service found: postgresql-x64-14
    sc query postgresql-x64-14 | findstr "STATE"
) else (
    sc query postgresql-x64-13 >nul 2>&1
    if %errorlevel% == 0 (
        echo ✅ PostgreSQL service found: postgresql-x64-13
        sc query postgresql-x64-13 | findstr "STATE"
    ) else (
        sc query postgresql-x64-12 >nul 2>&1
        if %errorlevel% == 0 (
            echo ✅ PostgreSQL service found: postgresql-x64-12
            sc query postgresql-x64-12 | findstr "STATE"
        ) else (
            echo ❌ PostgreSQL service not found
            echo.
            echo Common PostgreSQL service names:
            echo - postgresql-x64-14
            echo - postgresql-x64-13  
            echo - postgresql-x64-12
            echo.
            echo To start PostgreSQL:
            echo 1. Open Services (services.msc)
            echo 2. Find PostgreSQL service
            echo 3. Right-click and select "Start"
            echo.
            echo Or try these commands:
            echo net start postgresql-x64-14
            echo net start postgresql-x64-13
            echo net start postgresql-x64-12
        )
    )
)

echo.
echo Checking if PostgreSQL is listening on port 5432...
netstat -an | findstr ":5432" >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ PostgreSQL is listening on port 5432
) else (
    echo ❌ PostgreSQL is not listening on port 5432
    echo Make sure PostgreSQL service is started
)

echo.
echo Press any key to continue...
pause >nul