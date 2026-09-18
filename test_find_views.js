const fs = require('fs');
const lines = fs.readFileSync('index.html', 'utf8').split('\n');
console.log('--- ALL TAB VIEWS IN INDEX.HTML ---');
lines.forEach((l, i) => {
  if (l.includes('class="tab-view') || (l.includes('id="') && l.includes('-view"'))) {
    console.log(`${i+1}: ${l.trim()}`);
  }
});
