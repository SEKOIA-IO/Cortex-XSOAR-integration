import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

import json
import urllib3
import dateparser
import requests
import time
from typing import Any, Dict, Tuple, List, Optional, Union, cast, Callable
from datetime import datetime
import re
import pytz

# Disable insecure warnings
urllib3.disable_warnings()


''' CONSTANTS '''
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
MAX_INCIDENTS_TO_FETCH = 50 # Default value to be used if the parameter is not set on the integration config.
MAX_EVENTS = 250 # Default value to limit the amount of events retrieved.
INTERVAL_SECONDS_EVENTS = 1
TIMEOUT_EVENTS = 30
INCIDENT_TYPE_NAME = 'Sekoia XDR'
SEKOIA_INCIDENT_FIELDS = {'short_id': 'The ID of the alert to edit',
                         'status': 'The name of the status.',
                         'xsoar_id': 'The XSOAR incident'
                         }

STATUS_TRANSITIONS = {
    "Ongoing": "Validate",
    "Acknowledged": "Acknowledge",
    "Rejected": "Reject",
    "Closed":"Close"
}

MIRROR_DIRECTION = {
    "None": None,
    "Incoming": "In",
    "Outgoing": "Out",
    "Incoming and Outgoing": "Both"
}

''' CLIENT CLASS '''

