#!/usr/bin/env python3
"""Builds the keep-or-drop review page: one local HTML file, pictures embedded.

    python3 build_review.py <findings.json> <evidence dir> <out.html>

findings.json   the findings in plain words, their sections and the candidate pieces of work
                (format: ../findings.md)
evidence dir    <id>-<width>-<n>.png pictures, manifest-*.json and status-*.json
                (format: ../evidence.md)

On each picture the part to look at is ringed and the rest dimmed; the rings are drawn by the
page from the manifest's boxes, never burnt into the picture. Each finding gets Keep / Drop /
Discuss and a note box; rulings are kept in the browser and exported as text.

The page may hold real user data from the screenshots. It is a local file: do not publish it.
Exits 1 if a manifest names a picture that is missing, or a finding or picture id is unknown.
"""
import base64
import glob
import html
import io
import json
import math
import os
import re
import sys
from urllib.parse import urlsplit

from PIL import Image

RING = '#ff2d8a'
RING_WIDTH = 3
DIM = 0.5

STATUS_WORDS = {
    'shown': ('Shown in a picture', 'ok'),
    'partly shown': ('Partly shown', 'part'),
    'not shown': ('No picture', 'none'),
    'contradicted': ('Picture contradicts the claim', 'bad'),
}


def esc(s):
    return html.escape(str(s), quote=True)


def rich(s):
    """Escape, then show `code` spans as code."""
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', esc(s))


def anchor(fid):
    return re.sub(r'[^a-z0-9]+', '-', fid.lower()).strip('-')


