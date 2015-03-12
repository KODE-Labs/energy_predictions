from eemeter.weather import WeatherSourceBase
from eemeter.weather import GSODWeatherSource
from eemeter.weather import ISDWeatherSource
from eemeter.weather import TMY3WeatherSource
from eemeter.weather import WeatherUndergroundWeatherSource
from eemeter.weather import zipcode_to_lat_lng
from eemeter.weather import lat_lng_to_zipcode
from eemeter.weather import tmy3_to_lat_lng
from eemeter.weather import lat_lng_to_tmy3
from eemeter.weather import zipcode_to_tmy3
from eemeter.weather import tmy3_to_zipcode
from eemeter.weather import haversine

from eemeter.consumption import ConsumptionHistory
from eemeter.consumption import Consumption

from datetime import datetime
import pytest
import os
import warnings

from numpy.testing import assert_allclose

RTOL = 1e-1
ATOL = 1e-1

##### Fixtures #####

@pytest.fixture
def consumption_history_one_summer_electricity():
    c_list = [Consumption(1600,"kWh","electricity",datetime(2012,6,1),datetime(2012,7,1)),
              Consumption(1700,"kWh","electricity",datetime(2012,7,1),datetime(2012,8,1)),
              Consumption(1800,"kWh","electricity",datetime(2012,8,1),datetime(2012,9,1))]
    return ConsumptionHistory(c_list)

@pytest.fixture(params=[(41.8955360374983,-87.6217660821178,"725340"),
                        (34.1678563835543,-118.126220490392,"722880"),
                        (42.3769095103979,-71.1247640734676,"725090"),
                        (42.3594006437094,-87.8581578622419,"725347")])
def lat_long_station(request):
    return request.param

@pytest.fixture(params=[(41.8955360374983,-87.6217660821178,"60611"),
                        (34.1678563835543,-118.126220490392,"91104"),
                        (42.3769095103979,-71.1247640734676,"02138"),
                        (42.3594006437094,-87.8581578622419,"60085"),
                        (None,None,"00000")])
def lat_long_zipcode(request):
    return request.param

@pytest.fixture(params=[('722874-93134',2012,2012),
                        ('722874',2012,2012)])
def gsod_weather_source(request):
    return request.param

@pytest.fixture(params=[('722874-93134',2012,2012),
                        ('722874',2012,2012)])
def isd_weather_source(request):
    return request.param

@pytest.fixture(params=[TMY3WeatherSource('722880')])
def tmy3_weather_source(request):
    return request.param

@pytest.fixture(params=[("60611","725340"),
                        ("91104","722880"),
                        ("02138","725090"),
                        ("60085","725347")])
def zipcode_to_station(request):
    return request.param


##### Tests #####

def test_zipcode_to_lat_lng(lat_long_zipcode):
    lat_lngs = [(41.8955360374983,-87.6217660821178),
               (34.1678563835543,-118.126220490392),
               (42.3769095103979,-71.1247640734676),
               (42.3594006437094,-87.8581578622419)]
    zipcodes = ["60611","91104","02138","60085"]
    for (lat,lng),zipcode in zip(lat_lngs,zipcodes):
        assert lat,lng == zipcode_to_lat_lng(zipcode)

def test_lat_lng_to_zipcode():
    lat_lngs = [(41.8955360374983,-87.6217660821178),
               (34.1678563835543,-118.126220490392),
               (42.3769095103979,-71.1247640734676),
               (42.3594006437094,-87.8581578622419)]
    zipcodes = ["60611","91104","02138","60085"]
    for (lat,lng),zipcode in zip(lat_lngs,zipcodes):
        assert zipcode == lat_lng_to_zipcode(lat,lng)

def test_tmy3_to_lat_lng():
    lat_lngs = [(41.8955360374983,-87.6217660821178),
               (34.1678563835543,-118.126220490392),
               (42.3769095103979,-71.1247640734676),
               (42.3594006437094,-87.8581578622419)]
    stations = ["725340","722880","725090","725347"]
    for (lat,lng),station in zip(lat_lngs,stations):
        assert lat,lng == tmy3_to_lat_lng(station)

def test_lat_lng_to_tmy3():
    lat_lngs = [(41.8955360374983,-87.6217660821178),
               (34.1678563835543,-118.126220490392),
               (42.3769095103979,-71.1247640734676),
               (42.3594006437094,-87.8581578622419)]
    stations = ["725340","722880","725090","725347"]
    for (lat,lng),station in zip(lat_lngs,stations):
        assert station == lat_lng_to_tmy3(lat,lng)

def test_zipcode_to_tmy3():
    zipcodes = ["60611","91104","02138","60085"]
    stations = ["725340","722880","725090","725347"]
    for zipcode,station in zip(zipcodes,stations):
        assert station == zipcode_to_tmy3(zipcode)

def test_tmy3_to_zipcode():
    zipcodes = ["97459","45433","55601","96740"]
    stations = ["726917","745700","727556","911975"]
    for zipcode,station in zip(zipcodes,stations):
        assert zipcode == tmy3_to_zipcode(station)

