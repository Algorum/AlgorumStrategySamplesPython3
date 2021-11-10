import datetime
import os
import traceback
import uuid

import AlgorumQuantClient.algorum_types
import golden_crossover_quant_strategy

if __name__ == '__main__':
    client = None

    try:
        if 'url' in os.environ:
            url = os.environ['url']
        else:
            url = None

        if url is None or url == '':
            url = 'ws://3.108.237.136:5000/quant/engine/api/v1'

        if 'apiKey' in os.environ:
            apikey = os.environ['apiKey']
        else:
            apikey = None

        if apikey is None or apikey == '':
            apikey = '528c9a1b3f8d4382a6af46f8403935dd'

        if 'launchMode' in os.environ:
            launchmode = os.environ['launchMode']
        else:
            launchmode = None

        if launchmode is None or launchmode == '':
            launchmode = AlgorumQuantClient.algorum_types.StrategyLaunchMode.Backtesting

        if 'sid' in os.environ:
            sid = os.environ['sid']
        else:
            sid = None

        if sid is None or sid == '':
            sid = uuid.uuid4().hex

        if 'bkApiKey' in os.environ:
            bk_api_key = os.environ['bkApiKey']
        else:
            bk_api_key = None

        if bk_api_key is None or bk_api_key == '':
            bk_api_key = 'PKKQLPM189KFT0V5DUZY'

        if 'bkApiSecretKey' in os.environ:
            bk_api_secret_key = os.environ['bkApiSecretKey']
        else:
            bk_api_secret_key = None

        if bk_api_secret_key is None or bk_api_secret_key == '':
            bk_api_secret_key = 'MFt6XHNqi0dp46d3kbhvLCNk2JcLNne4rxopZIu5'

        if 'clientCode' in os.environ:
            client_code = os.environ['clientCode']
        else:
            client_code = None

        if 'password' in os.environ:
            password = os.environ['password']
        else:
            password = None

        if 'twoFactorAuth' in os.environ:
            two_factor_auth = os.environ['twoFactorAuth']
        else:
            two_factor_auth = None

        if 'brokerageCountry' in os.environ:
            brokerage_country = os.environ['brokerageCountry']
        else:
            brokerage_country = None

        if brokerage_country is None or brokerage_country == '':
            brokerage_country = 'USA'

        if 'samplingTime' in os.environ:
            sampling_time = os.environ['samplingTime']
        else:
            sampling_time = 15

        url += '?sid=' + sid + '&apiKey=' + apikey + '&launchMode=' + launchmode + '&brokerageCountry=' + brokerage_country

        client = golden_crossover_quant_strategy.GoldenCrossoverQuantStrategy(
            url,
            apikey,
            launchmode,
            sid
        )

        if 'brokeragePlatform' in os.environ:
            brokerage_platform = os.environ['brokeragePlatform']
        else:
            brokerage_platform = None

        if brokerage_platform is None or brokerage_platform == '':
            brokerage_platform = AlgorumQuantClient.algorum_types.BrokeragePlatform.Alpaca

        # Backtesting mode
        if launchmode == AlgorumQuantClient.algorum_types.StrategyLaunchMode.Backtesting:
            if 'startDate' in os.environ:
                startDate = datetime.datetime.strptime(os.environ['startDate'], '%d-%m-%Y')
            else:
                startDate = None

            if startDate is None or startDate == '':
                startDate = datetime.datetime.strptime('07-04-2021', '%d-%m-%Y')

            if 'endDate' in os.environ:
                endDate = datetime.datetime.strptime(os.environ['endDate'], '%d-%m-%Y')
            else:
                endDate = None

            if endDate is None or endDate == '':
                endDate = datetime.datetime.strptime('09-04-2021', '%d-%m-%Y')

            backtestRequest = AlgorumQuantClient.algorum_types.BacktestRequest(
                startDate, endDate, sid, bk_api_key, bk_api_secret_key,
                client_code, password, two_factor_auth, sampling_time, brokerage_platform)
            client.backtest(backtestRequest)
        else:
            tradingRequest = AlgorumQuantClient.algorum_types.TradingRequest(
                bk_api_key, bk_api_secret_key,
                client_code, password, two_factor_auth, sampling_time, brokerage_platform)
            client.start_trading(tradingRequest)

        client.wait()
        print('Main strategy thread exited')
    except Exception:
        print(traceback.format_exc())

        if client is not None:
            client.log(AlgorumQuantClient.algorum_types.LogLevel.Error, traceback.format_exc())
