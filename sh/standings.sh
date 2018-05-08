#!/bin/sh
CHARID=`cat charid`
ACCESS=`cat access`
curl -H "Content-Type:application/json" \
    "https://esi.evetech.net/v1/characters/$CHARID/standings/?token=$ACCESS" |
aeson-pretty
