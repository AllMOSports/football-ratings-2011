import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import pandas as pd
from datetime import datetime, date, timedelta
import time
 
# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
 
SEASON_START  = date(2010, 8, 1)
SEASON_END    = date(2010, 12, 15)
BASE_URL      = "https://www.mshsaa.org/activities/scoreboard.aspx?alg=19&date={}"
MAX_POINTS    = 100
OUTPUT_PATH   = "football_ratings_2010.json"
CSV_PATH      = "football_scoreboard_2010.csv"
CLASSIFICATIONS_PATH  = "classifications.json"
SCHOOLS_CSV           = "mshsaa_schools.csv"
ITERATIONS            = 1000
LEARNING_RATE         = 0.1
COMPETITIVE_THRESHOLD = 40
 
# ---------------------------------------------------------------------------
# MANUAL GAMES (not listed on MSHSAA Scoreboard)
# ---------------------------------------------------------------------------
# Add any games missing from the MSHSAA scoreboard here.
# Format: ("YYYY-MM-DD", "Team 1 Name", score1, "Team 2 Name", score2)
# Team names must match exactly the names in classifications.json.
 
MANUAL_GAMES = [
    ("2011-08-26", "Portageville", 0, "Caruthersville", 58),
    ("2011-09-09", "Portageville", 48, "Charleston", 21),
    ("2011-09-16", "Portageville", 24, "Malden", 41),
    ("2011-09-23", "Portageville", 22, "Kennett", 40),
    ("2011-09-30", "Portageville", 30, "Scott City", 31),
    ("2011-10-07", "Portageville", 46, "East Prairie", 38),
    ("2011-08-26", "St. Vincent", 13, "Central (Park Hills)", 28),
    ("2011-09-23", "St. Vincent", 35, "St. Pius X (Festus)", 21),
    ("2011-10-04", "St. Vincent", 35, "Grandview", 20),
    ("2011-10-21", "St. Vincent", 7, "Valle Catholic", 48),
    ("2011-09-16", "Valle Catholic", 42, "Grandview (Hillsboro)", 14),
    ("2011-10-07", "Valle Catholic", 62, "St. Pius X (Festus)", 0),
    ("2011-09-23", "Greenfield", 14, "Hogan Prep Academy Charter", 35),
    ("2011-08-26", "Sacred Heart", 18, "Milan", 49),
    ("2011-09-16", "Sacred Heart", 54, "Wentworth Military Academy", 0),
    ("2011-10-07", "Sacred Heart", 32, "Rich Hill with Hume", 0),
    ("2011-10-07", "Tipton", 26, "South Callaway", 20),
    ("2011-09-09", "Windsor", 30, "St. Mary's (Independence)", 0),
    ("2011-10-08", "Windsor", 36, "Wentworth Military Academy", 0),
    ("2011-09-30", "Concordia", 32, "Wellington-Napoleon", 48),
    ("2011-09-09", "Crest Ridge", 0, "Wellington-Napoleon", 46),
    ("2011-09-16", "Santa Fe", 0, "Wellington-Napoleon", 39),
    ("2011-10-06", "University Academy Charter", 24, "Pembroke Hill", 48),
    ("2011-10-15", "University Academy Charter", 48, "Drexel with Miami (Amoret)", 28),
    ("2011-10-28", "University Academy Charter", 21, "Midway", 20),
    ("2011-09-02", "Louisiana", 34, "Highland", 6),
    ("2011-10-14", "Louisiana", 13, "South Shelby", 48),
    ("2011-10-28", "Louisiana", 36, "Van-Far", 8),
    ("2011-10-27", "Paris", 21, "South Shelby", 44),
    ("2011-08-26", "South Shelby", 20, "Trenton", 0),
    ("2011-09-02", "South Shelby", 33, "Mark Twain", 12),
    ("2011-09-09", "South Shelby", 0, "Macon", 52),
    ("2011-09-16", "South Shelby", 6, "Clark County", 41),
    ("2011-09-30", "South Shelby", 14, "Palmyra", 28),
    ("2011-10-07", "South Shelby", 34, "Highland", 32),
    ("2011-10-21", "South Shelby", 51, "Van-Far", 6),
    ("2011-10-27", "South Shelby", 44, "Paris", 21),
    ("2011-08-26", "Van-Far", 6, "Orchard Farm", 47),
    ("2011-09-16", "Van-Far", 24, "Winfield", 29),
    ("2011-09-23", "Van-Far", 30, "Wright City", 44),
    ("2011-08-26", "Knox County", 18, "Highland", 6),
    ("2011-09-09", "Knox County", 54, "North Shelby", 0),
    ("2011-09-16", "Knox County", 48, "Fayette", 13),
    ("2011-09-23", "Knox County", 16, "Schuyler County", 34),
    ("2011-10-07", "Knox County", 6, "Milan", 41),
    ("2011-10-14", "Knox County", 6, "Scotland County", 35),
    ("2011-10-21", "Knox County", 44, "North Shelby", 0),
    ("2011-10-28", "Knox County", 34, "Schuyler County", 13),
    ("2011-09-09", "North Shelby", 6, "Knox County", 54),
    ("2011-09-16", "North Shelby", 0, "Milan", 74),
    ("2011-09-30", "North Shelby", 14, "Schuyler County", 40),
    ("2011-10-07", "North Shelby", 28, "Scotland County", 69),
    ("2011-10-14", "North Shelby", 0, "Schuyler County", 47),
    ("2011-10-21", "North Shelby", 0, "Knox County", 44),
    ("2011-10-27", "North Shelby", 6, "Scotland County", 50),
    ("2011-09-02", "Schuyler County", 0, "Milan", 34),
    ("2011-10-20", "Schuyler County", 14, "Scotland County", 28),
    ("2011-09-09", "Scotland County", 18, "Highland", 34),
    ("2011-09-30", "Scotland County", 0, "Milan", 54),
    ("2011-10-14", "Scotland County", 35, "Knox County", 6),
    ("2011-10-27", "Scotland County", 50, "North Shelby", 6),
    ("2011-08-26", "Fayette", 13, "South Callaway", 41),
    ("2011-10-21", "Marceline", 6, "Milan", 7),
    ("2011-09-09", "Milan", 14, "Palmyra", 7),
    ("2011-09-23", "Milan", 35, "Braymer", 15),
    ("2011-10-14", "Milan", 35, "Princeton with Mercer", 16),
    ("2011-10-21", "Milan", 7, "Marceline", 6),
    ("2011-10-28", "Milan", 49, "Putnam County", 14),
    ("2011-10-14", "Orrick", 12, "Wellington-Napoleon", 53),
    ("2011-10-27", "Orrick", 28, "Wentworth Military Academy", 0),
    ("2011-08-26", "Wellington-Napoleon", 53, "Lathrop", 14),
    ("2011-09-23", "Wellington-Napoleon", 55, "St. Paul Lutheran (Concordia)", 20),
    ("2011-10-07", "Wellington-Napoleon", 53, "Sweet Springs with Malta Bend", 14),
    ("2011-10-14", "Wellington-Napoleon", 53, "Orrick", 12),
    ("2011-10-21", "Wellington-Napoleon", 60, "Wentworth Military Academy", 6),
    ("2011-10-27", "Wellington-Napoleon", 54, "St. Mary's (Independence)", 6),
    ("2011-09-16", "Gallatin", 30, "Maysville", 7),
    ("2011-10-27", "Gallatin", 26, "South Harrison", 42),
    ("2011-09-23", "South Harrison", 36, "Maysville", 7),
    ("2011-09-16", "Maysville", 7, "Gallatin", 30),
    ("2011-08-26", "Charleston", 27, "Kennett", 22),
    ("2011-09-16", "East Prairie", 13, "Kennett", 28),
    ("2011-09-30", "Malden", 75, "Kennett", 59),
    ("2011-09-03", "St. Pius X (Festus)", 6, "Soldan International Studies", 53),
    ("2011-09-09", "St. Pius X (Festus)", 15, "Grandview (Hillsboro)", 28),
    ("2011-10-07", "Brentwood", 21, "North Callaway", 26),
    ("2011-09-16", "Grandview (Hillsboro)", 14, "Valle Catholic", 42),
    ("2011-10-14", "Grandview (Hillsboro)", 21, "Principia", 28),
    ("2011-09-16", "Principia", 14, "Lutheran South", 41),
    ("2011-10-01", "Principia", 0, "Lutheran North", 41),
    ("2011-09-24", "Lift for Life Academy Charter", 32, "Beaumont", 0),
    ("2011-10-14", "Lift for Life Academy Charter", 22, "Transportation and Law", 6),
    ("2011-10-22", "Lift for Life Academy Charter", 20, "Carnahan", 30),
    ("2011-10-28", "Lift for Life Academy Charter", 6, "Maplewood-Richmond Hts.", 75),
    ("2011-08-26", "Maplewood-Richmond Hts.", 35, "MICDS", 36),
    ("2011-09-23", "Maplewood-Richmond Hts.", 31, "Central (Park Hills)", 6),
    ("2011-10-01", "Maplewood-Richmond Hts.", 52, "Perryville", 0),
    ("2011-10-15", "Maplewood-Richmond Hts.", 48, "Carnahan", 8),
    ("2011-10-21", "Maplewood-Richmond Hts.", 54, "Transportation and Law", 7),
    ("2011-10-27", "Maplewood-Richmond Hts.", 75, "Lift for Life Academy Charter", 6),
    ("2011-08-26", "Cuba", 6, "St. James", 43),
    ("2011-09-16", "Cuba", 6, "South Callaway", 48),
    ("2011-08-26", "Lamar", 34, "Carl Junction", 6),
    ("2011-09-02", "Lamar", 40, "Aurora", 19),
    ("2011-09-30", "Lamar", 21, "Cassville", 49),
    ("2011-10-14", "Blair Oaks", 19, "South Callaway", 45),
    ("2011-09-02", "Hermann", 26, "St. James", 32),
    ("2011-09-23", "Hermann", 34, "Owensville", 54),
    ("2011-10-27", "Hermann", 0, "South Callaway", 52),
    ("2011-10-21", "Montgomery County", 14, "South Callaway", 41),
    ("2011-09-02", "South Callaway", 34, "Hallsville", 7),
    ("2011-09-09", "South Callaway", 28, "North Callaway", 0),
    ("2011-09-23", "South Callaway", 50, "Southern Boone", 28),
    ("2011-09-30", "South Callaway", 39, "Orchard Farm", 3),
    ("2011-10-07", "South Callaway", 20, "Tipton", 26),
    ("2011-09-02", "Hallsville", 7, "South Callaway", 34),
    ("2011-09-16", "Hallsville", 12, "North Callaway", 37),
    ("2011-10-07", "Hallsville", 40, "Winfield", 0),
    ("2011-09-30", "Palmyra", 28, "South Shelby", 14),
    ("2011-09-29", "Carrollton", 6, "Hogan Prep Academy Charter", 40),
    ("2011-10-14", "Hogan Prep Academy Charter", 39, "Lathrop", 29),
    ("2011-10-27", "Central (New Madrid County)", 0, "Kennett", 25),
    ("2011-10-14", "Dexter", 68, "Kennett", 20),
    ("2011-10-21", "Fredericktown", 63, "Kennett", 14),
    ("2011-10-07", "Kennett", 0, "Sikeston", 56),
    ("2011-10-01", "Ste. Genevieve", 21, "John Burroughs", 41),
    ("2011-08-27", "Confluence Prep Academy Charter", 12, "Soldan International Studies", 52),
    ("2011-09-03", "Confluence Prep Academy Charter", 30, "Wentworth Military Academy", 0),
    ("2011-08-27", "John Burroughs", 37, "Pembroke Hill", 30),
    ("2011-09-10", "John Burroughs", 20, "MICDS", 45),
    ("2011-09-17", "John Burroughs", 42, "Windsor (Imperial)", 18),
    ("2011-09-24", "John Burroughs", 53, "Lutheran North", 16),
    ("2011-10-01", "John Burroughs", 41, "Ste. Genevieve", 21),
    ("2011-10-22", "John Burroughs", 45, "Imagine College Prep Charter", 12),
    ("2011-09-17", "Priory", 14, "Lutheran North", 49),
    ("2011-10-15", "Priory", 42, "Imagine College Prep Charter", 32),
    ("2011-08-26", "Cardinal Ritter", 14, "St. Dominic", 27),
    ("2011-09-16", "Cardinal Ritter", 12, "Duchesne", 7),
    ("2011-10-21", "Cardinal Ritter", 26, "Lutheran North", 28),
    ("2011-10-28", "Cardinal Ritter", 20, "Trinity Catholic", 36),
    ("2011-08-27", "Lutheran North", 42, "Clayton", 14),
    ("2011-09-03", "Lutheran North", 18, "Westminster Christian Academy", 7),
    ("2011-10-14", "Lutheran North", 44, "Trinity Catholic", 31),
    ("2011-09-03", "Bowling Green", 7, "Miller Career Academy", 68),
    ("2011-09-16", "Orchard Farm", 19, "Southern Boone", 56),
    ("2011-10-14", "Orchard Farm", 42, "Wright City", 0),
    ("2011-10-21", "Orchard Farm", 28, "Winfield", 21),
    ("2011-10-07", "Winfield", 0, "Hallsville", 40),
    ("2011-10-27", "Winfield", 20, "Wright City", 13),
    ("2011-10-14", "Wright City", 0, "Orchard Farm", 42),
    ("2011-09-23", "Missouri Military Academy", 42, "Wentworth Military Academy", 0),
    ("2011-10-27", "North Callaway", 38, "Southern Boone", 32),
    ("2011-10-14", "Osage", 53, "St. James", 7),
    ("2011-09-02", "Owensville", 6, "Sullivan", 44),
    ("2011-09-16", "Owensville", 0, "St. Clair", 28),
    ("2011-09-30", "Owensville", 33, "Pacific", 22),
    ("2011-10-07", "Owensville", 28, "Union", 68),
    ("2011-10-27", "Owensville", 80, "St. James", 75),
    ("2011-09-23", "Salem", 6, "Mountain Grove", 7),
    ("2011-10-20", "Salem", 43, "St. James", 27),
    ("2011-08-26", "St. James", 43, "Cuba", 6),
    ("2011-09-09", "St. James", 12, "Union", 48),
    ("2011-09-16", "St. James", 39, "Cabool", 13),
    ("2011-09-23", "St. James", 21, "Pacific", 24),
    ("2011-09-30", "St. James", 0, "St. Clair", 49),
    ("2011-10-07", "St. James", 14, "Sullivan", 41),
    ("2011-09-23", "Mountain Grove", 7, "Salem", 6),
    ("2011-09-09", "Aurora", 18, "Carl Junction", 13),
    ("2011-09-16", "Aurora", 7, "Cassville", 21),
    ("2011-10-07", "Cassville", 24, "Carl Junction", 10),
    ("2011-08-26", "Clinton", 67, "Northeast (Kansas City)", 8),
    ("2011-08-26", "Central (Kansas City)", 2, "Benton", 40),
    ("2011-09-02", "Central (Kansas City)", 0, "Liberty North", 48),
    ("2011-09-16", "Central (Kansas City)", 16, "East (Kansas City)", 6),
    ("2011-09-22", "Central (Kansas City)", 46, "Northeast (Kansas City)", 8),
    ("2011-09-30", "Central (Kansas City)", 12, "Washington", 30),
    ("2011-10-21", "Central (Kansas City)", 6, "Pembroke Hill", 42),
    ("2011-09-16", "Pembroke Hill", 53, "Northeast (Kansas City)", 0),
    ("2011-10-01", "East (Kansas City)", 50, "Wentworth Military Academy", 0),
    ("2011-10-20", "East (Kansas City)", 64, "Northeast (Kansas City)", 6),
    ("2011-10-01", "Oak Grove", 29, "Grain Valley", 20),
    ("2011-09-09", "Cameron", 25, "Grain Valley", 29),
    ("2011-08-26", "Sikeston", 14, "Gateway", 34),
    ("2011-09-23", "Sikeston", 35, "Jackson", 9),
    ("2011-09-09", "North County", 7, "Jackson", 14),
    ("2011-09-30", "North County", 65, "Windsor (Imperial)", 37),
    ("2011-09-09", "Affton", 2, "Clayton", 49),
    ("2011-09-16", "Affton", 21, "Normandy Collaborative", 34),
    ("2011-09-23", "Affton", 6, "McCluer South-Berkeley", 54),
    ("2011-10-08", "Affton", 14, "Jennings", 52),
    ("2011-10-21", "Affton", 7, "Windsor (Imperial)", 14),
    ("2011-09-02", "Gateway", 47, "Carnahan", 0),
    ("2011-09-17", "Gateway", 50, "Beaumont", 0),
    ("2011-10-07", "Gateway", 15, "Hickman", 27),
    ("2011-10-15", "Gateway", 30, "Miller Career Academy", 14),
    ("2011-10-22", "Gateway", 35, "Roosevelt", 28),
    ("2011-09-08", "Miller Career Academy", 78, "Beaumont", 0),
    ("2011-09-23", "Miller Career Academy", 44, "Sumner", 6),
    ("2011-10-06", "Miller Career Academy", 8, "De Smet Jesuit", 29),
    ("2011-10-29", "Miller Career Academy", 30, "Roosevelt", 12),
    ("2011-08-27", "Roosevelt", 8, "Imagine College Prep Charter", 6),
    ("2011-09-02", "Roosevelt", 6, "Chaminade College Prep", 54),
    ("2011-09-17", "Roosevelt", 38, "Soldan International Studies", 33),
    ("2011-10-01", "Roosevelt", 26, "Beaumont", 7),
    ("2011-10-14", "Roosevelt", 16, "St. Mary's South Side", 37),
    ("2011-09-10", "Soldan International Studies", 6, "Jennings", 38),
    ("2011-10-01", "Soldan International Studies", 46, "Carnahan", 6),
    ("2011-10-08", "Soldan International Studies", 43, "Transportation and Law", 0),
    ("2011-10-22", "Soldan International Studies", 64, "Beaumont", 8),
    ("2011-09-02", "Vashon", 22, "Union", 63),
    ("2011-09-30", "Vashon", 22, "Jackson", 14),
    ("2011-09-02", "Clayton", 14, "St. Francis Borgia", 31),
    ("2011-09-24", "Clayton", 18, "Jennings", 42),
    ("2011-10-01", "Clayton", 0, "Normandy Collaborative", 48),
    ("2011-10-06", "Clayton", 28, "Westminster Christian Academy", 17),
    ("2011-10-14", "Clayton", 22, "University City", 56),
    ("2011-10-27", "Clayton", 7, "MICDS", 35),
    ("2011-10-22", "MICDS", 50, "University City", 18),
    ("2011-09-09", "University City", 25, "Parkway North", 20),
    ("2011-09-16", "University City", 27, "Parkway Central", 57),
    ("2011-09-24", "University City", 30, "Seckman", 34),
    ("2011-10-07", "University City", 56, "Clayton", 22),
    ("2011-10-15", "Jennings", 8, "Westminster Christian Academy", 14),
    ("2011-10-28", "Jennings", 42, "St. Charles", 20),
    ("2011-09-16", "St. Charles", 13, "St. Charles West", 49),
    ("2011-10-21", "St. Charles", 33, "Westminster Christian Academy", 30),
    ("2011-09-24", "Westminster Christian Academy", 6, "Trinity Catholic", 37),
    ("2011-10-07", "St. Charles West", 36, "Imagine College Prep Charter", 12),
    ("2011-10-14", "St. Charles West", 21, "St. Francis Borgia", 28),
    ("2011-10-21", "St. Charles West", 21, "St. Dominic", 0),
    ("2011-10-27", "St. Dominic", 14, "St. Francis Borgia", 27),
    ("2011-09-21", "St. Francis Borgia", 27, "St. Dominic", 14),
    ("2011-09-07", "St. Francis Borgia", 0, "Duchesne", 13),
    ("2011-10-07", "Sullivan", 41, "St. James", 14),
    ("2011-10-21", "Webb City", 56, "McDonald County", 19),
    ("2011-10-27", "Webb City", 48, "Carl Junction", 7),
    ("2011-10-27", "Grain Valley", 29, "Harrisonville", 49),
    ("2011-09-02", "Harrisonville", 20, "Hazelwood West", 0),
    ("2011-10-27", "Harrisonville", 49, "Grain Valley", 29),
    ("2011-10-21", "Jackson", 8, "Seckman", 7),
    ("2011-09-16", "Seckman", 35, "Parkway West", 0),
    ("2011-09-30", "Seckman", 19, "Parkway North", 24),
    ("2011-08-27", "Chaminade College Prep", 47, "Riverview Gardens", 32),
    ("2011-09-02", "Chaminade College Prep", 54, "Roosevelt", 6),
    ("2011-10-15", "Parkway Central", 26, "Parkway North", 7),
    ("2011-09-16", "Parkway North", 35, "Timberland", 17),
    ("2011-10-06", "Parkway North", 35, "Parkway West", 7),
    ("2011-09-03", "Hazelwood East", 12, "De Smet Jesuit", 14),
    ("2011-09-17", "Hazelwood East", 34, "Hazelwood West", 10),
    ("2011-09-24", "Hazelwood East", 36, "Hazelwood Central", 18),
    ("2011-10-08", "Hazelwood East", 8, "Ritenour", 16),
    ("2011-10-22", "Hazelwood East", 64, "Riverview Gardens", 44),
    ("2011-10-29", "Hazelwood East", 37, "Normandy Collaborative", 14),
    ("2011-10-01", "Normandy Collaborative", 48, "Clayton", 0),
    ("2011-10-15", "Normandy Collaborative", 38, "Riverview Gardens", 18),
    ("2011-09-09", "Riverview Gardens", 12, "Ritenour", 53),
    ("2011-09-24", "Riverview Gardens", 14, "Hazelwood West", 28),
    ("2011-10-01", "Riverview Gardens", 0, "Hazelwood Central", 28),
    ("2011-10-22", "Riverview Gardens", 44, "Hazelwood East", 64),
    ("2011-08-26", "Vianney", 33, "Ritenour", 40),
    ("2011-09-23", "Camdenton", 9, "Kickapoo", 15),
    ("2011-08-26", "Waynesville", 10, "Kickapoo", 20),
    ("2011-09-30", "Central (Springfield)", 40, "Glendale", 47),
    ("2011-10-27", "Lee's Summit", 34, "Ruskin", 8),
    ("2011-09-30", "Ruskin", 24, "Central (St. Joseph)", 45),
    ("2011-08-26", "De Smet Jesuit", 28, "Hazelwood Central", 0),
    ("2011-10-21", "Christian Brothers College", 16, "Lafayette (Wildwood)", 7),
    ("2011-10-21", "Lafayette (Wildwood)", 7, "Christian Brothers College", 16),
    ("2011-10-21", "Hazelwood Central", 14, "Ritenour", 8),
    ("2011-10-29", "Hazelwood Central", 41, "Hazelwood West", 6),
    ("2011-09-02", "Hazelwood West", 0, "Harrisonville", 20),
    ("2011-09-09", "Hazelwood West", 9, "Hickman", 27),
    ("2011-10-14", "Hazelwood West", 8, "Ritenour", 56),
    ("2011-10-15", "Ritenour", 56, "Hazelwood West", 8),
    ("2011-09-02", "Francis Howell North", 0, "Ft. Zumwalt West", 52),
    ("2011-10-14", "Ft. Zumwalt West", 42, "Hickman", 12),
    ("2011-10-28", "Ft. Zumwalt West", 28, "Troy Buchanan", 7),
    ("2011-09-10", "Hickman", 27, "Hazelwood West", 9),
    ("2011-10-21", "Hickman", 33, "Troy Buchanan", 0),
    ("2011-10-20", "Blue Springs", 30, "Liberty", 21),
    ("2011-10-20", "Liberty", 21, "Blue Springs", 30),
]
 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.mshsaa.org/"
}
 
