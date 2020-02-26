import datetime
import random
from datetime import datetime as dt
from urllib.parse import quote

import pytz
import requests

from ccalendar.models import Google
from meeting.models import Details, Host, Status
from property.models import Room
from userProfile.models import UserProfile


def encode_timezone_aware_datetime(datetimes, timezone):
    tzone = pytz.timezone(timezone)
    local_time = tzone.localize(datetimes).isoformat()
    encode_local_time = quote(local_time)
    return encode_local_time


def create_dict_of_events(events, events_dict):
    list_of_events = []
    previous_date = ''

    for item in events:
        start_date = item['start']['dateTime']
        event_start = start_date.split('T')
        event_start_date = event_start[0]
        event_start_time = (event_start[1].split('+'))[0]

        end_date = item['end']['dateTime']
        event_end = end_date.split('T')
        event_end_time = (event_end[1].split('+'))[0]

        event = {
            'start_time': event_start_time,
            'end_time': event_end_time
        }

        if previous_date != event_start_date:
            list_of_events = []

        try:
            list_of_events = events_dict[event_start_date]
        except KeyError:
            print('New Entry')

        list_of_events.append(event)

        events_dict[event_start_date] = list_of_events
        previous_date = event_start_date

    for key, value in events_dict.items():
        value = sorted(value, key=lambda i: (i['start_time']))
        events_dict[key] = value

    return events_dict


def get_events_from_google_calendar(meeting_uid):
    url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMax={0}&timeMin={1}&orderBy=startTime&singleEvents=True'
    host = Host.objects.get(uid=meeting_uid)
    user_profile = UserProfile.objects.get(user=host.host)

    participants = Status.objects.filter(meeting_host=host)
    start_time = user_profile.office_start_time
    end_time = user_profile.office_end_time

    office_start_datetime = datetime.datetime.combine(
        host.start_date, start_time)
    office_start_time = encode_timezone_aware_datetime(
        office_start_datetime, host.timezone)

    office_end_datetime = datetime.datetime.combine(
        host.end_date, end_time)
    office_end_time = encode_timezone_aware_datetime(
        office_end_datetime, host.timezone)

    events = {}

    try:
        host_google = Google.objects.get(user=host.host)
        host_access_token = host_google.access
        headers = {'access_token': host_access_token}

        url = url.format(office_end_time, office_start_time)

        try:
            res = requests.get(url, headers)
            google_events = res.json()

            events = create_dict_of_events(google_events['items'], events)

        except:
            print('An error occured')

    except:
        print(host.host.email + ' has not connected their google account')
    finally:
        participants = Status.objects.filter(meeting_host=host)
        for participant in participants:
            try:
                participant_google = Google.objects.get(
                    user=participant.participant)
                participant_access_token = participant_google.access
                headers = {'access_token': participant_access_token}

                url = url.format(office_end_time, office_start_time)

                try:
                    res = requests.get(url, headers)

                    google_events = res.json()
                    events = create_dict_of_events(
                        google_events['items'], events)

                except:
                    print('An error occured')
            except:
                print(participant.participant.email +
                      ' has not connected their google account')
    print(events)
    return events


def get_app_events(meeting_id):
    meeting = Host.objects.get(uid=meeting_id)
    participants = Status.objects.filter(meeting_host=meeting)
    events = {}

    start_date = meeting.start_date
    end_date = meeting.end_date
    difference_in_date = end_date-start_date

    for i in range(difference_in_date.days + 1):
        events_list = []
        meeting_list = []
        suggestion_date = start_date + datetime.timedelta(days=i)

        meetings_on_date = Details.objects.filter(meeting_date=suggestion_date)

        for meeting_on_date in meetings_on_date:
            if not meeting_on_date.meeting.host == meeting.host:
                continue

            meeting_list.append(meeting_on_date.meeting)
            event = {
                'start_time': (meeting_on_date.start_time).strftime('%H:%M:%S'),
                'end_time': (meeting_on_date.end_time).strftime('%H:%M:%S')
            }

            events_list.append(event)

        for participant in participants:
            meetings_on_date = Details.objects.filter(
                meeting_date=suggestion_date).exclude(meeting__in=meeting_list)

            for meeting_on_date in meetings_on_date:
                if not meeting_on_date.meeting.host == participant.participant:
                    continue

                event = {
                    'start_time': (meeting_on_date.start_time).strftime('%H:%M:%S'),
                    'end_time': (meeting_on_date.end_time).strftime('%H:%M:%S')
                }

                events_list.append(event)

        if events_list:
            events[suggestion_date.isoformat()] = events_list
    return events


