const { execSync } = require('child_process');
const path = require('path');

async function main() {
    console.log('Starting auto.ru parser...');
    const pythonPath = process.env.PYTHON_PATH || 'python3';
    const scriptPath = path.join(__dirname, 'src', 'main.py');
    try {
        execSync(`${pythonPath} ${scriptPath}`, {
            encoding: 'utf-8',
            stdio: 'inherit',
            env: { ...process.env, PYTHONPATH: path.join(__dirname, 'src') }
        });
    } catch (error) {
        console.error('Python script failed:', error.message);
        process.exit(1);
    }
}
main();
