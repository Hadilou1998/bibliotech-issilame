# BiblioTech — Clean Code et qualité logicielle

**Projet fil rouge : TP1, TP2 et TP3**  
**Application :** gestion d'une bibliothèque municipale en Python  
**Dépôt GitHub :** [bibliotech-issilame](https://github.com/Hadilou1998/bibliotech-issilame)  
**Branche de travail du TP3 :** `qualite`  
**Version Python :** 3.10 ou supérieure

## 1. Présentation du projet

BiblioTech est une application en ligne de commande qui permet de gérer une bibliothèque municipale. Elle propose la consultation du catalogue, la liste des membres, les emprunts et les retours, le suivi des retards, le calcul des pénalités, les rappels, les rapports et l'export CSV.

Le programme fonctionnait déjà au début des travaux, mais certaines parties étaient difficiles à lire, contenaient des répétitions ou réunissaient trop de responsabilités. Pendant les trois TP, mon objectif a été d'améliorer le code **sans modifier son comportement attendu**.

## 2. TP1 — Nettoyage du code

### Objectif du TP1

Le premier TP consistait à repérer les défauts de lisibilité et à rendre le programme plus compréhensible.

### Travail réalisé pendant le TP1

- Analyse du fichier principal `bibliotech.py` pour identifier les portions de code difficiles à comprendre.
- Amélioration des noms et des commentaires pour mieux expliquer le rôle des différentes parties.
- Utilisation de constantes pour les durées d'emprunt, les limites et les tarifs de pénalité.
- Simplification de plusieurs traitements, tout en conservant les messages et les règles métier du programme.
- Vérification du résultat avec les tests et les outils de qualité.

### Bilan du TP1

Un code propre n'est pas seulement un code qui fonctionne : il doit aussi être lisible par une autre personne. Des noms explicites et des fonctions bien organisées rendent les corrections futures plus faciles.

## 3. TP2 — Refactoring et tests

### Objectif du TP2

Le deuxième TP avait pour but de réorganiser le programme **sans changer ce qu'il fait**.

### Travail réalisé pendant le TP2

- Séparation des vérifications liées aux emprunts : membre actif, retards, limite d'emprunts, document déjà emprunté et disponibilité.
- Extraction de certaines responsabilités dans des méthodes plus courtes, notamment `refusal_reason()`, `borrow_document()` et `create_loan()`.
- Centralisation du calcul des pénalités dans la fonction `late_fee()`, réutilisée à plusieurs endroits.
- Ajout de tests pour vérifier les règles d'emprunt et éviter les régressions.
- Contrôle régulier avec `pytest`, `ruff` et `radon`.

### Bilan du TP2

Le refactoring consiste à améliorer l'intérieur du programme tout en gardant le même résultat pour l'utilisateur. Les tests sont importants, car ils permettent de vérifier que les modifications n'ont pas cassé une fonctionnalité existante.

## 4. TP3 — Fiabilité et mesures de qualité

### Objectif du TP3

Le dernier TP consistait à renforcer la fiabilité de BiblioTech, à simplifier une fonction complexe et à mesurer les progrès avec des outils.

### Préparation

J'ai conservé l'état de référence de la fin du TP2 avec le tag Git `v2-fin-j2`, puis travaillé sur la branche `qualite`. Cela permet de comparer l'état initial et l'état final du TP3.

### Amélioration 1 — Journaliser les erreurs des extensions

Dans `run_plugins()`, une extension peut provoquer une exception. J'ai utilisé `logging.exception()` pour conserver une trace de l'erreur, tout en permettant aux autres extensions de continuer leur exécution.

**Pourquoi ?** Une erreur enregistrée dans les journaux est plus facile à comprendre et à corriger qu'une erreur ignorée silencieusement.

Un test dédié a été ajouté dans `tests/test_plugins.py`.

### Amélioration 2 — Harmoniser le formatage

J'ai utilisé `ruff format` pour appliquer une présentation cohérente aux fichiers Python du projet.

**Pourquoi ?** Un formatage identique facilite la lecture et évite de perdre du temps sur des différences de présentation.

À la fin du TP3, **9 fichiers sont correctement formatés**.

### Amélioration 3 — Simplifier le rapport

La méthode `report()` effectuait à la fois les calculs des statistiques et leur affichage. J'ai extrait les calculs des emprunts dans `report_loan_statistics()`.

**Pourquoi ?** Chaque méthode a maintenant un rôle plus précis : l'une calcule les statistiques, l'autre les affiche. La méthode `report()` est ainsi plus simple à comprendre.

J'ai ajouté `tests/test_report.py` pour vérifier que le rapport affiche toujours ses principales rubriques. Une erreur de récursion rencontrée pendant le refactoring a également été corrigée avant la validation finale.

### Amélioration 4 — Renforcer les contrôles Ruff

J'ai adapté le fichier `pyproject.toml` pour activer des règles de qualité supplémentaires :

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "B", "S", "C90", "SIM"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "S603"]
```

Les exceptions `S101` et `S603` sont limitées aux fichiers de test. Les vérifications restent actives pour le code de l'application.

### Comparaison des résultats

| Indicateur | Début du TP3 | Fin du TP3 |
| --- | ---: | ---: |
| Avertissements Ruff (audit ciblé hors tests) | 1 | **0** |
| Tests réussis | 36 | **38** |
| Complexité moyenne (Radon) | A (3,15) | **A (3,09)** |
| Complexité de `Library.report()` | B (10) | **B (7)** |
| Fonctions de niveau C ou pire | 0 | **0** |
| Maintenabilité (Radon MI) | Non relevée | **A (24,28)** |

La complexité de `report()` est passée de **10 à 7**, soit une réduction de **30 %**. Le nombre de tests réussis est passé de **36 à 38**. L'audit Ruff ciblé ne signale plus d'avertissement.

> La note de maintenabilité finale est une mesure du code après modifications ; aucune mesure initiale comparable n'a été relevée.

### Historique des commits du TP3

| Commit | Travail réalisé |
| --- | --- |
| `a04a8f0` | Journalisation des erreurs des extensions |
| `9fe1477` | Harmonisation du formatage avec Ruff |
| `10be3a3` | Première extraction des statistiques du rapport |
| `d97a88a` | Correction et finalisation du refactoring du rapport |
| `e51f6a8` | Renforcement des règles Ruff |

La comparaison a été effectuée entre `v2-fin-j2` et la branche `qualite`.

## 5. Bilan personnel des trois TP

Au **TP1**, j'ai appris à reconnaître un code difficile à lire et à améliorer sa présentation.

Au **TP2**, j'ai appris à découper les traitements et à éviter de répéter les mêmes règles dans plusieurs fonctions. J'ai aussi compris pourquoi il faut relancer les tests après chaque changement.

Au **TP3**, j'ai appris à mesurer la qualité du code plutôt qu'à me fier uniquement à mon impression. J'ai utilisé Ruff pour détecter des problèmes, Radon pour mesurer la complexité et Pytest pour vérifier le fonctionnement.

La difficulté la plus marquante a été le refactoring du rapport : une première version contenait un appel récursif incorrect. J'ai corrigé cette erreur, ajouté un test et relancé les contrôles avant d'enregistrer la version finale.

**Ce que je retiens :** un bon développeur ne cherche pas seulement à faire fonctionner un programme. Il doit aussi être capable d'expliquer son code, de le tester, de corriger ses erreurs et de suivre ses modifications avec Git.

## 6. Installation et utilisation

### Prérequis

- Python 3.10 ou une version supérieure.
- Git, pour récupérer le projet.
- Les dépendances indiquées dans `requirements.txt`.

### Installer le projet

```powershell
git clone https://github.com/Hadilou1998/bibliotech-issilame.git
cd bibliotech-issilame
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Sous Linux ou macOS, la commande d'activation est `source .venv/bin/activate`.

