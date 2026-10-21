# TP1 — Clean Code et qualité logicielle
## Projet BiblioTech — Compte-rendu des travaux

**Projet :** BiblioTech, gestion d'une bibliothèque municipale  
**Dépôt GitHub :** https://github.com/Hadilou1998/bibliotech-issilame  
**Branche de travail :** `tp1/nettoyage`  
**Fichier principal :** `bibliotech.py`  
**Date du bilan :** 21 octobre 2026

## 1. Objectif du TP

L'objectif de ce TP était d'améliorer la qualité du code de BiblioTech sans modifier son fonctionnement. Pour cela, j'ai repéré les défauts dans le programme, puis j'ai appliqué les principes du *Clean Code* : rendre les noms plus compréhensibles, supprimer les répétitions, simplifier les conditions, sécuriser certains traitements et faciliter la maintenance.

La méthode demandée était de procéder par petites corrections, de lancer les tests après les modifications et de conserver un historique avec Git.

## 2. Préparation du projet et utilisation de Git

J'ai travaillé dans mon dépôt GitHub `bibliotech-issilame`. J'ai récupéré les fichiers du projet BiblioTech à partir du dépôt modèle de l'enseignant, puis j'ai préparé l'environnement Python et installé les dépendances nécessaires.

J'ai effectué les modifications sur la branche `tp1/nettoyage`, afin de ne pas travailler directement sur `main`. J'ai utilisé Git pour enregistrer les modifications et envoyer le travail sur GitHub.

La dernière vérification visible confirme la création du commit `7efe208`, intitulé **« Correction finale Clean Code et simplification des commandes »**, et son envoi réussi sur `origin/tp1/nettoyage`.

## 3. Défauts repérés et corrections apportées

| Défaut constaté | Emplacement | Correction apportée | Principe appliqué |
| --- | --- | --- | --- |
| Imports peu lisibles ou inutiles | Début de `bibliotech.py` | Organisation des imports nécessaires | Lisibilité |
| Utilisation de `eval()` pour lire un prix | `load()` | Remplacement par `float()` | Sécurité et simplicité |
| Gestion d'exception trop générale | Chargement des pénalités dans `load()` | Utilisation de `except (ValueError, IndexError)` | Gestion précise des erreurs |
| Durées d'emprunt écrites directement (`21`, `7`, `3`) | Fonction d'emprunt | Création des constantes `LOAN_DAYS_BOOK`, `LOAN_DAYS_DVD` et `LOAN_DAYS_MAGAZINE` | Suppression des nombres magiques |
| Limites d'emprunt écrites directement | Fonction d'emprunt | Constantes pour les étudiants, membres premium et autres membres ; limite étudiant conservée à **5** | Lisibilité et maintenance |
| Tarifs de pénalité répétés | `ret()`, `overdue()`, `report()`, `export()` | Constantes de pénalités et fonction commune `late_fee()` | DRY : éviter les répétitions |
| Conditions longues, comme `== True` ou `!= None` | Plusieurs fonctions | Conditions simplifiées, avec `is None`, `is not None` et expressions booléennes | Lisibilité |
| Fonction d'emprunt trop imbriquée et nom peu explicite | `do_stuff()` | Création de `borrow_document()` avec des vérifications successives ; ancien nom conservé comme relais de compatibilité | Responsabilité claire et simplification |
| Recherche répétée dans plusieurs collections | `find()` | Sélection de la collection puis recherche commune | DRY |
| Boucles de comptage inutilement longues | `nb()`, `dispo()`, `report()` | Utilisation de `sum()` et de compteurs simplifiés | Concision et lisibilité |
| Ouverture et fermeture manuelles des CSV | `load()`, `save()`, `export()` | Utilisation de `with open()` | Gestion fiable des ressources |
| Risque de partager un dictionnaire entre appels | `register_plugin()` | Remplacement de `options={}` par `options=None` | Éviter les arguments mutables |
| Exception interceptée trop largement dans les plugins | `run_plugins()` | Remplacement de `except:` par `except Exception:` | Robustesse |
| Calcul d'une variable de retard manquant lors d'une correction intermédiaire | `overdue()` | Calcul de `days_late` avant son utilisation | Correction de bug |
| Fonction de commandes trop complexe | `process()` | Séparation du traitement des commandes en petites fonctions | Responsabilité unique et complexité réduite |
| Lignes de code trop longues | Plusieurs lignes | Réorganisation du code pour respecter Ruff | Convention de style |
| Absence de saut de ligne final | Fin de `bibliotech.py` | Ajout du saut de ligne | Convention de style |

