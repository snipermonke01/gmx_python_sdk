import numpy as np

from ..get.get_markets import Markets
from ..get.get_oracle_prices import OraclePrices

from ..gmx_utils import get_tokens_address_dict


class LiquidityArgumentParser:

    def __init__(self, config, is_deposit: bool = False, is_withdrawal: bool = False):

        self.parameters_dict = None
        self.is_deposit = is_deposit
        self.is_withdrawal = is_withdrawal
        self.config = config

        if is_deposit:

            self.required_keys = [
                "chain",
                "market_key",
                "long_token_address",
                "short_token_address",
                "long_token_amount",
                "short_token_amount"
            ]

        if is_withdrawal:

            self.required_keys = [
                "chain",
                "market_key",
                "out_token_address",
                "gm_amount"
            ]

        self.missing_base_key_methods = {
            "chain": self._handle_missing_chain,
            "market_key": self._handle_missing_market_key,
            "long_token_address": self._handle_missing_long_token_address,
            "short_token_address": self._handle_missing_short_token_address,
            "long_token_amount": self._handle_missing_long_token_amount,
            "short_token_amount": self._handle_missing_short_token_amount,
            "out_token_address": self._handle_missing_out_token_address
        }

    def process_parameters_dictionary(self, parameters_dict):
        """
        For a given set parameters, format to produce the
        inputs required for a deposit or withdrawal

        Parameters
        ----------
        parameters_dict : dict
            dictionary containing necesssary parameters.

        Returns
        -------
        dict
            formatted dictionary.

        """

        # find which keys are in our required list
        missing_keys = self._determine_missing_keys(parameters_dict)

        self.parameters_dict = parameters_dict

        # Loop the missing keys and call required methods to fix outputs
        for missing_key in missing_keys:
            if missing_key in self.missing_base_key_methods:
                self.missing_base_key_methods[missing_key]()

        # If withdrawal, quick dirty way to convert gm amount
        if self.is_withdrawal:
            parameters_dict['gm_amount'] = int(parameters_dict['gm_amount'] * 10**18)

        return self.parameters_dict

    def _determine_missing_keys(self, parameters_dict):
        """
        Compare keys in the supposed dictionary to a list of keys which are required to create an
        order

        Parameters
        ----------
        parameters_dict : dict
            user suppled dictionary of parameters to create order.

        """
        return [key for key in self.required_keys if key not in parameters_dict]

    def _handle_missing_chain(self):
        """
        Will trigger is chain is missing from parameters dictionary, chain must be supplied by user
        """

        raise Exception("Please pass chain name in parameters dictionary!")

    def _handle_missing_index_token_address(self):
        """
        Will trigger if index token address is missing. Can be determined if index token symbol is
        found, but will raise an exception if that cant be found either
        """

        try:
            token_symbol = self.parameters_dict['market_token_symbol']
        except KeyError:
            raise Exception("Market Token Address and Symbol not provided!")

        self.parameters_dict['market_token_address'] = self.find_key_by_symbol(
            get_tokens_address_dict(
                self.parameters_dict['chain']
            ),
            token_symbol

        )

    def _handle_missing_market_key(self):
        """
        Will trigger if market key is missing. Can be determined from index token address.
        """

        self._handle_missing_index_token_address()
        index_token_address = self.parameters_dict['market_token_address']

        # use the index token address to find the market key from get_available_markets
        self.parameters_dict['market_key'] = self.find_market_key_by_index_address(
            Markets(self.config).get_available_markets(),
            index_token_address
        )

    def _handle_missing_long_token_address(self):
        """
        Will trigger if start token address is missing. Can be determined if start token symbol is
        found, but will raise an exception if that cant be found either.
        """

        try:
            long_token_symbol = self.parameters_dict['long_token_symbol']

            if long_token_symbol == "BTC":
                self.parameters_dict[
                    'long_token_address'
                ] = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
                return
            if long_token_symbol is None:
                raise KeyError
        except KeyError:
            self.parameters_dict['long_token_address'] = None
            print("Long Token Address and Symbol not provided!")
            return

        # search the known tokens for a contract address using the user supplied symbol
        self.parameters_dict['long_token_address'] = self.find_key_by_symbol(
            get_tokens_address_dict(
                self.parameters_dict['chain']),
            long_token_symbol
        )

    def _handle_missing_short_token_address(self):
        """
        Will trigger if start token address is missing. Can be determined if start token symbol
        is found, but will raise an exception if that cant be found either.
        """

        try:
            short_token_symbol = self.parameters_dict['short_token_symbol']
            if short_token_symbol is None:
                raise KeyError
        except KeyError:
            self.parameters_dict['short_token_address'] = None
            print("Short Token Address and Symbol not provided!")
            return

        # search the known tokens for a contract address using the user supplied symbol
        self.parameters_dict['short_token_address'] = self.find_key_by_symbol(
            get_tokens_address_dict(
                self.parameters_dict['chain']),
            short_token_symbol
        )

    def _handle_missing_out_token_address(self):
        """
        Will trigger if out token address is missing. Can be determined if out token symbol
        is found, but will raise an exception if that cant be found either.

        """

        try:
            out_token_symbol = self.parameters_dict['out_token_symbol']
            if out_token_symbol is None:
                raise KeyError
        except KeyError:
            raise Exception("Must provided either out token symbol or address")

        # search the known tokens for a contract address using the user supplied symbol
        out_token_address = self.find_key_by_symbol(
            get_tokens_address_dict(
                self.parameters_dict['chain']),
            out_token_symbol
        )

        markets = Markets(self.config).get_available_markets()
        market = markets[self.parameters_dict['market_key']]

        if out_token_symbol == "BTC":
            out_token_address = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"

        if out_token_address not in [market['long_token_address'], market['short_token_address']]:
            raise Exception(
                "Out token must be either the long or short token of the market")
        else:
            self.parameters_dict['out_token_address'] = out_token_address

    def _handle_missing_long_token_amount(self):
        """
        Will trigger if long token address is missing. Can be determined if long token symbol
        is found, but will raise an exception if that cant be found either.
        """

        if self.parameters_dict["long_token_address"] is None:
            self.parameters_dict["long_token_amount"] = 0
            return
        prices = OraclePrices(chain=self.config.chain).get_recent_prices()
        price = np.median(
            [float(prices[self.parameters_dict["long_token_address"]]['maxPriceFull']),
             float(prices[self.parameters_dict["long_token_address"]]['minPriceFull'])]
        )
        decimal = get_tokens_address_dict(
            self.parameters_dict['chain']
        )[self.parameters_dict["long_token_address"]]['decimals']
        oracle_factor = decimal - 30

        price = price * 10 ** oracle_factor

        self.parameters_dict["long_token_amount"] = int((
            self.parameters_dict["long_token_usd"] / price) * 10**decimal)

    def _handle_missing_short_token_amount(self):
        """
        Will trigger if short token address is missing. Can be determined if long token symbol
        is found, but will raise an exception if that cant be found either.
        """

        if self.parameters_dict["short_token_address"] is None:
            self.parameters_dict["short_token_amount"] = 0
            return

        prices = OraclePrices(chain=self.parameters_dict['chain']).get_recent_prices()
        price = np.median(
            [float(prices[self.parameters_dict["short_token_address"]]['maxPriceFull']),
             float(prices[self.parameters_dict["short_token_address"]]['minPriceFull'])]
        )
        decimal = get_tokens_address_dict(
            self.parameters_dict['chain']
        )[self.parameters_dict["short_token_address"]]['decimals']
        oracle_factor = decimal - 30

        price = price * 10 ** oracle_factor

        self.parameters_dict["short_token_amount"] = int((
            self.parameters_dict["short_token_usd"] / price) * 10**decimal)

    @staticmethod
    def find_key_by_symbol(input_dict: dict, search_symbol: str):
        """
        For a given token symbol, identify that key in input_dict that matches the value for
        'symbol'

        Parameters
        ----------
        input_dict : dict
            Input dictionary containing token information.
        search_symbol : str
            string of symbol we want to find the key of.

        """

        for key, value in input_dict.items():
            if value.get('symbol') == search_symbol:
                return key
        raise Exception('"{}" not a known token for GMX v2!'.format(search_symbol))

    @staticmethod
    def find_market_key_by_index_address(input_dict: dict, index_token_address: str):
        """
        For a given index token address, identify that key in input_dict that matches the value for
        'index_token_address'

        Parameters
        ----------
        input_dict : dict
            Input dictionary containing token information.
        index_token_address : str
            string of index address we want to find the key of.

        """

        for key, value in input_dict.items():
            if value.get('index_token_address') == index_token_address:
                return key
        return None
