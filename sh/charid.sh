#!/bin/sh
ACCESS=`cat access`
curl -XGET -H "Authorization: Bearer $ACCESS" \
     https://login.eveonline.com/oauth/verify |
aeson-pretty
