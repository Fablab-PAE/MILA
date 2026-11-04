# Instructions pour le dépôt Mila

## Compilation, tests et exécution

Les commandes Angular s’exécutent depuis `RaspberryPi/node-server/front-end` :

```sh
npm start
npm run build
npm test
npm test -- --include src/app/app.spec.ts
npm test -- --filter="should render title"
```

Angular CLI utilise Vitest. `--include` limite l’exécution à un fichier de test et `--filter` sélectionne les tests dont le nom correspond au motif. Aucun script lint n’est configuré.

Avant le build ou les tests, créez les fichiers locaux ignorés par Git à partir des exemples :

- `src/environments/environment-example.ts` → `src/environments/environment.ts`
- `src/environments/environment.development-example.ts` → `src/environments/environment.development.ts`

Définissez `raspberryPiHost` dans les deux fichiers. La configuration de développement remplace `environment.ts` par `environment.development.ts`.

Le serveur Express s’exécute depuis `RaspberryPi/node-server` avec `npm start` (port 3000). Il requiert un `.env` local contenant `JETSON_IP_HOST` et `RASPBERRY_PI_HOST`. Son script `npm test` est un espace réservé qui échoue ; aucun test ou lint backend n’est configuré.

## Architecture

- Mila répartit ses responsabilités sur trois cartes : le Jetson assure la capture vidéo, le suivi du visage, la commande des servomoteurs et le broker MQTT ; l’ESP32-S3 génère le PWM des servomoteurs à partir des commandes série ; le Raspberry Pi gère la voix, l’audio et les yeux animés.
- Les scripts Python de `Jetson/` mettent en œuvre le suivi caméra/TensorRT et l’écoute des commandes MQTT. Le contrôle envoie des commandes série `PAN:<angle>` et `TILT:<angle>` à l’ESP32. Les descriptions détaillées du flux matériel et du déploiement sont dans `docs/contents/01-architecture_generale.md`, `docs/contents/04-controle_servomoteurs.md` et `docs/contents/05-inference_suivi_visage.md`.
- L’interface Web Angular est dans `RaspberryPi/node-server/front-end`; l’API est dans `RaspberryPi/node-server`, en Express/CommonJS. Angular appelle `/mila/start` et `/mila/stop`; Express lance `mosquitto_pub` vers `JETSON_IP_HOST`, sur le topic `mila/control`, avec les messages `start_main_script` et `stop_main_script`.
- Express sert le bundle Angular depuis `front-end/dist/node-client/browser`. Le service systemd et son exemple de configuration locale sont dans `RaspberryPi/services`. Voir `docs/contents/00-procedure_lancement_manuel.md` pour le démarrage/arrêt et `docs/contents/03-installation.md` pour le déploiement.

## Conventions et limites des composants

- L’application Angular utilise un composant racine autonome (`src/app/app.ts`) et les fournisseurs de `src/app/app.config.ts`. Utilisez `HttpClient` pour l’API et les signaux pour l’état simple du composant ; gardez les adresses propres à l’environnement dans `src/environments/`.
- Préservez la séparation frontend/API : le frontend appelle les routes HTTP, et seul le serveur traduit ces appels en commandes MQTT. Le contrôle matériel ne doit pas être déplacé dans l’application Angular.
- Le serveur Node utilise CommonJS et charge `.env` depuis son répertoire de travail. Préservez les noms `JETSON_IP_HOST` et `RASPBERRY_PI_HOST`, ainsi que les origines CORS nécessaires au frontend local et au Raspberry Pi.
- Lors d’un changement à la compilation Angular, conservez le répertoire de sortie `front-end/dist/node-client/browser`, attendu par le middleware de fichiers statiques Express.