class Client(BaseClient):
    """Client class to interact with the service API
    """

    def list_alerts(self,alerts_limit: Optional[int],alerts_status: Optional[str],
                    alerts_createdAt: Optional[str],alerts_updatedAt: Optional[str],alerts_urgency: Optional[str],
                    alerts_type: Optional[str],sort_by: Optional[str]) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        ''' Normal parameters'''
        if alerts_limit:
            request_params['limit'] = alerts_limit

        ''' Matching parameters'''
        if alerts_status:
            request_params['match[status_name]'] = alerts_status
        if alerts_createdAt:
            request_params['date[created_at]'] = alerts_createdAt
        if alerts_updatedAt:
            request_params['date[updated_at]'] = alerts_updatedAt
        if alerts_urgency:
            request_params['range[urgency]'] = alerts_urgency
        if alerts_type:
            request_params['match[type_value]'] = alerts_type

        ''' Sorting parameters'''
        if sort_by:
            request_params['sort'] = sort_by

        return self._http_request(
            method='GET',
            url_suffix='/sic/alerts',
            params=request_params
        )

    def get_alert(self, alert_uuid: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        return self._http_request(
            method='GET',
            url_suffix='/sic/alerts/' + alert_uuid,
            params=request_params
        )

    def query_events(self, events_earliest_time: str, events_lastest_time: str,
                    events_term: str, max_last_events: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        ''' Normal parameters'''
        if events_earliest_time:
            request_params['earliest_time'] = events_earliest_time
        if events_lastest_time:
            request_params['latest_time'] = events_lastest_time
        if events_term:
            request_params['term'] = events_term
        if max_last_events:
            request_params['max_last_events'] = max_last_events

        return self._http_request(
            method='POST',
            url_suffix='/sic/conf/events/search/jobs',
            params=request_params
        )

    def query_events_status(self, event_search_job_uuid: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        return self._http_request(
            method='GET',
            url_suffix='/sic/conf/events/search/jobs/' + event_search_job_uuid,
            params=request_params
        )

    def retrieve_events(self, event_search_job_uuid: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        ''' Normal parameters'''
        if event_search_job_uuid:
            request_params['event_search_job_uuid'] = event_search_job_uuid

        return self._http_request(
            method='GET',
            url_suffix='/sic/conf/events/search/jobs/' + event_search_job_uuid + '/events',
            params=request_params
        )

    def update_status_alert(self, alert_uuid: str, action_uuid: str, comment: Optional[str]) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        ''' Normal parameters'''
        if action_uuid:
            request_params['action_uuid'] = action_uuid
        if comment:
            request_params['comment'] = comment

        return self._http_request(
            method='PATCH',
            url_suffix='/sic/alerts/' + alert_uuid + '/workflow',
            json_data=request_params,
        )

    def post_comment_alert(self, alert_uuid: str, content: str, author: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        ''' Normal parameters'''
        if content:
            request_params["content"] = content
        if author:
            request_params["author"] = author


        response = self._http_request(
            method='POST',
            url_suffix='/sic/alerts/' + alert_uuid + '/comments',
            json_data=request_params
        )

        return response

    def get_comments_alert(self, alert_uuid: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        return self._http_request(
            method='GET',
            url_suffix='/sic/alerts/' + alert_uuid + '/comments',
            params=request_params
        )

    def get_workflow_alert(self, alert_uuid: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        return self._http_request(
            method='GET',
            url_suffix='/sic/alerts/' + alert_uuid + '/workflow',
            params=request_params
        )

    def get_cases_alert(self, alert_uuid: str, case_id: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        ''' Matching parameters'''
        if alert_uuid:
            request_params['match[alert_uuid]'] = alert_uuid
        if case_id:
            request_params['match[short_id]'] = case_id

        return self._http_request(
            method='GET',
            url_suffix='/sic/cases',
            params=request_params
        )

    def get_asset(self, asset_uuid: str) -> List[Dict[str, Any]]:

        return self._http_request(
            method='GET',
            url_suffix='/asset-management/assets/' + asset_uuid,
            params=None
        )

    def list_asset(self, limit: str, assets_type: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        ''' Normal parameters'''
        if limit:
            request_params["limit"] = limit

        ''' Matching parameters'''
        if assets_type:
            request_params['match[type_name]'] = assets_type

        return self._http_request(
            method='GET',
            url_suffix='/asset-management/assets',
            params=request_params
        )

    def get_user(self, user_uuid: str) -> List[Dict[str, Any]]:

        return self._http_request(
            method='GET',
            url_suffix='/users/' + user_uuid,
            params=None
        )

    def add_attributes_asset(self, asset_uuid: str, name:str, value:str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        ''' Normal parameters'''
        if name:
            request_params["name"] = name
        if value:
            request_params["value"] = value


        return self._http_request(
            method='POST',
            url_suffix='/asset-management/assets/' + asset_uuid + '/attr',
            params=request_params
        )

    def add_keys_asset(self, asset_uuid: str, name:str, value:str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        ''' Normal parameters'''
        if name:
            request_params["name"] = name
        if value:
            request_params["value"] = value

        return self._http_request(
            method='POST',
            url_suffix='/asset-management/assets/' + asset_uuid + '/keys',
            params=request_params
        )

    def remove_attribute_asset(self, asset_uuid: str, attribute_uuid:str) -> List[Dict[str, Any]]:

        return self._http_request(
            method='DELETE',
            url_suffix='/asset-management/assets/' + asset_uuid + '/attr/' + attribute_uuid,
            resp_type='text'
        )

    def remove_key_asset(self, asset_uuid: str, key_uuid:str) -> List[Dict[str, Any]]:

        return self._http_request(
            method='DELETE',
            url_suffix='/asset-management/assets/' + asset_uuid + '/keys/' + key_uuid,
            resp_type='text'
        )

    def get_kill_chain(self, kill_chain_uuid: str) -> List[Dict[str, Any]]:

        request_params: Dict[str, Any] = {}

        return self._http_request(
            method='GET',
            url_suffix='/sic/kill-chains/' + kill_chain_uuid
        )

    def http_request(self, method: str, url_sufix: str, params: str) -> List[Dict[str, Any]]:

        if not params:
            params = {}

        return self._http_request(
            method=method,
            url_suffix=url_sufix,
            params=params
        )


''' HELPER FUNCTIONS '''

def arg_to_timestamp(arg: Any, arg_name: str, required: bool = False) -> int:
    """
    Converts an XSOAR argument to a timestamp (seconds from epoch).
    This function is used to quickly validate an argument provided to XSOAR
    via ``demisto.args()`` into an ``int`` containing a timestamp (seconds
    since epoch). It will throw a ValueError if the input is invalid.
    If the input is None, it will throw a ValueError if required is ``True``,
    or ``None`` if required is ``False``.

    Args:
        arg: argument to convert
        arg_name: argument name.
        required: throws exception if ``True`` and argument provided is None

    Returns:
        returns an ``int`` containing a timestamp (seconds from epoch) if conversion works
        returns ``None`` if arg is ``None`` and required is set to ``False``
        otherwise throws an Exception
    """
    if arg is None:
        if required is True:
            raise ValueError(f'Missing "{arg_name}"')

    if isinstance(arg, str) and arg.isdigit():
        # timestamp is a str containing digits - we just convert it to int
        return int(arg)
    if isinstance(arg, str):
        # we use dateparser to handle strings either in ISO8601 format, or
        # relative time stamps.
        # For example: format 2019-10-23T00:00:00 or "3 days", etc
        date = dateparser.parse(arg, settings={'TIMEZONE': 'UTC'})
        if date is None:
            # if d is None it means dateparser failed to parse it
            raise ValueError(f'Invalid date: {arg_name}')

        return int(date.timestamp())
    if isinstance(arg, (int, float)):
        # Convert to int if the input is a float
        return int(arg)
    raise ValueError(f'Invalid date: "{arg_name}"')

def timezone_format(epoch: int) -> str:
    """
    Converts an epoch timestamp into a formatted date in
    a specific timezone defined in the integration parameter.

    Args:
        epoch: argument to convert in epoch format

    Returns:
        returns an ``str`` containing a fomatted datestring in the timezone selected
    """
    utc_datetime = datetime.utcfromtimestamp(epoch)
    timezone = demisto.params().get('timezone', 'UTC')
    timezoneFormat = pytz.timezone(timezone)
    format_datetime = utc_datetime.astimezone(timezoneFormat)
    return format_datetime.strftime('%Y-%m-%dT%H:%M:%S')


def time_converter(time):
    time_format = None
    # Regular expression pattern to match ISO 8601 format
    iso_8601_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
    # Regular expression pattern to match UNIX timestamp format
    unix_timestamp_pattern = re.compile(r"^\d+$")
    # check if input matches ISO 8601 format
    if iso_8601_pattern.match(time):
        time_format = 'iso8601'
    # check if input matches UNIX timestamp format
    elif unix_timestamp_pattern.match(time):
        time_format = 'unix'
    else:
        raise ValueError("Invalid time format")

    if time_format == 'unix':
        time = datetime.fromtimestamp(int(time),pytz.utc)
    else:
        time = datetime.fromisoformat(time)
    # convert datetime object to desired format
    time = time.strftime(DATE_FORMAT)
    return time

def convert_to_demisto_severity(severity: str) -> int:
    """
    Maps Sekoia XDR urgency to Cortex XSOAR severity.
    Converts the Sekoia XDR alert urgency level ('Low','Moderate','High','Major','Urgent') to Cortex XSOAR incident
    severity (1 to 4).

    Args:
        urgency (str): urgency display text as returned from the Sekoia XDR API.

    Returns:
        int: Cortex XSOAR Severity (1 to 4)
    """

    return {
        'Low': IncidentSeverity.LOW,
        'Moderate': IncidentSeverity.MEDIUM,
        'High': IncidentSeverity.HIGH,
        'Major': IncidentSeverity.HIGH,
        'Urgent': IncidentSeverity.CRITICAL
    }[severity]

def exclude_info_events(event_info: dict, exclude_info: str) -> dict:
    """
    Exclude information from the events.
    This function will exclude information from the events that is duplicated or not needed.

    Args:
        event_info (dict): JSON to be transformed removing some of the information.
        exclude_info (str): the event fields to be removed from the results.

    Returns:
        dict: JSON transformed with the information removed.
    """
    exclude_info = exclude_info.split(',')

    ''' Exclude information from the context output as well
    new_events = []
    for event in events['items']:
        new_events = {}

        for field in exclude_info
            event.pop(field, None)
    events = json.dumps()
    '''

    ''' Exclude headers from the readable output '''
    headers = list(event_info['items'][0].keys())
    for header in exclude_info:
        if header in headers:
            headers.remove(header)
    return(headers)


def undot(json_data: dict) -> dict:
    """
    Remove/Replace dots from the key names of a JSON.
    This function transform the name of the JSON keys that contain "dots" to make it easier to reference them in XSOAR.

    Args:
        json_data (dict): JSON to be transformed.

    Returns:
        dict: JSON with the key names that contain "dots" transformed.
    """
    replace_symbol = demisto.params().get('replace_dots_event', '_')

    if isinstance(json_data, str):
        data = json.loads(json_data)
    elif isinstance(json_data, dict):
        data = json_data
    else:
        raise TypeError("JSON data sent to undot function must be a string or a dictionary")

    # Iterate over each item in the items array
    for item in data['items']:
        # Replace dots with underscores in each key
        for key in list(item.keys()):
            new_key = key.replace(".", replace_symbol)
            if new_key != key:
                item[new_key] = item.pop(key)
    # Convert back to JSON and return it
    return json.dumps(data)


''' COMMAND FUNCTIONS '''

def fetch_incidents(client: Client, max_results: int, last_run: Dict[str, int],
                    first_fetch_time: Optional[int], alert_status: Optional[str],
                    alert_urgency: Optional[str], alert_type: Optional[str],
                    fetch_mode: Optional[str], mirror_direction: Optional[str],
                    fetch_with_assets:Optional[str],fetch_with_kill_chain:Optional[str]) -> Tuple[Dict[str, int], List[dict]]:
    """
    This function retrieves new alerts every interval (default is 1 minute).
    It has to implement the logic of making sure that incidents are fetched only onces and no incidents are missed.
    By default it's invoked by XSOAR every minute. It will use last_run to save the timestamp of the last incident it
    processed. If last_run is not provided, it should use the integration parameter first_fetch_time to determine when
    to start fetching the first time.

    Args:
        client (Client): Sekoia XDR client to use.
        max_results (int): Maximum numbers of incidents per fetch.
        last_run (dict): A dict with a key containing the latest incident created time we got from last fetch.
        first_fetch_time(int): If last_run is None (first time we are fetching), it contains the timestamp in
            milliseconds on when to start fetching incidents.
        alert_status (str): status of the alert to search for.
        alert_urgency (str): alert urgency range to search for. Format: "MIN_urgency,MAX_urgency". i.e: 80,100.
        alert_type (str): type of alerts to search for.
        fetch_mode (str): If the alert will be fetched with or without the events.
        mirror_direction (str): The direction of the mirroring can be set to None or to Incoming.
        fetch_with_assets (str): If the alert will include the assets information on the fetching.
        fetch_with_kill_chain (str): If the alert will include the kill chain information on the fetching.
    Returns:
        dict: Next run dictionary containing the timestamp that will be used in ``last_run`` on the next fetch.
        list: List of incidents that will be created in XSOAR.
    """

    # Get the last fetch time, if exists
    # last_run is a dict with a single key, called last_fetch
    last_fetch = last_run.get('last_fetch', None)
    # Handle first fetch time
    if last_fetch is None:
        # if missing, use what provided via first_fetch_time
        last_fetch = first_fetch_time
    else:
        # otherwise use the stored last fetch
        last_fetch = int(last_fetch)

    # Convert time from epoch to ISO8601 in the correct format and add the ,now also
    alerts_createdAt = time_converter(str(last_fetch)) + ',now'

    # for type checking, making sure that latest_created_time is int
    latest_created_time = cast(int, last_fetch)

    # Initialize an empty list of incidents to return
    # Each incident is a dict with a string as a key
    incidents: List[Dict[str, Any]] = []
    alerts = client.list_alerts(alerts_limit=max_results,alerts_status=alert_status,alerts_createdAt=alerts_createdAt,alerts_updatedAt=None,
                                alerts_urgency=alert_urgency,alerts_type=alert_type,sort_by='created_at')

    for alert in alerts['items']:

        # If no created_time set is as epoch (0). We use time in ms so we must
        # convert it from the Sekoia XDR API response
        incident_created_time = int(alert.get('created_at', '0'))
        incident_created_time_ms = incident_created_time * 1000

        # to prevent duplicates, we are only adding incidents with creation_time > last fetched incident
        if last_fetch:
            if incident_created_time <= last_fetch:
                continue

        # If no name is present it will throw an exception
        incident_name = alert['title']
        urgency = alert['urgency']

        if fetch_mode == 'Fetch With All Events':
            # Add the events to the alert
            earliest_time = alert['first_seen_at']
            lastest_time = 'now'
            term = "alert_short_ids:" + alert['short_id']
            interval_in_seconds = INTERVAL_SECONDS_EVENTS
            timeout_in_seconds = TIMEOUT_EVENTS
            max_last_events = MAX_EVENTS

            # Add the events to the alert
            args = {
                'earliest_time': earliest_time,
                'lastest_time': lastest_time,
                'query': term,
                'interval_in_seconds': interval_in_seconds,
                'timeout_in_seconds': timeout_in_seconds,
                'max_last_events': max_last_events
            }
            events = search_events_command(client, args)
            alert['events'] = events.outputs

        if fetch_with_assets == True:
            # Add assets information to the alert
            asset_list = []
            for asset in alert['assets']:
                try:
                    asset_info = client.get_asset(asset_uuid=asset)
                    asset_list.append(asset_info)
                except Exception as e:
                    # Handle the exception if there is any problem with the API call
                    demisto.debug(f"Error fetching asset {asset}: {e}")
                    # Continue with the next asset
                    continue
            alert['assets'] = asset_list

        if fetch_with_kill_chain == True:
            # Add kill chain information to the alert
            if alert['kill_chain_short_id']:
                try:
                    kill_chain = client.get_kill_chain(kill_chain_uuid=alert['kill_chain_short_id'])
                    alert['kill_chain'] = kill_chain
                except Exception as e:
                    # Handle the exception if there is any problem with the API call
                    demisto.debug(f"Error fetching kill chain information {kill_chain}: {e}")

        # If the integration parameter is set to mirror add the instance name to be mapped to dbotMirrorInstance
        if mirror_direction != 'None':
            alert['mirror_instance'] = demisto.integrationInstance()

        incident = {
            'name': incident_name,
            'occurred': timestamp_to_datestring(incident_created_time_ms),
            'rawJSON': json.dumps(alert),
            'severity': convert_to_demisto_severity(urgency.get('display', 'Low'))
        }
        # If the integration parameter is set to mirror add the appropiate fields to the incident
        if mirror_direction != 'None':
            incident['dbotMirrorDirection'] = MIRROR_DIRECTION.get(mirror_direction)
            incident['dbotMirrorId'] = alert['short_id']

        incidents.append(incident)

        # Update last run and add incident if the incident is newer than last fetch
        if incident_created_time > latest_created_time:
            latest_created_time = incident_created_time

    # Save the next_run as a dict with the last_fetch key to be stored
    next_run = {'last_fetch': latest_created_time}
    return next_run, incidents

# =========== Mirroring Mechanism ===========

def get_remote_data_command(client, args: dict,
                            close_incident: bool, close_note: str, mirror_events: bool, mirror_kill_chain: bool, reopen_incident: bool):
    """ get-remote-data command: Returns an updated alert and error entry (if needed)

    Args:
        client (Client): Sekoia XDR client to use.
        args (dict): The command arguments
        close_incident (bool): Indicates whether to close the corresponding XSOAR incident if the alert
            has been closed on Sekoia's end.
        close_note (str): Indicates the notes to be including when the incident gets closed by mirroring.
        mirror_events (bool): If the events will be included in the mirroring of the alerts or not.
        mirror_kill_chain: If the kill chain information from the alerts will be mirrored.
        reopen_incident: Indicates whether to reopen the corresponding XSOAR incident if the alert
            has been reopened on Sekoia's end.
    Returns:
        GetRemoteDataResponse: The Response containing the update alert to mirror and the entries
    """

    demisto.debug(f'#### Entering MIRRORING IN - get_remote_data_command ####')

    parsed_args = GetRemoteDataArgs(args)
    alert = client.get_alert(alert_uuid=parsed_args.remote_incident_id)

    alert_short_id = alert['short_id']
    alert_status = alert['status']['name']

    last_update = arg_to_timestamp(
        arg=args.get('lastUpdate'),
        arg_name='lastUpdate',
        required=True
    )

    alert_last_update = arg_to_timestamp(
        arg=alert.get('updated_at'),
        arg_name='updated_at',
        required=False
    )

    demisto.debug(f'Alert {alert_short_id} with status {alert_status} : last_update is {last_update} , alert_last_update is {alert_last_update}')

    '''
    if last_update > alert_last_update:
        demisto.debug(f'Nothing new updated in the alert {alert_short_id} with status {alert_status}.')
        alert = {}


    else:
    '''
    entries = []

    if mirror_events and alert['status']['name'] not in ["Closed", "Rejected"]:
        # Add the events to the alert
        earliest_time = alert['first_seen_at']
        lastest_time = 'now'
        term = "alert_short_ids:" + alert['short_id']
        interval_in_seconds = INTERVAL_SECONDS_EVENTS
        timeout_in_seconds = TIMEOUT_EVENTS
        max_last_events = MAX_EVENTS

        # Add the events to the alert
        args = {
            'earliest_time': earliest_time,
            'lastest_time': lastest_time,
            'query': term,
            'interval_in_seconds': interval_in_seconds,
            'timeout_in_seconds': timeout_in_seconds,
            'max_last_events': max_last_events
        }
        events = search_events_command(client, args)
        alert['events'] = events.outputs


    if mirror_kill_chain and alert['kill_chain_short_id']:
        try:
            # Add the kill chain information to the alert
            kill_chain = client.get_kill_chain(kill_chain_uuid=alert['kill_chain_short_id'])
            alert['kill_chain'] = kill_chain
        except Exception as e:
            # Handle the exception if there is any problem with the API call
            demisto.debug(f"Error fetching kill_chain {kill_chain}: {e}")


    #This adds all the infomation from the XSOAR incident.
    #demisto.debug(f'Alert {alert_short_id} with status {alert_status} have this info updated: {alert}')
    demisto.debug(f'The parsed args are {parsed_args}')
    #incident = demisto.context()
    #demisto.debug(f'The context information is {incident}')
    investigation = demisto.investigation()
    demisto.debug(f'The investigation information is {investigation}')

    incident_id = investigation['id']
    incident_status = investigation['status']

    demisto.debug(f'The XSOAR incident is {incident_id} with status {incident_status} is being mirrored with the alert {alert_short_id} that have the status {alert_status}.')

    # Close the XSOAR incident using mirroring
    if ((close_incident) and (alert_status in ["Closed", "Rejected"]) and (investigation['status'] != 1)):
        demisto.debug(f'Alert {alert_short_id} with status {alert_status} was closed or rejected in Sekoia, closing incident {incident_id} in XSOAR')
        entries = [{
                'Type': EntryType.NOTE,
                'Contents': {
                    'dbotIncidentClose': True,
                    'closeReason': f'{alert_status} - Mirror',
                    'closeNotes': close_note
                },
                'ContentsFormat': EntryFormat.JSON
            }]

    # Reopen the XSOAR incident using mirroring
    if ((reopen_incident) and (alert_status not in ["Closed", "Rejected"]) and (investigation['status'] == 1)):
        demisto.debug(f'Alert {alert_short_id} with status {alert_status} was reopened in Sekoia, reopening incident {incident_id} in XSOAR')
        entries = [{
                'Type': EntryType.NOTE,
                'Contents': {
                    'dbotIncidentReopen': True
                },
                'ContentsFormat': EntryFormat.JSON
            }]

    demisto.debug(f'#### Leaving MIRRORING IN - get_remote_data_command ####')

    return GetRemoteDataResponse(mirrored_object=alert, entries=entries)



def get_modified_remote_data_command(client, args):
    """ Gets the list of all alert ids that have change since a given time

    Args:
        client (Client): Sekoia XDR client to use.
        args (dict): The command argumens

    Returns:
        GetModifiedRemoteDataResponse: The response containing the list of ids of notables changed
    """
    modified_alert_ids = []
    remote_args = GetModifiedRemoteDataArgs(args)
    last_update = remote_args.last_update
    last_update_utc = dateparser.parse(last_update, settings={'TIMEZONE': 'UTC'})  # converts to a UTC timestamp
    formatted_last_update = last_update_utc.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00')

    demisto.debug(formatted_last_update)
    converted_time = time_converter(formatted_last_update)
    last_update_time = converted_time + ',now'

    raw_alerts = client.list_alerts(alerts_updatedAt=last_update_time, alerts_limit=100,alerts_status=None,
                    alerts_createdAt=None,alerts_urgency=None,alerts_type=None,sort_by='updated_at')

    for item in raw_alerts['items']:
        modified_alert_ids.append(item['short_id'])

    return_results(GetModifiedRemoteDataResponse(modified_incident_ids=modified_alert_ids))

def update_remote_system_command(client, args):
    """update-remote-system command: pushes local changes to the remote system

    :type client: ``Client``
    :param client: XSOAR client to use

    :type args: ``Dict[str, Any]``
    :param args:
        all command arguments, usually passed from ``demisto.args()``.
        ``args['data']`` the data to send to the remote system
        ``args['entries']`` the entries to send to the remote system
        ``args['incidentChanged']`` boolean telling us if the local incident indeed changed or not
        ``args['remoteId']`` the remote incident id
        args: A dictionary containing the data regarding a modified incident, including: data, entries, incident_changed,
         remote_incident_id, inc_status, delta

    :return:
        ``str`` containing the remote incident id - really important if the incident is newly created remotely

    :rtype: ``str``
    """
    demisto.debug(f'#### Entering MIRRORING OUT - update_remote_system_command ####')
    parsed_args = UpdateRemoteSystemArgs(args)
    delta = parsed_args.delta
    remote_incident_id = parsed_args.remote_incident_id
    xsoar_incident = parsed_args.data.get('xsoar_id')
    demisto.debug(f'parsed_args: {parsed_args.data}')
    demisto.debug(f'delta: {delta}')
    demisto.debug(f'remote_incident_id: {remote_incident_id}')
    demisto.debug(f'local_incident_id: {xsoar_incident}')
    demisto.debug(f'changes: {parsed_args.incident_changed}')
    try:
        if parsed_args.incident_changed:
            sekoia_status = delta.get("status", None)
            closing_notes = delta.get("closeNotes", "")
            if sekoia_status:
                demisto.debug(f'The incident #{xsoar_incident} had the sekoia status of the alert {remote_incident_id} changed to: {sekoia_status}. Sending changes to Sekoia.')
                sekoia_transition = STATUS_TRANSITIONS.get(sekoia_status)

                workflow = client.get_workflow_alert(alert_uuid=remote_incident_id)
                for action in workflow['actions']:
                    if action['name'] == sekoia_transition:
                        change_status = client.update_status_alert(alert_uuid=remote_incident_id,action_uuid=action['id'],comment=None)
                        demisto.debug(change_status)

    except Exception as e:
        demisto.error(f'Error in Sekoia outgoing mirror for incident {remote_incident_id}. '
                      f'Error message: {str(e)}')

    return remote_incident_id


def get_mapping_fields_command() -> GetMappingFieldsResponse:
    """
     this command pulls the remote schema for the different incident types, and their associated incident fields,
     from the remote system.
    :return: A list of keys you want to map
    """
    sekoia_incident_type_scheme = SchemeTypeMapping(type_name=INCIDENT_TYPE_NAME)
    for argument, description in SEKOIA_INCIDENT_FIELDS.items():
        sekoia_incident_type_scheme.add_field(name=argument, description=description)

    mapping_response = GetMappingFieldsResponse()
    mapping_response.add_scheme_type(sekoia_incident_type_scheme)

    return mapping_response


# =========== Mirroring Mechanism ===========


def list_alerts_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    limit = args.get('limit')
    status = args.get('status')
    created_at = args.get('created_at')
    updated_at = args.get('updated_at')
    urgency = args.get('urgency')
    alerts_type = args.get('alerts_type')
    sort_by = args.get('sort_by')

    alerts = client.list_alerts(alerts_limit=limit,alerts_status=status,alerts_createdAt=created_at,alerts_updatedAt=updated_at,
                                alerts_urgency=urgency,alerts_type=alerts_type,sort_by=sort_by)

    return CommandResults(
        outputs_prefix='SekoiaXDR.ListAlerts',
        outputs_key_field='short_id',
        outputs=alerts['items']
    )

def get_alert_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    alert_uuid = args.get('id')

    alert = client.get_alert(alert_uuid=alert_uuid)

    readable_output = tableToMarkdown(f'Alert {alert_uuid}:', alert)

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.Alert',
        outputs_key_field='uuid',
        outputs=alert
    )

def query_events_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    earliest_time = args.get('earliest_time')
    lastest_time = args.get('lastest_time')
    term = args.get('query')
    max_last_events = args.get('max_last_events')

    jobQuery = client.query_events(events_earliest_time=earliest_time,events_lastest_time=lastest_time,
                                events_term=term,max_last_events=max_last_events)

    readable_output = tableToMarkdown(f'Event search created using the term {term}:', jobQuery)

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.Events',
        outputs_key_field='uuid',
        outputs=jobQuery
    )

def query_events_status_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    search_job_uuid = args.get('uuid')

    status = client.query_events_status(event_search_job_uuid=search_job_uuid)

    readable_output = tableToMarkdown(f'Status of the job {search_job_uuid}:', status)

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.Events',
        outputs_key_field='search_job_uuid',
        outputs=status
    )

def retrieve_events_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    search_job_uuid = args.get('uuid')

    events = client.retrieve_events(event_search_job_uuid=search_job_uuid)

    readable_output = tableToMarkdown(f'Events retrieved for the search {search_job_uuid}:', events)

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.Events',
        outputs_key_field='search_job_uuid',
        outputs=events['items']
    )

def search_events_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    earliest_time = args.get('earliest_time')
    lastest_time = args.get('lastest_time')

    term = args.get('query')

    interval_in_seconds = int(args.get('interval_in_seconds'))
    timeout_in_seconds = int(args.get('timeout_in_seconds'))
    max_last_events = args.get('max_last_events')
    exclude_info_arg = args.get('exclude_info')
    exclude_info_param = demisto.params().get('exclude_info_events')
    replace_symbol = demisto.params().get('replace_dots_event')

    search = client.query_events(events_earliest_time=earliest_time,events_lastest_time=lastest_time,
                                events_term=term,max_last_events=max_last_events)
    search_job_uuid = search['uuid']

    start_time = time.time()
    while True:
        if time.time() - start_time > timeout_in_seconds:
            print ("The query of the events have timeout without a valid status result.")
            break
        query_status = client.query_events_status(event_search_job_uuid=search_job_uuid)
        status = query_status['status']
        if status == 2:
            events = client.retrieve_events(event_search_job_uuid=search_job_uuid)
            if max_last_events:
                total = max_last_events
            else:
                total = events['total']

            # If there is event info to exclude sent on arguments
            if exclude_info_arg and len(events['items']) > 0:
                ''' Collect the headers with the removed info and replace the dots'''
                headers = exclude_info_events(event_info=events, exclude_info=exclude_info_arg)
                headers = [header.replace(".",replace_symbol) for header in headers]
                ''' Remove dots from events key names'''
                events_undot = undot(json_data=events)
                readable_output = tableToMarkdown(f'{total} events out of ' + str(events['total']) + f' retrieved for the {term}:', events['items'],headers=headers if ['items'] else None)

            # If there is event info to exclude in the paramenters but not sent in the arguments
            elif exclude_info_param and len(events['items']) > 0 and exclude_info_arg is None:
                ''' Collect the headers with the removed info and replace the dots'''
                headers = exclude_info_events(event_info=events, exclude_info=",".join(exclude_info_param))
                headers = [header.replace(".",replace_symbol) for header in headers]
                ''' Remove dots from events key names'''
                events_undot = undot(json_data=events)
                readable_output = tableToMarkdown(f'{total} events out of ' + str(events['total']) + f' retrieved for the {term}:', events['items'],headers=headers if ['items'] else None)

            # If there is no event info to exclude in the paramenters nor in the arguments
            elif (exclude_info_arg is None) and (not exclude_info_param) and (len(events['items']) > 0):
                events_undot = undot(json_data=events)
                readable_output = tableToMarkdown(f'{total} events out of ' + str(events['total']) + f' retrieved for the {term}:', events['items'])

            # If there is no events found
            elif len(events['items']) <= 0:
                readable_output = tableToMarkdown(f'{total} events out of ' + str(events['total']) + f' retrieved for the {term}:', events['items'])

            # ELSE
            else:
                readable_output = tableToMarkdown(f'{total} events out of ' + str(events['total']) + f' retrieved for the {term}:', events['items'])

            return CommandResults(
                readable_output=readable_output,
                outputs_prefix='SekoiaXDR.Events.Results',
                outputs_key_field='search_job_uuid',
                outputs=events
            )
            break
        time.sleep(interval_in_seconds)


def update_status_alert_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    alert_uuid = args.get('id')
    updated_status = args.get('status')
    sekoia_transition = STATUS_TRANSITIONS.get(updated_status)
    comment = args.get('comment')
    readable_output = "Unknown alert"

    workflow = client.get_workflow_alert(alert_uuid=alert_uuid)

    for action in workflow['actions']:
        if action['name'] == sekoia_transition:
            update = client.update_status_alert(alert_uuid=alert_uuid,action_uuid=action['id'],comment=comment)
            if update or update == {}:
                readable_output = "### Alert " + alert_uuid + " updated to status: " + updated_status
            else:
                raise ValueError("Failure to update the status of the alert. Run the command !sekoia-get-workflow-alert to see the possible transitions and review the code.")

    return CommandResults(
        readable_output=readable_output
    )


def post_comment_alert_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    alert_uuid = args.get('id')
    comment = args.get('comment')
    author = args.get('author')

    response = client.post_comment_alert(alert_uuid=alert_uuid,content=comment,author=author)

    readable_output = tableToMarkdown(f'Alert {alert_uuid} updated with the comment: \n {comment}:', response)

    return CommandResults(
        readable_output=readable_output,
        outputs=response
    )

def get_comments_alert_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    alert_uuid = args.get('id')

    response = client.get_comments_alert(alert_uuid=alert_uuid)

    for item in response['items']:
        # Add author of the comment
        if(item['author'].startswith('user')):
            user = client.get_user(user_uuid=item['created_by'])
            item['user'] = user.get('firstname') + ' ' + user.get('lastname')
        elif(item['author'].startswith('apikey')):
            item['user'] = 'Commented via API'
        elif(item['author'].startswith('application')):
            item['user'] = 'Sekoia.io'
        else:
            item['user'] = item['author']
        # Add formated date of the comment
        item['date'] = timezone_format(item['date'])

    readable_output = tableToMarkdown(f'Alert {alert_uuid} have the following comments:', response['items'])

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.Comments',
        outputs_key_field='alert_uuid',
        outputs=response
    )

def get_workflow_alert_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    alert_uuid = args.get('id')

    response = client.get_workflow_alert(alert_uuid=alert_uuid)

    readable_output = tableToMarkdown(f'Alert {alert_uuid} have the following available status transitions:', response['actions'])

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.StatusTransitions',
        outputs_key_field='alert_uuid',
        outputs=response
    )

def get_cases_alert_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    alert_uuid = args.get('alert_id')
    case_id = args.get('case_id')

    response = client.get_cases_alert(alert_uuid=alert_uuid,case_id=case_id)

    readable_output = tableToMarkdown(f'Alert {alert_uuid} have the following cases:', response['items'])

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.Cases',
        outputs_key_field='alert_uuid',
        outputs=response['items']
    )

def get_asset_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    asset_uuid = args.get('asset_uuid')

    asset = client.get_asset(asset_uuid=asset_uuid)
    readable_output = tableToMarkdown(f'Asset {asset_uuid} have the following information:', asset)

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.Asset',
        outputs_key_field='uuid',
        outputs=asset
    )

def list_asset_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    limit = args.get('limit')
    assets_type = args.get('assets_type')

    assets = client.list_asset(limit=limit,assets_type=assets_type)
    num_assets = assets['total']
    readable_output = tableToMarkdown(f'List of {num_assets} assets found:', assets['items'])

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.Assets',
        outputs_key_field='asset_uuid',
        outputs=assets
    )

def get_user_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    user_uuid = args.get('user_uuid')
    user = client.get_user(user_uuid=user_uuid)
    readable_output = tableToMarkdown(f'User {user_uuid} have the following information:', user)

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.User',
        outputs_key_field='user_uuid',
        outputs=user
    )
def add_attributes_asset_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    asset_uuid = args.get('asset_uuid')
    name = args.get('name')
    value = args.get('value')

    asset_attributes = client.add_attributes_asset(asset_uuid=asset_uuid,name=name,value=value)
    readable_output = tableToMarkdown(f'Asset {asset_uuid} was updated with new attributes:', asset_attributes)

    return CommandResults(
        readable_output=readable_output,
        outputs_key_field='asset_uuid',
        outputs=asset_attributes
    )

def add_keys_asset_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    asset_uuid = args.get('asset_uuid')
    name = args.get('name')
    value = args.get('value')

    asset_keys = client.add_keys_asset(asset_uuid=asset_uuid,name=name,value=value)
    readable_output = tableToMarkdown(f'Asset {asset_uuid} was updated with new keys:', asset_keys)

    return CommandResults(
        readable_output=readable_output,
        outputs_key_field='asset_uuid',
        outputs=asset_keys
    )

def remove_attribute_asset_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    asset_uuid = args.get('asset_uuid')
    attribute_uuid = args.get('attribute_uuid')

    remove_asset_attribute = client.remove_attribute_asset(asset_uuid=asset_uuid,attribute_uuid=attribute_uuid)
    readable_output = f'Asset {asset_uuid} had the following attribute removed:\n{attribute_uuid}'

    return CommandResults(
        readable_output=readable_output
    )

def remove_key_asset_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    asset_uuid = args.get('asset_uuid')
    key_uuid = args.get('key_uuid')

    remove_asset_key = client.remove_key_asset(asset_uuid=asset_uuid,key_uuid=key_uuid)
    readable_output = f'Asset {asset_uuid} had the following key removed:\n{key_uuid}'

    return CommandResults(
        readable_output=readable_output
    )

def get_kill_chain_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    kill_chain_uuid = args.get('kill_chain_uuid')

    kill_chain = client.get_kill_chain(kill_chain_uuid=kill_chain_uuid)
    readable_output = tableToMarkdown(f'Kill chain {kill_chain_uuid} have the following information:', kill_chain)

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.KillChain',
        outputs_key_field='uuid',
        outputs=kill_chain
    )