# ---------------------------------------------------------------------------
# CLASSIFICATIONS
# ---------------------------------------------------------------------------
 
def load_classifications(path=CLASSIFICATIONS_PATH):
    """Return team_to_class and team_to_district dicts keyed by school name."""
    with open(path) as f:
        data = json.load(f)
    team_to_class    = {}
    team_to_district = {}
    for entry in data["teams"]:
        school = entry["school"]
        team_to_class[school]    = entry["classification"]
        team_to_district[school] = entry["district"]
    return team_to_class, team_to_district
 
 
# ---------------------------------------------------------------------------
# NAME RESOLUTION
# ---------------------------------------------------------------------------
 
def build_id_to_classname(team_to_class, schools_csv=SCHOOLS_CSV):
    """
    Build { school_id_str : classification_name } by exact-matching
    mshsaa_schools.csv names to classifications.json names after stripping
    the ' High School' suffix. No fuzzy matching used.
 
    MANUAL_OVERRIDES covers the 21 schools whose mshsaa_schools.csv name
    does not match their classifications.json name. IDs were looked up
    directly from the MSHSAA scoreboard pages.
    """
    MANUAL_OVERRIDES = {
        "271": "Clopton with Elsberry",
        "331": "King City with Pattonsburg",
        "126": "Lockwood with Golden City",
        "421": "Princeton with Mercer",
        "424": "Rich Hill with Hume",
        "431": "Salisbury",
        "435": "Scott City",
        "443": "Skyline",
        "193": "Slater",
        "194": "Smith-Cotton",
        "197": "South Callaway",
        "549": "St. Mary's South Side",
        "463": "Stockton",
        "207": "Sullivan",
        "208": "Sumner",
        "469": "Sweet Springs with Malta Bend",
        "198": "Truman",
        "479": "University Academy Charter",
        "204": "Van Horn",
        "206": "Vashon",
        "20": "Appleton City with Montrose",
        "275": "Drexel with Miami (Amoret)",
        "575": "Renaissance Academy Charter",
        "172": "St. James",
        "35": "DeSoto with Kingston",
        "917": "Father Tolton with Calvary Lutheran",
        "342": "Liberal with Bronaugh",
        "776": "Transportation and Law with Beaumont",
        "483": "Van-Far with Community",
    }
 
    df = pd.read_csv(schools_csv)
    known_class_names = set(team_to_class.keys())
 
    id_to_classname = {}
    for _, row in df.iterrows():
        full_name = row["school_name"]
        sid       = str(row["school_id"])
        stripped  = full_name.replace(" High School", "").strip()
 
        if stripped in known_class_names:
            id_to_classname[sid] = stripped
        elif full_name in known_class_names:
            id_to_classname[sid] = full_name
 
    # Apply manual overrides last so they always take priority
    id_to_classname.update(MANUAL_OVERRIDES)
 
    print(f"  [name-resolve] {len(id_to_classname)} schools mapped by ID "
          f"({len(MANUAL_OVERRIDES)} via manual overrides)")
    return id_to_classname
 
 
