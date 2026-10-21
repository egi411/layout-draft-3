// Выгружает офферы RKO Group для страницы: список со ставками, описания и короткие ссылки.
// Ключ берётся из секрета RKO_API_KEY. Заявки и баланс сюда не попадают: репозиторий публичный.
import {readFile, writeFile, mkdir} from 'node:fs/promises';

const KEY = process.env.RKO_API_KEY, BASE = 'https://rko-group.ru/api/app/v1', OUT = 'data/rko.json', DAY = 864e5;
if (!KEY) { console.error('RKO_API_KEY не задан'); process.exit(1); }
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function api(path, body) {
  for (let i = 0; ; i++) {
    const res = await fetch(BASE + path, {
      method: body ? 'POST' : 'GET',
      headers: {'X-API-Key': KEY, ...(body ? {'Content-Type': 'application/json'} : {})},
      body: body ? JSON.stringify(body) : undefined,
    });
    const j = await res.json().catch(() => null);
    if (res.status === 429 && i < 4) { await sleep(2000 * (i + 1)); continue; }
    if (!res.ok || j?.error) { const e = new Error(`${path}: ${res.status} ${j?.error?.message || ''}`); e.status = res.status; throw e; }
    return j.data;
  }
}
async function all(path, body) {
  const out = [];
  for (let page = 1; page <= 50; page++) {
    const d = await api(path, {...body, pagination: {page, per_page: 100}});
    out.push(...(d?.items || []));
    if (!d?.pagination || page >= d.pagination.pages) break;
  }
  return out;
}
async function pool(items, n, fn) {
  let i = 0;
  await Promise.all(Array.from({length: n}, async () => { while (i < items.length) await fn(items[i++]); }));
}

const prev = JSON.parse(await readFile(OUT, 'utf8').catch(() => '{}'));
const now = Date.now();
// без явной сортировки страницы списка пересекаются: одни офферы приходят дважды, другие теряются
const list = await all('/offer/list', {filter: {state: {open: true, paused: true, archived: false}}, order: {name: 'created_at', direction: 'desc'}});
const offers = [...new Map(list.map(o => [o.uuid, o])).values()]
  .filter(o => o.user_rate)
  .map(o => ({uuid: o.uuid, title: o.title, category: {title: o.category?.title, main_id: o.category?.main_id}, state: o.state,
    configuration: o.configuration, access_level: o.access_level, advertiser: {title: o.advertiser?.title}, user_rate: o.user_rate}));

// описания и ссылки меняются редко: перезапрашиваем раз в сутки
const details = {};
await pool(offers, 3, async o => {
  const old = prev.details?.[o.uuid];
  if (old && now - (old.at || 0) < DAY) { details[o.uuid] = old; return; }
  try {
    const d = await api('/offer/' + encodeURIComponent(o.uuid)), links = [];
    for (const l of d?.landings || []) {
      try {
        const g = await api(`/offer/get-links?o=${encodeURIComponent(o.uuid)}&l=${encodeURIComponent(l.uuid)}`);
        if (g?.short) links.push({title: l.title || '', url: g.short});
      } catch (e) { console.warn('ссылка', o.uuid, e.message); }
    }
    details[o.uuid] = {at: now, short_description: d?.short_description || '', description: d?.description || '',
      forbidden: (d?.words?.forbidden || []).map(w => w.word).filter(Boolean), links};
  } catch (e) { if (old) details[o.uuid] = old; console.warn('описание', o.uuid, e.message); }
});

let products = null;
const ag = {};
try { products = await api('/offer-ag/products'); } catch (e) { if (e.status !== 403) throw e; }
for (const p of products ? [...(products.banks || []), ...(products.others || [])] : []) {
  if (p.external_url) continue;
  try { ag[p.id] = await api('/offer-ag/offers', {product_id: p.id}); } catch (e) { console.warn('банки', p.id, e.message); }
}

const data = {offers, details, products, ag};
const same = JSON.stringify(data) === JSON.stringify({offers: prev.offers, details: prev.details, products: prev.products, ag: prev.ag});
if (same) { console.log('без изменений'); process.exit(0); }
await mkdir('data', {recursive: true});
await writeFile(OUT, JSON.stringify({at: new Date(now).toISOString(), ...data}));
console.log('офферов', offers.length, 'описаний', Object.keys(details).length);