def http_request_command(client: Client, args: Dict[str, Any]) -> CommandResults:

    ''' Parameters'''
    method = args.get('method')
    url_sufix = args.get('url_sufix')
    params = args.get('parameters')


    request = client.http_request(method=method,params=params,url_sufix=url_sufix)
    readable_output = tableToMarkdown(f'The HTTP {method} request with params {params} returned the following information:', request)

    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='SekoiaXDR.http_request',
        outputs_key_field='uuid',
        outputs=request
    )


def test_module(client: Client, params: Dict[str, Any], first_fetch_time: int) -> str:
    """
    Tests API connectivity and authentication'
    When 'ok' is returned it indicates the integration works like it is supposed to and connection to the service is
    successful.
    Raises exceptions if something goes wrong.

    Args:
        client (Client): Sekoia XDR client to use.
        params (Dict): Integration parameters.
        first_fetch_time (int): The first fetch time as configured in the integration params.

    Returns:
        str: 'ok' if test passed, anything else will raise an exception and will fail the test.
    """
    try:
            if params.get('isFetch'):  # Tests fetch incident:
                alerts_status = params.get('alerts_status', None)
                alerts_type = params.get('alerts_type', None)
                alerts_urgency = params.get('alerts_urgency', None)
                fetch_mode = params.get('fetch_mode', None)

                fetch_incidents(
                client=client,
                max_results=1,
                last_run={},
                first_fetch_time=first_fetch_time,
                alert_status=alerts_status,
                alert_urgency=alerts_urgency,
                alert_type=alerts_type,
                fetch_mode=None,
                mirror_direction=None,
                fetch_with_assets=False,
                fetch_with_kill_chain=False
                )

            else:
                client.list_alerts(alerts_limit=1,alerts_status=None,alerts_createdAt='-30d,now', alerts_updatedAt=None,
                                alerts_urgency=None,alerts_type=None,sort_by=None)

    except DemistoException as e:
        if 'Forbidden' in str(e):
            return 'Authorization Error: make sure API Key is correctly set'
        else:
            raise e

    return 'ok'