def resolve_name(cell, id_to_classname, known_teams):
    """
    Resolve a scoreboard table cell to a classification name.
 
    Step 1: Extract s= ID from href → look up in id_to_classname.
            Handles renamed/merged schools (e.g. 'Scott City with Chaffee'
            → 'Scott City') because the ID in the href never changes.
    Step 2: Exact match of display text against known_teams.
            Handles co-op names that exist in classifications as-is.
    Returns None if unresolvable — game will be skipped.
    """
    a = cell.find("a", href=lambda h: h and "/MySchool/Schedule.aspx" in h)
    if not a:
        return None
 
    # Step 1: ID-based lookup
    href  = a.get("href", "")
    match = re.search(r"[?&]s=(\d+)", href, re.IGNORECASE)
    if match:
        sid = match.group(1)
        if sid in id_to_classname:
            return id_to_classname[sid]
 
    # Step 2: Exact display text match
    display_text = a.get_text(strip=True)
    if display_text in known_teams:
        return display_text
 
    return None
 
 
# ---------------------------------------------------------------------------
# SCRAPING
# ---------------------------------------------------------------------------
 
def is_mshsaa_team(cell):
    return cell.find(
        "a", href=lambda h: h and "/MySchool/Schedule.aspx" in h
    ) is not None
 
 
