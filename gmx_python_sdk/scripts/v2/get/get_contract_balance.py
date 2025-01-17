import numpy as np

from .get import GetData
from .get_markets import Markets
from .get_oracle_prices import OraclePrices
from ..gmx_utils import get_token_balance_contract, save_json_file_to_datastore


class GetPoolTVL(GetData):
    def __init__(self, config):
        super().__init__(config)
        self.oracle_prices_dict = OraclePrices(
            chain=config.chain
        ).get_recent_prices

    def get_pool_balances(self, to_json: bool = False):
        """
        Get the USD balances of each pool and optionally save to json file

        Parameters
        ----------
        to_json : bool, optional
            to save to json file or not. The default is False.

        Returns
        -------
        pool_tvl_dict : dict
            dictionary of total USD value per pool.

        """
        markets = Markets(self.config).get_available_markets()
        pool_tvl_dict = {}

        for market in markets:
            print("\n" + markets[market]['market_symbol'])

            long_token_address = markets[market]['long_token_address']

            short_token_address = markets[market]['short_token_address']
            long_token_balance, short_token_balance = self._query_balances(
                market,
                long_token_address,
                short_token_address
            )
            oracle_precision = 10 ** (
                30 - markets[market]['long_token_metadata']['decimals']
            )

            long_usd_balance = self._calculate_usd_value(
                long_token_balance,
                long_token_address,
                oracle_precision
            )

            dictionary_key = markets[market]['market_symbol']

            pool_tvl_dict[dictionary_key] = {
                'total_tvl': long_usd_balance + short_token_balance,
                'long_token': markets[market]['long_token_address'],
                'short_token': markets[market]['short_token_address']
            }

            print(
                "Pool USD Value: ${}".format(
                    long_usd_balance + short_token_balance
                )
            )

        if to_json:
            save_json_file_to_datastore(
                "{}_pool_tvl.json".format(self.config.chain),
                pool_tvl_dict
            )
        else:
            return pool_tvl_dict

    def _query_balances(
        self, market: str, long_token_address: str, short_token_address: str
    ):
        """
        Get token balance of each pool for a given market and its long and
        short token addresses

        Parameters
        ----------
        market : str
            GMX market address.
        long_token_address : str
            long token address.
        short_token_address : str
            short token address.

        Returns
        -------
        long_token_balance : float
            balance of token in adjusted significant figures.
        short_token_balance : float
            balance of token in adjusted significant figures.

        """
        long_token_contract = get_token_balance_contract(
            self.config,
            long_token_address
        )
        long_token_balance = long_token_contract.functions.balanceOf(
            market
        ).call() / 10 ** long_token_contract.functions.decimals().call()
        short_token_contract = get_token_balance_contract(
            self.config,
            short_token_address
        )
        short_token_balance = short_token_contract.functions.balanceOf(
            market
        ).call() / 10 ** short_token_contract.functions.decimals().call()

        return long_token_balance, short_token_balance

    def _calculate_usd_value(
        self, token_balance: float, contract_address: str,
        oracle_precision: int
    ):
        """
        For given contract(token) address, calculate the USD value from the
        input token amount

        Parameters
        ----------
        token_balance : float
            amount of tokens.
        contract_address : str
            address of token.
        oracle_precision : int
            number of decimals to apply to price output.

        Returns
        -------
        token_balance: float
            usd value of tokens.

        """
        try:
            token_price = np.median(
                [
                    float(
                        self.oracle_prices_dict()[
                            contract_address
                        ]['maxPriceFull']
                    ) / oracle_precision,
                    float(
                        self.oracle_prices_dict()[
                            contract_address
                        ]['minPriceFull']
                    ) / oracle_precision
                ]
            )
            return token_price * token_balance
        except KeyError:
            print("Contract address not known")
            return token_balance


if __name__ == "__main__":
    # chain = sys.argv[1]
    # chain = 'arbitrum'
    pool_dict = GetPoolTVL(chain='arbitrum').get_data(to_json=False)
