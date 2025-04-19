import datetime
import logging
import os
import requests
from google.adk.agents import Agent
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('adk_agent')

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Get API keys from environment variables
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
logger.info(f"Weather API Key loaded: {'Yes' if WEATHER_API_KEY else 'No'}")
logger.info(f"Gemini API Key loaded: {'Yes' if GEMINI_API_KEY else 'No'}")

# Set the Gemini API key in the environment
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# TODO: Replace these mock events with actual Google Calendar API integration
# These are temporary mock events for demonstration purposes only
# In production, this should be replaced with:
# 1. Google Calendar API authentication
# 2. Real-time calendar event fetching
# 3. Proper event synchronization
MOCK_CALENDAR_EVENTS = [
    {
        "title": "Deep Learning Lecture",
        "start_time": "08:50",
        "end_time": "10:20",
        "day": "Monday",
        "location": "Room 101",
        "instructor": "Dr. Smith"
    },
    {
        "title": "Agentic AI Lecture",
        "start_time": "15:00",
        "end_time": "16:30",
        "day": "Monday",
        "location": "Room 203",
        "instructor": "Prof. Johnson"
    },
    {
        "title": "Machine Learning Lab",
        "start_time": "13:00",
        "end_time": "15:00",
        "day": "Wednesday",
        "location": "Lab 3",
        "instructor": "Dr. Brown"
    },
    {
        "title": "Natural Language Processing",
        "start_time": "11:00",
        "end_time": "12:30",
        "day": "Friday",
        "location": "Room 105",
        "instructor": "Prof. Davis"
    },
    {
        "title": "Agentic AI Project Report Submission",
        "start_time": "10:00",
        "end_time": "11:00",
        "day": "Saturday",
        "location": "Online",
        "instructor": "Prof. Johnson"
    },
    {
        "title": "Deep Learning Assignment Review",
        "start_time": "14:00",
        "end_time": "15:30",
        "day": "Saturday",
        "location": "Virtual Classroom",
        "instructor": "Dr. Smith"
    },
    {
        "title": "Research Paper Discussion",
        "start_time": "16:00",
        "end_time": "17:30",
        "day": "Saturday",
        "location": "Library Study Room",
        "instructor": "Dr. Brown"
    }
]

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

def get_calendar_info(query: str) -> dict:
    """Retrieves calendar information based on the query.
    
    Args:
        query (str): The query about calendar events (e.g., "What's my schedule for Monday?",
                    "When is my next lecture?", "Where is the Deep Learning class?")
        
    Returns:
        dict: status and result or error msg.
    """
    logger.info(f"Processing calendar query: {query}")
    
    try:
        # Convert query to lowercase for case-insensitive matching
        query = query.lower()
        
        # Get current day and time
        now = datetime.datetime.now()
        current_day = now.strftime("%A")
        current_time = now.strftime("%H:%M")
        
        # Initialize response
        response = {
            "status": "success",
            "events": [],
            "message": ""
        }
        
        # Handle different types of queries
        if "today" in query or current_day.lower() in query:
            # Filter events for today
            today_events = [event for event in MOCK_CALENDAR_EVENTS 
                          if event["day"].lower() == current_day.lower()]
            if today_events:
                response["events"] = today_events
                response["message"] = f"Here are your events for {current_day}:"
            else:
                response["message"] = f"You have no events scheduled for {current_day}."
                
        elif "next" in query:
            # Find next event
            all_events = sorted(MOCK_CALENDAR_EVENTS, 
                              key=lambda x: (x["day"], x["start_time"]))
            next_event = None
            for event in all_events:
                if (event["day"] == current_day and event["start_time"] > current_time) or \
                   (event["day"] != current_day):
                    next_event = event
                    break
            if next_event:
                response["events"] = [next_event]
                response["message"] = "Your next event is:"
            else:
                response["message"] = "You have no upcoming events."
                
        elif any(event["title"].lower() in query for event in MOCK_CALENDAR_EVENTS):
            # Search for specific event
            for event in MOCK_CALENDAR_EVENTS:
                if event["title"].lower() in query:
                    response["events"] = [event]
                    response["message"] = f"Here's the information about {event['title']}:"
                    break
                    
        else:
            # Return all events if no specific query
            response["events"] = MOCK_CALENDAR_EVENTS
            response["message"] = "Here are all your scheduled events:"
        
        # Format the response
        if response["events"]:
            formatted_events = []
            for event in response["events"]:
                formatted_event = (
                    f"{event['title']} "
                    f"({event['day']}, {event['start_time']}-{event['end_time']}) "
                    f"at {event['location']} with {event['instructor']}"
                )
                formatted_events.append(formatted_event)
            response["formatted_events"] = formatted_events
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_calendar_info: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error_message": f"Error retrieving calendar information: {str(e)}"
        }

root_agent = Agent(
    name="student_assistant",
    model="gemini-2.0-flash-exp",
    description=(
        "Agent to answer questions about weather and student calendar."
    ),
    instruction=(
        "I can answer your questions about weather in a city and your student calendar."
    ),
    tools=[get_weather, get_calendar_info],
)