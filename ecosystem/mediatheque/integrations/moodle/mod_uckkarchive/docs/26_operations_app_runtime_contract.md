# 26 — Operations App Runtime Contract

**Path recommandé:** `docs/26_operations_app_runtime_contract.md`
**Statut:** Final target specification
**Portée:** Application / GUI d’opérations UCKK pour synchronisation, seed, serveur, caches et vérifications runtime.
**Source opérationnelle:** Notes d’intervention du 2026-06-01.
**But:** Définir un contrat stable pour éviter les erreurs de déploiement, les confusions entre fichiers source et état Moodle réel, les blocages SSH invisibles, les seeds appliqués en mauvais mode et les chemins serveur incorrects.

---

## 1. Décision canonique

L’app d’opérations UCKK n’est pas seulement une interface de boutons.

Elle est une console guidée qui connaît :

```text
Repo source
Runtime Moodle
DB Moodle
SSH readiness
Seed mode
Cache state
Smoke-test state
```

Formule canonique :

```text
L’app ne suppose pas qu’un fichier source est déjà actif dans Moodle.
L’app vérifie les préconditions avant chaque action serveur.
L’app rend visibles les modes, chemins, commandes, résultats et jonctions critiques.
```

Règle finale :

```text
Aucune action serveur ne doit être lancée si SSH n’est pas prêt.
Aucune application de seed ne doit laisser Moodle en mode apply.
Aucune purge cache ne doit supposer un seul chemin fixe.
```

---

## 2. Modèle mental obligatoire

Toujours distinguer :

```text
Repo source
Runtime Moodle
DB Moodle
```

Définition :

| Couche | Description | Exemple |
|---|---|---|
| `Repo source` | Fichiers officiels versionnés Git | `academic_registry_json/categories.json` |
| `Runtime Moodle` | Moodle réellement exécuté sur le serveur | `/var/www/moodle/public` |
| `DB Moodle` | Données réellement affichées par Moodle | catégories visibles dans `/course/index.php` |

Règle :

```text
Modifier un fichier source ne modifie pas automatiquement ce que Moodle affiche.
```

Exemple canonique :

```text
categories.json = recette
seed categories = appliquer la recette
DB Moodle = ce que Moodle affiche
```

---

## 3. Variables canoniques — chemins

| Variable | Valeur canonique | Rôle |
|---|---|---|
| `LOCAL_SOURCE_REPO_ROOT` | `C:\mycode\UCKK\uckk-moodle` | Repo source local. |
| `SERVER_SOURCE_REPO_ROOT` | `/opt/uckk/uckk-moodle` | Repo source serveur. |
| `MOODLE_PUBLIC_ROOT` | `/var/www/moodle/public` | Racine Moodle publique observée. |
| `MOODLE_REAL_ROOT` | `/var/www/moodle` | Racine Moodle réelle observée. |
| `MOODLE_CONFIG_PATH` | `/var/www/moodle/config.php` | Fichier config Moodle. |
| `ACADEMIC_REGISTRY_PATH` | `academic_registry_json` | Registre source JSON. |
| `UCKKSEED_CLI_PUBLIC_PATH` | `/var/www/moodle/public/admin/tool/uckkseed/cli/seed.php` | CLI seed observé. |
| `CACHE_PURGE_PRIMARY_PATH` | `/var/www/moodle/public/admin/cli/purge_caches.php` | Chemin purge attendu. |
| `CACHE_PURGE_FALLBACK_PATH` | `/var/www/moodle/admin/cli/purge_caches.php` | Chemin purge réel trouvé. |

Règle :

```text
Les chemins peuvent différer entre documentation et serveur.
L’app doit détecter les chemins critiques au lieu de les supposer.
```

---

## 4. Variables canoniques — SSH

| Variable | Valeur canonique |
|---|---|
| `SSH_USER` | `ubuntu` |
| `SSH_HOST` | `57.129.115.159` |
| `SSH_IDENTITY_FILE_WINDOWS` | `$env:USERPROFILE\.ssh\id_ed25519` |
| `SSH_BATCH_MODE` | `true` |
| `SSH_READY_COMMAND` | `ssh -i "$env:USERPROFILE\.ssh\id_ed25519" -o IdentitiesOnly=yes -o BatchMode=yes ubuntu@57.129.115.159 "echo OK"` |
| `SSH_READY_EXPECTED_OUTPUT` | `OK` |
| `SSH_NOT_READY_STATE` | `blocked` |

Règle :

```text
Avant tout bouton serveur, l’app doit exécuter un test SSH non interactif.
```

Si le test ne retourne pas exactement :

```text
OK
```

l’app doit bloquer :

```text
Pull serveur
Dry-run categories serveur
Apply categories serveur
Purger caches serveur
Toute action distante avec sudo
```

Message utilisateur :