def get_single_events_dict(google_events, app_events):
    events = {}

    for key, value in google_events.items():
        event = []

        if key in app_events:
            event = app_events[key]

        event.extend(value)
        events[key] = event

    for key, value in app_events.items():
        event = []

        if key in events:
            continue

        events[key] = value

    for key, value in events.items():
        value = sorted(value, key=lambda i: (i['start_time']))
        events[key] = value

    return events


'''
May need to +- 10 minutes to start_time and end_time to better filter the results
'''


def get_empty_room(date, start_time, end_time, meeting):
    user_profile = UserProfile.objects.get(user=meeting.host)
    booked_rooms_on_date = Details.objects.filter(meeting_date=date)
    booked_room_list = []
    meeting_type = meeting.type

    for room in booked_rooms_on_date:
        room_booked_start_time = room.start_time
        room_booked_end_time = room.end_time

        if room_booked_start_time <= start_time <= room_booked_end_time or room_booked_start_time <= end_time <= room_booked_end_time:
            booked_room_list.append(room.room.id)

    private_rooms = UserProfile.objects.filter(building=user_profile.building)

    for private_room in private_rooms:
        if private_room.room is not None:
            booked_room_list.append(private_room.room.id)

    members = len(meeting.participant_email)
    members += Status.objects.filter(meeting_host=meeting).count()

    if meeting_type != 'CF':
        remaining_rooms = Room.objects.filter(property=user_profile.building, room_type__in=[
                                              'MR', 'PO', 'DH'], room_capacity__gte=members, is_active=True).exclude(id__in=booked_room_list)
    else:
        remaining_rooms = Room.objects.filter(
            property=user_profile.building, room_type='CR', room_capacity__gte=members, is_active=True).exclude(id__in=booked_room_list)

    if not remaining_rooms.exists():
        remaining_rooms = Room.objects.filter(
            property=user_profile.building, room_capacity__gte=members, is_active=True).exclude(id__in=booked_room_list)

    if remaining_rooms.exists():
        return random.choice(remaining_rooms)
    return None


def get_room_status(date, start_time, end_time, room):
    meetings = Details.objects.filter(meeting_date=date).filter(room=room)

    for meeting in meetings:
        if meeting.start_time <= start_time < meeting.end_time or meeting.start_time < end_time <= meeting.end_time:
            return None

    return Room.objects.get(id=room)


def get_suggestion(suggestion_date, suggestions, meeting, event_start_time, event_end_time, room):
    difference = event_end_time - event_start_time
    difference_in_minutes = int(difference.seconds/60)
    duration = meeting.duration
    tzone = meeting.timezone
    local_tz = pytz.timezone(tzone)
    duration = int(duration.seconds / 60)
    suggestion_available = int(difference_in_minutes / duration)

    end_time = event_start_time
    for j in range(suggestion_available):
        suggestion_start_time = end_time.time()
        suggestion_end_time = (
            end_time + datetime.timedelta(minutes=duration)).time()

        if dt.now(local_tz) > end_time.replace(tzinfo=local_tz):
            end_time = end_time + datetime.timedelta(minutes=duration)
            continue

        if room == -1:
            empty_room = get_empty_room(
                suggestion_date, suggestion_start_time, suggestion_end_time, meeting)
        else:
            empty_room = get_room_status(
                suggestion_date, suggestion_start_time, suggestion_end_time, room)

        if empty_room is None:
            print('Room not found on {0}'.format(suggestion_date))
            continue

        suggestion = {
            'date': suggestion_date.isoformat(),
            'start_time': end_time.strftime('%I:%M%p'),
            'end_time': (end_time + datetime.timedelta(minutes=duration)).strftime('%I:%M%p'),
            'room_number': empty_room.room_number,
            'room_id': empty_room.id
        }

        suggestions.append(suggestion)
        end_time = dt.strptime(suggestion_date.strftime(
            '%Y-%m-%d') + suggestion['end_time'], '%Y-%m-%d%I:%M%p')

    return suggestions


