# Plan : retour d'état du Jetson en temps réel

Ce plan est destiné à être exécuté par un humain, avec un agent comme guide. Chaque phase est petite, testable en ligne de commande, et se termine par un point de validation. Ne passez à la phase suivante que lorsque la validation de la phase courante est réussie.

> Les adresses, noms d'utilisateur et mots de passe sont toujours des variables (`<Jetson address>`, etc.). Ne les écrivez jamais dans ce fichier ni dans le dépôt.

## 0. Mode d'emploi pour l'agent guide

Le **participant** écrit et exécute le code. L'**agent** guide : il explique, relit, pose des questions et propose des corrections, sans réaliser les phases à la place du participant (sauf demande explicite).

Au début de chaque session :

1. Lire ce fichier en entier, puis [.github/copilot-instructions.md](./.github/copilot-instructions.md) (commandes, architecture, conventions).
2. Lire la section « Suivi d'avancement » ci-dessous pour savoir où reprendre. Si elle est vide, commencer à la Phase 0.
3. Vérifier la branche Git courante : le travail se fait dans une branche dédiée, jamais sur `main`.

Pour chaque phase :

1. Résumer l'objectif en deux phrases et demander au participant ce qu'il prévoit de faire avant de lui donner des pistes.
2. Laisser le participant coder, puis relire son code en regard des cases à cocher de la phase.
3. Faire exécuter les commandes de la section **Validation** et lire avec lui les résultats. Une phase n'est terminée que si tout est observé, pas supposé.
4. Cocher les cases, noter les mesures réelles dans le suivi, puis proposer un commit (un par phase).

Où s'exécute quoi :

| Lieu | Ce qui s'y fait |
| ---- | --------------- |
| Poste de développement | Édition du dépôt, front-end Angular (`npm test`, `npm run build`) |
| Jetson (SSH) | Recopie manuelle de `Jetson/*.py` (voir en-têtes des scripts), exécution du handler et du script principal, broker MQTT |
| Raspberry Pi (SSH) | Serveur Express (service `server-mila`), tests `curl` |

Règles :

- Toujours demander la confirmation du participant avant une commande qui modifie le Jetson ou le Raspberry Pi.
- Ne jamais mettre d'adresse IP, de nom d'utilisateur ou de mot de passe dans un fichier du dépôt.
- Si une validation échoue, déboguer avec `mosquitto_sub -h <Jetson address> -t mila/# -v` avant de changer le code.
- Si le contrat de la section 3 doit changer, le modifier ici d'abord, puis adapter le code.

## Suivi d'avancement

À mettre à jour par le participant avec l'agent, à la fin de chaque phase.

| Phase | Statut | Commit | Mesures et notes (délais réels, problèmes rencontrés) |
| ----- | ------ | ------ | ------------------------------------------------------ |
| 0 | à faire | | |
| 1 | à faire | | |
| 2 | à faire | | |
| 3 | à faire | | |
| 4 | à faire | | |
| 5a | à faire | | |
| 5b | à faire | | |
| 6 | à faire | | |
| 7 | à faire | | |

## 1. Objectif et besoins

Le Jetson publie son état. Le Raspberry Pi le relaie jusqu'au front-end Angular.

| Besoin | Valeur | Source |
| ------ | ------ | ------ |
| Jetson en ligne | `online: true\|false` | Last Will MQTT + heartbeat |
| MILA peut être activé | `can_start: true\|false` + `reason` (court message si `false`) | Vérifications de prérequis par le Jetson |
| MILA est en marche | `running: true\|false` + `phase` (`stopped`, `starting`, `running`) | `true` seulement quand le script principal confirme lui-même que le modèle est chargé, la caméra ouverte et le port série ouvert. `false` après `stop_main_script` ou si le processus meurt seul |
| Panne | Message d'erreur avec mini-description | Fin anormale du script principal ou échec de démarrage |

Cible finale : Jetson → MQTT → Express → front-end Angular, en temps réel.

## 2. État actuel (point de départ)

