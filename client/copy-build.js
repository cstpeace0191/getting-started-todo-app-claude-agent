import fs from 'node:fs';
import path from 'node:path';

const srcDir = path.resolve('dist');
const destDir = path.resolve('../backend/src/static');

if (fs.existsSync(srcDir)) {
    fs.mkdirSync(destDir, { recursive: true });
    fs.cpSync(srcDir, destDir, { recursive: true });
    console.log(`Copied build files from ${srcDir} to ${destDir}`);
} else {
    console.error(`Build output directory not found: ${srcDir}`);
    process.exit(1);
}
