import logging

from ..gmx_utils import (
    contract_map, get_tokens_address_dict, get_reader_contract
)

from .get_oracle_prices import OraclePrices


class Markets:
    def __init__(self, config):
        self.config = config
        self.info = self._process_markets()
        self.log = logging.getLogger(__name__)

    def get_index_token_address(self, market_key: str) -> str:
        return self.info[market_key]['index_token_address']

    def get_long_token_address(self, market_key: str) -> str:
        return self.info[market_key]['long_token_address']

    def get_short_token_address(self, market_key: str) -> str:
        return self.info[market_key]['short_token_address']

    def get_market_symbol(self, market_key: str) -> str:
        return self.info[market_key]['market_symbol']

    def get_decimal_factor(
        self, market_key: str, long: bool = False, short: bool = False
    ) -> int:
        if long:
            return self.info[market_key]['long_token_metadata']['decimals']
        elif short:
            return self.info[market_key]['short_token_metadata']['decimals']
        else:
            return self.info[market_key]['market_metadata']['decimals']

    def is_synthetic(self, market_key: str) -> bool:
        return self.info[market_key]['market_metadata']['synthetic']

    def get_available_markets(self):
        """
        Get the available markets on a given chain

        Returns
        -------
        Markets: dict
            dictionary of the available markets.

        """
        logging.info("Getting Available Markets..")
        return self._process_markets()

    def _get_available_markets_raw(self):
        """
        Get the available markets from the reader contract

        Returns
        -------
        Markets: tuple
            tuple of raw output from the reader contract.

        """

        reader_contract = get_reader_contract(self.config)
        data_store_contract_address = (
            contract_map[self.config.chain]['datastore']['contract_address']
        )

        return reader_contract.functions.getMarkets(
            data_store_contract_address,
            0,
            50
        ).call()

    def _process_markets(self):
        """
        Call and process the raw market data

        Returns
        -------
        decoded_markets : dict
            dictionary decoded market data.

        """
        token_address_dict = get_tokens_address_dict(self.config.chain)
        raw_markets = self._get_available_markets_raw()

        decoded_markets = {}
        for raw_market in raw_markets:
            try:

                if not self._check_if_index_token_in_signed_prices_api(
                    raw_market[1]
                ):
                    continue
                market_symbol = token_address_dict[raw_market[1]]['symbol']

                if raw_market[2] == raw_market[3]:
                    market_symbol = f"{market_symbol}2"
                decoded_markets[raw_market[0]] = {
                    'gmx_market_address': raw_market[0],
                    'market_symbol': market_symbol,
                    'index_token_address': raw_market[1],
                    'market_metadata': token_address_dict[raw_market[1]],
                    'long_token_metadata': token_address_dict[raw_market[2]],
                    'long_token_address': raw_market[2],
                    'short_token_metadata': token_address_dict[raw_market[3]],
                    'short_token_address': raw_market[3]
                }
                if raw_market[0] == "0x0Cf1fb4d1FF67A3D8Ca92c9d6643F8F9be8e03E5":
                    decoded_markets[raw_market[0]]["market_symbol"] = "wstETH"
                    decoded_markets[raw_market[0]
                                    ]["index_token_address"] = "0x5979D7b546E38E414F7E9822514be443A4800529"

            # If KeyError it is because there is no market symbol and it is a
            # swap market
            except KeyError:
                if not self._check_if_index_token_in_signed_prices_api(
                    raw_market[1]
                ):
                    continue

                decoded_markets[raw_market[0]] = {
                    'gmx_market_address': raw_market[0],
                    'market_symbol': 'SWAP {}-{}'.format(
                        token_address_dict[raw_market[2]]['symbol'],
                        token_address_dict[raw_market[3]]['symbol']
                    ),
                    'index_token_address': raw_market[1],
                    'market_metadata': {'symbol': 'SWAP {}-{}'.format(
                        token_address_dict[raw_market[2]]['symbol'],
                        token_address_dict[raw_market[3]]['symbol']
                    )},
                    'long_token_metadata': token_address_dict[raw_market[2]],
                    'long_token_address': raw_market[2],
                    'short_token_metadata': token_address_dict[raw_market[3]],
                    'short_token_address': raw_market[3]
                }

        return decoded_markets

    def _check_if_index_token_in_signed_prices_api(self, index_token_address):

        try:
            prices = OraclePrices(chain=self.config.chain).get_recent_prices()

            if index_token_address == "0x0000000000000000000000000000000000000000":
                return True
            prices[index_token_address]
            return True
        except KeyError:

            print("{} market not live on GMX yet..".format(index_token_address))
            return False


if __name__ == '__main__':
    pass
