const { Pool } = require('pg');

async function autoFixDatabase() {
    console.log('🔧 AquaMonitor Database Auto-Fixer');
    console.log('===================================');
    console.log('');
    
    // Common PostgreSQL passwords to try
    const commonPasswords = ['password', 'postgres', '123456', 'admin', '', 'root'];
    const host = 'localhost';
    const port = 5432;
    const user = 'postgres';
    
    let workingPassword = null;
    
    console.log('🔍 Testing common PostgreSQL passwords...');
    
    for (const password of commonPasswords) {
        try {
            console.log(`   Trying password: "${password || '(empty)'}"`);
            
            const testPool = new Pool({
                user: user,
                host: host,
                port: port,
                password: password,
            });
            
            const client = await testPool.connect();
            console.log(`✅ Success! Password is: "${password || '(empty)'}"`);
            workingPassword = password;
            client.release();
            await testPool.end();
            break;
            
        } catch (error) {
            console.log(`   ❌ Failed: ${error.message.split('\n')[0]}`);
        }
    }
    
    if (!workingPassword && workingPassword !== '') {
        console.log('');
        console.log('❌ None of the common passwords worked.');
        console.log('💡 Please run: node fix-database.js to enter your password manually');
        return;
    }
    
    console.log('');
    console.log('🔍 Checking/creating aquamonitor database...');
    
    try {
        // Connect to PostgreSQL server
        const serverPool = new Pool({
            user: user,
            host: host,
            port: port,
            password: workingPassword,
        });
        
        const client = await serverPool.connect();
        
        // Check if aquamonitor database exists
        const dbResult = await client.query(
            "SELECT 1 FROM pg_database WHERE datname = 'aquamonitor'"
        );
        
        if (dbResult.rows.length === 0) {
            console.log('📝 Creating aquamonitor database...');
            await client.query('CREATE DATABASE aquamonitor');
            console.log('✅ Database created successfully');
        } else {
            console.log('✅ Database aquamonitor already exists');
        }
        
        client.release();
        await serverPool.end();
        
        // Test connection to aquamonitor database
        const appPool = new Pool({
            user: user,
            host: host,
            database: 'aquamonitor',
            password: workingPassword,
            port: port,
        });
        
        const appClient = await appPool.connect();
        console.log('✅ AquaMonitor database connection successful');
        
        // Check and create tables if needed
        const tablesResult = await appClient.query(`
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('aquafarms', 'pond_locations')
        `);
        
        const existingTables = tablesResult.rows.map(r => r.table_name);
        console.log('📋 Existing tables:', existingTables);
        
        if (existingTables.length < 2) {
            console.log('📝 Creating/updating required tables...');
            
            // Create aquafarms table
            await appClient.query(`
                CREATE TABLE IF NOT EXISTS aquafarms (
                    id SERIAL PRIMARY KEY,
                    farm_name VARCHAR(255) NOT NULL,
                    farm_id VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    owner_name VARCHAR(255),
                    contact_email VARCHAR(255),
                    contact_phone VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            `);
            
            // Create pond_locations table
            await appClient.query(`
                CREATE TABLE IF NOT EXISTS pond_locations (
                    id SERIAL PRIMARY KEY,
                    farm_id VARCHAR(100) REFERENCES aquafarms(farm_id) ON DELETE CASCADE,
                    pond_name VARCHAR(255) NOT NULL,
                    latitude DECIMAL(10, 8) NOT NULL,
                    longitude DECIMAL(11, 8) NOT NULL,
                    species VARCHAR(100) DEFAULT 'general',
                    secondary_species VARCHAR(100),
                    pond_type VARCHAR(50) DEFAULT 'pond',
                    status VARCHAR(50) DEFAULT 'active',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            `);
            
            console.log('✅ Tables created successfully');
        } else {
            console.log('✅ All required tables exist');
        }
        
        // Check if there's existing data
        const farmsCount = await appClient.query('SELECT COUNT(*) FROM aquafarms');
        const locationsCount = await appClient.query('SELECT COUNT(*) FROM pond_locations');
        
        console.log(`📊 Existing data: ${farmsCount.rows[0].count} farms, ${locationsCount.rows[0].count} locations`);
        
        appClient.release();
        await appPool.end();
        
        // Update server.js with correct credentials
        console.log('');
        console.log('📝 Updating server.js with correct credentials...');
        
        const fs = require('fs');
        const serverPath = './server.js';
        let serverContent = fs.readFileSync(serverPath, 'utf8');
        
        // Replace database configuration
        const newConfig = `const pool = new Pool({
    user: '${user}',
    host: '${host}', 
    database: 'aquamonitor',
    password: '${workingPassword}',
    port: ${port},
    // For production deployment, use environment variables:
    // connectionString: process.env.DATABASE_URL,
    // ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});`;
        
        serverContent = serverContent.replace(
            /const pool = new Pool\({[\s\S]*?}\);/,
            newConfig
        );
        
        fs.writeFileSync(serverPath, serverContent);
        console.log('✅ Server.js updated with correct credentials');
        
        console.log('');
        console.log('🎉 Database setup completed successfully!');
        console.log('');
        console.log('✅ Connection Details:');
        console.log(`   Host: ${host}`);
        console.log(`   Port: ${port}`);
        console.log(`   Database: aquamonitor`);
        console.log(`   User: ${user}`);
        console.log(`   Password: ${workingPassword || '(empty)'}`);
        console.log('');
        console.log('🚀 Next steps:');
        console.log('1. Run: node server.js');
        console.log('2. Open: http://localhost:3000');
        console.log('');
        
    } catch (error) {
        console.error('❌ Error setting up database:', error.message);
        console.log('');
        console.log('💡 Try running: node fix-database.js for manual setup');
    }
}

autoFixDatabase();