```text
SSH non prêt. Corriger l’accès SSH avant d’utiliser les actions serveur.
```

---

## 5. Règle SSH anti-gel

Le GUI ne doit jamais masquer une demande SSH ou sudo invisible.

Interdit :

```text
lancer une commande distante pouvant demander un mot de passe
lancer une commande SSH sans BatchMode pour une action automatisée
afficher seulement “en cours” sans sortie brute
bloquer l’interface sans journal visible
```

Obligatoire :

```text
précheck SSH
journal visible
statut final explicite
commande copiée si action manuelle requise
blocage des boutons dépendants en cas d’échec
```

---

## 6. Variables canoniques — seed

| Variable | Valeur canonique | Règle |
|---|---|---|
| `SEED_TOOL_COMPONENT` | `tool_uckkseed` | Composant Moodle du seed. |
| `SEED_DEFAULTMODE_SETTING` | `tool_uckkseed/defaultmode` | Configuration Moodle qui contrôle le mode réel. |
| `SEED_SAFE_MODE` | `dry_run` | Mode sûr par défaut. |
| `SEED_APPLY_MODE` | `apply` | Mode temporaire pour écriture réelle. |
| `SEED_FORCE_ALONE_APPLIES` | `false` | `--force` seul ne garantit pas l’écriture. |
| `SEED_CLI_ACCEPTS_MODE_OPTION` | `false` | `--mode=apply` n’est pas accepté par le CLI actuel. |
| `SEED_APPLY_PATTERN` | `set_config apply → seed --force → set_config dry_run` | Séquence obligatoire. |

Règle :

```text
Le seed réel vient de defaultmode, pas seulement de --force.
```

---

## 7. Workflow seed canonique

Séquence obligatoire pour appliquer un preset :

```text
1. Vérifier SSH
2. Git pull serveur
3. Dry-run seed
4. Changer defaultmode à apply
5. Lancer seed.php avec --force
6. Remettre defaultmode à dry_run
7. Purger caches
8. Vérifier visuellement ou par smoke test
```

Règle de jonction :

```text
Ne pas aller à l’étape apply si le dry-run échoue.
Ne pas quitter après apply sans remettre defaultmode à dry_run.
Ne pas considérer l’opération terminée avant purge cache.
```

---

## 8. Commandes seed canoniques

### 8.1 Lire / définir `defaultmode=apply`

```bash
cd /var/www/moodle/public

sudo -u www-data php <<'PHP'
<?php
define('CLI_SCRIPT', true);
require('/var/www/moodle/config.php');
set_config('defaultmode', 'apply', 'tool_uckkseed');
echo "defaultmode=apply\n";
PHP
```

### 8.2 Appliquer le seed

```bash
sudo -u www-data php /var/www/moodle/public/admin/tool/uckkseed/cli/seed.php --presetpath=/opt/uckk/uckk-moodle/academic_registry_json --preset=categories --force
```

Sortie attendue pour succès :

```text
Mode: apply
Status: completed
failed: 0
errors: 0
```

### 8.3 Remettre le mode sûr

```bash
sudo -u www-data php <<'PHP'
<?php
define('CLI_SCRIPT', true);
require('/var/www/moodle/config.php');
set_config('defaultmode', 'dry_run', 'tool_uckkseed');
echo "defaultmode=dry_run\n";
PHP
```

Sortie attendue :

```text
defaultmode=dry_run
```

---

## 9. Variables canoniques — purge caches

| Variable | Valeur |
|---|---|
| `CACHE_PURGE_COMMAND_MODE` | `detect_first_existing_path` |
| `CACHE_PURGE_PRIMARY` | `/var/www/moodle/public/admin/cli/purge_caches.php` |
| `CACHE_PURGE_FALLBACK` | `/var/www/moodle/admin/cli/purge_caches.php` |
| `CACHE_PURGE_USER` | `www-data` |

Commande robuste :

```bash
PURGE=""
for f in \
  /var/www/moodle/public/admin/cli/purge_caches.php \
  /var/www/moodle/admin/cli/purge_caches.php
do
  if [ -f "$f" ]; then
    PURGE="$f"
    break
  fi
done

if [ -z "$PURGE" ]; then
  echo "No purge_caches.php found"
  exit 1
fi

sudo -u www-data php "$PURGE"
```

Règle :

```text
L’app ne doit pas échouer silencieusement si le chemin public n’existe pas.
Elle doit tester les chemins et afficher celui utilisé.
```

---

## 10. États GUI canoniques

