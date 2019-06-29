# Copyright 2019 - Michael Bergeron
# Released under the terms of the MIT License
# See the LICENSE file for more information

import json
import logging
import os
from typing import Optional, Tuple

import flask
from lxml import etree
import requests

_baseUrl = "https://www.aviationweather.gov/adds/dataserver_current/httpparam"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)
_logger = logging.getLogger('slack_taf')
_logger.setLevel(logging.WARNING)

_signing_token = os.environ["SLACK_SIGNING_TOKEN"]


def _requestData(tag: str,
                 station: Optional[str] = 'KPDX') -> str:
    """
    Handles the retrieval of the data from NWS ADDS service, and gets the
    first entry in the list of responses (which always seems to be the
    most recent)
    """
    global _baseUrl
    global _logger

    ret_val = ''

    params = {
        'dataSource': '',
        'requestType': 'retrieve',
        'format': 'xml',
        'stationString': station,
        'hoursBeforeNow': 1
    }

    if tag is "METAR":
        params['dataSource'] = "metars"
    elif tag is "TAF":
        params['dataSource'] = "tafs"
    else:
        _logger.warning("Invalid tag: " + str(tag))
        return ret_val

    try:
        _logger.debug("Begin data request")
        resp = requests.get(_baseUrl, params)
        _logger.debug(resp)
        root = etree.fromstring(resp.content)
        _logger.debug(root)
        data_tag = root.find('.//data')
        _logger.debug(data_tag)
        size = data_tag.get('num_results')
        _logger.debug(size)
        if int(size) > 0:
            first_taf = data_tag.find('.//' + tag)
            _logger.debug(first_taf)
            raw_text = first_taf.find('.//raw_text')
            ret_val = raw_text.text
            if tag == "TAF":
                ret_val = ret_val.replace(" FM", "\n     FM")

    except Exception as e: # FIXME: Bare except
        _logger.warning("Hit an exception")
        _logger.warning(e)

    finally:
        _logger.debug("Returning data: " + ret_val)
        return ret_val


def _getStationName(input: flask.Request) -> str:
    """
    Handles changing the station name based on what is provided by the HTTP
    endpoint. Does some sanity checking, but not complete (like fully
    checking that the station is real)
    """
    global _baseUrl
    global _logger

    _logger.debug("Get station name")
    _logger.debug(input)
    ret_val = 'KPDX'

    if not input:   # Support empty input for debug / test
        _logger.debug("No input; skipping station check")
        return ret_val

    val_in = input.form.get('text', type=str)
    _logger.debug("Value in: " + str(val_in))
    if val_in:
        # TODO: We only support one station right now
        val_list = val_in.split(' ')
        val_in = val_list[0]

        # FIXME: A dumb sanity check that the name looks sane
        if len(val_in) == 4:
            _logger.debug("Station length looks OK")
            ret_val = val_in
        else:
            _logger.warning("Invalid station length received")

    _logger.debug("Returning station: " + ret_val)
    return ret_val


def _buildSlackResponse(text: str,
                        inChannel: Optional[bool] = True) -> str:
    """
    Builds responses for Slack commands. Returns the JSON text "body", HTTP
    status code, and headers (content type)
    """
    response = {
        "response_type": "in_channel",
        "text": "Not set"
    }
    if not text:
        response['text'] = 'No text set. Bad identifier? Other error?'
    else:
        response['text'] = text
        response['blocks'] = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```" + text + "```"
            }
        }]

    return json.dumps(response)


def getSlackMetar(input: flask.Request) -> Tuple[str, int, dict]:
    """
    Endpoint handler for the slack_metar HTTP function trigger
    """
    global _baseUrl
    global _logger

    _logger.debug("Entered metar")
    station = _getStationName(input)
    txt = _requestData('METAR', station)
    return (_buildSlackResponse(txt),
            200,
            {'Content-type': 'application/json'})


def getSlackTaf(input: flask.Request) -> Tuple[str, int, dict]:
    """
    Endpoint handler for the slack_taf HTTP function trigger
    """
    global _baseUrl
    global _logger

    _logger.debug("Entered taf")
    station = _getStationName(input)
    txt = _requestData('TAF', station)
    return (_buildSlackResponse(txt),
            200,
            {'Content-type': 'application/json'})


if __name__ == '__main__':
    print(getSlackMetar(None))
    print(getSlackTaf(None))