def test_weather_source_base(consumption_history_one_summer_electricity):
    weather_source = WeatherSourceBase()
    consumptions = consumption_history_one_summer_electricity.get("electricity")
    with pytest.raises(NotImplementedError):
        avg_temps = weather_source.get_average_temperature(consumptions,"degF")
    with pytest.raises(NotImplementedError):
        hdds = weather_source.get_hdd(consumptions,"degF",base=65)

@pytest.mark.slow
@pytest.mark.internet
def test_gsod_weather_source(consumption_history_one_summer_electricity,gsod_weather_source):
    gsod_weather_source = GSODWeatherSource(*gsod_weather_source)
    consumptions = consumption_history_one_summer_electricity.get("electricity")

    avg_temps = gsod_weather_source.get_average_temperature(consumptions,"degF")
    assert_allclose(avg_temps, [66.3833,67.803,74.445], rtol=RTOL,atol=ATOL)

    hdds = gsod_weather_source.get_hdd(consumptions,"degF",65)
    assert_allclose(hdds, [0.7,20.4,0.0], rtol=RTOL,atol=ATOL)

    cdds = gsod_weather_source.get_cdd(consumptions,"degF",65)
    assert_allclose(cdds, [42.2,107.3,292.8], rtol=RTOL,atol=ATOL)

    hdds_per_day = gsod_weather_source.get_hdd_per_day(consumptions,"degF",65)
    assert_allclose(hdds_per_day, [0.023,0.658,0.0], rtol=RTOL,atol=ATOL)

    cdds_per_day = gsod_weather_source.get_cdd_per_day(consumptions,"degF",65)
    assert_allclose(cdds_per_day, [1.406,3.461,9.445], rtol=RTOL,atol=ATOL)

@pytest.mark.slow
@pytest.mark.internet
def test_weather_underground_weather_source(consumption_history_one_summer_electricity):
    wunderground_api_key = os.environ.get('WEATHERUNDERGROUND_API_KEY')
    if wunderground_api_key:
        wu_weather_source = WeatherUndergroundWeatherSource('60605',
                                                            datetime(2012,6,1),
                                                            datetime(2012,10,1),
                                                            wunderground_api_key)
        consumptions = consumption_history_one_summer_electricity.get("electricity")

        avg_temps = wu_weather_source.get_average_temperature(consumptions,"degF")
        assert_allclose(avg_temps, [74.433,82.677,75.451], rtol=RTOL,atol=ATOL)

        hdds = wu_weather_source.get_hdd(consumptions,"degF",65)
        assert_allclose(hdds, [14.0,0.0,0.0], rtol=RTOL,atol=ATOL)

        cdds = wu_weather_source.get_cdd(consumptions,"degF",65)
        assert_allclose(cdds, [297.0,548.0,324.0], rtol=RTOL,atol=ATOL)
    else:
        warnings.warn("Skipping WeatherUndergroundWeatherSource tests. "
            "Please set the environment variable "
            "WEATHERUNDERGOUND_API_KEY to run the tests.")

@pytest.mark.slow
@pytest.mark.internet
def test_isd_weather_source(consumption_history_one_summer_electricity,isd_weather_source):
    isd_weather_source = ISDWeatherSource(*isd_weather_source)
    consumptions = consumption_history_one_summer_electricity.get("electricity")

    avg_temps = isd_weather_source.get_average_temperature(consumptions,"degF")
    assert_allclose(avg_temps, [66.576,68.047,74.697], rtol=RTOL,atol=ATOL)

    hdds = isd_weather_source.get_hdd(consumptions,"degF",65)
    assert_allclose(hdds, [0.294,20.309,0.0], rtol=RTOL,atol=ATOL)

    cdds = isd_weather_source.get_cdd(consumptions,"degF",65)
    assert_allclose(cdds, [47.603,113.775,300.722], rtol=RTOL,atol=ATOL)

@pytest.mark.slow
@pytest.mark.internet
def test_tmy3_weather_source(consumption_history_one_summer_electricity,tmy3_weather_source):
    consumptions = consumption_history_one_summer_electricity.get("electricity")

    avg_temps = tmy3_weather_source.get_average_temperature(consumptions,"degF")
    assert_allclose(avg_temps, [68.1822,73.05548,74.315], rtol=RTOL,atol=ATOL)

    hdds = tmy3_weather_source.get_hdd(consumptions,"degF",65)
    assert_allclose(hdds, [10.072,0.0749,0.0], rtol=RTOL,atol=ATOL)

    cdds = tmy3_weather_source.get_cdd(consumptions,"degF",65)
    assert_allclose(cdds, [105.540,249.795,288.780], rtol=RTOL,atol=ATOL)

def test_haversine():
    lat_lng_dists = [(0,0,0,0,0),
                     (76,1,76,1,0),
                     (76,1,76,361,0),
                     (0,0,0,90,10007.54339801),
                     (0,0,0,180,20015.08679602),
                     (0,-180,0,180,0),
                     (-90,0,90,0,20015.08679602),
                     (-90,0,90,180,20015.08679602),
                     ]

    for lat1,lng1,lat2,lng2,dist in lat_lng_dists:
        assert_allclose(haversine(lat1,lng1,lat2,lng2),dist,rtol=RTOL,atol=ATOL)