| État | Valeur | Description |
|---|---|---|
| `ssh_state` | `unknown`, `ready`, `blocked` | État SSH. |
| `git_state` | `unknown`, `clean`, `pulled`, `failed` | État Git serveur. |
| `seed_mode_state` | `unknown`, `dry_run`, `apply`, `unsafe` | État du mode seed. |
| `dry_run_state` | `not_run`, `completed`, `failed` | État dry-run. |
| `apply_state` | `not_run`, `completed`, `failed`, `cleanup_required` | État apply. |
| `cache_state` | `unknown`, `purged`, `failed` | État cache. |
| `smoke_state` | `not_run`, `passed`, `failed`, `manual_required` | État vérification. |

Règle :

```text
Chaque bouton doit afficher ses préconditions.
Chaque action doit écrire un journal.
Chaque statut final doit être visible sans lire la console brute.
```

---

## 11. Boutons GUI canoniques

| Bouton | Précondition | Action | Échec bloque |
|---|---|---|---|
| `Vérifier SSH` | aucune | test SSH BatchMode | actions serveur |
| `Pull serveur` | `ssh_state=ready` | git pull dans repo serveur | dry-run/apply |
| `Dry-run categories serveur` | `ssh_state=ready` | seed en mode dry_run | apply |
| `Apply categories serveur` | `ssh_state=ready` + dry-run OK | apply temporaire + force + cleanup | smoke test |
| `Purger caches serveur` | `ssh_state=ready` | détection chemin + purge | smoke test |
| `Smoke test catégories` | purge faite | ouvrir ou tester `/course/index.php` | statut final |

Règle :

```text
Un bouton bloqué doit expliquer pourquoi.
```

---

## 12. Bloc opératoire recommandé

Style utilisateur :

```text
Colle ce bloc.
Arrête là.
Colle-moi le résultat.
```

Règle :

```text
Ne pas donner 8 petits blocs si un seul bloc complet peut être collé.
Mais arrêter aux jonctions importantes.
```

Jonctions obligatoires :

```text
1. test SSH
2. git pull
3. dry-run
4. apply
5. cleanup/cache
6. smoke test
```

---

## 13. Commande de vérification SSH locale

PowerShell :

```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519" -o IdentitiesOnly=yes -o BatchMode=yes ubuntu@57.129.115.159 "echo OK"
```

Résultat obligatoire :

```text
OK
```

Si résultat différent :

```text
ne pas utiliser les boutons serveur
corriger SSH d’abord
```

---

## 14. Commande d’installation de clé SSH

Commande qui ajoute la clé publique locale au serveur :

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | ssh ubuntu@57.129.115.159 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

Après exécution, refaire :

```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519" -o IdentitiesOnly=yes -o BatchMode=yes ubuntu@57.129.115.159 "echo OK"
```

---

## 15. Encodage PowerShell

Problème observé :

```text
VÃ©rifier chemins
Sync source â†’ Moodle local
```

Cause probable :

```text
.ps1 lu comme ANSI par Windows PowerShell
```

Correction canonique :

```powershell
$path = "C:\mycode\UCKK\uckk-moodle\tools\uckk-ops\uckk_ops_gui.ps1"
$bytes = [System.IO.File]::ReadAllBytes($path)
$text = [System.Text.Encoding]::UTF8.GetString($bytes)
$utf8bom = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText($path, $text, $utf8bom)
```

Règle :

```text
Les scripts GUI PowerShell doivent être sauvegardés en UTF-8 avec BOM ou exécutés avec PowerShell 7.
```

---

## 16. Journalisation minimale

Chaque action GUI doit écrire :

```text
timestamp
action name
preconditions
command summary
raw output
parsed status
next recommended step
cleanup status
```

Exemple :

```text
[2026-06-01 17:22:00] Apply categories
SSH: ready
Seed defaultmode before: dry_run
Set defaultmode: apply
Seed result: completed, failed=0, errors=0
Set defaultmode: dry_run
Next: purge caches
```

---

## 17. Smoke tests canoniques

| Test | URL / commande | Résultat attendu |
|---|---|---|
| `SMOKE_COURSE_INDEX` | `https://uckk.org/course/index.php` | Catégories publiques visibles. |
| `SMOKE_MOODLE_HOME` | `https://uckk.org/` | Moodle répond. |
| `SMOKE_SSH` | `ssh ... "echo OK"` | `OK`. |
| `SMOKE_CACHE_PURGE` | commande purge détectée | exit code 0. |

Règle :

```text
Un seed réussi sans smoke test reste “completed, verification pending”.
```

---

## 18. Règles de sécurité opérationnelle

Interdit :

```text
laisser defaultmode=apply après une opération
masquer une commande sudo interactive
lancer un apply sans dry-run réussi
lancer un apply si SSH n’est pas prêt
supposer que public/admin/cli/purge_caches.php existe
confondre registry JSON et plugin runtime
présenter un git pull comme preuve que Moodle DB est à jour
```

Obligatoire :

```text
dry_run par défaut
apply temporaire seulement
cleanup automatique
journal visible
préconditions explicites
smoke test final
```