- [Jetson/mqtt-handler.py](./Jetson/mqtt-handler.py) écoute seulement le topic `mila/control` (`start_main_script`, `stop_main_script`). Il ne publie rien.
- Le broker Mosquitto tourne sur le Jetson (`localhost:1883`).
- [RaspberryPi/node-server/server.js](./RaspberryPi/node-server/server.js) publie les commandes avec `mosquitto_pub`. Il ne reçoit aucun état.
- [Angular `app.ts`](./RaspberryPi/node-server/front-end/src/app/app.ts) met `status` à jour à partir de la réponse HTTP de `start`/`stop`, pas de l'état réel du Jetson.
- Les scripts du dossier `Jetson/` sont installés manuellement sur le Jetson (voir leurs commentaires d'en-tête). Toute modification doit être recopiée sur le Jetson pour être testée.

## 3. Contrat MQTT (à valider avant de coder)

Le topic de commande `mila/control` ne change pas. Les nouveaux topics sont sous `mila/status/` et sont publiés **retained** (sauf `error` et `main`). Un client qui se connecte reçoit donc immédiatement le dernier état connu.

**Principe : aucune valeur codée en dur.** Chaque champ vient d'une mesure réelle : état du processus (`poll()`), existence réelle des fichiers et du port série, confirmation envoyée par le script principal, heure système. Aucun état n'est déduit d'une commande reçue seulement (ex. recevoir `start_main_script` ne suffit pas pour déclarer `running: true`).

| Topic | Retained | Contenu |
| ----- | -------- | ------- |
| `mila/status/online` | oui | `true` ou `false`. `false` est publié automatiquement par le broker (Last Will) si le handler se déconnecte sans prévenir |
| `mila/status/state` | oui | JSON, voir ci-dessous. Republié à chaque changement et en heartbeat |
| `mila/status/error` | non | JSON d'événement ponctuel, voir ci-dessous |
| `mila/status/main` | non | Publié par le **script principal** lui-même (voir Phase 2) : confirmation réelle qu'il fonctionne |

`mila/status/state` :

```json
{
  "running": false,
  "phase": "stopped",
  "can_start": true,
  "reason": null,
  "ts": "2026-01-01T12:00:00Z"
}
```

`mila/status/main` (publié par le script principal, 1 fois par seconde) :

```json
{
  "phase": "ready",
  "fps": 28.4,
  "ts": "2026-01-01T12:00:00Z"
}
```

`phase` vaut `loading` (modèle en chargement ou caméra en ouverture) puis `ready`. `fps` est mesuré, jamais fixé.

`mila/status/error` :

```json
{
  "code": "main_script_exited",
  "message": "Le script principal s'est arrêté (code 1)",
  "ts": "2026-01-01T12:00:00Z"
}
```

Règles :

- `reason` est `null` quand `can_start` vaut `true`, sinon une courte phrase (ex. « Port série de l'ESP32 introuvable »).
- `ts` est en UTC, format ISO 8601.
- Délais (maximum 5 s, objectif de 1 à 3 s) : keepalive MQTT du handler et du script principal à **2 s** (le broker publie le Last Will après environ 1,5 × keepalive, soit ≈ 3 s) ; heartbeat de `state` et de `main` toutes les **1 s** ; côté Express, un état plus vieux que **3 s** est considéré comme « Jetson hors ligne », même si le Last Will n'a pas été reçu.
- Le heartbeat de 1 s est léger (messages de quelques dizaines d'octets). Vérifier sur le Jetson que la charge CPU reste négligeable.
- Les messages d'erreur sont courts et ne contiennent ni chemin complet, ni nom d'utilisateur, ni adresse IP.

Codes d'erreur proposés : `main_script_exited`, `start_failed`, `prerequisite_missing`.

## 4. Phases

### Phase 0 — Préparation (aucun code)

- [ ] Valider le contrat MQTT de la section 3 (noms de topics, champs, délais : keepalive 2 s, heartbeat 1 s, péremption 3 s).
- [ ] Vérifier l'accès SSH au Jetson et au Raspberry Pi, et que `mosquitto_sub` / `mosquitto_pub` sont installés sur le poste de test.
- [ ] Sur le Jetson, confirmer que le broker accepte les connexions réseau (`sudo ss -ltnp | grep 1883` doit afficher `0.0.0.0:1883`).

**Validation :** une commande `mosquitto_pub -h <Jetson address> -t mila/control -m stop_main_script` depuis le Raspberry Pi est reçue par `mosquitto_sub -h <Jetson address> -t mila/# -v` lancé ailleurs.

### Phase 1 — « Jetson en ligne » (Last Will + retained)

Fichier : [Jetson/mqtt-handler.py](./Jetson/mqtt-handler.py)

- [ ] Avant `connect`, définir le Last Will : topic `mila/status/online`, message `false`, retained.
- [ ] Dans `on_connect`, publier `true` (retained) sur `mila/status/online`, en plus de la souscription actuelle.
- [ ] Lors d'un arrêt propre (bloc `finally`), publier `false` avant `disconnect`.
- [ ] Dans la Phase 1, remplacer le keepalive actuel de 60 s par **2 s** dans `client.connect(...)`.
- [ ] Vérifier la version de `paho-mqtt` sur le Jetson (`pip show paho-mqtt`). Avec la version 2.x, `mqtt.Client()` sans argument échoue : il faut `mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)` (ou adapter la signature des callbacks). Le code actuel suppose la version 1.x.
- [ ] Avec `loop_forever()`, la publication depuis un autre thread est permise, mais le Last Will doit être défini (`will_set`) **avant** `connect`.

**Validation en ligne de commande** (depuis n'importe quelle machine du réseau) :

```bash
mosquitto_sub -h <Jetson address> -t mila/status/online -v
```

1. Démarrer le handler : affiche `mila/status/online true`.
2. Tuer le handler brutalement (`kill -9`) : le broker publie `mila/status/online false` en ≈ 3 s (keepalive de 2 s). Mesurer le délai réel et le noter.
3. Ouvrir un nouvel abonné après coup : il reçoit immédiatement la dernière valeur (retained).

### Phase 2 — « MILA est en marche » (`running`)

Fichier : [Jetson/mqtt-handler.py](./Jetson/mqtt-handler.py)

- [ ] Créer une fonction unique `publish_state()` qui construit et publie le JSON de `mila/status/state` (retained) à partir de mesures réelles.
- [ ] **Script principal** ([Jetson/2_Automated_servo_control_no_display_v2.py](./Jetson/2_Automated_servo_control_no_display_v2.py)) : ajouter un client MQTT qui publie `mila/status/main` (voir section 3) :
  - `phase: "loading"` dès le démarrage du script ;
  - `phase: "ready"` seulement quand le moteur TensorRT est chargé, la caméra est ouverte (`cap.isOpened()`) et le port série du `ServoController` est ouvert ;
  - ensuite un heartbeat par seconde avec le `fps` calculé dans la boucle existante ;
  - ne rien publier en cas d'échec : l'absence de messages est elle-même le signal.
- [ ] Le script principal s'exécute dans l'environnement virtuel `myenv` : vérifier que `paho-mqtt` y est installé (`python3 -c "import paho.mqtt.client"`), sinon l'installer.
- [ ] **Handler** : s'abonner à `mila/status/main` et calculer, à chaque heartbeat de 1 s :
  - processus absent → `phase: "stopped"`, `running: false` ;
  - processus vivant, aucun message `ready` reçu depuis moins de 3 s → `phase: "starting"`, `running: false` ;
  - processus vivant et `ready` reçu depuis moins de 3 s → `phase: "running"`, `running: true`.
- [ ] Appeler `publish_state()` après chaque commande, à chaque changement de phase et toutes les secondes (heartbeat, `loop_start()` + minuterie ou thread).
- [ ] Si `running` ou `phase` change sans commande (le processus est mort), publier l'état et passer à la Phase 4.

**Validation :**

```bash
mosquitto_sub -h <Jetson address> -t mila/status/# -v
mosquitto_pub -h <Jetson address> -t mila/control -m start_main_script
mosquitto_pub -h <Jetson address> -t mila/control -m stop_main_script
```

- Après `start_main_script` : `phase` passe à `starting`, puis à `running` **seulement** quand le modèle est chargé (le délai réel observé correspond au temps de chargement).
- Les messages `main` contiennent un `fps` mesuré qui varie.
- Après `stop_main_script` : `phase: stopped`, `running: false`.
- Un `state` arrive chaque seconde sans action.
- Un second `start_main_script` consécutif ne lance pas un second processus.
- Test d'échec : renommer temporairement le fichier de modèle `.trt` ; `running` ne doit jamais passer à `true`.

### Phase 3 — « MILA peut être activé » (`can_start` + `reason`)

Fichier : [Jetson/mqtt-handler.py](./Jetson/mqtt-handler.py)

- [ ] Écrire `check_prerequisites()` qui retourne `(can_start, reason)`. Vérifications minimales, à ajuster avec l'équipe :
  - le script principal existe dans le dossier attendu ;
  - l'environnement virtuel existe ;
  - le fichier de modèle `yolov8n_Face_FP16.trt` existe ;
  - le port série de l'ESP32 (`/dev/esp32s3serial`) existe ;
  - MILA n'est pas déjà en marche (`can_start: false`, raison « Déjà en marche »).
- [ ] Retourner la **première** raison rencontrée, en une phrase courte, sans chemin complet.
- [ ] Appeler `check_prerequisites()` dans `publish_state()` (donc à chaque heartbeat).
- [ ] Refuser `start_main_script` si `can_start` est `false` : ne pas lancer le processus, publier `error` avec le code `prerequisite_missing`.

**Validation :**

1. ESP32 branché : `can_start: true`, `reason: null`.
2. Débrancher l'ESP32 : dans la seconde suivante, `can_start: false` avec la raison du port série.
3. Envoyer `start_main_script` dans cet état : le processus ne démarre pas et un message `mila/status/error` est publié.

### Phase 4 — Pannes (`mila/status/error`)

Fichier : [Jetson/mqtt-handler.py](./Jetson/mqtt-handler.py)

- [ ] Distinguer l'arrêt voulu d'une panne : mémoriser que `stop_main_script` a été demandé (drapeau) avant d'envoyer SIGTERM.
- [ ] Si le processus se termine seul (code non nul ou sans arrêt demandé), publier `mila/status/error` (`main_script_exited`) avec le code de retour réel, puis republier `state` avec `running: false`.
- [ ] Si le processus reste en `starting` plus de 60 s (valeur à ajuster selon le temps de chargement mesuré en Phase 2), publier `start_failed` avec le message « Démarrage trop long ».
- [ ] Si `Popen` échoue, publier `start_failed`.
- [ ] Si `running` était `true` et que les messages `main` s'arrêtent plus de 3 s alors que le processus est vivant (script figé), publier `main_script_unresponsive`.
- [ ] Optionnel : conserver la dernière ligne de stderr du script principal pour enrichir `message` (tronquée à 120 caractères, sans chemin ni nom d'utilisateur).

**Validation :**

- Démarrer MILA, puis tuer le script Python depuis un autre terminal : un `error` apparaît et `running` passe à `false`.
- Démarrer puis arrêter via `stop_main_script` : aucun `error`.

### Phase 5 — Express consomme l'état (toujours en ligne de commande)

Fichier : [RaspberryPi/node-server/server.js](./RaspberryPi/node-server/server.js)

**5a. Lecture simple :**

- [ ] Ajouter la dépendance `mqtt` (`npm --prefix RaspberryPi/node-server install mqtt`).
- [ ] Se connecter au broker (`JETSON_IP_HOST`) au démarrage, avec reconnexion automatique, un keepalive de **2 s**, et s'abonner à `mila/status/#`.
- [ ] Conserver en mémoire le dernier `online`, le dernier `state` (avec l'heure de réception) et la dernière `error`.
- [ ] Ajouter `GET /mila/status` :

```json
{
  "online": true,
  "running": false,
  "phase": "stopped",
  "can_start": true,
  "reason": null,
  "last_error": null,
  "updated_at": "2026-01-01T12:00:00Z"
}
```

- [ ] Pièges de fraîcheur : (1) les messages *retained* livrés à la connexion d'Express ont l'air récents alors qu'ils peuvent dater d'avant une panne : ne mettre à jour l'heure de réception que pour les messages **non retained** (`packet.retain === false`) ; (2) ne jamais comparer le `ts` du Jetson à l'horloge du Raspberry Pi (sans Internet, les deux horloges peuvent dériver) : mesurer l'âge avec l'heure locale de réception.
- [ ] Obsolescence : `online: false` si l'état a plus de **3 s**, si `online` vaut `false`, ou si Express n'est pas connecté au broker. Dans ce cas, `running: false`, `can_start: false` et `reason: "Jetson hors ligne"` (valeurs déduites, pas conservées de l'ancien état).
- [ ] Ne pas modifier `/mila/start` ni `/mila/stop` (publication avec `mosquitto_pub` conservée).

**Validation :**

```bash
curl http://<Raspberry address>:3000/mila/status
```

- Handler actif : `online: true`.
- Handler arrêté : `online: false` après au plus 3 s.
- Start/stop via les routes existantes : `phase` passe par `starting`, `running`, puis `stopped`.

**5b. Temps réel (SSE) :**

- [ ] Ajouter `GET /mila/events` (Server-Sent Events) : état courant à la connexion, puis un événement à chaque changement (y compris le passage à « hors ligne » après 3 s sans heartbeat), avec un commentaire keep-alive toutes les 15 s pour garder la connexion HTTP ouverte.
- [ ] Nettoyer les clients à la fermeture de la connexion.
- [ ] SSE plutôt que WebSocket : flux unidirectionnel serveur → navigateur, aucune dépendance supplémentaire, reconnexion native.

**Validation :**

```bash
curl -N http://<Raspberry address>:3000/mila/events
```

L'état arrive immédiatement, puis à chaque changement côté Jetson.

### Phase 6 — Angular affiche l'état

Fichiers : [app.ts](./RaspberryPi/node-server/front-end/src/app/app.ts), [app.html](./RaspberryPi/node-server/front-end/src/app/app.html)

- [ ] Remplacer l'état local `status` par un signal alimenté par `EventSource` sur `/mila/events` (hôte via `environment.raspberryPiHost`, comme les appels actuels).
- [ ] Afficher : Jetson en ligne / hors ligne, MILA arrêtée / en démarrage / en marche (`phase`), la `reason` si `can_start` est `false`, et la dernière erreur. Afficher uniquement les valeurs reçues, sans texte d'état par défaut codé en dur (avant la première réception : « État inconnu »).
- [ ] Désactiver Démarrer si `online` ou `can_start` est `false` (raison affichée). Désactiver Arrêter si MILA n'est pas en marche.
- [ ] Perte du flux SSE : afficher « Connexion au serveur perdue » (reconnexion automatique du navigateur).
- [ ] Angular ne parle jamais MQTT, seulement HTTP/SSE vers Express.
- [ ] Ajouter des tests dans [app.spec.ts](./RaspberryPi/node-server/front-end/src/app/app.spec.ts) (en ligne/hors ligne, démarrage impossible avec raison, erreur).

**Validation :**

```bash
cd RaspberryPi/node-server/front-end
npm test
npm test -- --include src/app/app.spec.ts
npm run build
```

Puis test manuel : couper/relancer le handler Jetson et observer la page se mettre à jour sans rechargement.

### Phase 7 — Finalisation

- [ ] Mettre à jour [docs/contents/01-architecture_generale.md](./docs/contents/01-architecture_generale.md) (flux d'état) et [docs/contents/00-procedure_lancement_manuel.md](./docs/contents/00-procedure_lancement_manuel.md) (lire l'état en ligne de commande).
- [ ] Mettre à jour [.github/copilot-instructions.md](./.github/copilot-instructions.md) : topics MQTT, routes `/mila/status` et `/mila/events`, dépendance `mqtt`.
- [ ] Vérifier le déploiement sur le Raspberry Pi (voir [docs/contents/03-installation.md](./docs/contents/03-installation.md)) : `npm --prefix RaspberryPi/node-server install`, `sudo systemctl restart server-mila`, `ng build`.
- [ ] Test de bout en bout : Jetson éteint → allumé → démarrer → panne simulée → arrêter, en observant la page Angular.

## 5. Risques et décisions à confirmer

- **Délais :** keepalive de 2 s, heartbeat de 1 s, péremption de 3 s. Détection d'une panne réseau ≈ 3 s au maximum. À mesurer à chaque phase ; si la charge ou les faux « hors ligne » posent problème, passer à 5 s (limite maximale).
- **Deux sources pour « en ligne » :** Last Will et heartbeat ; Express applique les deux règles.
- **Broker sans authentification :** hors périmètre ; ne jamais mettre d'identifiants dans le dépôt.
- **`/mila/start` et `/mila/stop` restent en GET :** inchangées.
- **`running: true` = modèle chargé :** confirmé par le script principal lui-même (Phase 2). Cela impose de modifier ce script et de s'assurer que `paho-mqtt` est disponible dans son environnement virtuel.
- **Fichiers Jetson non suivis par Git :** le travail se fait dans une branche dédiée ; en cas de problème grave, changer de branche. Ajouter les fichiers avant de commencer pour un commit par phase.

## 6. Ordre de livraison suggéré

Un commit par phase, dans une branche dédiée : 1 → 2 → 3 → 4 (côté Jetson ; la Phase 2 touche aussi le script principal), testables avec `mosquitto_sub`, puis 5a → 5b (Express), puis 6 (Angular), puis 7.
