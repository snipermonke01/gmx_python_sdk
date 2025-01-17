from .get import GetData
from ..gmx_utils import (
    get_reader_contract, contract_map, execute_threading,
    save_json_file_to_datastore, make_timestamped_dataframe,
    save_csv_to_datastore
)
from ..keys import (
    MAX_PNL_FACTOR_FOR_TRADERS, MAX_PNL_FACTOR_FOR_DEPOSITS,
    MAX_PNL_FACTOR_FOR_WITHDRAWALS
)


class GMPrices(GetData):
    def __init__(self, config: str):
        super().__init__(config)
        self.config = config
        self.to_json = None
        self.to_csv = None

    def get_price_withdraw(self, to_json: bool = False, to_csv: bool = False):
        """
        Get GM price if withdrawing from LP

        Parameters
        ----------
        to_json : bool, optional
            pass True to save price to json. The default is False.
        to_csv : bool, optional
            pass True to save price to json. The default is False.

        Returns
        -------
        gm_pool_prices: dict
            dictionary of gm prices.

        """
        self.to_json = to_json
        self.to_csv = to_csv
        pnl_factor_type = MAX_PNL_FACTOR_FOR_WITHDRAWALS

        return self._get_data_processing(pnl_factor_type)

    def get_price_deposit(self, to_json: bool = False, to_csv: bool = False):
        """
        Get GM price if depositing to LP

        Parameters
        ----------
        to_json : bool, optional
            pass True to save price to json. The default is False.
        to_csv : bool, optional
            pass True to save price to json. The default is False.

        Returns
        -------
        gm_pool_prices: dict
            dictionary of gm prices.

        """
        self.to_json = to_json
        self.to_csv = to_csv
        pnl_factor_type = MAX_PNL_FACTOR_FOR_DEPOSITS
        return self._get_data_processing(pnl_factor_type)

    def get_price_traders(self, to_json: bool = False, to_csv: bool = False):
        """
        Get GM price if trading from LP

        Parameters
        ----------
        to_json : bool, optional
            pass True to save price to json. The default is False.
        to_csv : bool, optional
            pass True to save price to json. The default is False.

        Returns
        -------
        gm_pool_prices: dict
            dictionary of gm prices.

        """
        self.to_json = to_json
        self.to_csv = to_csv
        pnl_factor_type = MAX_PNL_FACTOR_FOR_TRADERS
        return self._get_data_processing(pnl_factor_type)

    def _get_data_processing(self, pnl_factor_type):
        """
        Get GM pool prices for a given profit/loss factor

        Parameters
        ----------
        pnl_factor_type : hash
            descriptor for datastore.

        Returns
        -------
        gm_pool_prices : dict
            dictionary of gm prices.

        """
        output_list = []
        mapper = []
        self._filter_swap_markets()

        for iter, market_key in enumerate(self.markets.info):
            self._get_token_addresses(market_key)
            index_token_address = self.markets.get_index_token_address(
                market_key
            )
            oracle_prices = self._get_oracle_prices(
                market_key,
                index_token_address,
                return_tuple=True
            )

            market = [
                market_key,
                index_token_address,
                self._long_token_address,
                self._short_token_address
            ]

            output = self._make_market_token_price_query(
                market,
                oracle_prices[0],
                oracle_prices[1],
                oracle_prices[2],
                pnl_factor_type
            )

            # add the uncalled web3 object to list
            output_list.append(output)

            # add the market symbol to a list to use to map to dictionary later
            mapper.append(self.markets.get_market_symbol(market_key))

        # feed the uncalled web3 objects into threading function
        threaded_output = execute_threading(output_list)

        for key, output in zip(mapper, threaded_output):
            # divide by 10**30 to turn into USD value
            self.output[key] = output[0] / 10**30

        if self.to_json:
            filename = "{}_gm_prices.json".format(self.config.chain)
            save_json_file_to_datastore(
                filename,
                self.output
            )

        if self.to_csv:
            dataframe = make_timestamped_dataframe(self.output)

            save_csv_to_datastore(
                "{}_gm_prices.csv".format(self.config.chain),
                dataframe)

        self.output['parameter'] = "gm_prices"
        del self.output["long"]
        del self.output["short"]

        return self.output

    def _make_market_token_price_query(
            self,
            market: list,
            index_price_tuple: tuple,
            long_price_tuple: tuple,
            short_price_tuple: tuple,
            pnl_factor_type
    ):
        """
        Get the raw GM price from the reader contract for a given market tuple,
        index, long, and
        short max/min price tuples, and the pnl factor hash.

        Parameters
        ----------
        market : list
            list containing contract addresses of the market.
        index_price_tuple : tuple
            tuple of min and max prices.
        long_price_tuple : tuple
            tuple of min and max prices..
        short_price_tuple : tuple
            tuple of min and max prices..
        pnl_factor_type : hash
            descriptor for datastore.

        Returns
        -------
        output : TYPE
            DESCRIPTION.

        """
        # maximise to take max prices in calculation
        maximise = True
        output = self.reader_contract.functions.getMarketTokenPrice(
            self.data_store_contract_address,
            market,
            index_price_tuple,
            long_price_tuple,
            short_price_tuple,
            pnl_factor_type,
            maximise
        )

        return output


if __name__ == "__main__":
    output = GMPrices(chain="arbitrum").get_price_traders(to_csv=True)