### Commandes de l'application

```powershell
python bibliotech.py list
python bibliotech.py members
python bibliotech.py borrow M005 B005
python bibliotech.py return L004
python bibliotech.py overdue
python bibliotech.py report
python bibliotech.py export emprunts.csv
```

Les identifiants utilisés pour `borrow` et `return` sont des exemples : ils doivent correspondre aux données présentes dans les fichiers CSV du dossier `data`.

Pour fixer la date lors d'un essai :

```powershell
python bibliotech.py report --today 2026-10-21
```

### Vérifier la qualité du projet

**Lancer les tests :**

```powershell
pytest -q
```

**Contrôler le code et le formatage :**

```powershell
ruff check .
ruff format --check .
```

**Mesurer la complexité et la maintenabilité :**

```powershell
radon cc -s -a --exclude "tests/*" .
radon cc -s -n C --exclude "tests/*" .
radon mi -s --exclude "tests/*" .
```

**Reproduire l'audit Ruff ciblé du TP3 :**

```powershell
ruff check . --select E,W,F,B,S,C90,SIM --extend-exclude tests --statistics
```

### Résultat de la dernière vérification

- **38 tests réussis** avec Pytest.
- **Aucune erreur** avec `ruff check .`.
- **9 fichiers conformes** avec `ruff format --check .`.
- **Aucune fonction classée C ou pire** avec Radon.

## Conclusion

Ces trois TP m'ont permis d'améliorer progressivement BiblioTech : d'abord en nettoyant le code, ensuite en le réorganisant, puis en renforçant les tests et les contrôles de qualité.

Le projet conserve ses fonctionnalités tout en étant plus facile à lire, à tester et à maintenir. Les résultats mesurés et l'historique Git permettent de justifier les améliorations réalisées.