## 4. Exemples de corrections expliquées

### 4.1. Remplacer les nombres magiques

Avant, le programme utilisait directement les valeurs `21`, `7` et `3` pour calculer la durée d'un emprunt. Ces nombres ne permettaient pas de comprendre immédiatement leur signification.

Après correction, j'ai utilisé des constantes explicites :

```python
LOAN_DAYS_BOOK = 21
LOAN_DAYS_DVD = 7
LOAN_DAYS_MAGAZINE = 3
```

Ainsi, les règles de durée sont plus faciles à retrouver et à modifier.

### 4.2. Éviter de répéter le calcul des pénalités

Au départ, le calcul des frais de retard était présent à plusieurs endroits du programme. Une modification de tarif aurait donc nécessité plusieurs corrections.

J'ai regroupé ce calcul dans la fonction `late_fee(days, book, member)`. Elle tient compte du type de document, du statut du membre et du plafond correspondant au prix du document. Les fonctions de retour, de retard, de rapport et d'export peuvent maintenant réutiliser le même calcul.

### 4.3. Simplifier l'emprunt d'un document

L'ancienne fonction `do_stuff()` contenait de nombreux `if` imbriqués, ce qui compliquait sa lecture. J'ai utilisé une fonction au nom plus clair, `borrow_document()`, qui vérifie progressivement les règles : existence du membre et du document, activation du compte, retards, limite d'emprunts, doublon et disponibilité.

En cas de refus, la fonction affiche le motif et s'arrête immédiatement. Le déroulement est donc plus facile à suivre.

### 4.4. Simplifier les commandes de l'application

La fonction `process()` gérait directement toutes les commandes (`list`, `members`, `borrow`, `return`, `overdue`, `report`, `export`). Ruff signalait une complexité trop élevée (`C901`).

J'ai séparé les traitements dans des fonctions plus petites et simplifié la sélection des commandes. Cela permet de modifier une commande sans alourdir la fonction principale.

### 4.5. Améliorer la gestion des fichiers

J'ai remplacé les ouvertures de fichiers suivies de `close()` par des blocs `with open()`. Python ferme ainsi automatiquement les fichiers, y compris lorsqu'une erreur survient pendant le traitement.

## 5. Vérifications et résultats

Après les corrections, j'ai lancé les outils de vérification depuis Git Bash, dans le dossier du projet et sur la branche `tp1/nettoyage`.

| Vérification | Commande | Résultat constaté |
| --- | --- | --- |
| Tests automatiques | `python -m pytest` | **21 tests réussis sur 21** (`21 passed in 3.08s`) |
| Qualité du code | `ruff check .` | **`All checks passed!`** |
| Enregistrement Git | `git commit` | Commit **`7efe208`** créé |
| Envoi sur GitHub | `git push origin tp1/nettoyage` | Envoi réussi vers la branche distante |

Ces résultats montrent que les tests fournis continuent de réussir et que Ruff ne signale plus de problème avec la configuration utilisée.

## 6. Ce que ce TP m'a appris

Ce travail m'a permis de comprendre qu'un programme peut fonctionner tout en étant difficile à lire ou à faire évoluer. J'ai appris à donner des noms plus précis aux fonctions et aux constantes, à éviter de copier plusieurs fois le même calcul, à simplifier les conditions et à utiliser les outils de contrôle de qualité.

J'ai également pratiqué le travail sur une branche Git séparée de `main`, la création de commits et l'envoi des modifications sur GitHub.

## 7. Vérifications restantes avant le rendu

Les points suivants ne sont pas confirmés par les dernières captures et doivent être vérifiés avant de remettre le TP :

- [ ] Vérifier que le tag `v0-initial` est bien présent sur GitHub.
- [ ] Vérifier les accès du binôme et de l'enseignant `Massamba07`.
- [ ] Ajouter ce fichier `SYNTHESE_TP1.md` sur la branche `tp1/nettoyage` et le pousser.
- [ ] Ouvrir une Pull Request de `tp1/nettoyage` vers `main`.
- [ ] Laisser la Pull Request ouverte pour la relecture de l'enseignant, **sans la fusionner**.

## 8. Conclusion

J'ai amélioré le code de BiblioTech en appliquant plusieurs principes du Clean Code tout en conservant le comportement attendu par les tests. À la fin de la phase de nettoyage, les **21 tests Pytest réussissent** et **Ruff ne signale plus d'erreur**. Le code est désormais plus lisible et plus facile à maintenir.

Il reste à joindre cette synthèse au dépôt et à créer la Pull Request demandée pour finaliser le rendu du TP1.
