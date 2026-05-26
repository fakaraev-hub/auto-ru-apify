const { execSync } = require('child_process');
const path = require('path');
const { Actor } = require('apify');

async function main() {
    console.log('Starting auto.ru parser...');
    await Actor.init();
    const input = await Actor.getInput();
    const pythonPath = process.env.PYTHON_PATH || 'python3';
    const scriptPath = path.join(__dirname, 'src', 'main.py');
    try {
        execSync(`${pythonPath} ${scriptPath}`, {
            encoding: 'utf-8',
            stdio: 'inherit',
            env: {
                ...process.env,
                PYTHONPATH: path.join(__dirname, 'src'),
                APIFY_INPUT: JSON.stringify(input || {}),
            }
        });
        await Actor.exit();
    } catch (error) {
        console.error('Python script failed:', error.message);
        await Actor.fail(error);
        process.exit(1);
    }
}
main();