def parse_score(text):
    text = text.strip()
    if not text:
        return None
    try:
        score = int(text)
    except ValueError:
        return None
    return score if 0 <= score <= MAX_POINTS else None
 
 
def is_forfeit(c1, c2):
    return "forfeit" in (c1.get_text() + c2.get_text()).lower()
 
 
def scrape_date(target_date, id_to_classname, known_teams):
    url = BASE_URL.format(target_date.strftime("%m%d%Y"))
    try:
        resp = requests.get(url, timeout=20, headers=HEADERS)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Failed {target_date}: {e}")
        return []
 
    soup  = BeautifulSoup(resp.text, "html.parser")
    games = []
 
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue
        if "final" not in rows[-1].get_text().lower():
            continue
 
        t1c = rows[1].find_all("td")
        t2c = rows[2].find_all("td")
        if len(t1c) < 3 or len(t2c) < 3:
            continue
        if not is_mshsaa_team(t1c[1]) or not is_mshsaa_team(t2c[1]):
            continue
        if is_forfeit(t1c[1], t2c[1]):
            continue
 
        name1 = resolve_name(t1c[1], id_to_classname, known_teams)
        name2 = resolve_name(t2c[1], id_to_classname, known_teams)
 
        if name1 is None or name2 is None:
            continue
 
        s1 = parse_score(t1c[2].get_text())
        s2 = parse_score(t2c[2].get_text())
        if s1 is None or s2 is None:
            continue
 
        games.append((
            target_date.strftime("%Y-%m-%d"),
            name1, s1,
            name2, s2
        ))
 
    return games
 
 
