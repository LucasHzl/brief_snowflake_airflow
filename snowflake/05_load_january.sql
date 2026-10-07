-- Chargement du fichier de janvier déjà déposé à la racine du stage.
-- Prérequis : 04_raw.sql et transfert avec ingestion/upload_file.py.
USE ROLE TRANSFORMER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE NYC_TAXI_WH;

COPY INTO NYC_TAXI.RAW.YELLOW_TRIPDATA
FROM @NYC_TAXI.RAW.TLC_STAGE
FILES = ('yellow_tripdata_2025-01.parquet')
FILE_FORMAT = (
    FORMAT_NAME = 'NYC_TAXI.RAW.PARQUET_FORMAT'
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
INCLUDE_METADATA = (
    _source_file = METADATA$FILENAME,
    _loaded_at = METADATA$START_SCAN_TIME
)
ON_ERROR = ABORT_STATEMENT
FORCE = FALSE;
