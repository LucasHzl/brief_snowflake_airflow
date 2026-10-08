-- Fichier du mois de l'exécution Airflow, jamais du mois courant.
COPY INTO NYC_TAXI.RAW.YELLOW_TRIPDATA
FROM @NYC_TAXI.RAW.TLC_STAGE
FILES = ('yellow_tripdata_{{ logical_date.strftime("%Y-%m") }}.parquet')
FILE_FORMAT = (FORMAT_NAME = 'NYC_TAXI.RAW.PARQUET_FORMAT')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
INCLUDE_METADATA = (
    _source_file = METADATA$FILENAME,
    _loaded_at = METADATA$START_SCAN_TIME
)
ON_ERROR = ABORT_STATEMENT
FORCE = FALSE;
