// Simulate browser auth test using Node.js
const axios = require('axios');

// Configure exactly like the frontend
axios.defaults.baseURL = 'http://127.0.0.1:8000';

async function testRegistration() {
    console.log('Testing registration...');
    
    const registrationData = {
        email: 'browsertest@example.com',
        username: 'browseruser',
        password: 'BrowserPass123',
        full_name: 'Browser Test User'
    };
    
    try {
        const response = await axios.post('/api/auth/register', registrationData, {
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3001'
            }
        });
        
        console.log('✅ Registration SUCCESS!');
        console.log('Response:', JSON.stringify(response.data, null, 2));
        
        // Test immediate login
        return response.data;
    } catch (error) {
        console.log('❌ Registration FAILED!');
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
}

async function testLogin() {
    console.log('\nTesting login...');
    
    const loginData = {
        email_or_username: 'browseruser',
        password: 'BrowserPass123'
    };
    
    try {
        const response = await axios.post('/api/auth/login', loginData, {
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3001'
            }
        });
        
        console.log('✅ Login SUCCESS!');
        console.log('Response:', JSON.stringify(response.data, null, 2));
        return response.data;
    } catch (error) {
        console.log('❌ Login FAILED!');
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
}

async function testAuthFlow() {
    try {
        // Test registration
        const regData = await testRegistration();
        
        // Test login
        const loginData = await testLogin();
        
        // Test authenticated endpoint
        console.log('\nTesting authenticated endpoint...');
        const meResponse = await axios.get('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${loginData.access_token}`,
                'Origin': 'http://localhost:3001'
            }
        });
        
        console.log('✅ Authenticated endpoint SUCCESS!');
        console.log('User info:', JSON.stringify(meResponse.data, null, 2));
        
        console.log('\n🎉 ALL TESTS PASSED! Authentication is working correctly.');
        
    } catch (error) {
        console.log('\n💥 TESTS FAILED!');
        process.exit(1);
    }
}

testAuthFlow();