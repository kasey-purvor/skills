// Photographs every screen on a list at every width, once, into one shared set that all the
// review agents work from. Also measures what a picture cannot show at a glance: how far the
// page is wider than the screen, and which elements cross the right edge.
//
//   NODE_PATH=<project>/node_modules node capture.cjs --screens screens.json --out <folder> \
//     [--base http://localhost:5173] [--widths 390,820,1280] [--state session.json] [--heights 390:664]
//
// screens.json is a list (format and the rules for choosing screens: ../capture.md):
//   [{ "slug": "customers", "path": "/customers", "ready": "h1",
//      "steps": [{ "click": "text=Orders" }, { "scrollRight": ".table-wrap" }, { "wait": 500 }] }]
// An entry may give "url" in place of "path". Supported steps: click, scrollRight, wait, press.
// Click/press can write: this helper does not enforce read-only use. Keep write journeys out
// of batch lists because each entry repeats at every width; capture those journeys live.
//
// Writes <slug>--<width>.png (the whole page) and report.json. Refuses to overwrite a folder
// that already holds a report, so two runs are never mixed. Exits 1 if any screen failed.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const HEIGHTS = { 390: 844, 820: 1180, 1024: 768, 1280: 800 };

function args() {
  const a = process.argv.slice(2), o = {};
  for (let i = 0; i < a.length; i += 2) o[a[i].replace(/^--/, '')] = a[i + 1];
  return o;
}

(async () => {
  const o = args();
  if (!o.screens || !o.out) { console.error('usage: node capture.cjs --screens screens.json --out <folder> [--base url] [--widths 390,820,1280] [--state session.json] [--heights 390:664]'); process.exit(2); }
  const screens = JSON.parse(fs.readFileSync(o.screens, 'utf8'));
  const widths = (o.widths || '390,820,1280').split(',').map(Number);
  const heights = { ...HEIGHTS };
  for (const pair of (o.heights || '').split(',').filter(Boolean)) { const [w, h] = pair.split(':').map(Number); heights[w] = h; }
  if (fs.existsSync(path.join(o.out, 'report.json'))) { console.error(`${o.out} already holds a run; choose a new folder`); process.exit(2); }
  fs.mkdirSync(o.out, { recursive: true });

  const browser = await chromium.launch();
  const report = [];
  let failed = 0;
  for (const width of widths) {
    const context = await browser.newContext({
      viewport: { width, height: heights[width] || 900 },
      storageState: o.state && fs.existsSync(o.state) ? o.state : undefined,
      reducedMotion: 'reduce',
    });
    for (const s of screens) {
      const row = { slug: s.slug, width, height: heights[width] || 900 };
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', (e) => errors.push(String(e).slice(0, 200)));
      try {
        await page.goto(s.url || (o.base || '') + s.path, { waitUntil: 'networkidle', timeout: 45000 });
        if (s.ready) await page.waitForSelector(s.ready, { timeout: 20000 });
        for (const step of s.steps || []) {
          if (step.click) await page.click(step.click, { timeout: 10000 });
          else if (step.press) await page.keyboard.press(step.press);
          else if (step.scrollRight) await page.$eval(step.scrollRight, (e) => { e.scrollLeft = e.scrollWidth; });
          else if (step.wait) await page.waitForTimeout(step.wait);
        }
        await page.evaluate(() => document.fonts && document.fonts.ready);
        await page.waitForTimeout(300);
        Object.assign(row, await page.evaluate((w) => {
          const doc = document.documentElement;
          const over = Math.max(doc.scrollWidth, document.body.scrollWidth) - w;
          const crossing = [];
          if (over > 1) {
            for (const e of document.querySelectorAll('body *')) {
              const r = e.getBoundingClientRect();
              if (r.width && r.right > w + 1 && !crossing.some((c) => c.el.contains(e))) crossing.push({ el: e, right: Math.round(r.right) });
              if (crossing.length >= 8) break;
            }
          }
          return {
            pageHeight: doc.scrollHeight,
            screens: +(doc.scrollHeight / window.innerHeight).toFixed(1),
            overflow: over > 1 ? over : 0,
            crossing: crossing.map((c) => `${c.el.tagName.toLowerCase()}${c.el.className && typeof c.el.className === 'string' ? '.' + c.el.className.split(/\s+/).slice(0, 3).join('.') : ''} (right edge at ${c.right}px)`),
          };
        }, width));
        row.file = `${s.slug}--${width}.png`;
        await page.screenshot({ path: path.join(o.out, row.file), fullPage: true });
        row.errors = errors;
        console.log(`${row.file}  ${row.pageHeight}px tall (${row.screens} screens)${row.overflow ? `  WIDER THAN THE SCREEN by ${row.overflow}px` : ''}`);
      } catch (e) {
        row.failed = String(e).split('\n')[0].slice(0, 300);
        failed++;
        console.log(`${s.slug} at ${width}: NOT CAPTURED: ${row.failed}`);
      }
      report.push(row);
      await page.close();
    }
    await context.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(o.out, 'report.json'), JSON.stringify(report, null, 2));
  console.log(`${report.length - failed} of ${report.length} captured; report.json written`);
  process.exit(failed ? 1 : 0);
})();