---

## 19. États finaux valides

Un cycle categories est complet seulement si :

```text
SSH fonctionnel = oui
Git pull serveur = oui
Dry-run categories = completed, errors 0
Apply categories = completed, errors 0
Seed defaultmode remis à dry_run = oui
Purge caches = oui
Smoke test = passed ou vérification manuelle demandée
```

Si une étape échoue :

```text
ne pas déclarer l’opération complète
afficher l’étape bloquante
afficher la commande ou sortie utile
proposer la prochaine jonction, pas toute la suite
```

---

## 20. Relation avec `academic_registry_json`

Variables :

| Variable | Valeur |
|---|---|
| `ACADEMIC_REGISTRY_RUNTIME_COMPONENT` | `false` |
| `ACADEMIC_REGISTRY_IS_SOURCE_ONLY` | `true` |
| `ACADEMIC_REGISTRY_APPLY_METHOD` | `tool_uckkseed` |

Règle :

```text
academic_registry_json n’est pas un composant runtime Moodle.
Il ne doit pas être traité comme local_uckk, mod_uckkarchive, theme_uckk ou tool_uckkseed.
```

Flux correct :

```text
modifier academic_registry_json/categories.json
→ git commit + push
→ git pull serveur
→ seed categories
→ purge caches
→ vérifier dans Moodle
```

---

## 21. Relation avec les plugins Moodle

Les plugins Moodle doivent être synchronisés dans le runtime Moodle :

```text
local/uckk
mod/uckkarchive
theme/uckk
admin/tool/uckkseed
```

Le registre académique JSON reste source-only :

```text
academic_registry_json
```

Règle :

```text
L’app doit avoir des actions distinctes pour :
- sync plugin runtime
- seed registry data
- purge cache
- smoke test
```

---

## 22. Messages utilisateur canoniques

SSH non prêt :

```text
SSH non prêt. Corriger l’accès SSH avant d’utiliser les actions serveur.
```

Dry-run requis :

```text
Le dry-run doit réussir avant l’application réelle.
```

Mode seed dangereux :

```text
Le seed est encore en mode apply. Remise en dry_run requise avant de continuer.
```

Purge introuvable :

```text
Aucun purge_caches.php trouvé dans les chemins connus.
```

Succès seed :

```text
Seed complété. Mode safe restauré. Purge caches requise.
```

Succès final :

```text
Opération complétée. Vérifier visuellement Moodle si le smoke test n’a pas été automatisé.
```

---

## 23. Tests obligatoires

Tests unitaires / fonctionnels :

```text
SSH ready parser accepts exact OK
SSH ready parser rejects empty output
server buttons disabled when SSH blocked
apply button disabled when dry-run failed
apply flow sets defaultmode=apply
apply flow restores defaultmode=dry_run
apply flow flags cleanup_required if restore fails
cache purge selects fallback path when public path missing
registry JSON is classified source-only
plugin paths are classified runtime components
PowerShell encoding check warns on broken accents
```

Tests de non-régression :

```text
--force alone is not treated as apply guarantee
--mode=apply is not emitted for current CLI
git pull is not treated as DB update
cache purge path is detected, not hardcoded only
```

---

## 24. Anti-dérive finale

Ces noms sont définitifs :

```text
Repo source
Runtime Moodle
DB Moodle
defaultmode
dry_run
apply
SSH ready
seed categories
purge caches
smoke test
academic_registry_json
source-only registry
```

Noms à éviter :

```text
sync DB
deploy JSON directly
apply with --mode
force apply
runtime registry component
Moodle source DB
```

Règle :

```text
Ne pas utiliser un nom qui laisse croire qu’un fichier JSON source est automatiquement visible dans Moodle.
Ne pas utiliser un nom qui laisse croire que --force suffit pour écrire.
```

---

## 25. Résumé exécutable

```text
Avant serveur : vérifier SSH en BatchMode.
Avant apply : dry-run réussi.
Pour apply : passer defaultmode à apply, lancer seed --force, remettre defaultmode à dry_run.
Après apply : purger caches avec détection de chemin.
Après purge : smoke test ou vérification visuelle.
Toujours distinguer repo source, runtime Moodle et DB Moodle.
```

---

## 26. État cible de l’app

L’app d’opérations UCKK doit permettre à l’utilisateur de savoir clairement :

```text
ce qui existe dans Git
ce qui est synchronisé dans Moodle
ce qui a été écrit dans la DB Moodle
si SSH est prêt
si le seed est safe
si les caches sont purgés
quelle étape vient ensuite
quelle commande a réellement tourné
```

Final rule :

```text
L’app doit réduire l’ambiguïté opérationnelle.
Elle ne doit jamais cacher une attente interactive, un mode dangereux ou une différence entre source, runtime et DB.
```
