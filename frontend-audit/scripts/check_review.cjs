// Check the rendered report and exercise its controls in a fresh browser context.
// This never opens the owner's browser profile, touches their rulings, or fetches links.
//
// NODE_PATH=<project>/node_modules node check_review.cjs <review.html|localhost URL> [finding id ...]
// Optional named-card screenshots go beside a local report in check/. HTTP checks are read-only
// and omit screenshots. Network requests outside the selected local origin are refused.
'use strict';
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const anchor = (id) => id.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const source = process.argv[2];
const ids = process.argv.slice(3);
let file, url;
try {
  if (/^https?:\/\//i.test(source || '')) {
    url = new URL(source);
    assert.equal(url.protocol, 'http:', 'use the local HTTP review server');
    assert.ok(['localhost', '127.0.0.1', '[::1]'].includes(url.hostname), 'URL must be loopback');
    assert.ok(!url.username && !url.password, 'URL must not include credentials');
  } else {
    assert.ok(source, 'missing report');
    file = path.resolve(source);
    assert.ok(fs.statSync(file).isFile(), 'report must be a file');
    url = pathToFileURL(file);
  }
} catch (error) {
  console.error('usage: node check_review.cjs <review.html|http://localhost:port/review.html> [finding id ...]');
  console.error(error.message);
  process.exit(2);
}

async function decodeImages(page) {
  return page.evaluate(async () => {
    for (const image of document.images) image.loading = 'eager';
    const decoded = await Promise.all(Array.from(document.images, async (image) => {
      try { await image.decode(); return true; } catch { return false; }
    }));
    return decoded.filter((ok) => !ok).length;
  });
}

async function inspect(page) {
  const decodeFailures = await decodeImages(page);
  return page.evaluate((decodeFailures) => {
    const problems = [];
    const fail = (message) => problems.push(message);
    const close = (a, b) => Math.abs(a - b) <= 1;
    const images = Array.from(document.images);
    const anchors = new Set();
    for (const element of document.querySelectorAll('[id]')) {
      if (anchors.has(element.id)) fail('duplicate id: ' + element.id);
      anchors.add(element.id);
    }
    for (const link of document.querySelectorAll('a[href]')) {
      const href = link.getAttribute('href');
      if (href.startsWith('#')) {
        let target;
        try { target = decodeURIComponent(href.slice(1)); } catch { fail('bad fragment: ' + href); continue; }
        if (!target || !anchors.has(target)) fail('missing anchor: ' + href);
      } else {
        const parsed = new URL(href, location.href);
        if (!['http:', 'https:', 'file:'].includes(parsed.protocol)) fail('unsafe link protocol: ' + parsed.protocol);
      }
    }
    if (decodeFailures) fail(decodeFailures + ' images failed to decode');
    for (const image of images) {
      if (!image.complete || !image.naturalWidth || !image.naturalHeight) fail('broken image');
    }
    for (const shot of document.querySelectorAll('.shot')) {
      const image = shot.querySelector('img');
      if (!image) { fail('screenshot has no image'); continue; }
      const overlay = shot.querySelector('svg.hl');
      if (!overlay) continue;
      const ir = image.getBoundingClientRect(), sr = overlay.getBoundingClientRect();
      const vb = overlay.viewBox.baseVal;
      if (!close(ir.x, sr.x) || !close(ir.y, sr.y) || !close(ir.width, sr.width) || !close(ir.height, sr.height)) {
        fail('overlay/image geometry differs: ' + image.alt);
      }
      if (vb.x !== 0 || vb.y !== 0 || vb.width !== image.naturalWidth || vb.height !== image.naturalHeight) {
        fail('overlay coordinates differ from decoded image: ' + image.alt);
      }
      for (const ring of overlay.querySelectorAll('.ring')) {
        const values = ['x', 'y', 'width', 'height'].map((key) => Number(ring.getAttribute(key)));
        const [x, y, w, h] = values;
        if (!values.every(Number.isFinite) || x < 0 || y < 0 || w <= 0 || h <= 0 ||
            x + w > vb.width || y + h > vb.height) fail('invalid highlight box: ' + image.alt);
        const rr = ring.getBoundingClientRect();
        if (!close(rr.x, ir.x + x * ir.width / vb.width) || !close(rr.y, ir.y + y * ir.height / vb.height) ||
            !close(rr.width, w * ir.width / vb.width) || !close(rr.height, h * ir.height / vb.height)) {
          fail('highlight projection differs from image: ' + image.alt);
        }
      }
    }
    if (document.documentElement.scrollWidth > window.innerWidth + 1) fail('page overflows viewport');
    for (const wrapper of document.querySelectorAll('.tw')) {
      const table = wrapper.querySelector('table');
      if (!table) { fail('table scroller has no table'); continue; }
      if (!['auto', 'scroll'].includes(getComputedStyle(wrapper).overflowX)) fail('table cannot scroll horizontally');
      for (const cell of table.querySelectorAll('th,td')) {
        if (cell.getBoundingClientRect().width < 64) fail('table column compressed below readable width');
      }
      if (wrapper.scrollWidth + 1 < table.getBoundingClientRect().width) fail('table exceeds its scroll range');
      wrapper.scrollLeft = wrapper.scrollWidth;
      const edge = wrapper.getBoundingClientRect().left + wrapper.clientWidth;
      const last = table.querySelector('thead tr th:last-child');
      if (last && last.getBoundingClientRect().right > edge + 1) fail('last table column cannot be scrolled into view');
      wrapper.scrollLeft = 0;
    }
    return { findings: document.querySelectorAll('.item[data-id]').length, pictures: images.length,
      rings: document.querySelectorAll('.ring').length, noPicture: document.querySelectorAll('.nopic').length,
      tables: document.querySelectorAll('.tw').length, pageWidth: document.documentElement.scrollWidth, problems };
  }, decodeFailures);
}

