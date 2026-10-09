# Démonstration technique — 15 minutes

## Déroulé

| Temps | Manipulation et preuve |
|---|---|
| 0–2 min | Exécuter snowflake/verify_permissions.sql : droits TRANSFORMER, lecture autorisée, refus hors périmètre avec rôles secondaires désactivés |
| 2–4 min | Afficher les trois runs de nyc_taxi_monthly, leur date logique et le graphe avec les trois couches et les contrôles |
| 4–6 min | Exécuter verify_pipeline_counts.sql, rejouer février avec Clear, relancer le comptage des 18 objets |
| 6–9 min | Abaisser temporairement max_rejection_rate_pct de 10 à 1 dans le DAG, attendre sa prise en compte puis rejouer janvier ; montrer le log (True, False) et les descendants upstream_failed |
| 9–11 min | Rétablir 10, attendre la prise en compte et utiliser Clear sur janvier, y compris les tâches bloquées ; vérifier le retour en succès |
| 11–14 min | Exécuter business_analysis.sql : demande à Midtown Center, ventilation par paiement, limites des montants ; montrer verify_quality_comparison.sql |
| 14–15 min | Présenter verify_credits.sql avec un rôle d'administration autorisé et expliquer le périmètre du relevé |

Les fichiers SQL de cette table sont dans snowflake/. Les preuves déjà enregistrées
sont accessibles depuis VALIDATION.md. Pour le rejeu de février, l'identifiant du
run commence par scheduled__2025-03-01 ; pour janvier, par scheduled__2025-02-01.
La date logique représente le début du mois, l'identifiant planifié sa borne finale.
Ne pas utiliser un déclenchement daté du jour pour traiter un mois historique.

Les anciens résultats MARTS restent présents pendant un échec : le contrôle bloque
leur actualisation, il ne supprime pas une publication antérieure. Avant de terminer,
vérifier le seuil à 10 dans le fichier, les trois runs en succès et l'absence de
modification involontaire à committer. Arrêter Airflow avec astro dev stop après
la session ; le warehouse se suspend automatiquement après son inactivité.

## Choix à expliquer

- **Pourquoi ces droits ?** TRANSFORMER travaille dans les quatre schémas de NYC_TAXI
  et utilise un warehouse. Il ne reçoit pas les droits d'administration du compte.
  Les attributions sont portées par le rôle ; AIRFLOW_SVC reçoit ce rôle.
- **Pourquoi un stage ?** PUT transfère un fichier vers un stockage accessible à
  Snowflake. COPY INTO lit ce fichier pour remplir une table et tracer son origine.
- **Pourquoi la date logique ?** Un rejeu en octobre doit charger le même fichier
  de janvier. La date du jour ne désigne pas la période traitée.
- **Pourquoi cet ordre ?** RAW alimente les vues STAGING, puis FLAGGED et ENRICHED.
  Les dimensions doivent exister avant les faits ; les agrégats utilisent les faits.
  Les contrôles bloquent les transformations dépendantes en cas d'anomalie.
- **Que change un quatrième mois ?** Le périmètre est volontairement borné à trois
  mois : étendre source_url, end_date, end_month, les tests de calendrier et les
  vérifications métier, puis vérifier la publication du fichier et les types RAW.
  Le générateur de DIM_DATE fourni doit aussi couvrir toute la période.
- **Que signifie rejouable ?** COPY reconnaît les fichiers chargés pendant sa fenêtre
  de suivi ; DELETE/INSERT remplace un mois dans une transaction par tâche, et les
  tables d'analyse sont recalculées. Les contrôles de volumes constatent la stabilité
  sur le rejeu testé, sans garantir toutes les situations futures.
- **Que représente un montant ?** Le total enregistré comprend des composantes de
  facturation ; il ne mesure pas un bénéfice net ni nécessairement un encaissement.
  Les catégories No charge et Dispute ainsi que les valeurs extrêmes l'illustrent.
- **Pourquoi les anomalies ne sont-elles pas supprimées dans RAW ?** La source est
  conservée pour l'audit ; FLAGGED attribue une raison, ENRICHED retient les valides.