def generate_suggestions(events, meeting_id, room):
    meeting = Host.objects.get(uid=meeting_id)

    suggestions = []

    start_date = meeting.start_date
    end_date = meeting.end_date
    difference_in_date = end_date-start_date
    user_profile = UserProfile.objects.get(user=meeting.host)

    for i in range(difference_in_date.days + 1):
        suggestion_date = start_date + datetime.timedelta(days=i)

        office_start_time = dt.strptime(suggestion_date.strftime(
            '%Y-%m-%d') + user_profile.office_start_time.isoformat(), '%Y-%m-%d%H:%M:%S')
        office_end_time = dt.strptime(suggestion_date.strftime(
            '%Y-%m-%d') + user_profile.office_end_time.isoformat(), '%Y-%m-%d%H:%M:%S')

        try:
            event_on_date = events[suggestion_date.isoformat()]

            for index, event in enumerate(event_on_date):

                event_start_time = dt.strptime(suggestion_date.strftime(
                    '%Y-%m-%d') + event['start_time'], '%Y-%m-%d%H:%M:%S')
                event_end_time = dt.strptime(suggestion_date.strftime(
                    '%Y-%m-%d') + event['end_time'], '%Y-%m-%d%H:%M:%S')

                if event_end_time < office_start_time or event_end_time >= office_end_time:
                    continue

                if len(event_on_date) == 1:
                    suggestions = get_suggestion(
                        suggestion_date, suggestions, meeting, office_start_time, event_start_time, room)
                    suggestions = get_suggestion(
                        suggestion_date, suggestions, meeting, event_end_time, office_end_time, room)
                else:
                    if index == 0:
                        if event_start_time > office_start_time:
                            event_end_time = event_start_time
                            event_start_time = office_start_time
                        else:
                            event_start_time = event_end_time
                            event_end_time = dt.strptime(suggestion_date.strftime(
                                '%Y-%m-%d') + event_on_date[index + 1]['start_time'], '%Y-%m-%d%H:%M:%S')
                    else:
                        previous_event_end_time = dt.strptime(suggestion_date.strftime(
                            '%Y-%m-%d') + event_on_date[index - 1]['end_time'], '%Y-%m-%d%H:%M:%S')
                        if previous_event_end_time <= office_start_time:
                            suggestions = get_suggestion(
                                suggestion_date, suggestions, meeting, office_start_time, event_start_time, room)

                        try:
                            event_start_time = event_end_time
                            event_end_time = dt.strptime(suggestion_date.strftime(
                                '%Y-%m-%d') + event_on_date[index + 1]['start_time'], '%Y-%m-%d%H:%M:%S')
                        except IndexError:
                            event_end_time = office_end_time
                    suggestions = get_suggestion(
                        suggestion_date, suggestions, meeting, event_start_time, event_end_time, room)

        except KeyError:
            suggestions = get_suggestion(
                suggestion_date, suggestions, meeting, office_start_time, office_end_time, room)
    print(suggestions)
    return suggestions


def meetings_details(meetings, filter_meeting, user, upcoming):
    meeting_list = []

    for meeting in meetings:
        participant = Status.objects.filter(
            meeting_host=meeting.meeting).filter(participant=user)

        if meeting.meeting.host == user or participant.exists():
            if meeting.meeting_date == datetime.date.today():
                if upcoming:
                    if meeting.start_time <= datetime.datetime.now().time():
                        continue
                else:
                    if meeting.start_time >= datetime.datetime.now().time():
                        continue

            meeting_item = {
                'meeting_id': meeting.meeting.uid,
                'title': meeting.meeting.title,
                'start_time': meeting.start_time.strftime('%I:%M%p'),
                'end_time': meeting.end_time.strftime('%I:%M%p'),
                'room': meeting.room.room_number,
                'date': meeting.meeting_date,
                'host': meeting.meeting.host == user,
            }

            meeting_list.append(meeting_item)

    if filter_meeting == 'hosted':
        key_val_list = [True]
        hosted_list = list(
            filter(lambda meeting: meeting['host'] in key_val_list, meeting_list))
        return hosted_list
    elif filter_meeting == 'participated':
        key_val_list = [False]
        participated_list = list(
            filter(lambda meeting: meeting['host'] in key_val_list, meeting_list))
        return participated_list

    return meeting_list


def root_suggestion(meeting_id, room_id):
    google_events = get_events_from_google_calendar(meeting_id)
    print('Google Events{0}'.format(google_events))

    app_events = get_app_events(meeting_id)
    events = get_single_events_dict(google_events, app_events)

    suggestions = generate_suggestions(events, meeting_id, room_id)



    return suggestions
