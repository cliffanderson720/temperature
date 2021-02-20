# Configuration
Configuration options in `params.yaml` are used to query the API and in writing the temperature logs.

Using this module requires an account with OpenWeather. Parameters used to query the API, notably the
APPID, are stored in `params.yaml`. If the thermostat setpoint is not constant, the schedule may be provided under the 
`setpoints` field as key pairs of `transition time (24h): new setpoint`.

```
APPID: xxxxx
q: City
units: imperial

setpoints:
  6.5: 65
  12: 63
  20: 58
```