async function checkAnchors(page) {
  const hrefs = await page.locator('.bar nav a').evaluateAll((links) => links.map((link) => link.getAttribute('href')));
  assert.ok(hrefs.length, 'toolbar needs section anchors');
  for (const href of hrefs) {
    await page.locator('.bar nav a').evaluateAll((links, wanted) => {
      links.find((link) => link.getAttribute('href') === wanted).click();
    }, href);
    await page.waitForFunction((target) => {
      const el = document.getElementById(target.slice(1));
      return el && el.getBoundingClientRect().top >= document.querySelector('.bar').getBoundingClientRect().bottom - 1;
    }, href);
  }
}

async function checkControls(page) {
  const first = page.locator('.item[data-id]').first();
  const total = await page.locator('.item[data-id]').count();
  if (!total) {
    await page.locator('#save').click();
    assert.equal(await page.locator('#save').textContent(), 'Nothing yet', 'empty export is explicit');
    return 'coverage-only report: empty export checked';
  }
  const id = await first.getAttribute('data-id');
  const key = await page.locator('body').getAttribute('data-key');
  const ruling = (value) => first.locator('.o-' + value);
  for (const value of ['keep', 'drop', 'discuss']) {
    await ruling(value).click();
    assert.equal(await ruling(value).locator('input').isChecked(), true, value + ' radio');
    assert.ok((await page.locator('#anstext').textContent()).includes(id + ' ' + value), value + ' export');
    assert.ok(await first.evaluate((el, wanted) => el.classList.contains('a-' + wanted), value), value + ' card state');
  }
  await ruling('discuss').click();
  assert.equal(await ruling('discuss').locator('input').isChecked(), false, 'repeat-click clear');
  assert.ok(!(await page.locator('#anstext').textContent()).includes(id + ' discuss'), 'clear export');
  await ruling('keep').click();
  await first.locator('.clear-ruling').click();
  assert.equal(await ruling('keep').locator('input').isChecked(), false, 'explicit clear');
  await ruling('keep').click();
  await first.locator('.note').fill('Checker note\nsecond line');
  assert.ok((await page.locator('#anstext').textContent()).includes(id + ' keep: Checker note / second line'));
  await page.reload();
  await decodeImages(page);
  assert.equal(await ruling('keep').locator('input').isChecked(), true, 'ruling survives reload');
  assert.equal(await first.locator('.note').inputValue(), 'Checker note\nsecond line', 'note survives reload');
  const chip = page.locator('td .c').filter({ hasText: id }).first();
  if (await chip.count()) assert.ok(await chip.evaluate((el) => el.classList.contains('keep')), 'table chip follows ruling');
  await page.locator('#unans').click();
  assert.equal(await first.isVisible(), false, 'unruled filter hides answered card');
  assert.equal(await page.locator('.item[data-id]:visible').count(), total - 1, 'unruled filter retains other cards');
  await page.locator('#unans').click();
  assert.equal(await first.isVisible(), true, 'filter can be reset');
  await page.locator('#hl').click();
  assert.equal(await page.locator('#hl').getAttribute('aria-pressed'), 'false', 'highlight toggle off');
  for (const overlay of await page.locator('svg.hl').all()) assert.equal(await overlay.isVisible(), false, 'highlight hidden');
  await page.locator('#hl').click();
  assert.equal(await page.locator('#hl').getAttribute('aria-pressed'), 'true', 'highlight toggle on');
  const shot = page.locator('.shot').first();
  if (await shot.count()) {
    await shot.click();
    assert.equal(await page.locator('#zoom').isVisible(), true, 'lightbox opens');
    assert.equal(await page.locator('#zoom img').count(), 1, 'lightbox image');
    const zoomInfo = await inspect(page);
    assert.deepEqual(zoomInfo.problems, [], 'lightbox geometry and identifiers');
    const closePicture = page.locator('#zoom button');
    assert.equal(await closePicture.evaluate((el) => el === document.activeElement), true, 'lightbox focuses close button');
    for (const key of ['Tab', 'Tab', 'Shift+Tab', 'Shift+Tab']) {
      await page.keyboard.press(key);
      assert.equal(await closePicture.evaluate((el) => el === document.activeElement), true, key + ' stays in lightbox');
    }
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#zoom').isVisible(), false, 'Escape closes lightbox');
    assert.equal(await shot.evaluate((el) => el === document.activeElement), true, 'Escape returns focus to screenshot');
    await shot.focus();
    await page.keyboard.press('Enter');
    await closePicture.click();
    assert.equal(await page.locator('#zoom').isVisible(), false, 'close button closes lightbox');
    assert.equal(await shot.evaluate((el) => el === document.activeElement), true, 'close button returns focus to screenshot');
    await page.keyboard.press('Space');
    assert.equal(await page.locator('#zoom').isVisible(), true, 'Space opens lightbox');
    await page.locator('#zoom').click({ position: { x: 1, y: 1 } });
    assert.equal(await page.locator('#zoom').isVisible(), false, 'backdrop closes lightbox');
    assert.equal(await shot.evaluate((el) => el === document.activeElement), true, 'backdrop returns focus to screenshot');
  }
  const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#save').click()]);
  assert.equal(download.suggestedFilename(), key + '-rulings.txt', 'export filename');
  assert.equal(fs.readFileSync(await download.path(), 'utf8'), id + ' keep: Checker note / second line\n', 'export content');
  // Capture Copy deterministically without changing the operator's system clipboard.
  await page.evaluate(() => {
    window.__reviewCopied = null;
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
      writeText: async (text) => { window.__reviewCopied = text; }
    } });
    document.execCommand = (command) => {
      if (command === 'copy') window.__reviewCopied = document.activeElement.value;
      return command === 'copy';
    };
  });
  await page.locator('#copy').click();
  await page.waitForFunction(() => window.__reviewCopied !== null);
  assert.equal(await page.evaluate(() => window.__reviewCopied), id + ' keep: Checker note / second line', 'copy content');
  await first.locator('.clear-ruling').click();
  assert.ok((await page.locator('#anstext').textContent()).includes(id + ' no ruling: Checker note / second line'), 'clear preserves note');
  await first.locator('.note').fill('');
  await page.reload();
  assert.equal(await page.locator('#anstext').textContent(), 'No rulings yet.', 'clear persists');
  assert.equal(await first.locator('.note').inputValue(), '', 'note removal persists');
  return 'Keep/Drop/Discuss, both clears, notes/reload, filter, highlights, lightbox, save and copy checked';
}

