'use strict';
// Instalação web apenas. Não interceptar pedidos nem guardar conversas/chaves.
// Sem modo offline: a autenticação e os dados continuam a depender do servidor.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