def main() -> None:
    """
    main function, parses params and runs command functions
    """

    params = demisto.params()
    args = demisto.args()
    command = demisto.command()

    api_key = params.get('credentials', {}).get('password')

    # get the service API url
    base_url = urljoin(params.get('url'), '/v1')

    # if your Client class inherits from BaseClient, SSL verification is
    # handled out of the box by it, just pass ``verify_certificate`` to
    # the Client constructor
    verify_certificate = not params.get('insecure', False)

    # How much time before the first fetch to retrieve incidents
    first_fetch_time = arg_to_datetime(
        arg=params.get('first_fetch', '3 days'),
        arg_name='First fetch time',
        required=True
    )
    first_fetch_timestamp = int(first_fetch_time.timestamp()) if first_fetch_time else None
    # Using assert as a type guard (since first_fetch_time is always an int when required=True)
    assert isinstance(first_fetch_timestamp, int)

    # if your Client class inherits from BaseClient, system proxy is handled
    # out of the box by it, just pass ``proxy`` to the Client constructor
    proxy = params.get('proxy', False)

    demisto.debug(f'Command being called is {command}')
    try:
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        client = Client(
            base_url=base_url,
            verify=verify_certificate,
            headers=headers,
            proxy=proxy)

        if command == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(client, params, first_fetch_timestamp)
            return_results(result)

        elif command == 'fetch-incidents':
            # Set and define the fetch incidents command to run after activated via integration settings.
            alerts_status = ','.join(params.get('alerts_status', None))
            alerts_type = ','.join(params.get('alerts_type', None))
            alerts_urgency = params.get('alerts_urgency', None)
            fetch_mode = params.get('fetch_mode')
            fetch_with_assets = params.get('fetch_with_assets')
            fetch_with_kill_chain = params.get('fetch_with_kill_chain')
            mirror_direction = params.get('mirror_direction')

            # Convert the argument to an int using helper function or set to MAX_INCIDENTS_TO_FETCH
            max_results = params.get('max_fetch', MAX_INCIDENTS_TO_FETCH)

            if not max_results:# or max_results > MAX_INCIDENTS_TO_FETCH:
                max_results = MAX_INCIDENTS_TO_FETCH

            next_run, incidents = fetch_incidents(
                client=client,
                max_results=max_results,
                last_run=demisto.getLastRun(),  # getLastRun() gets the last run dict
                first_fetch_time=first_fetch_timestamp,
                alert_status=alerts_status,
                alert_urgency=alerts_urgency,
                alert_type=alerts_type,
                fetch_mode=fetch_mode,
                mirror_direction=mirror_direction,
                fetch_with_assets=fetch_with_assets,
                fetch_with_kill_chain=fetch_with_kill_chain
            )

            # saves next_run for the time fetch-incidents is invoked
            demisto.setLastRun(next_run)
            # fetch-incidents calls ``demisto.incidents()`` to provide the list of incidents to create
            demisto.incidents(incidents)


        elif command == 'sekoia-list-alerts':
            return_results(list_alerts_command(client,args))
        elif command == 'sekoia-get-alert':
            return_results(get_alert_command(client,args))
        elif command == 'sekoia-events-execute-query':
            return_results(query_events_command(client,args))
        elif command == 'sekoia-events-status-query':
            return_results(query_events_status_command(client,args))
        elif command == 'sekoia-events-results-query':
            return_results(retrieve_events_command(client,args))
        elif command == 'sekoia-search-events':
            return_results(search_events_command(client,args))
        elif command == 'sekoia-update-status-alert':
            return_results(update_status_alert_command(client,args))
        elif command == 'sekoia-post-comment-alert':
            return_results(post_comment_alert_command(client,args))
        elif command == 'sekoia-get-comments':
            return_results(get_comments_alert_command(client,args))
        elif command == 'sekoia-get-workflow-alert':
            return_results(get_workflow_alert_command(client,args))
        elif command == 'sekoia-get-cases-alert':
            return_results(get_cases_alert_command(client,args))
        elif command == 'sekoia-get-asset':
            return_results(get_asset_command(client,args))
        elif command == 'sekoia-list-assets':
            return_results(list_asset_command(client,args))
        elif command == 'sekoia-get-user':
            return_results(get_user_command(client,args))
        elif command == 'sekoia-add-attributes-asset':
            return_results(add_attributes_asset_command(client,args))
        elif command == 'sekoia-add-keys-asset':
            return_results(add_keys_asset_command(client,args))
        elif command == 'sekoia-remove-attribute-asset':
            return_results(remove_attribute_asset_command(client,args))
        elif command == 'sekoia-remove-key-asset':
            return_results(remove_key_asset_command(client,args))
        elif command == 'sekoia-get-kill-chain':
            return_results(get_kill_chain_command(client,args))
        elif command == 'sekoia-http-request':
            return_results(http_request_command(client,args))
        elif command == 'get-remote-data':
            return_results(get_remote_data_command(client,args,
                                                    close_incident=demisto.params().get('close_incident'),
                                                    close_note=demisto.params().get('close_note'),
                                                    mirror_events=demisto.params().get('mirror_events'),
                                                    mirror_kill_chain=demisto.params().get('mirror_kill_chain'),
                                                    reopen_incident=demisto.params().get('reopen_incident')))
        elif command == 'get-modified-remote-data':
            get_modified_remote_data_command(client,args)
        elif command == 'update-remote-system':
            update_remote_system_command(client,args)
        elif command == 'get-mapping-fields':
            return_results(get_mapping_fields_command())
        else:
            raise NotImplementedError(f'Command {command} is not implemented')

    # Log exceptions and return errors
    except Exception as e:
        return_error(f'Failed to execute {command} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
