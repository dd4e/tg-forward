# tg-forward
Telegram message forwarder

## QuickStart

1. Add [@iForwardBot](https://t.me/iForwardBot) bot
2. Send `/token` command
3. Bot return your forward token
4. Use http requests in API to send messages to yourself through the bot

## API Manual

**API Url:** `https://ifwd.dd4e.ru/v1/message`

### Forward message via POST

#### Request

Method: `POST`

Content-Type: `application/json`

Body:

```JSON
{
    "token": "your forward token",
    "message": "forwarded message",
    "format": "'Markdown' or 'HTML'",
    "silent": false
}
```

> `format` is optional, default plain text  
> `silent` is optional, defaul `false`

#### Response

Code: `200`

Content-Type: `application/json`

```JSON
{
    "ok": true,
    "messageID": 512
}
```

### Forward message via GET

#### Request

Method: `GET`

Query params:

- t=`your forward token`
- m=`forwarded message`
- f=`'Markdown' or 'HTML'`
- s=`false`

> `format` is optional, default plain text  
> `silent` is optional, defaul `false`

#### Response

Code: `200`

Content-Type: `application/json`

```JSON
{
    "ok": true,
    "messageID": 512
}
```

### Edit sended message

#### Request

Method: `PUT`

Query params:

- t=`your forward token`
- m=`edited message`
- mid=`forwarded 'messageID'`

#### Response

Code: `200`

Content-Type: `application/json`

```JSON
{
    "ok": true
}
```

### Delete message

Method: `DELETE`

Query params:

- t=`your forward token`
- mid=`forwarded 'messageID'`

#### Response

Code: `200`

Content-Type: `application/json`

```JSON
{
    "ok": true
}
```
