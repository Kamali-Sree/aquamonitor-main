const { Pool } = require('pg');

// Local PostgreSQL configuration
const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'aquamonitor',
    password: 'kamalimsd@127',
    port: 5432,
});

async function setupDatabase() {
    try {
        console.log('🔧 Setting up AquaMonitor database...');
        
        // Create aquafarms table
        await pool.query(`
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
        await pool.query(`
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
        
        console.log('✅ Database tables created successfully');
        console.log('📊 AquaMonitor database is ready for use');
        
    } catch (error) {
        console.error('❌ Database setup failed:', error.message);
        console.log('💡 Make sure PostgreSQL is running and accessible');
        console.log('💡 Default connection: localhost:5432, database: aquamonitor, user: postgres');
    } finally {
        await pool.end();
    }
}

setupDatabase();