#!/bin/sh
AUTH=`base64 -w 0 <client-data`
REFRESH=`cat refresh`
echo $AUTH $REFRESH
curl -XPOST -H "Content-Type:application/json" \
     -H "Authorization:Basic $AUTH" \
     -d "{\"grant_type\":\"refresh_token\", \"refresh_token\":\"$REFRESH\"}" \
     https://login.eveonline.com/oauth/token |
aeson-pretty |
tee authresult