def scrape_full_season(id_to_classname, known_teams):
    all_games = []
    current   = SEASON_START
    while current <= min(SEASON_END, date.today()):
        print(f"  Scraping {current}...", end=" ", flush=True)
        day_games = scrape_date(current, id_to_classname, known_teams)
        all_games.extend(day_games)
        print(f"{len(day_games)} games")
        current += timedelta(days=1)
        time.sleep(0.5)
    return all_games
 
 
def deduplicate_games(all_games):
    """
    Remove duplicate games where the same two teams played on the same date
    with the same scores, regardless of which team is listed as home or away.
 
    A game is considered a duplicate if another game exists with:
      - The same date
      - The same two team names (in either order)
      - The same two scores (in either order)
 
    The key is built from a frozenset of (team, score) pairs so that
    (Date, Team A, 54, Team B, 13) and (Date, Team B, 13, Team A, 54)
    produce the same key and only one is kept.
    """
    seen         = set()
    unique_games = []
    duplicates   = 0
 
    for game in all_games:
        date_str, t1, s1, t2, s2 = game
        # Key is date + frozenset of team names only — order independent.
        # Scores are intentionally excluded so that (Team A home, Team B away)
        # and (Team B home, Team A away) on the same date are always treated
        # as the same game regardless of which score appears first.
        key = (date_str, frozenset([t1, t2]))
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique_games.append(game)
 
    if duplicates:
        print(f"  Removed {duplicates} duplicate game(s). "
              f"{len(unique_games)} unique games remain.")
    else:
        print(f"  No duplicates found. {len(unique_games)} games.")
 
    return unique_games
 
 
