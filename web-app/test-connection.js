const { Pool } = require('pg');

// Local PostgreSQL configuration
const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'aquamonitor',
    password: 'password',
    port: 5432,
});

async function testConnection() {
    try {
        console.log('🔍 Testing database connection...');
        
        const client = await pool.connect();
        console.log('✅ PostgreSQL connection successful');
        
        // Test basic query
        const result = await client.query('SELECT NOW() as current_time');
        console.log('⏰ Database time:', result.rows[0].current_time);
        
        // Check if tables exist
        const tablesResult = await client.query(`
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('aquafarms', 'pond_locations')
        `);
        
        console.log('📋 Available tables:', tablesResult.rows.map(r => r.table_name));
        
        client.release();
        console.log('🎉 Database connection test completed successfully');
        
    } catch (error) {
        console.error('❌ Database connection failed:', error.message);
        console.log('');
        console.log('🔧 Troubleshooting steps:');
        console.log('1. Make sure PostgreSQL is installed and running');
        console.log('2. Create database: CREATE DATABASE aquamonitor;');
        console.log('3. Update credentials in this file if needed');
        console.log('4. Run: node setup-database.js');
    } finally {
        await pool.end();
    }
}

testConnection();