def checked_boxes(value, width, height, filename):
    """Keep valid crop-relative coordinates exactly; a bad box must be remeasured."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError('%s: boxes must be a list' % filename)
    for n, box in enumerate(value, 1):
        if (not isinstance(box, (list, tuple)) or len(box) != 4
                or any(isinstance(v, bool) or not isinstance(v, (int, float))
                       or not math.isfinite(v) for v in box)):
            raise ValueError('%s: box %d must contain four finite numbers' % (filename, n))
        x, y, w, h = box
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
            raise ValueError('%s: box %d %s is outside the %dx%d image or has no area'
                             % (filename, n, box, width, height))
    return value


def table(headers, rows):
    """The viewport clips the table, not its columns; scroll all columns into view."""
    return ('<div class="tw" tabindex="0" role="region" aria-label="Scrollable table"><table><thead><tr>%s</tr>'
            '</thead><tbody>%s</tbody></table></div>'
            % (''.join('<th scope="col">%s</th>' % esc(h) for h in headers),
               ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % c for c in row) for row in rows)))


def finding_links(ids):
    return ''.join('<a class="c" data-for="%s" href="#%s">%s</a>'
                   % (esc(i), anchor(i), esc(i)) for i in ids)


def render_context(spec):
    """Optional account of the review, rendered natively rather than injected HTML."""
    body, nav = [], []
    coverage = spec.get('coverage')
    if coverage:
        nav.append(('coverage', 'Coverage'))
        body.append('<h2 id="coverage">Review coverage</h2>')
        if coverage.get('summary'):
            body.append('<p>%s</p>' % rich(coverage['summary']))
        for label, key in (('Roles', 'roles'), ('Viewports', 'viewports')):
            if coverage.get(key):
                body.append('<p><b>%s:</b> %s</p>' % (label, ', '.join(esc(x) for x in coverage[key])))
        if coverage.get('journeys'):
            body.append(table(['Role', 'Viewport', 'Journey', 'Outcome', 'Evidence'], [
                [rich(j.get(k, '')) for k in ('role', 'viewport', 'journey', 'outcome', 'evidence')]
                for j in coverage['journeys']]))
        if coverage.get('gaps'):
            body.append('<h3>Meaningful gaps</h3><ul>%s</ul>'
                        % ''.join('<li>%s</li>' % rich(g) for g in coverage['gaps']))
    if spec.get('actions'):
        nav.append(('actions', 'Changes'))
        body.append('<h2 id="actions">Actions and changes left in the environment</h2>')
        body.append(table(['Role', 'Action', 'Safe record reference', 'Observed outcome', 'What remains'], [
            [rich(a.get(k, '')) for k in ('role', 'action', 'record', 'outcome', 'left_in_environment')]
            for a in spec['actions']]))
    if spec.get('reconciliation'):
        nav.append(('reconciliation', 'Tickets'))
        body.append('<h2 id="reconciliation">Ticket reconciliation</h2>')
        rows = []
        for r in spec['reconciliation']:
            ticket = esc(r.get('ticket', ''))
            if r.get('url'):
                ticket = '<a href="%s">%s</a>' % (esc(r['url']), ticket or 'Ticket')
            rows.append([ticket, finding_links(r.get('finding_ids', [])), rich(r['match']),
                         rich(r['summary']), rich(r.get('checked', ''))])
        body.append(table(['Ticket', 'Findings', 'Match', 'Decision or difference', 'Actually checked'], rows))
    return body, nav


def validate_optional(spec, known):
    for f in spec['findings']:
        if 'classification' in f and f['classification'] not in ('defect', 'improvement', 'policy'):
            raise ValueError('%s: classification must be defect, improvement or policy' % f['id'])
        for field in ('confidence', 'impact', 'recovery'):
            if field in f and not isinstance(f[field], str):
                raise ValueError('%s: %s must be a string' % (f['id'], field))
    coverage = spec.get('coverage')
    if coverage is not None:
        if not isinstance(coverage, dict):
            raise ValueError('coverage must be an object')
        for key in ('roles', 'viewports', 'gaps'):
            if key in coverage and (not isinstance(coverage[key], list)
                                    or any(not isinstance(x, str) for x in coverage[key])):
                raise ValueError('coverage.%s must be a list of strings' % key)
        if 'summary' in coverage and not isinstance(coverage['summary'], str):
            raise ValueError('coverage.summary must be a string')
        journeys = coverage.get('journeys', [])
        if not isinstance(journeys, list):
            raise ValueError('coverage.journeys must be a list')
        for j in journeys:
            if not isinstance(j, dict) or not all(isinstance(j.get(k), str) for k in ('journey', 'outcome')):
                raise ValueError('each coverage journey needs journey and outcome strings')
            for key in ('role', 'viewport', 'evidence'):
                if key in j and not isinstance(j[key], str):
                    raise ValueError('coverage journey.%s must be a string' % key)
    for name, required, optional in (
            ('actions', ('action', 'outcome'), ('role', 'record', 'left_in_environment')),
            ('reconciliation', ('match', 'summary'), ('ticket', 'url', 'checked'))):
        entries = spec.get(name, [])
        if not isinstance(entries, list):
            raise ValueError('%s must be a list' % name)
        for entry in entries:
            if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) for k in required):
                raise ValueError('each %s entry needs %s strings' % (name, ', '.join(required)))
            for key in optional:
                if key in entry and not isinstance(entry[key], str):
                    raise ValueError('%s.%s must be a string' % (name, key))
    for r in spec.get('reconciliation', []):
        if r['match'] not in ('exact', 'partial', 'new', 'apparently-resolved', 'not-verified'):
            raise ValueError('reconciliation.match is not a supported match type')
        ids = r.get('finding_ids', [])
        if not isinstance(ids, list) or any(not isinstance(i, str) or i not in known for i in ids):
            raise ValueError('reconciliation names an unknown finding')
        if r.get('url'):
            url = urlsplit(r['url'])
            if url.scheme not in ('http', 'https') or not url.netloc or url.username or url.password:
                raise ValueError('reconciliation.url must be an http(s) URL without credentials')


def read_evidence(folder, known):
    """Pictures and statuses by finding id. A status id 'N11/3' belongs to finding N11 unless N11/3 is itself a finding."""
    pics, status, problems = {}, {}, []
    for path in sorted(glob.glob(os.path.join(folder, 'manifest-*.json'))):
        for p in json.load(open(path, encoding='utf-8')):
            fid = p.get('finding') or p['id']
            if fid not in known:
                problems.append('%s: picture %s names unknown finding %s' % (os.path.basename(path), p.get('file'), fid))
            pics.setdefault(fid, []).append(p)
    for path in sorted(glob.glob(os.path.join(folder, 'status-*.json'))):
        for s in json.load(open(path, encoding='utf-8')):
            fid = s['id'] if s['id'] in known else s['id'].split('/')[0]
            if fid not in known:
                problems.append('%s: status names unknown finding %s' % (os.path.basename(path), s['id']))
            status.setdefault(fid, []).append(s)
    return pics, status, problems


class Shots:
    def __init__(self, folder):
        self.folder = folder
        self.n = 0
        self.count = 0
        self.made = 0
        self.missing = []

    def render(self, pic, contradicted=False):
        path = os.path.join(self.folder, pic['file'])
        if not os.path.exists(path):
            self.missing.append(pic['file'])
            return ''
        with Image.open(path) as original:
            im = original.convert('RGB')
        W, H = im.size
        boxes = checked_boxes(pic.get('boxes'), W, H, pic['file'])
        capture = pic.get('capture')
        if capture is not None:
            if not isinstance(capture, dict):
                raise ValueError('%s: capture must be an object' % pic['file'])
            if 'output' in capture:
                output = capture['output']
                if (not isinstance(output, dict) or output.get('width') != W or output.get('height') != H
                        or isinstance(output.get('width'), bool) or isinstance(output.get('height'), bool)):
                    raise ValueError('%s: capture.output does not match the %dx%d image' % (pic['file'], W, H))
        buf = io.BytesIO()
        im.save(buf, 'WEBP', quality=82, method=6)
        src = 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')
        overlay = ''
        if boxes:
            self.n += 1
            holes = ''.join('<rect x="%g" y="%g" width="%g" height="%g" rx="8" fill="black"/>' % tuple(b) for b in boxes)
            rings = ''.join('<rect class="ring" x="%g" y="%g" width="%g" height="%g" rx="8"/>' % tuple(b) for b in boxes)
            overlay = ('<svg class="hl" viewBox="0 0 %d %d" preserveAspectRatio="none" aria-hidden="true">'
                       '<defs><mask id="__picture-mask-%d"><rect width="%d" height="%d" fill="white"/>%s</mask></defs>'
                       '<rect class="dim" width="%d" height="%d" mask="url(#__picture-mask-%d)"/>%s</svg>'
                       % (W, H, self.n, W, H, holes, W, H, self.n, rings))
        self.count += 1
        made = pic.get('kind') == 'made'
        self.made += made
        width = int(pic.get('width') or W)
        tag = '%dpx wide screen' % width
        if W > width + 20:
            tag += ', whole width of the page shown'
        kind = ('<span class="k k-made">Real screen, invented data</span>' if made
                else '<span class="k k-seen">Observed in the app</span>')
        show = min(W, 300 if W <= 480 else 560 if W <= 900 else 720)
        notes = ''
        if made and pic.get('made_note'):
            notes += '<div class="made">Invented or switched on: %s</div>' % esc(pic['made_note'])
        fault = pic.get('shows_fault', 'yes')
        if fault == 'no' and not contradicted:
            notes += '<div class="pnote"><b>For comparison:</b> this picture does not show the fault. %s</div>' % esc(pic.get('note', ''))
        elif fault != 'yes':
            notes += '<div class="doubt">%s%s</div>' % (
                'The picture does not show the fault. ' if fault == 'no' else 'The picture shows the fault only in part. ',
                esc(pic.get('note', '')))
        elif pic.get('note'):
            notes += '<div class="pnote">%s</div>' % esc(pic['note'])
        return ('<figure class="fig" style="--w:%dpx"><div class="tag">%s %s</div>'
                '<div class="shot" data-w="%d" tabindex="0" role="button" aria-label="Enlarge: %s">'
                '<div class="shot-media"><img src="%s" width="%d" height="%d" alt="%s" loading="lazy">%s</div></div>'
                '<figcaption>%s%s</figcaption></figure>'
                % (show, esc(tag), kind, W, esc(pic.get('caption', 'picture')), src, W, H, esc(pic.get('caption', '')), overlay,
                   esc(pic.get('caption', '')), notes))


def overall_status(fid, pics, status):
    """One status for the finding: the reviewers' own word where given, else worked out from its pictures."""
    entries = status.get(fid, [])
    words = [e.get('status', '').lower() for e in entries]
    if len(entries) == 1 and words[0] in STATUS_WORDS:
        return words[0], entries[0].get('note', '')
    if entries:
        shown = sum(1 for w in words if w == 'shown')
        if 'contradicted' in words:
            word = 'contradicted'
        elif shown == len(words):
            word = 'shown'
        elif shown or 'partly shown' in words:
            word = 'partly shown'
        else:
            word = 'not shown'
        return word, '%d of %d parts shown.' % (shown, len(words))
    return ('shown' if pics.get(fid) else 'not shown'), ''


