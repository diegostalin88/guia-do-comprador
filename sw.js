// Guia do Comprador: funciona offline com a última versão baixada.
// App e dados: tenta a rede primeiro (para pegar atualizações) e usa o cache se estiver sem internet.
const CACHE = "guia-v6";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png",
  "data/ipva.json", "data/taxas.json", "data/combustivel.json", "data/modelos.json"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET") return;
  const proprio = url.origin === self.location.origin, fontes = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (fontes) { e.respondWith(caches.match(req).then(r => r || fetch(req).then(res => { const cp = res.clone(); caches.open(CACHE).then(c => c.put(req, cp)); return res; }))); return; }
  if (!proprio) return; // FIPE e CEP vão direto para a internet
  e.respondWith(fetch(req).then(res => { if (res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(req, cp)); } return res; })
    .catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match("index.html"))));
});
