import datetime
import os
import traceback
import uuid

import AlgorumQuantClient.algorum_types
import golden_crossover_quant_strategy
import trend_reversal_quant_strategy
import support_resistance_quant_strategy
import rsi_quant_strategy
import gapup_quant_strategy

if __name__ == '__main__':
    client = None

    try:
        if 'url' in os.environ:
            url = os.environ['url']
        else:
            url = None

        if url is None or url == '':
            url = 'ws://52.66.253.87:5000/quant/engine/api/v1'

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

        if 'samplingTime' in os.environ:
            sampling_time = os.environ['samplingTime']
        else:
            sampling_time = 15

        url += '?sid=' + sid + '&apiKey=' + apikey + '&launchMode=' + launchmode

        # Golden crossover quant strategy
        client = golden_crossover_quant_strategy.GoldenCrossoverQuantStrategy(
            url,
            apikey,
            launchmode,
            sid
        )

        # Trend Reversal quant strategy
        # client = trend_reversal_quant_strategy.TrendReversalQuantStrategy(
        #     url,
        #     apikey,
        #     launchmode,
        #     sid
        # )

        # Support Resistance quant strategy
        # client = support_resistance_quant_strategy.SupportResistanceQuantStrategy(
        #     url,
        #     apikey,
        #     launchmode,
        #     sid
        # )

        # RSI quant strategy
        # client = rsi_quant_strategy.RSIQuantStrategy(
        #     url,
        #     apikey,
        #     launchmode,
        #     sid
        # )

        # GapUp quant strategy
        # client = gapup_quant_strategy.GapUpQuantStrategy(
        #     url,
        #     apikey,
        #     launchmode,
        #     sid
        # )

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
                startDate = datetime.datetime.strptime('01-03-2021', '%d-%m-%Y')

            if 'endDate' in os.environ:
                endDate = datetime.datetime.strptime(os.environ['endDate'], '%d-%m-%Y')
            else:
                endDate = None

            if endDate is None or endDate == '':
                endDate = datetime.datetime.strptime('01-04-2021', '%d-%m-%Y')

            backtestRequest = AlgorumQuantClient.algorum_types.BacktestRequest(
                startDate, endDate, sid, bk_api_key, bk_api_secret_key,
                client_code, password, two_factor_auth, sampling_time, brokerage_platform,
                golden_crossover_quant_strategy.GoldenCrossoverQuantStrategy.Capital)
            client.backtest(backtestRequest)
        else:
            tradingRequest = AlgorumQuantClient.algorum_types.TradingRequest(
                bk_api_key, bk_api_secret_key,
                client_code, password, two_factor_auth, sampling_time, brokerage_platform,
                golden_crossover_quant_strategy.GoldenCrossoverQuantStrategy.Capital)
            client.start_trading(tradingRequest)

        client.wait()
        print('Main strategy thread exited')
    except Exception:
        print(traceback.format_exc())

        if client is not None:
            client.log(AlgorumQuantClient.algorum_types.LogLevel.Error, traceback.format_exc())

