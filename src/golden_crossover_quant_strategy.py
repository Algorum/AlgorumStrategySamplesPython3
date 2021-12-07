import datetime
import threading
import traceback
import uuid

import AlgorumQuantClient.quant_client
import AlgorumQuantClient.algorum_types
import jsonpickle


class GoldenCrossoverQuantStrategy(AlgorumQuantClient.quant_client.QuantEngineClient):
    Capital = 100000
    Leverage = 3  # 3x Leverage on Capital

    class State(object):
        def __init__(self):
            self.Bought = False
            self.LastTick = None
            self.CurrentTick = None
            self.Orders = []
            self.CurrentOrderId = None
            self.CurrentOrder = None
            self.CrossAboveObj = None

    def __init__(self, url, apikey, launchmode, sid, user_id, trace_ws=False):
        try:
            # Pass constructor arguments to base class
            super(GoldenCrossoverQuantStrategy, self).__init__(url, apikey, launchmode, sid, user_id, trace_ws)

            # Load any saved state
            state_json_str = self.get_data("state")

            if state_json_str is not None:
                self.State = jsonpickle.decode(state_json_str)

            if self.State is None or launchmode == AlgorumQuantClient.algorum_types.StrategyLaunchMode.Backtesting:
                self.State = GoldenCrossoverQuantStrategy.State()
                self.State.CrossAboveObj = AlgorumQuantClient.algorum_types.CrossAbove()

            self.StateLock = threading.RLock()

            # Subscribe for our symbol data
            # For India users
            self.symbol = AlgorumQuantClient.algorum_types.TradeSymbol(
                AlgorumQuantClient.algorum_types.SymbolType.FuturesIndex,
                'NIFTY',
                AlgorumQuantClient.algorum_types.FNOPeriodType.Monthly,
                0, 0,
                AlgorumQuantClient.algorum_types.OptionType.Unspecified,
                0, 0)

            # For USA users
            # self.symbol = AlgorumQuantClient.algorum_types.TradeSymbol(
            #     AlgorumQuantClient.algorum_types.SymbolType.Stock,
            #     'MSFT',
            #     AlgorumQuantClient.algorum_types.FNOPeriodType.Monthly,
            #     0, 0,
            #     AlgorumQuantClient.algorum_types.OptionType.Unspecified,
            #     0, 0)

            symbols = [self.symbol]
            self.subscribe_symbols(symbols)

            # Create indicator evaluator, which will be automatically synchronized with the real time or backtesting
            # data that is streaming into this algo
            self.evaluator = self.create_indicator_evaluator(
                AlgorumQuantClient.algorum_types.CreateIndicatorRequest(
                    self.symbol,
                    AlgorumQuantClient.algorum_types.CandlePeriod.Minute,
                    1))
        except Exception:
            print(traceback.format_exc())
            self.log(AlgorumQuantClient.algorum_types.LogLevel.Error, traceback.format_exc())

    # This method is called on each tick for the subscribed symbols
    def on_tick(self, tick_data):
        try:
            self.State.CurrentTick = tick_data

            ema50 = self.Evaluator.ema(50)
            ema200 = self.Evaluator.ema(200)

            if self.State.LastTick is not None and (
                    datetime.datetime.strptime(tick_data.Timestamp,
                                               AlgorumQuantClient.quant_client.QuantEngineClient.get_date_format(
                                                   tick_data.Timestamp)) -
                    datetime.datetime.strptime(self.State.LastTick.Timestamp,
                                               AlgorumQuantClient.quant_client.QuantEngineClient.get_date_format(
                                                   self.State.LastTick.Timestamp))).total_seconds() < 60:
                pass
            else:
                msg = str(tick_data.Timestamp) + ',' + str(tick_data.LTP) + ', ema50 ' \
                      + str(ema50) + ', ema200 ' + str(ema200)
                print(msg)
                self.log(AlgorumQuantClient.algorum_types.LogLevel.Information, msg)
                self.State.LastTick = tick_data

            if ema50 > 0 and ema200 > 0 and \
                    self.State.CrossAboveObj.evaluate(ema50, ema200) and \
                    not self.State.Bought and \
                    self.State.CurrentOrderId is None:
                self.State.CurrentOrderId = uuid.uuid4().hex
                place_order_request = AlgorumQuantClient.algorum_types.PlaceOrderRequest()
                place_order_request.OrderType = AlgorumQuantClient.algorum_types.OrderType.Market
                place_order_request.Price = tick_data.LTP
                place_order_request.Quantity = \
                    (GoldenCrossoverQuantStrategy.Capital / tick_data.LTP) * GoldenCrossoverQuantStrategy.Leverage
                place_order_request.Symbol = self.symbol
                place_order_request.Timestamp = tick_data.Timestamp

                if self.LaunchMode == AlgorumQuantClient.algorum_types.StrategyLaunchMode.Backtesting:
                    place_order_request.TradeExchange = AlgorumQuantClient.algorum_types.TradeExchange.PAPER
                else:
                    place_order_request.TradeExchange = AlgorumQuantClient.algorum_types.TradeExchange.NSE

                place_order_request.OrderDirection = AlgorumQuantClient.algorum_types.OrderDirection.Buy
                place_order_request.Tag = self.State.CurrentOrderId
                place_order_request.SlippageType = AlgorumQuantClient.algorum_types.SlippageType.TIME
                place_order_request.Slippage = 1000

                self.place_order(place_order_request)
                self.set_data("state", self.State)

                msg = 'Placed buy order for ' + str(place_order_request.Quantity) + ' units of ' + self.symbol.Ticker + \
                      ' at price (approx) ' + str(tick_data.LTP) + ', ' + str(tick_data.Timestamp)
                print(msg)
                self.log(AlgorumQuantClient.algorum_types.LogLevel.Information, msg)
            else:
                if self.State.CurrentOrder is not None and \
                        ((tick_data.LTP - self.State.CurrentOrder.AveragePrice >= (
                                self.State.CurrentOrder.AveragePrice * (0.1 / 100))) or
                         (self.State.CurrentOrder.AveragePrice - tick_data.LTP >= (
                                 self.State.CurrentOrder.AveragePrice * (0.25 / 100)))) and self.State.Bought:
                    qty = self.State.CurrentOrder.FilledQuantity

                    self.State.CurrentOrderId = uuid.uuid4().hex
                    place_order_request = AlgorumQuantClient.algorum_types.PlaceOrderRequest()
                    place_order_request.OrderType = AlgorumQuantClient.algorum_types.OrderType.Market
                    place_order_request.Price = tick_data.LTP
                    place_order_request.Quantity = qty
                    place_order_request.Symbol = self.symbol
                    place_order_request.Timestamp = tick_data.Timestamp

                    if self.LaunchMode == AlgorumQuantClient.algorum_types.StrategyLaunchMode.Backtesting:
                        place_order_request.TradeExchange = AlgorumQuantClient.algorum_types.TradeExchange.PAPER
                    else:
                        place_order_request.TradeExchange = AlgorumQuantClient.algorum_types.TradeExchange.NSE

                    place_order_request.TriggerPrice = tick_data.LTP
                    place_order_request.OrderDirection = AlgorumQuantClient.algorum_types.OrderDirection.Sell
                    place_order_request.Tag = self.State.CurrentOrderId
                    place_order_request.SlippageType = AlgorumQuantClient.algorum_types.SlippageType.TIME
                    place_order_request.Slippage = 1000

                    self.place_order(place_order_request)
                    self.set_data("state", self.State)

                    msg = 'Placed sell order for ' + str(qty) + ' units of ' + self.symbol.Ticker + \
                          ' at price (approx) ' + str(tick_data.LTP) + ', ' + str(tick_data.Timestamp)
                    print(msg)
                    self.log(AlgorumQuantClient.algorum_types.LogLevel.Information, msg)

            if self.LaunchMode == AlgorumQuantClient.algorum_types.StrategyLaunchMode.Backtesting:
                self.send_progress_async(tick_data)
        except Exception:
            self.log(AlgorumQuantClient.algorum_types.LogLevel.Error, traceback.format_exc())

    # This method is called on order updates, once the place_order method is called
    def on_order_update(self, order: AlgorumQuantClient.algorum_types.Order):
        try:
            if order.Status == AlgorumQuantClient.algorum_types.OrderStatus.Completed:
                self.StateLock.acquire()
                self.State.Orders.append(order)
                self.StateLock.release()

                if order.OrderDirection == AlgorumQuantClient.algorum_types.OrderDirection.Buy:
                    self.State.Bought = True
                    self.State.CurrentOrder = order
                    msg = 'Order Id ' + order.OrderId + ' Bought ' + \
                          str(order.FilledQuantity) + ' units of ' + order.Symbol.Ticker + ' at price ' + \
                          str(order.AveragePrice)
                    print(msg)
                    self.log(AlgorumQuantClient.algorum_types.LogLevel.Information, msg)
                else:
                    self.State.Bought = False
                    self.State.CurrentOrder = None
                    msg = 'Order Id ' + order.OrderId + ' Sold ' + \
                          str(order.FilledQuantity) + ' units of ' + order.Symbol.Ticker + ' at price ' + \
                          str(order.AveragePrice)
                    print(msg)
                    self.log(AlgorumQuantClient.algorum_types.LogLevel.Information, msg)

                self.State.CurrentOrderId = None
                stats = self.get_stats(self.State.CurrentTick)
                self.publish_stats(stats)

                for k, v in stats.items():
                    print('Key: ' + str(k) + ', Value: ' + str(v))

            self.set_data("state", self.State)
        except Exception:
            self.log(AlgorumQuantClient.algorum_types.LogLevel.Error, traceback.format_exc())

    def backtest(self, backtest_request: AlgorumQuantClient.algorum_types.BacktestRequest):
        # Preload the indicator evaluator with 200 candles
        self.evaluator.preload_candles(200, backtest_request.StartDate, backtest_request.ApiKey,
                                       backtest_request.ApiSecretKey)

        AlgorumQuantClient.quant_client.QuantEngineClient.backtest(self, backtest_request)

    def get_stats(self, tick_date: AlgorumQuantClient.algorum_types.TickData):
        stats_map = None

        try:
            stats_map = {"Capital": GoldenCrossoverQuantStrategy.Capital, "Order Count": len(self.State.Orders)}

            buy_val = 0.0
            sell_val = 0.0
            buy_qty = 0.0
            sell_qty = 0.0

            for order in self.State.Orders:
                if (order.Status == AlgorumQuantClient.algorum_types.OrderStatus.Completed) and \
                        (order.OrderDirection == AlgorumQuantClient.algorum_types.OrderDirection.Buy) and \
                        order.Symbol.Ticker == tick_date.Symbol.Ticker:
                    buy_val += order.FilledQuantity * order.AveragePrice
                    buy_qty += order.FilledQuantity

                if (order.Status == AlgorumQuantClient.algorum_types.OrderStatus.Completed) and \
                        (order.OrderDirection == AlgorumQuantClient.algorum_types.OrderDirection.Sell) and \
                        order.Symbol.Ticker == tick_date.Symbol.Ticker:
                    sell_val += order.FilledQuantity * order.AveragePrice
                    sell_qty += order.FilledQuantity

            if sell_qty < buy_qty:
                sell_val += (buy_qty - sell_qty) * tick_date.LTP

            pl = sell_val - buy_val
            stats_map['PL'] = pl
            stats_map['Portfolio Value'] = GoldenCrossoverQuantStrategy.Capital + pl

            self.log(AlgorumQuantClient.algorum_types.LogLevel.Information, "PL: " + str(pl))
            self.log(AlgorumQuantClient.algorum_types.LogLevel.Information,
                     "Portfolio Value: " + str(stats_map['Portfolio Value']))

        except Exception:
            self.log(AlgorumQuantClient.algorum_types.LogLevel.Error, traceback.format_exc())

        return stats_map
