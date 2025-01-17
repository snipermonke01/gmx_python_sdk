from .get import GetData
from ..gmx_utils import (
    get_glv_reader_contract,
    save_json_file_to_datastore, make_timestamped_dataframe,
    save_csv_to_datastore, get_token_balance_contract
)
from .get_oracle_prices import OraclePrices
from .get_gm_prices import GMPrices
from ..keys import MAX_PNL_FACTOR_FOR_TRADERS


class GlvStats(GetData):
    def __init__(self, config: str):
        super().__init__(config)
        self.config = config
        self.to_json = None
        self.to_csv = None
        self.GMPrices_obj = GMPrices(config)

    def get_glv_stats(self, to_json: bool = False, to_csv: bool = False):
        """
        Get GLVs info, incl price and composition

        Parameters
        ----------
        to_json : bool, optional
            pass True to save GLV prices to json. The default is False.
        to_csv : bool, optional
            pass True to save GLV prices to json. The default is False.

        Returns
        -------
        glv_info_dict: dict
            dictionary of glv info.

        """
        self.to_json = to_json
        self.to_csv = to_csv

        return self._get_data_processing()

    def _get_data_processing(self):
        """
        Get GLVs info, incl price and composition

        Returns
        -------
        glv_info_dict: dict
            dictionary of glv info.

        """

        glv_info_dict = self._get_glv_info_list()

        for glv_market_address in glv_info_dict.keys():

            # Need to build a list of the max/min prices of the index tokens
            index_token_prices = []
            glv_markets_metadata = {}

            for market_address in glv_info_dict[glv_market_address]["glv_market_addresses"]:

                self._get_token_addresses(market_address)
                index_token_address = self.markets.get_index_token_address(
                    market_address
                )
                oracle_prices = self._get_oracle_prices(
                    market_address,
                    index_token_address,
                    return_tuple=True
                )
                index_token_prices += [oracle_prices[0]]

                oracle_prices_dict = OraclePrices(self.config.chain).get_recent_prices()

                long_token_price_dict = oracle_prices_dict[
                    glv_info_dict[glv_market_address]["long_address"]
                ]
                short_token_price_dict = oracle_prices_dict[
                    glv_info_dict[glv_market_address]["short_address"]
                ]

                long_token_price = (
                    int(long_token_price_dict["maxPriceFull"]),
                    int(long_token_price_dict["minPriceFull"])
                )
                short_token_price = (
                    int(short_token_price_dict["maxPriceFull"]),
                    int(short_token_price_dict["minPriceFull"])
                )

                market_token_balance = self._get_glv_composition(
                    glv_market_address,
                    market_address
                )
                gm_price = self.GMPrices_obj._make_market_token_price_query(
                    [
                        market_address,
                        index_token_address,
                        self._long_token_address,
                        self._short_token_address
                    ],
                    oracle_prices[0],
                    long_token_price,
                    short_token_price,
                    MAX_PNL_FACTOR_FOR_TRADERS
                ).call()[0] / 10**30

                market_symbol = self.markets.get_market_symbol(market_address)
                glv_markets_metadata[market_address] = {"address": market_address,
                                                        'market symbol': market_symbol,
                                                        "balance": market_token_balance,
                                                        "gm price": gm_price}

            glv_info_dict[glv_market_address]['markets_metadata'] = glv_markets_metadata

            glv_price = self._get_glv_token_price(
                glv_market_address,
                glv_info_dict[glv_market_address]["glv_market_addresses"],
                index_token_prices,
                long_token_price,
                short_token_price
            )

            glv_info_dict[glv_market_address]['glv_price'] = glv_price

        return glv_info_dict

    def _get_glv_info_list(self):
        """
        Call glvReader to get the list of glv markets live

        Returns
        -------
        glvs : dict
            dictionary GLV info.

        """

        raw_output = get_glv_reader_contract(self.config).functions.getGlvInfoList(
            self.data_store_contract_address,
            0,
            10
        ).call()

        glvs = {}

        for raw_glv in raw_output:

            glvs[raw_glv[0][0]] = {
                "glv_address": raw_glv[0][0],
                "long_address": raw_glv[0][1],
                "short_address": raw_glv[0][2],
                "glv_market_addresses": raw_glv[1]
            }

        return glvs

    def _get_glv_token_price(
            self,
            glv_address: str,
            glv_market_addresses: list,
            index_token_prices: list,
            long_token_price: list,
            short_token_price: list
    ):
        """
        Get the price of a given GLV market

        Parameters
        ----------
        glv_address : str
            Address of GLV
        glv_market_addresses : list
            List of market addresses in glv.
        index_token_prices : list
            list of tuple max/min prices.
        long_token_price : list
            tuple max/min prices.
        short_token_price : list
            tuple max/min prices.

        Returns
        -------
        float
            price of 1 GLV token.

        """

        maximise = True
        glv_price = get_glv_reader_contract(self.config).functions.getGlvTokenPrice(
            self.data_store_contract_address,
            glv_market_addresses,
            index_token_prices,
            long_token_price,
            short_token_price,
            glv_address,
            maximise
        ).call()

        return glv_price[0] * 10**-30

    def _get_glv_composition(self, glv_address: str, market_address: str):
        """
        Get the token balance for each component of GLV

        Parameters
        ----------
        glv_address : str
            contract address of GLV.
        market_address : str
            market address to query the balance for.

        Returns
        -------
        market_token_balance : float
            amount of tokens in given GLV.

        """

        market_token_contract = get_token_balance_contract(
            self.config,
            market_address
        )
        market_token_balance = market_token_contract.functions.balanceOf(
            glv_address
        ).call() / 10 ** 18

        return market_token_balance


if __name__ == "__main__":
    pass
