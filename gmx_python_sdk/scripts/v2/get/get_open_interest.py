import time
from numerize import numerize

from .get import GetData
from .get_oracle_prices import OraclePrices
from ..gmx_utils import execute_threading


class OpenInterest(GetData):
    def __init__(self, config: str):
        super().__init__(config)

    def _get_data_processing(self):
        """
        Generate the dictionary of open interest data

        Returns
        -------
        funding_apr : dict
            dictionary of open interest data.

        """
        oracle_prices_dict = OraclePrices(
            self.config.chain
        ).get_recent_prices()
        print("GMX v2 Open Interest\n")

        long_oi_output_list = []
        short_oi_output_list = []
        long_pnl_output_list = []
        short_pnl_output_list = []
        mapper = []
        long_precision_list = []

        for market_key in self.markets.info:
            self._filter_swap_markets()
            self._get_token_addresses(market_key)

            index_token_address = self.markets.get_index_token_address(
                market_key
            )

            market = [
                market_key,
                index_token_address,
                self._long_token_address,
                self._short_token_address
            ]

            min_price = int(
                oracle_prices_dict[index_token_address]['minPriceFull']
            )
            max_price = int(
                oracle_prices_dict[index_token_address]['maxPriceFull']
            )
            prices_list = [min_price, max_price]

            # If the market is a synthetic one we need to use the decimals
            # from the index token
            print(market_key)
            try:
                if self.markets.is_synthetic(market_key):
                    decimal_factor = self.markets.get_decimal_factor(
                        market_key,
                    )
                else:
                    decimal_factor = self.markets.get_decimal_factor(
                        market_key,
                        long=True
                    )
            except KeyError:
                decimal_factor = self.markets.get_decimal_factor(
                    market_key,
                    long=True
                )

            oracle_factor = (30 - decimal_factor)
            precision = 10 ** (decimal_factor + oracle_factor)
            long_precision_list = long_precision_list + [precision]

            long_oi_with_pnl, long_pnl = self._get_pnl(
                market,
                prices_list,
                is_long=True
            )

            short_oi_with_pnl, short_pnl = self._get_pnl(
                market,
                prices_list,
                is_long=False
            )

            long_oi_output_list.append(long_oi_with_pnl)
            short_oi_output_list.append(short_oi_with_pnl)
            long_pnl_output_list.append(long_pnl)
            short_pnl_output_list.append(short_pnl)
            mapper.append(self.markets.get_market_symbol(market_key))

        # TODO - currently just waiting x amount of time to not hit rate limit,
        # but needs a retry
        long_oi_threaded_output = execute_threading(long_oi_output_list)
        time.sleep(0.2)
        short_oi_threaded_output = execute_threading(short_oi_output_list)
        time.sleep(0.2)
        long_pnl_threaded_output = execute_threading(long_pnl_output_list)
        time.sleep(0.2)
        short_pnl_threaded_output = execute_threading(short_pnl_output_list)

        for (
            market_symbol,
            long_oi,
            short_oi,
            long_pnl,
            short_pnl,
            long_precision
        ) in zip(
            mapper,
            long_oi_threaded_output,
            short_oi_threaded_output,
            long_pnl_threaded_output,
            short_pnl_threaded_output,
            long_precision_list
        ):
            precision = 10 ** 30
            long_value = (long_oi - long_pnl) / long_precision
            short_value = (short_oi - short_pnl) / precision

            self.log.info(
                f"{market_symbol} Long: ${numerize.numerize(long_value)}"
            )
            self.log.info(
                f"{market_symbol} Short: ${numerize.numerize(short_value)}"
            )

            self.output['long'][market_symbol] = long_value
            self.output['short'][market_symbol] = short_value
        self.output['parameter'] = "open_interest"

        return self.output


if __name__ == '__main__':
    data = OpenInterest(chain="arbitrum").get_data(to_csv=False)
    print(data)
