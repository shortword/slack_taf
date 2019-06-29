# slack_taf
Google Cloud function code for retriving METARs and TAF for a slash command in Slack.

## Basic About

Currently this is designed to be run in a Google Cloud function.
Plenty more still to do, but it seems to work most of the time.

Data source is the US National Weather Service / Aviation Weather, so available locations are whatever they are currently providing.

## Installing
A basic `gcloud` command to install this software would look something like this:
```
gcloud functions deploy slack_taf --entry-point=getSlackTaf --runtime=python37 --set-env-vars=SLACK_SIGNING_TOKEN=your_signing_token_here --memory=128MB --trigger-http
gcloud functions deploy slack_metar --entry-point=getSlackMetar --runtime=python37 --set-env-vars=SLACK_SIGNING_TOKEN=your_signing_token_here --memory=128MB --trigger-http
```