def report_missing_teams(all_games, team_to_class):
    """
    After scraping is complete, compare every team in classifications.json
    against the teams that actually appeared in scraped games.
    Print only the teams that have zero games — these are the ones that
    genuinely need attention (either their ID needs adding or their
    classifications.json name needs correcting).
    """
    teams_with_games = set()
    for _, t1, _, t2, _ in all_games:
        teams_with_games.add(t1)
        teams_with_games.add(t2)
 
    missing = sorted(
        t for t in team_to_class if t not in teams_with_games
    )
 
    if missing:
        print(f"\n  MISSING TEAMS: {len(missing)} classification schools have "
              f"no games in the scraped data.")
        print(f"  These teams need attention — either their MSHSAA page shows")
        print(f"  a different name than classifications.json, or they did not")
        print(f"  play any games this season.")
        print(f"  Missing: {missing}\n")
    else:
        print("\n  All classification schools have at least one game. \n")
 
 
# ---------------------------------------------------------------------------
# CSV OUTPUT
# ---------------------------------------------------------------------------
 
def save_csv(all_games):
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Home Team", "Home Score", "Away Team", "Away Score"])
        for date_str, t1, s1, t2, s2 in all_games:
            writer.writerow([date_str, t1, s1, t2, s2])
    print(f"Saved {len(all_games)} games to {CSV_PATH}")
 
 
# ---------------------------------------------------------------------------
# RATING ENGINE
# ---------------------------------------------------------------------------
 
