# Revue finale — 9 octobre 2026

## Correspondance avec les attendus

| Critère | Réalisation et preuve |
|---|---|
| C2 — Sources | [Fiche des trajets](fiche_trajets.md), schéma et anomalies de janvier mesurés |
| C3 — Architecture | [README](../README.md), schéma, couches, droits, stage et types RAW expliqués |
| C8 — Extraction | Scripts paramétrés, calendrier mensuel, reprises, [rejeu de février](validation_pipeline.md) |
| C9 — SQL | Deux contrôles ajoutés au contrôle fourni, [réponse métier](REPONSE.md), comparaison indépendante ci-dessous |
| C14 — Entrepôt | Scripts 01 à 04 versionnés, contrat RAW respecté, métadonnées, authentification par clé |
| C15 — Orchestration | Trois runs complets en succès, 21 tâches, 18 volumes stables au rejeu, contrôle bloquant démontré |
| C16 — Administration | [Droits et refus](validation_droits.md), [consommation mesurée](consommation.md), XS et suspension à 60 secondes |

Le dépôt GitHub est public ; sa visibilité a été vérifiée lors de la revue.

## Vérifications exécutées

- Cinq tests d'ingestion : réponses COPY et contrôle de présence RAW.
- Quatre tests Airflow dans le conteneur existant : imports, trois intervalles,
  rendu de tous les SQL, dépendances et refus de résultats faux par SQLCheckOperator.
- Contrôles de configuration locale : génération JSON, permissions 600,
  préservation d'un fichier existant et refus d'une clé de format incorrect.
- Comparaison Git avec le commit initial : aucun SQL fourni modifié ; trois SQL
  ont été ajoutés pour COPY et les deux contrôles complémentaires.
- Lecture réelle de Snowflake sous TRANSFORMER, rôles secondaires désactivés.
- Aucun lien Markdown local cassé. Aucun fichier .env, clé privée ou Parquet suivi.
  La recherche de blocs de clés privées et de jetons GitHub dans 102 versions
  de fichiers texte de l’historique ne retourne aucun résultat ; ce contrôle
  ciblé ne constitue pas une garantie exhaustive de détection des secrets.

Les tests ne remplacent pas les exécutions réelles. Aucun environnement neuf
ni clone propre n'a été lancé dans cette revue.

## Comparaison des anomalies

[verify_quality_comparison.sql](../snowflake/verify_quality_comparison.sql)
recalcule directement depuis RAW les raisons de rejet, sans utiliser FLAGGED.
La priorité des règles est conservée : un trajet reçoit la première raison
applicable. Les comptes ne sont donc pas la somme de conditions indépendantes
qui pourraient se chevaucher. Les seuils sont 180 minutes et 100 miles.

Résultat : **18 groupes comparés, 18 concordances, aucun écart**.
[Export de la comparaison](resultats/audit_quality_comparison_2026-10-09.csv).
Identifiant Snowflake : `01c79d75-0002-2b22-0002-d7060002c30e`.

| Mois | RAW | Rejetés | Valides avant dédoublonnage |
|---|---:|---:|---:|
| Janvier | 3 475 226 | 223 889 | 3 251 337 |
| Février | 3 577 543 | 272 297 | 3 305 246 |
| Mars | 4 145 257 | 319 462 | 3 825 795 |
| Total | 11 198 026 | 815 648 | 10 382 378 |

L'[audit de FCT_TRIPS](resultats/audit_final_counts_2026-10-09.csv) confirme les
mêmes volumes valides par mois, des clés distinctes et aucune clé manquante.
Les montants extrêmes positifs ne sont pas exclus par les règles fournies ; leur
impact sur les moyennes est analysé dans REPONSE.md.

## Chargements et restauration

L'[historique COPY](resultats/audit_load_history_2026-10-09.csv) contient les trois
fichiers, tous Loaded, sans erreur, avec autant de lignes lues que chargées.
[Requête reproductible](../snowflake/verify_load_history.sql), limitée aux 14 derniers jours.
Identifiant Snowflake : `01c79d75-0002-2b22-0002-d7060002c312`.
Les heures de cet export portent explicitement leur décalage UTC.

L'[export Airflow](resultats/airflow_runs_2026-10-09.csv) confirme les trois succès,
y compris janvier après restauration du seuil à 10 %. Les exécutions observées
se sont terminées le 9 octobre à 08:48:40, 08:22:40 et 08:14:12 UTC.

## Journaux et limites

Les tests Airflow émettent des avertissements du runtime : backend de secrets
Astro désactivé et import déprécié dans le provider standard. L'appel direct d'un
opérateur dans le test unitaire signale aussi l'absence de Task Runner. Ces
avertissements n'ont pas empêché les tests ni les runs ; ils ne sont pas masqués.
L'exception du contrôle à 1 % est l'échec volontaire documenté.

La prévention des recopies RAW dépend de l'historique COPY ; elle n'est pas une
politique de reprise illimitée. Les limites de 64 jours et de remplacement de
fichier sont documentées dans [chargement_raw.md](chargement_raw.md).

## Inventaire des preuves visuelles

Les six catégories de captures demandées par le brief sont présentes :

| Attendu | Capture |
|---|---|
| Trois exécutions réussies | [Vue Airflow](captures/airflow_trois_runs_success.png) |
| Graphe du DAG | [Pipeline complet](captures/airflow_janvier_pipeline_complet.png) |
| Contrôle en échec | [Contrôle bloquant](captures/controle_rejet_echec.png) |
| Historique de chargement Snowflake | [Trois fichiers chargés](captures/snowflake_historique_chargements.png) |
| Droits du rôle des outils | [Attributions TRANSFORMER](captures/snowflake_droits_transformer.png) |
| Suivi des crédits | [Consommation du warehouse](captures/snowflake_consommation_credits.png) |

La capture des droits est complétée par l'[export intégral des 36 attributions](resultats/droits_transformer_2026-10-09_1528.csv).
Le relevé de crédits complémentaire porte le total documenté à 1,176806 crédit brut ;
les deux relevés sont distingués dans [consommation.md](consommation.md).
Le dépôt conserve aussi le rejeu avant/après, les volumes finaux, l'accès refusé
et les résultats métier.
