import datetime
import logging
import os
import requests
from google.adk.agents import Agent
from google.cloud import bigquery
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('adk_agent')

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
service_account_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "service_account.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS to {service_account_path}")

# Get API keys from environment variables
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
logger.info(f"Weather API Key loaded: {'Yes' if WEATHER_API_KEY else 'No'}")
logger.info(f"Gemini API Key loaded: {'Yes' if GEMINI_API_KEY else 'No'}")

# Set the Gemini API key in the environment
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city using WeatherAPI.com.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    logger.info(f"Getting weather for city: {city}")
    
    if not WEATHER_API_KEY:
        logger.error("Weather API key not found in environment variables")
        return {
            "status": "error",
            "error_message": "Weather API key not configured. Please check your .env file."
        }
    
    try:
        # Make API request to WeatherAPI.com
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
        logger.info(f"Making API request to: {url}")
        
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse the JSON response
        data = response.json()
        logger.info(f"Weather API response received: {data}")
        
        # Extract relevant weather information
        location = data.get("location", {})
        current = data.get("current", {})
        condition = current.get("condition", {})
        
        # Format the weather report
        report = (
            f"The weather in {location.get('name', city)} is {condition.get('text', 'unknown')} "
            f"with a temperature of {current.get('temp_c', 'unknown')} degrees Celsius "
            f"({current.get('temp_f', 'unknown')} degrees Fahrenheit). "
            f"Humidity is {current.get('humidity', 'unknown')}% and "
            f"wind speed is {current.get('wind_kph', 'unknown')} km/h."
        )
        
        logger.info(f"Weather report generated: {report}")
        
        return {
            "status": "success",
            "report": report,
            "data": data
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making weather API request: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error retrieving weather information: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_weather: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error_message": f"Unexpected error retrieving weather information: {str(e)}"
        }


def search_name_in_usa_names(name: str) -> dict:
    """Searches for a name in the USA Names public dataset.
    
    This function queries the BigQuery public dataset to find information about
    how many times a specific name has been used in the United States between 1910 and 2013.
    
    Args:
        name (str): The name to search for in the dataset.
        
    Returns:
        dict: status and result or error msg.
    """
    logger.info(f"Starting search for name: '{name}' in USA Names dataset")
    try:
        # Initialize BigQuery client using Application Default Credentials
        logger.info("Initializing BigQuery client using Application Default Credentials")
        client = bigquery.Client()
        logger.info("BigQuery client initialized successfully")
        
        # Define the query to search for the name in the USA Names dataset
        query = """
        SELECT
          name,
          SUM(number) AS total_occurrences
        FROM
          `bigquery-public-data.usa_names.usa_1910_2013`
        WHERE
          LOWER(name) = LOWER(@name)
        GROUP BY
          name
        """
        logger.info(f"Query prepared: {query}")
        
        # Set up the query parameters
        logger.info(f"Setting up query parameters with name: '{name}'")
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("name", "STRING", name),
            ]
        )
        
        # Execute the query
        logger.info("Executing BigQuery query")
        start_time = datetime.datetime.now()
        query_job = client.query(query, job_config=job_config)
        
        # Wait for the query to complete
        logger.info("Waiting for query results")
        results = query_job.result()
        end_time = datetime.datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"Query executed in {execution_time:.2f} seconds")
        
        # Process the results
        logger.info("Processing query results")
        rows = list(results)
        logger.info(f"Query returned {len(rows)} rows")
        
        if rows:
            # Get the first row (there should only be one)
            row = rows[0]
            logger.info(f"Found data for name '{row.name}': {row.total_occurrences} occurrences")
            result = {
                "name": row.name,
                "total_occurrences": row.total_occurrences
            }
            
            report = (
                f"The name '{result['name']}' has been used {result['total_occurrences']} times "
                f"in the United States between 1910 and 2013."
            )
        else:
            logger.info(f"No data found for name '{name}'")
            result = {
                "name": name,
                "total_occurrences": 0
            }
            
            report = f"The name '{name}' was not found in the USA Names dataset."
        
        logger.info("Name search completed successfully")
        return {
            "status": "success",
            "report": report,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error in search_name_in_usa_names: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error_message": f"Error searching for name in USA Names dataset: {str(e)}"
        }


root_agent = Agent(
    name="weather_name_agent",
    model="gemini-2.0-flash-exp",
    description=(
        "Agent to answer questions about weather in a city and name popularity data."
    ),
    instruction=(
        "I can answer your questions about weather in a city and provide information about name popularity in the United States."
    ),
    tools=[get_weather, search_name_in_usa_names],
)