def run_iterations(games, teams, off_rating, def_rating, league_avg,
                   iterations, phase_label, ovr_filter=None):
    for iteration in range(iterations):
        off_error    = {t: 0.0 for t in teams}
        def_error    = {t: 0.0 for t in teams}
        games_played = {t: 0   for t in teams}
 
        eligible_games = games
        if ovr_filter is not None:
            eligible_games = [
                (t1, t2, s1, s2) for t1, t2, s1, s2 in games
                if abs((off_rating[t1] + def_rating[t1]) -
                       (off_rating[t2] + def_rating[t2])) <= ovr_filter
            ]
 
        for t1, t2, actual_s1, actual_s2 in eligible_games:
            predicted_s1 = off_rating[t1] - def_rating[t2] + league_avg
            predicted_s2 = off_rating[t2] - def_rating[t1] + league_avg
 
            error_s1 = actual_s1 - predicted_s1
            error_s2 = actual_s2 - predicted_s2
 
            off_error[t1] += error_s1
            off_error[t2] += error_s2
            def_error[t1] += -error_s2
            def_error[t2] += -error_s1
 
            games_played[t1] += 1
            games_played[t2] += 1
 
        for team in teams:
            if games_played[team] > 0:
                off_rating[team] += (
                    (off_error[team] / games_played[team]) * LEARNING_RATE
                )
                def_rating[team] += (
                    (def_error[team] / games_played[team]) * LEARNING_RATE
                )
 
        if (iteration + 1) % 100 == 0:
            eligible_count = (
                len(eligible_games) if ovr_filter is not None else len(games)
            )
            print(
                f"  [{phase_label}] Iteration {iteration + 1}/{iterations} complete"
                + (f" | Competitive games: {eligible_count}" if ovr_filter else "")
            )
 
 
def calculate_ratings(all_games, iterations=ITERATIONS):
    games = [(t1, t2, s1, s2) for _, t1, s1, t2, s2 in all_games]
 
    teams = list({t for t1, t2, _, _ in games for t in (t1, t2)})
    if not teams:
        return {}, {}, {}, 0
 
    all_scores = [s for _, _, s1, s2 in games for s in (s1, s2)]
    league_avg = sum(all_scores) / len(all_scores)
    print(f"  League average: {league_avg:.2f} points per game")
 
    off_rating = {t: 0.0 for t in teams}
    def_rating = {t: 0.0 for t in teams}
 
    print(f"\n  Running Phase 1 ({iterations} iterations, all games)...")
    run_iterations(games, teams, off_rating, def_rating, league_avg,
                   iterations=iterations, phase_label="Phase 1", ovr_filter=None)
 
    print(f"\n  Running Phase 2 ({iterations} iterations, "
          f"competitive games within {COMPETITIVE_THRESHOLD} OVR pts)...")
    run_iterations(games, teams, off_rating, def_rating, league_avg,
                   iterations=iterations, phase_label="Phase 2",
                   ovr_filter=COMPETITIVE_THRESHOLD)
 
    ovr_rating = {t: round(off_rating[t] + def_rating[t], 2) for t in teams}
    return off_rating, def_rating, ovr_rating, league_avg
 
 
# ---------------------------------------------------------------------------
# JSON OUTPUT
# ---------------------------------------------------------------------------
 
def build_team_entries(off_rating, def_rating, ovr_rating,
                       team_to_class, team_to_district,
                       class_filter=None):
    all_teams = list(ovr_rating.keys())
 
    pool = (
        [t for t in all_teams if team_to_class.get(t) == class_filter]
        if class_filter is not None
        else all_teams
    )
 
    ovr_sorted = sorted(pool, key=lambda t: ovr_rating[t], reverse=True)
    off_sorted = sorted(pool, key=lambda t: off_rating[t], reverse=True)
    def_sorted = sorted(pool, key=lambda t: def_rating[t], reverse=True)
 
    ovr_rank = {t: i + 1 for i, t in enumerate(ovr_sorted)}
    off_rank = {t: i + 1 for i, t in enumerate(off_sorted)}
    def_rank = {t: i + 1 for i, t in enumerate(def_sorted)}
 
    return [
        {
            "ovr_rank":       ovr_rank[t],
            "school":         t,
            "classification": team_to_class.get(t),
            "district":       team_to_district.get(t),
            "ovr_rating":     ovr_rating[t],
            "off_rating":     round(off_rating[t], 2),
            "off_rank":       off_rank[t],
            "def_rating":     round(def_rating[t], 2),
            "def_rank":       def_rank[t],
        }
        for t in ovr_sorted
    ]
 
 
