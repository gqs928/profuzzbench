const fs = require('fs')
const path = require('path')

const root = process.argv[2]
if (!root) throw new Error('usage: node summarize-v8-coverage.js COVERAGE_DIR')
const files = fs.readdirSync(root, { withFileTypes: true })
  .filter(entry => entry.isFile() && entry.name.endsWith('.json'))
  .map(entry => path.join(root, entry.name))
const scripts = new Set()
let functions = 0, called = 0
for (const file of files) {
  const data = JSON.parse(fs.readFileSync(file, 'utf8'))
  for (const script of data.result || []) {
    if (!script.url.startsWith('file:///src/Haraka/')) continue
    scripts.add(script.url)
    for (const fn of script.functions || []) {
      functions++
      if (fn.ranges && fn.ranges.some(range => range.count > 0)) called++
    }
  }
}
process.stdout.write(JSON.stringify({
  scope: '/src/Haraka (Node V8 runtime coverage; independent of AFLNet mutation feedback)',
  coverage_json_files: files.length,
  target_scripts_observed: scripts.size,
  functions_observed: functions,
  functions_executed: called,
  method: 'Node built-in NODE_V8_COVERAGE function-range counters; raw JSON retained'
}, null, 2) + '\n')
