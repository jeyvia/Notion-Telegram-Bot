import os
from dotenv import load_dotenv
import requests
import datetime
from operator import itemgetter
import html
import pytz

load_dotenv()
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
timezone = pytz.timezone('Singapore')
today = datetime.datetime.now(timezone).date()
headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def parse_notion_object(obj):
    event_name = obj['properties']['Name']['title'][0]['plain_text']
    event_date = obj['properties']['Date']['date']['start']
    time = obj['properties']['Time']['rich_text']
    if time:
        time = obj['properties']['Time']['rich_text'][0]['plain_text']
    else:
        time = ""
    tags = []
    all_tags = obj['properties']['Tags']['multi_select']
    for tag in all_tags:
        tags.append(tag['name'])
    url = obj['url']

    return event_name, event_date, time, tags, url


def get_activities(NOTION_DATABASE_ID):
    activities = []
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    payload = {"page_size": 50}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    if data['object'] == 'error':
        return 'error'
    for result in data["results"]:
        event_name, event_date, event_time, event_tags, event_url = parse_notion_object(result)
        if event_date == today:
            activity = {
                'Name': event_name,
                'Time': event_time,
                'Tags': ', '.join(event_tags),
                'URL': event_url
            }
            activities.append(activity)
    return activities


def sort_activities(activities):
    sortedActivities = sorted(activities, key=itemgetter('Time'))
    return sortedActivities


def craft_msg(activities):
    final_msg = ""
    for activity in activities:
        msg = ""
        msg += f"<b>Activity name:</b> {activity['Name']}\n"
        if activity['Time']:
            msg += f"<b>Time:</b> {activity['Time']}\n"
        msg += f"<b>Tags:</b> {activity['Tags']}\n"
        link_url = activity['URL']
        html_link = f'<a href="{html.escape(link_url)}">Click here to open it in Notion App</a>'
        msg += html_link
        final_msg += (msg + "\n\n")
    return final_msg


def connectToNotion(database_id):
    activities = get_activities(database_id)
    if activities == 'error':
        return 'error'
    elif activities:
        activities = sort_activities(activities)
    else:
        return ''
    return craft_msg(activities)
