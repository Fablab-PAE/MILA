# Instructions pour le dépôt Mila

## Architecture

- Mila est réparti sur trois cartes matérielles : le Jetson gère la capture vidéo, le suivi des visages, la logique de commande des servomoteurs et le broker MQTT ; l’ESP32-S3 commande les servomoteurs ; le Raspberry Pi gère la voix, l’audio et les yeux animés. Consultez `docs/contents/01-architecture_generale.md` et `docs/home.md` pour l’architecture matérielle et les procédures d’utilisation. Les répertoires de code du Jetson et de l’ESP32-S3 sont des espaces réservés dans ce dépôt ; ne supposez pas que leur code d’exécution y est implémenté.
- L’interface Web du Raspberry Pi se trouve dans `RaspberryPi/node-server/front-end` (Angular) et son API/serveur dans `RaspberryPi/node-server` (Express en CommonJS). Express sert les fichiers Angular compilés depuis `front-end/dist/node-client/browser`. Les routes `/mila/start` et `/mila/stop` publient des messages MQTT de commande vers le Jetson avec `mosquitto_pub`.
- L’application Angular lit l’adresse du Raspberry Pi dans sa configuration d’environnement et appelle ces routes Express. Le serveur lit `JETSON_IP_HOST` et `RASPBERRY_PI_HOST` depuis `RaspberryPi/node-server/.env`. Le service systemd et le modèle de fichier d’environnement local se trouvent dans `RaspberryPi/services`.

## Compilation, tests et exécution

Exécutez les commandes du frontend depuis `RaspberryPi/node-server/front-end` :

```sh
npm start
npm run build
npm test
npm test -- --include src/app/app.spec.ts
npm test -- --filter="should render title"
```

L’option `--include` lance un fichier de tests ; `--filter` sélectionne les tests dont le nom de suite ou de test correspond au motif. Angular CLI utilise Vitest.

Avant de compiler ou de lancer les tests, créez les fichiers de configuration locaux ignorés par Git à partir des modèles :

- Copiez `src/environments/environment-example.ts` vers `src/environments/environment.ts`.
- Copiez `src/environments/environment.development-example.ts` vers `src/environments/environment.development.ts`.
- Dans chaque fichier, définissez `raspberryPiHost` avec l’adresse du Raspberry Pi.

La configuration de développement Angular remplace `environment.ts` par `environment.development.ts`; ces deux fichiers sont ignorés par Git. Le serveur a également besoin du fichier `RaspberryPi/node-server/.env`, ignoré par Git, contenant `JETSON_IP_HOST` et `RASPBERRY_PI_HOST`.

Lancez le serveur Express depuis `RaspberryPi/node-server` avec `npm start` (port 3000). Le script `npm test` de ce répertoire est un espace réservé qui se termine avec une erreur ; aucune commande de test ou de lint n’est configurée pour le backend.

## Conventions de code et limites des composants

- La racine Angular est un composant autonome (`src/app/app.ts`), configuré avec les fournisseurs de `src/app/app.config.ts`. Utilisez `HttpClient` d’Angular pour les appels à l’API et les signaux pour l’état simple du composant ; les adresses propres à chaque environnement doivent rester dans `src/environments/`.
- Préservez la séparation entre le Web et l’API : le frontend appelle `/mila/start` et `/mila/stop`, et Express les traduit en commandes MQTT. Le contrôle matériel et la vision sont décrits dans la documentation, mais ne sont pas implémentés dans l’application Angular.
- Le service Express utilise des modules CommonJS et sert la version de production du bundle Angular. Si vous modifiez la configuration de compilation Angular, conservez le chemin de sortie attendu par le middleware de fichiers statiques.
- Consultez `docs/contents/00-procedure_lancement_manuel.md` pour le fonctionnement des commandes de démarrage et d’arrêt, et `docs/contents/03-installation.md` pour le déploiement sur Raspberry Pi et la configuration systemd.