def badges(items):
    return ''.join('<span class="badge b-%s">%s</span>' % (cls, esc(text)) for text, cls in items if text)


def render_finding(f, shots, pics, status, piece_of):
    fid = f['id']
    word, note = overall_status(fid, pics, status)
    label, cls = STATUS_WORDS[word]
    figs = ''.join(shots.render(p, contradicted=(word == 'contradicted')) for p in pics.get(fid, []))
    meta = [(b, 'plain') for b in f.get('badges', [])] + [(b, 'flag') for b in f.get('flags', [])]
    if f.get('classification'):
        labels = {'defect': 'Reproduced defect', 'improvement': 'Usability improvement', 'policy': 'Policy question'}
        meta.insert(0, (labels[f['classification']], 'plain'))
    ev = [(label, 'ev-' + cls)]
    if any(p.get('kind') == 'made' for p in pics.get(fid, [])):
        ev.append(('Invented data', 'made'))
    body = ''
    assessment = [(label, f.get(key)) for label, key in
                  (('Confidence', 'confidence'), ('Task impact', 'impact'), ('Recovery', 'recovery')) if f.get(key)]
    if assessment:
        body += '<dl class="assessment">%s</dl>' % ''.join(
            '<div><dt>%s</dt><dd>%s</dd></div>' % (label, rich(value)) for label, value in assessment)
    if f.get('already'):
        body += '<p class="today">%s</p>' % rich(f['already'])
    for head, key in (('What is wrong', 'wrong'), ('Who meets it', 'who'), ('Proposed fix', 'fix')):
        if f.get(key):
            body += '<h4>%s</h4><p>%s</p>' % (head, rich(f[key]))
    if f.get('detail'):
        body += '<details class="more"><summary>The reviewer\'s full wording</summary><div>%s</div></details>' % rich(f['detail'])
    entries = status.get(fid, [])
    if len(entries) > 1:
        body += '<ul class="parts">%s</ul>' % ''.join(
            '<li><b>%s</b>: %s</li>' % (esc(STATUS_WORDS.get(e.get('status', '').lower(), (e.get('status', ''), ''))[0]),
                                        esc(e.get('note', ''))) for e in entries)
    elif note:
        body += '<p class="evnote"><b>Picture check:</b> %s</p>' % esc(note)
    pieces = piece_of.get(fid, [])
    if pieces:
        body += '<p class="piece">Would be fixed in: %s</p>' % ', '.join(
            '<a href="#%s">%s</a>' % (anchor(p), esc(p)) for p in pieces)
    radios = ''.join(
        '<label class="opt o-%s"><input type="radio" name="a-%s" value="%s"><span>%s</span></label>'
        % (v, esc(fid), v, t) for v, t in (('keep', 'Keep'), ('drop', 'Drop'), ('discuss', 'Discuss')))
    answer = ('<fieldset class="answer" data-d="%s"><legend class="sr">%s: your ruling</legend>%s'
              '<button class="clear-ruling" type="button">Clear ruling</button>'
              '<textarea class="note" rows="1" placeholder="Note (optional)" aria-label="Note on %s"></textarea>'
              '</fieldset>' % (esc(fid), esc(fid + ' ' + f['title']), radios, esc(fid)))
    return ('<article class="item st-%s" id="%s" data-id="%s">'
            '<header><h3><span class="fid">%s</span> %s</h3><div class="badges">%s%s</div></header>'
            '<div class="cols"><div class="text">%s</div><div class="figs">%s</div></div>%s</article>'
            % (cls, anchor(fid), esc(fid), esc(fid), esc(f['title']), badges(meta), badges(ev), body,
               figs or '<p class="nopic">No picture of this fault exists yet.</p>', answer))