def save_overall_json(off_rating, def_rating, ovr_rating, league_avg,
                      team_to_class, team_to_district):
    entries = build_team_entries(off_rating, def_rating, ovr_rating,
                                 team_to_class, team_to_district)
    output = {
        "last_updated":   datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "league_average": round(league_avg, 2),
        "teams": entries,
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
 
    print(f"Saved {len(entries)} teams to {OUTPUT_PATH}")
    print("Top 5 overall:")
    for e in entries[:5]:
        print(f"  {e['ovr_rank']}. {e['school']} (Class {e['classification']}) "
              f"| OVR: {e['ovr_rating']:+.2f} "
              f"| OFF: {e['off_rating']:+.2f} "
              f"| DEF: {e['def_rating']:+.2f}")
 
 
def save_class_jsons(off_rating, def_rating, ovr_rating, league_avg,
                     team_to_class, team_to_district):
    for cls in range(1, 7):
        entries = build_team_entries(off_rating, def_rating, ovr_rating,
                                     team_to_class, team_to_district,
                                     class_filter=cls)
        if not entries:
            print(f"  Class {cls}: no teams found — skipping.")
            continue
 
        path = f"football_ratings_2010_class{cls}.json"
        output = {
            "last_updated":   datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "league_average": round(league_avg, 2),
            "classification": cls,
            "teams": entries,
        }
        with open(path, "w") as f:
            json.dump(output, f, indent=2)
 
        print(f"  Class {cls}: {len(entries)} teams → {path}")
        print("    Top 3: " + " | ".join(
            f"{e['ovr_rank']}. {e['school']} ({e['ovr_rating']:+.2f})"
            for e in entries[:3]
        ))
 
 
 
# ---------------------------------------------------------------------------
# CSV RANKINGS OUTPUT
# ---------------------------------------------------------------------------
 
def save_rankings_csv(off_rating, def_rating, ovr_rating,
                      team_to_class, team_to_district,
                      class_filter=None):
    """
    Save a rankings CSV for either all teams (class_filter=None) or a
    specific class.  Rankings (OFF Rank, DEF Rank, OVR Rank) are computed
    within the pool so class CSVs show class-specific ranks.
 
    Columns: School, OFF Rating, DEF Rating, OVR Rating,
             OFF Rank, DEF Rank, OVR Rank
    """
    all_teams = list(ovr_rating.keys())
 
    pool = (
        [t for t in all_teams if team_to_class.get(t) == class_filter]
        if class_filter is not None
        else all_teams
    )
 
    if not pool:
        label = f"Class {class_filter}" if class_filter else "Overall"
        print(f"  {label}: no teams — skipping CSV.")
        return
 
    ovr_sorted = sorted(pool, key=lambda t: ovr_rating[t], reverse=True)
    off_sorted = sorted(pool, key=lambda t: off_rating[t], reverse=True)
    def_sorted = sorted(pool, key=lambda t: def_rating[t], reverse=True)
 
    ovr_rank = {t: i + 1 for i, t in enumerate(ovr_sorted)}
    off_rank = {t: i + 1 for i, t in enumerate(off_sorted)}
    def_rank = {t: i + 1 for i, t in enumerate(def_sorted)}
 
    rows = [
        {
            "School":      t,
            "OFF Rating":  round(off_rating[t], 2),
            "DEF Rating":  round(def_rating[t], 2),
            "OVR Rating":  round(ovr_rating[t], 2),
            "OFF Rank":    off_rank[t],
            "DEF Rank":    def_rank[t],
            "OVR Rank":    ovr_rank[t],
        }
        for t in ovr_sorted
    ]
 
    df = pd.DataFrame(rows, columns=[
        "School", "OFF Rating", "DEF Rating", "OVR Rating",
        "OFF Rank", "DEF Rank", "OVR Rank"
    ])
 
    if class_filter is None:
        path  = "football_rankings_2010_all.csv"
        label = "All teams"
    else:
        path  = f"football_rankings_2010_class{class_filter}.csv"
        label = f"Class {class_filter}"
 
    df.to_csv(path, index=False)
    print(f"  {label}: {len(df)} teams — {path}")
 
 
def save_all_rankings_csvs(off_rating, def_rating, ovr_rating,
                           team_to_class, team_to_district):
    """Save overall + one CSV per class (1-6)."""
    save_rankings_csv(off_rating, def_rating, ovr_rating,
                      team_to_class, team_to_district,
                      class_filter=None)
    for cls in range(1, 7):
        save_rankings_csv(off_rating, def_rating, ovr_rating,
                          team_to_class, team_to_district,
                          class_filter=cls)
 
# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
 
if __name__ == "__main__":
    print("=== MSHSAA Football Ratings 2010 ===")
 
    print("\nLoading classifications...")
    team_to_class, team_to_district = load_classifications()
    known_teams = set(team_to_class.keys())
    print(f"  Loaded {len(team_to_class)} teams from {CLASSIFICATIONS_PATH}")
 
    print("\nBuilding school ID → classification name lookup...")
    id_to_classname = build_id_to_classname(team_to_class, SCHOOLS_CSV)
 
    print("\nScraping season scoreboard...")
    all_games = scrape_full_season(id_to_classname, known_teams)
    print(f"\nTotal valid games (before deduplication): {len(all_games)}")
    if not all_games:
        print("No games found — exiting.")
        exit(1)
 
    if MANUAL_GAMES:
        print(f"\nAdding {len(MANUAL_GAMES)} manual game(s)...")
        all_games.extend(MANUAL_GAMES)
 
    print("\nDeduplicating games...")
    all_games = deduplicate_games(all_games)
 
    print("\nChecking for missing teams...")
    report_missing_teams(all_games, team_to_class)
 
    print("Saving scoreboard CSV...")
    save_csv(all_games)
 
    print(f"\nRunning ratings engine "
          f"({ITERATIONS} Phase 1 + {ITERATIONS} Phase 2 iterations)...")
    off_rating, def_rating, ovr_rating, league_avg = calculate_ratings(all_games)
 
    print("\nSaving overall ratings JSON...")
    save_overall_json(off_rating, def_rating, ovr_rating, league_avg,
                      team_to_class, team_to_district)
 
    print("\nSaving per-class ratings JSONs...")
    save_class_jsons(off_rating, def_rating, ovr_rating, league_avg,
                     team_to_class, team_to_district)
 
    print("\nSaving rankings CSVs...")
    save_all_rankings_csvs(off_rating, def_rating, ovr_rating,
                           team_to_class, team_to_district)
 
    print("\n=== Done ===")
