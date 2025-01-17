import numpy as np

from .get_markets import Markets
from .get_oracle_prices import OraclePrices
from ..keys import pool_amount_key
from ..gmx_utils import (
    get_datastore_contract, save_json_file_to_datastore,
    make_timestamped_dataframe, save_csv_to_datastore
)


class GetPoolTVL:
    def __init__(self, config: str):
        self.config = config
        self.oracle_prices_dict = OraclePrices(
            chain=config.chain
        ).get_recent_prices

    def get_pool_balances(self, to_json: bool = False, to_csv: bool = False):
        """
        Call to get the amounts across all pools on a given chain defined in
        class init. Pass either to_json or to_csv to save locally in datastore

        Parameters
        ----------
        to_json : bool, optional
            save output to json file. The default is False.
        to_csv : bool, optional
            save out to csv file. The default is False.

        Returns
        -------
        data : dict
            dictionary of data.

        """
        markets = Markets(self.config).get_available_markets()
        pool_tvl_dict = {
            "total_tvl": {},
            "long_token": {},
            "short_token": {}
        }

        for market in markets:
            print("\n" + markets[market]['market_symbol'])

            index_token_address = markets[market]['index_token_address']
            long_token_metadata = markets[market]['long_token_metadata']
            short_token_metadata = markets[market]['short_token_metadata']

            long_token_balance, short_token_balance = self._query_balances(
                market,
                long_token_metadata,
                short_token_metadata
            )

            long_precision = 10 ** long_token_metadata['decimals']
            short_precision = 10 ** short_token_metadata['decimals']
            long_token_balance = long_token_balance / long_precision
            short_token_balance = short_token_balance / short_precision

            # If market is synthetic we need to use the long token as the
            # index token for price
            # try:
            #     if markets[market]['market_metadata']['synthetic']:
            index_token_address = markets[market]['long_token_address']
            # except KeyError:
            #     pass

            oracle_precision = 10 ** (
                30 - markets[market]['long_token_metadata']['decimals']
            )
            long_usd_balance = self._calculate_usd_value(
                index_token_address,
                long_token_balance,
                oracle_precision
            )
            short_usd_balance = short_token_balance

            dictionary_key = markets[market]['market_symbol']

            pool_tvl_dict['total_tvl'][dictionary_key] = (
                long_usd_balance + short_usd_balance
            )
            pool_tvl_dict['long_token'][dictionary_key] = (
                markets[market]['long_token_address']
            )
            pool_tvl_dict['short_token'][dictionary_key] = (
                markets[market]['short_token_address']
            )

            print(
                "Pool USD Value: ${}".format(
                    long_usd_balance + short_usd_balance
                )
            )

        if to_json:
            save_json_file_to_datastore(
                "{}_pool_tvl.json".format(self.config.chain),
                pool_tvl_dict
            )

        if to_csv:
            dataframe = make_timestamped_dataframe(pool_tvl_dict['total_tvl'])
            save_csv_to_datastore(
                "{}_total_tvl.csv".format(self.config.chain),
                dataframe
            )
        else:
            return pool_tvl_dict

    def _query_balances(
        self,
        market: str,
        long_token_metadata: dict,
        short_token_metadata: dict
    ):
        """
        For a given GMX market get the balance of long and short tokens from
        the datastore contract

        Parameters
        ----------
        market : str
            contract address of the market.
        long_token_metadata : dict
            dictionary containing address.
        short_token_metadata : dict
            dictionary containing address.

        Returns
        -------
        long_token_balance : int
            amount of tokens.
        short_token_balance : int
            amount of tokens.
        """
        datastore = get_datastore_contract(self.config)
        pool_amount_hash_data = pool_amount_key(
            market,
            long_token_metadata['address']
        )
        long_token_balance = datastore.functions.getUint(
            pool_amount_hash_data
        ).call()

        datastore = get_datastore_contract(self.config)
        pool_amount_hash_data = pool_amount_key(
            market,
            short_token_metadata['address']
        )
        short_token_balance = datastore.functions.getUint(
            pool_amount_hash_data
        ).call()

        return long_token_balance, short_token_balance

    def _calculate_usd_value(
        self,
        token_address: str,
        token_balance: int,
        oracle_precision: int,
    ):
        """
        Calculate the USD value from token amounts for a given token address

        Parameters
        ----------
        token_address : str
            contracta address.
        token_balance : int
            amount of tokens.
        oracle_precision : int
            factor to power 10 to divide price api output.

        Returns
        -------
        value: float
            USD value of the token amount.
        """
        try:
            token_price = np.median(
                [
                    float(
                        self.oracle_prices_dict()[
                            token_address
                        ]['maxPriceFull']
                    ) / oracle_precision,
                    float(
                        self.oracle_prices_dict()[
                            token_address
                        ]['minPriceFull']
                    ) / oracle_precision
                ]
            )
            return token_price * token_balance
        except KeyError:
            return token_balance


if __name__ == "__main__":
    # chain = sys.argv[1]
    pool_dict = GetPoolTVL(chain="arbitrum").get_pool_balances(to_csv=True)