(async () => {
  const browser = await chromium.launch();
  let bad = 0;
  try {
    for (const width of [1280, 390]) {
      // Nonpersistent contexts cannot read or mutate the owner's browser storage.
      const context = await browser.newContext({ viewport: { width, height: 900 }, acceptDownloads: true });
      const page = await context.newPage();
      const errors = [], blocked = [];
      page.on('pageerror', (error) => errors.push(String(error)));
      await context.route('**/*', async (route) => {
        const requested = new URL(route.request().url());
        const permitted = url.protocol === 'file:' ? requested.protocol === 'file:' : requested.origin === url.origin;
        if (permitted || ['data:', 'blob:'].includes(requested.protocol)) return route.continue();
        blocked.push(requested.origin); return route.abort();
      });
      try {
        const response = await page.goto(url.href);
        if (response) assert.ok(response.ok(), 'report HTTP response: ' + response.status());
        const info = await inspect(page);
        console.log(width + 'px', JSON.stringify(info));
        assert.deepEqual(info.problems, [], 'rendered report checks');
        await checkAnchors(page);
        for (const id of ids) {
          const card = page.locator('[id=' + JSON.stringify(anchor(id)) + ']');
          assert.equal(await card.count(), 1, 'finding id: ' + id);
          if (file) {
            const outDir = path.join(path.dirname(file), 'check');
            fs.mkdirSync(outDir, { recursive: true });
            await card.scrollIntoViewIfNeeded();
            await card.screenshot({ path: path.join(outDir, `${anchor(id)}-${width}.png`) });
          }
        }
        console.log(width + 'px controls:', await checkControls(page));
        assert.deepEqual(errors, [], 'script errors');
        assert.deepEqual(blocked, [], 'report attempted an external network request');
      } catch (error) {
        bad++;
        console.error(width + 'px FAILED:', error.message);
        if (errors.length) console.error('script errors:', JSON.stringify(errors));
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
  process.exitCode = bad ? 1 : 0;
})().catch((error) => { console.error(error.message); process.exitCode = 1; });
