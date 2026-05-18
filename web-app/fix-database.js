const { Pool } = require('pg');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function askQuestion(question) {
    return new Promise((resolve) => {
        rl.question(question, (answer) => {
            resolve(answer);
        });
    });
}

async function fixDatabase() {
    console.log('🔧 AquaMonitor Database Connection Fixer');
    console.log('=========================================');
    console.log('');
    
    // Get current PostgreSQL credentials
    console.log('Please provide your PostgreSQL credentials:');
    const host = await askQuestion('Host (default: localhost): ') || 'localhost';
    const port = await askQuestion('Port (default: 5432): ') || '5432';
    const user = await askQuestion('Username (default: postgres): ') || 'postgres';
    const password = await askQuestion('Password: ');
    
    console.log('');
    console.log('🔍 Testing connection...');
    
    // Test connection to PostgreSQL server (without specific database)
    const serverPool = new Pool({
        user: user,
        host: host,
        port: parseInt(port),
        password: password,
        // Don't specify database initially
    });
    
    try {
        const client = await serverPool.connect();
        console.log('✅ PostgreSQL server connection successful');
        
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
        
        // Now test connection to aquamonitor database
        const appPool = new Pool({
            user: user,
            host: host,
            database: 'aquamonitor',
            password: password,
            port: parseInt(port),
        });
        
        const appClient = await appPool.connect();
        console.log('✅ AquaMonitor database connection successful');
        
        // Check tables
        const tablesResult = await appClient.query(`
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('aquafarms', 'pond_locations')
        `);
        
        const existingTables = tablesResult.rows.map(r => r.table_name);
        console.log('📋 Existing tables:', existingTables);
        
        if (existingTables.length === 0) {
            console.log('📝 Creating required tables...');
            
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
            console.log('✅ Required tables already exist');
        }
        
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
    password: '${password}',
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
        console.log('Next steps:');
        console.log('1. Run: node server.js');
        console.log('2. Open: http://localhost:3000');
        console.log('');
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        console.log('');
        console.log('💡 Common solutions:');
        console.log('1. Make sure PostgreSQL service is running');
        console.log('2. Check if the password is correct');
        console.log('3. Try connecting with pgAdmin or psql first');
        console.log('4. On Windows, check Services for "postgresql" service');
    }
    
    rl.close();
}

fixDatabase();