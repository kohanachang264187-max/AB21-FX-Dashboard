// AB21 private research PWA. Never cache HTML, CSV, JSON, or authenticated responses.
const CACHE='ab21-static-v2';
const STATIC=['./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',event=>{
 event.waitUntil(self.skipWaiting());
});
self.addEventListener('activate',event=>{
 event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('ab21-')).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
 const request=event.request;
 if(request.method!=='GET'||request.mode==='navigate'||request.credentials==='include')return;
 const url=new URL(request.url);
 if(url.origin!==self.location.origin)return;
 if(!STATIC.some(p=>url.pathname===new URL(p,self.registration.scope).pathname))return;
 event.respondWith(fetch(request,{cache:'no-store'}).catch(()=>caches.match(request)));
});