CSS = """
:root{color-scheme:light;--bg:#f5f6f4;--card:#fff;--ink:#1b211f;--mute:#56615c;--line:#dde2df;--soft:#eef1ef;
--accent:#0f6b5c;--accent-soft:#e3f1ec;--ok:#1d6b3a;--ok-bg:#e2f3e8;--part:#1f4f99;--part-bg:#e5ecfa;
--warn:#8a4b00;--warn-bg:#fbefdc;--bad:#9c1c2c;--bad-bg:#fbe4e7}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#141917;--card:#1c2320;--ink:#e6ebe8;
--mute:#a3aea9;--line:#33403b;--soft:#232c28;--accent:#5cc4ad;--accent-soft:#1d3530;--ok:#7fd39b;--ok-bg:#1d3526;
--part:#9cbcf2;--part-bg:#1f2b42;--warn:#f0b46a;--warn-bg:#3a2a14;--bad:#f19aa6;--bad-bg:#40191f}}
*{box-sizing:border-box}
html{scroll-padding-top:calc(var(--bar-height,120px) + 12px)}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--accent)}
code{font-size:.9em;background:var(--soft);padding:0 4px;border-radius:4px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.bar{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:8px 16px;
display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between}
.bar .t{font-weight:700;font-size:15px}
.bar>*{min-width:0}.bar .t{overflow-wrap:anywhere}
.bar .b{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.bar nav{flex-basis:100%;display:flex;flex-wrap:wrap;gap:4px 16px;font-size:14px}
.bar nav a{padding:2px 0}
.bar button{font:inherit;font-size:14px;padding:6px 12px;border:1px solid var(--line);border-radius:8px;
background:var(--card);color:var(--ink);cursor:pointer}
.bar button[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent)}
#count{font-size:14px;color:var(--mute)}
main{max-width:1280px;margin:0 auto;padding:16px}
h1{font-size:28px;line-height:1.25;margin:8px 0 6px}
h2{font-size:22px;margin:44px 0 6px;padding-top:8px;border-top:2px solid var(--line)}
h3{font-size:18px;margin:0;line-height:1.3}
p{max-width:78ch;margin:8px 0}
.lede{font-size:17px}
.mute{color:var(--mute)}
.stats{display:flex;flex-wrap:wrap;gap:10px;list-style:none;padding:0;margin:16px 0}
.stats li{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:120px}
.stats b{display:block;font-size:26px;line-height:1.1}.stats span{font-size:13px;color:var(--mute)}
.how{background:var(--accent-soft);border-radius:10px;padding:10px 14px;max-width:none}
.item{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--line);border-radius:12px;padding:16px;margin:16px 0}
.item.a-keep{border-left-color:var(--ok)}.item.a-drop{border-left-color:var(--mute);opacity:.72}
.item.a-discuss{border-left-color:var(--part)}
.item header{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:baseline;justify-content:space-between;margin-bottom:8px}
.fid{display:inline-block;font-weight:700;color:var(--accent);margin-right:4px}
.badges{display:flex;flex-wrap:wrap;gap:6px;min-width:0}
.badge{display:inline-block;font-size:12px;font-weight:600;border-radius:12px;padding:1px 9px;max-width:100%;
background:var(--soft);color:var(--mute)}
.b-flag{background:var(--warn-bg);color:var(--warn)}.b-ev-ok{background:var(--ok-bg);color:var(--ok)}
.b-ev-part{background:var(--part-bg);color:var(--part)}.b-ev-none,.b-ev-bad{background:var(--bad-bg);color:var(--bad)}
.b-made{background:var(--part-bg);color:var(--part)}
.cols{display:grid;grid-template-columns:minmax(260px,380px) minmax(0,1fr);gap:20px;align-items:start}
.text h4{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--mute);margin:12px 0 2px}
.text h4:first-child{margin-top:0}
.text p{margin:0 0 6px}
.assessment{margin:0 0 12px;font-size:14px}.assessment div{margin-bottom:4px}
.assessment dt{font-weight:600;color:var(--mute)}.assessment dd{margin:0}
.today{background:var(--part-bg);color:var(--ink);border-radius:8px;padding:8px 10px;font-size:15px}
.piece,.evnote{font-size:14px;color:var(--mute)}
.parts{font-size:14px;color:var(--mute);padding-left:18px;margin:6px 0}
details.more{margin-top:8px;font-size:14px}
details.more summary{cursor:pointer;color:var(--accent)}
details.more div{color:var(--mute);margin-top:4px}
.figs{display:flex;flex-wrap:wrap;gap:14px;align-items:flex-start}
.fig{margin:0;width:var(--w);max-width:100%}
.tag{font-size:12px;font-weight:700;margin-bottom:4px;color:var(--mute)}
.k{font-weight:600;border-radius:99px;padding:0 7px;margin-left:4px;white-space:nowrap}
.k-made{background:var(--part-bg);color:var(--part)}.k-seen{background:var(--ok-bg);color:var(--ok)}
.shot{position:relative;border:1px solid var(--line);border-radius:6px;overflow:hidden;cursor:zoom-in;background:#fff;
max-height:900px}
.shot.tall::after{content:"Click to see the whole picture";position:absolute;left:0;right:0;bottom:0;padding:18px 8px 6px;
font-size:12px;text-align:center;color:#fff;background:linear-gradient(transparent,rgba(0,0,0,.7))}
.shot img{display:block;width:100%;height:auto}
.shot-media{position:relative}
.hl{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.dim{fill:#000;fill-opacity:DIMV}
.ring{fill:none;stroke:RINGV;stroke-width:RINGW;vector-effect:non-scaling-stroke}
body.nohl .hl{display:none}
figcaption{font-size:14px;margin-top:6px}
.made,.pnote,.doubt{font-size:13px;color:var(--mute);margin-top:4px}
.doubt{color:var(--bad);font-weight:600}
.nopic{background:var(--bad-bg);color:var(--bad);border-radius:8px;padding:10px 12px;font-weight:600}
.answer{border:0;border-top:1px solid var(--line);margin:14px 0 0;padding:12px 0 0;display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start}
.opt{position:relative}
.opt input{position:absolute;opacity:0;inset:0;cursor:pointer}
.opt span{display:inline-block;min-width:84px;text-align:center;padding:8px 14px;border:1px solid var(--line);border-radius:8px;
font-weight:600;background:var(--card)}
.opt input:focus-visible+span{outline:2px solid var(--accent);outline-offset:2px}
.o-keep input:checked+span{background:var(--ok-bg);border-color:var(--ok);color:var(--ok)}
.o-drop input:checked+span{background:var(--soft);border-color:var(--mute)}
.o-discuss input:checked+span{background:var(--part-bg);border-color:var(--part);color:var(--part)}
.clear-ruling{font:inherit;font-size:14px;min-height:42px;padding:8px;border:1px solid var(--line);
border-radius:8px;background:var(--card);color:var(--mute);cursor:pointer}
.note{flex:1 1 260px;min-height:40px;font:inherit;font-size:15px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;
background:var(--card);color:var(--ink);resize:vertical}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(340px,100%),1fr));gap:14px}
.grid .item{margin:0}.grid .cols{grid-template-columns:minmax(0,1fr)}
table{border-collapse:collapse;width:100%;font-size:14px;background:var(--card)}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600}
.tw{max-width:100%;overflow-x:auto;margin:10px 0;border-radius:8px}
.tw table{min-width:720px}.tw th,.tw td{min-width:100px;overflow-wrap:anywhere}
.tw:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
td .c{display:inline-block;margin:1px 4px 1px 0;padding:0 7px;border-radius:99px;background:var(--soft);font-size:13px;text-decoration:none;color:var(--ink);white-space:nowrap}
td .c.keep{background:var(--ok-bg);color:var(--ok)}td .c.drop{text-decoration:line-through;color:var(--mute)}
td .c.discuss{background:var(--part-bg);color:var(--part)}
#out{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin-top:12px}
#out pre{white-space:pre-wrap;font-size:14px;margin:8px 0;max-height:320px;overflow:auto}
#out button{font:inherit;font-size:14px;padding:8px 14px;border:1px solid var(--line);border-radius:8px;background:var(--card);
color:var(--ink);cursor:pointer;margin-right:8px}
body.unans .item.answered{display:none}
#zoom{position:fixed;inset:0;z-index:20;background:rgba(0,0,0,.85);display:none;overflow:auto;padding:24px;cursor:zoom-out}
#zoom.on{display:block}#zoom .shot{margin:0 auto;cursor:zoom-out;max-height:none}#zoom .shot.tall::after{display:none}
#zoom button{position:sticky;top:0;z-index:1;display:block;margin:0 0 12px auto;padding:8px 16px;
font:inherit;background:#fff;color:#111;border:0;border-radius:8px;cursor:pointer}
footer{margin:48px 0 24px;font-size:13px;color:var(--mute)}
@media (max-width:800px){.cols{grid-template-columns:minmax(0,1fr)}h1{font-size:23px}h2{font-size:20px}.item{padding:12px}}
""".replace('DIMV', str(DIM)).replace('RINGV', RING).replace('RINGW', str(RING_WIDTH))

