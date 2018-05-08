#!/bin/sh
AUTH=`base64 -w 0 <client-data`
COOKIE=`cat cookie`
echo $AUTH $COOKIE
curl -XPOST -H "Content-Type:application/json" \
     -H "Authorization:Basic $AUTH" \
     -d "{\"grant_type\":\"authorization_code\", \"code\":\"$COOKIE\"}" \
     https://login.eveonline.com/oauth/token | 
aeson-pretty |
tee authresult
