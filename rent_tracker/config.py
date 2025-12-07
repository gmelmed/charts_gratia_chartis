"""Configuration constants for rent tracker pipeline."""

# Region mapping for metros
REGION_MAP = {
    "New York, NY": "Northeast",
    "Los Angeles, CA": "West",
    "Chicago, IL": "Midwest",
    "Dallas, TX": "Southwest",
    "Houston, TX": "Southwest",
    "Atlanta, GA": "Southeast",
    "Washington, DC": "Northeast",
    "Philadelphia, PA": "Northeast",
    "Miami, FL": "Southeast",
    "Phoenix, AZ": "Southwest",
    "Boston, MA": "Northeast",
    "Riverside, CA": "West",
    "San Francisco, CA": "West",
    "Detroit, MI": "Midwest",
    "Seattle, WA": "West",
    "Minneapolis, MN": "Midwest",
    "Tampa, FL": "Southeast",
    "San Diego, CA": "West",
    "Denver, CO": "West",
    "Baltimore, MD": "Northeast",
    "Orlando, FL": "Southeast",
    "Charlotte, NC": "Southeast",
    "St. Louis, MO": "Midwest",
    "San Antonio, TX": "Southwest",
    "Portland, OR": "West",
    "Austin, TX": "Southwest",
    "Pittsburgh, PA": "Northeast",
    "Sacramento, CA": "West",
    "Las Vegas, NV": "West",
    "Cincinnati, OH": "Midwest",
    "Kansas City, MO": "Midwest",
    "Columbus, OH": "Midwest",
    "Indianapolis, IN": "Midwest",
    "Nashville, TN": "Southeast",
    "Cleveland, OH": "Midwest",
    "San Jose, CA": "West",
    "Virginia Beach, VA": "Southeast",
    "Jacksonville, FL": "Southeast",
    "Providence, RI": "Northeast",
    "Milwaukee, WI": "Midwest",
    "Raleigh, NC": "Southeast",
    "Oklahoma City, OK": "Southwest",
    "Louisville, KY": "Southeast",
    "Richmond, VA": "Southeast",
    "Memphis, TN": "Southeast",
    "Salt Lake City, UT": "West",
    "Birmingham, AL": "Southeast",
    "Grand Rapids, MI": "Midwest",
    "Buffalo, NY": "Northeast",
    "Hartford, CT": "Northeast"
}

# File paths
TOP_METROS_PATH = 'data/top_metros.json'  # CHANGED: removed rent_tracker/
USCITIES_PATH = 'data/uscities.csv'        # CHANGED: removed rent_tracker/

# Raw data output paths
RAW_DATA_DIR = 'data/raw/'                 # CHANGED: removed rent_tracker/
HOMEBUILDING_RAW = RAW_DATA_DIR + 'homebuilding_raw.csv'
HOMEBUILDING_RAW_TOP = RAW_DATA_DIR + 'homebuilding_raw_top50.csv'
POPULATION_RAW = RAW_DATA_DIR + 'population.csv'
CITIES_RAW = RAW_DATA_DIR + 'cities.csv'
ZILLOW_COUNTY_RAW = RAW_DATA_DIR + 'zillow_county_raw.csv'
ZILLOW_METRO_RAW = RAW_DATA_DIR + 'zillow_metro_raw.csv'
ZILLOW_AFFORDABILITY_RAW = RAW_DATA_DIR + 'zillow_affordability_raw.csv'

# Processed data output paths
PROCESSED_DATA_DIR = 'data/processed/'     # CHANGED: removed rent_tracker/
HOMEBUILDING_CLEAN = PROCESSED_DATA_DIR + 'homebuilding_clean.csv'
HOMEBUILDING_MOST_RECENT_ALL = PROCESSED_DATA_DIR + 'homebuilding_most_recent_all.csv'
ZORI_COUNTY_CLEAN = PROCESSED_DATA_DIR + 'zori_county_clean.csv'
ZORI_METRO_LONG = PROCESSED_DATA_DIR + 'zori_metro_long.csv'
ZORI_METRO_MOST_RECENT = PROCESSED_DATA_DIR + 'zori_metro_most_recent.csv'
ZORI_METRO_BUILDING_MOST_RECENT = PROCESSED_DATA_DIR + 'zori_metro_homebuilding_most_recent.csv'
ZORI_AFFORDABILITY_LONG = PROCESSED_DATA_DIR + 'zori_affordability_long.csv'
ZORI_AFFORDABILITY_MOST_RECENT = PROCESSED_DATA_DIR + 'zori_affordability_most_recent.csv'

# External data URLs
CENSUS_BASE_URL_2024 = 'https://www.census.gov/construction/bps/xls/cbsamonthly_{}.xls'
CENSUS_BASE_URL_PRE2024 = 'https://www.census.gov/construction/bps/xls/msamonthly_{}.xls'
POPULATION_URL = "https://www2.census.gov/programs-surveys/popest/tables/2020-2024/metro/totals/cbsa-met-est2024-pop.xlsx"
ZILLOW_COUNTY_URL = "https://files.zillowstatic.com/research/public_csvs/zori/County_zori_uc_sfrcondomfr_sm_month.csv?t=1734717130"
ZILLOW_METRO_URL = "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv?t=1734717130"
ZILLOW_AFFORDABILITY_URL = "https://files.zillowstatic.com/research/public_csvs/new_renter_affordability/Metro_new_renter_affordability_uc_sfrcondomfr_sm_sa_month.csv?t=1765129851"

# Scraping parameters
YEARS_BACK = 6
REQUEST_DELAY_MIN = 2  # seconds
REQUEST_DELAY_MAX = 4  # seconds
REQUEST_TIMEOUT = 10  # seconds

# User agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'