JS = r"""
(function () {
  var BASE = document.body.getAttribute('data-key'), KEY = BASE + '-answers', NKEY = BASE + '-notes';
  function load(k) { try { var v = JSON.parse(localStorage.getItem(k) || '{}'); return v && typeof v === 'object' ? v : {}; } catch (e) { return {}; } }
  function store(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  var answers = load(KEY), notes = load(NKEY);
  var items = Array.prototype.slice.call(document.querySelectorAll('.item[data-id]'));
  var order = items.map(function (i) { return i.getAttribute('data-id'); });
  var count = document.getElementById('count'), pre = document.getElementById('anstext');

  function text() {
    var lines = [];
    order.forEach(function (id) {
      var a = answers[id], n = (notes[id] || '').trim();
      if (a || n) lines.push(id + ' ' + (a || 'no ruling') + (n ? ': ' + n.replace(/\s*\n\s*/g, ' / ') : ''));
    });
    return lines.join('\n');
  }
  function refresh() {
    var n = 0, tally = { keep: 0, drop: 0, discuss: 0 };
    items.forEach(function (it) {
      var id = it.getAttribute('data-id'), a = answers[id];
      it.classList.remove('a-keep', 'a-drop', 'a-discuss');
      it.classList.toggle('answered', !!a);
      if (a) { it.classList.add('a-' + a); n++; tally[a]++; }
    });
    count.textContent = n + ' of ' + order.length + ' ruled: ' + tally.keep + ' keep, ' + tally.drop + ' drop, ' + tally.discuss + ' discuss';
    document.querySelectorAll('td .c').forEach(function (c) {
      c.classList.remove('keep', 'drop', 'discuss');
      var a = answers[c.getAttribute('data-for')]; if (a) c.classList.add(a);
    });
    pre.textContent = text() || 'No rulings yet.';
  }
  document.querySelectorAll('fieldset.answer').forEach(function (fs) {
    var id = fs.getAttribute('data-d');
    fs.querySelectorAll('input').forEach(function (inp) {
      inp.checked = answers[id] === inp.value;
      inp.addEventListener('change', function () { if (inp.checked) { answers[id] = inp.value; store(KEY, answers); refresh(); } });
      // A second click on the chosen answer clears it.
      inp.addEventListener('click', function () {
        if (inp.dataset.was === '1') { inp.checked = false; delete answers[id]; store(KEY, answers); refresh(); }
        fs.querySelectorAll('input').forEach(function (o) { o.dataset.was = o.checked ? '1' : ''; });
      });
      inp.dataset.was = inp.checked ? '1' : '';
    });
    fs.querySelector('.clear-ruling').addEventListener('click', function () {
      delete answers[id];
      fs.querySelectorAll('input').forEach(function (inp) { inp.checked = false; inp.dataset.was = ''; });
      store(KEY, answers); refresh();
    });
    var ta = fs.querySelector('textarea');
    ta.value = notes[id] || '';
    ta.addEventListener('input', function () { if (ta.value) notes[id] = ta.value; else delete notes[id]; store(NKEY, notes); refresh(); });
  });
  function flash(b, t) { var o = b.textContent; b.textContent = t; setTimeout(function () { b.textContent = o; }, 1600); }
  document.getElementById('copy').addEventListener('click', function () {
    var b = this, t = text(); if (!t) { flash(b, 'Nothing yet'); return; }
    function fallback() {
      var ta = document.createElement('textarea'); ta.value = t; document.body.appendChild(ta); ta.select();
      var ok = false; try { ok = document.execCommand('copy'); } catch (e) {} ta.remove();
      flash(b, ok ? 'Copied' : 'Copy failed: use Save');
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).then(function () { flash(b, 'Copied'); }, fallback);
    else fallback();
  });
  document.getElementById('save').addEventListener('click', function () {
    var t = text(); if (!t) { flash(this, 'Nothing yet'); return; }
    var url = URL.createObjectURL(new Blob([t + '\n'], { type: 'text/plain;charset=utf-8' }));
    var a = document.createElement('a'); a.href = url; a.download = BASE + '-rulings.txt';
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  });
  var hl = document.getElementById('hl');
  hl.addEventListener('click', function () {
    var off = document.body.classList.toggle('nohl'); hl.textContent = 'Highlights: ' + (off ? 'off' : 'on');
    hl.setAttribute('aria-pressed', off ? 'false' : 'true');
  });
  var un = document.getElementById('unans');
  un.addEventListener('click', function () {
    var on = document.body.classList.toggle('unans'); un.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  var zoom = document.getElementById('zoom');
  var zoomSource = null;
  function closeZoom() {
    zoom.classList.remove('on'); zoom.innerHTML = '';
    if (zoomSource) zoomSource.focus();
    zoomSource = null;
  }
  document.querySelectorAll('.shot').forEach(function (s) {
    var img = s.querySelector('img');
    function mark() { if (img.clientHeight > 900) s.classList.add('tall'); }
    if (img.complete) mark(); else img.addEventListener('load', mark);
    function openZoom() {
      var c = s.cloneNode(true);
      c.style.width = Math.min(Math.max(s.dataset.w * 1.5, s.clientWidth * 1.6), window.innerWidth - 48) + 'px';
      c.removeAttribute('tabindex'); c.removeAttribute('role'); c.removeAttribute('aria-label');
      c.querySelectorAll('mask[id]').forEach(function (mask) {
        var old = mask.id; mask.id += '-zoom';
        c.querySelectorAll('[mask]').forEach(function (part) {
          if (part.getAttribute('mask') === 'url(#' + old + ')') part.setAttribute('mask', 'url(#' + mask.id + ')');
        });
      });
      var close = document.createElement('button'); close.type = 'button'; close.textContent = 'Close picture';
      zoom.innerHTML = ''; zoom.appendChild(close); zoom.appendChild(c); zoom.classList.add('on');
      zoomSource = s; close.focus();
    }
    s.addEventListener('click', openZoom);
    s.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openZoom(); }
    });
  });
  zoom.addEventListener('click', closeZoom);
  document.addEventListener('keydown', function (e) {
    if (!zoom.classList.contains('on')) return;
    if (e.key === 'Escape') closeZoom();
    else if (e.key === 'Tab') {
      // Close is the only keyboard control in the enlarged picture.
      e.preventDefault(); zoom.querySelector('button').focus();
    }
  });
  var bar = document.querySelector('.bar');
  function fitBar() { document.documentElement.style.setProperty('--bar-height', bar.getBoundingClientRect().height + 'px'); }
  if (window.ResizeObserver) new ResizeObserver(fitBar).observe(bar);
  window.addEventListener('resize', fitBar); fitBar();
  refresh();
})();
"""


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    spec_path, evidence, out_path = sys.argv[1:]
    spec = json.load(open(spec_path, encoding='utf-8'))
    findings = spec['findings']
    known = {f['id'] for f in findings}
    if len(known) != len(findings):
        sys.exit('findings.json: duplicate finding ids')
    validate_optional(spec, known)
    ids = {'answers', 'zoom', 'out', 'save', 'copy', 'count', 'unans', 'hl', 'anstext'}
    ids.update(key for key in ('coverage', 'actions', 'reconciliation', 'pieces') if spec.get(key))
    for entry in findings + spec['sections'] + spec.get('pieces', []):
        if not isinstance(entry['id'], str) or not entry['id'].strip():
            raise ValueError('finding, section and piece ids must be nonempty strings')
        name = anchor(entry['id'])
        if not name or name in ids:
            raise ValueError('%s: duplicate or empty report anchor %s' % (entry['id'], name))
        ids.add(name)
    pics, status, problems = read_evidence(evidence, known)
    piece_of = {}
    for p in spec.get('pieces', []):
        for fid in p['findings']:
            if fid not in known:
                problems.append('piece %s names unknown finding %s' % (p['id'], fid))
            piece_of.setdefault(fid, []).append(p['id'])
    shots = Shots(evidence)
    body, nav = render_context(spec)
    for sec in spec['sections']:
        mine = [f for f in findings if f.get('section') == sec['id']]
        if not mine:
            continue
        nav.append((anchor(sec['id']), sec['title']))
        body.append('<h2 id="%s">%s (%d)</h2>' % (anchor(sec['id']), esc(sec['title']), len(mine)))
        if sec.get('intro'):
            body.append('<p class="mute">%s</p>' % rich(sec['intro']))
        cards = ''.join(render_finding(f, shots, pics, status, piece_of) for f in mine)
        body.append('<div class="grid">%s</div>' % cards if sec.get('layout') == 'grid' else cards)
    orphans = [f['id'] for f in findings if f.get('section') not in {s['id'] for s in spec['sections']}]
    if orphans:
        problems.append('findings in no section: %s' % ', '.join(orphans))
    if spec.get('pieces'):
        rows = ''.join(
            '<tr id="%s"><td><b>%s</b></td><td><b>%s</b><br>%s</td><td>%s</td><td>%s</td></tr>'
            % (anchor(p['id']), esc(p['id']), esc(p['name']), rich(p.get('covers', '')), esc(p.get('size', '')),
               finding_links(p['findings']))
            for p in spec['pieces'])
        body.append('<h2 id="pieces">How the kept findings would be built</h2>'
                    '<p class="mute">Candidate pieces of work: a menu, not a plan. Each finding\'s chip changes as '
                    'you rule on it.</p><div class="tw" tabindex="0" role="region" aria-label="Candidate work table"><table><thead><tr><th>#</th><th>Piece</th><th>Size</th>'
                    '<th>Findings</th></tr></thead><tbody>%s</tbody></table></div>' % rows)
        nav.append(('pieces', 'Candidate work'))
    nav.append(('answers', 'Your rulings'))
    joined = ''.join(body)
    nopic = joined.count('class="nopic"')
    page = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>%s</title><style>%s</style></head><body data-key="%s">'
            % (esc(spec['title']), CSS, esc(spec.get('storage_key') or anchor(spec['title']))),
            '<div class="bar"><div class="t">%s</div><div class="b"><span id="count"></span>' % esc(spec['title']),
            '<button id="unans" aria-pressed="false">Unruled only</button>',
            '<button id="hl" aria-pressed="true">Highlights: on</button></div>',
            '<nav aria-label="Review sections">%s</nav></div>' % ''.join(
                '<a href="#%s">%s</a>' % (esc(target), esc(label)) for target, label in nav),
            '<main><h1>%s</h1>' % esc(spec['title']),
            '<p class="lede">%s</p>' % rich(spec.get('lede', 'Rule on each finding: keep, drop or discuss. Your rulings '
                                            'are remembered in this browser; copy or save them at the bottom.')),
            '<ul class="stats"><li><b>%d</b><span>findings</span></li><li><b>%d</b><span>pictures, %d with invented data</span></li>'
            '<li><b>%d</b><span>with no picture</span></li></ul>' % (len(findings), shots.count, shots.made, nopic),
            '<p class="how"><b>Reading a picture.</b> The part to look at is ringed and the rest dimmed; click a '
            'picture to enlarge it. <span class="k k-seen">Observed in the app</span> is a photograph of the app '
            'as reached through its interface, including test records. <span class="k k-made">Real screen, invented data</span> labels legacy synthetic evidence from the real '
            'code, put into a state the review login cannot reach, with invented answers; what was invented is '
            'written under the picture. Such legacy evidence does not establish a reachable deployed journey.</p>',
            joined,
            '<h2 id="answers">Your rulings</h2><div id="out"><button id="copy">Copy</button>'
            '<button id="save">Save as a text file</button><pre id="anstext"></pre></div>',
            '<footer>%s</footer></main>' % rich(spec.get('footnote', 'May hold real user data: keep it on this machine.')),
            '<div id="zoom" role="dialog" aria-modal="true" aria-label="Enlarged picture"></div><script>%s</script></body></html>' % JS]
    if shots.missing:
        problems.append('picture files named in a manifest but missing: %s' % ', '.join(shots.missing))
    if problems:
        raise ValueError('\n'.join(problems))
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(''.join(page))
    os.chmod(out_path, 0o600)
    print('wrote %s (%.1f MB): %d findings, %d pictures (%d invented data), %d with no picture'
          % (out_path, os.path.getsize(out_path) / 1e6, len(findings), shots.count, shots.made, nopic))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as e:
        sys.exit('PROBLEM: %s' % e)
