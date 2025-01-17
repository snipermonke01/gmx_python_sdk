import logging

from .get_markets import Markets
from .get_oracle_prices import OraclePrices
from ..gmx_utils import (
    get_reader_contract, contract_map, save_json_file_to_datastore,
    save_csv_to_datastore, make_timestamped_dataframe
)


class GetData:
    def __init__(
        self, config: str, use_local_datastore: bool = False,
        filter_swap_markets: bool = True
    ):
        self.config = config
        self.use_local_datastore = use_local_datastore
        self.filter_swap_markets = filter_swap_markets

        self.log = logging.getLogger(self.__class__.__name__)
        self.markets = Markets(config)
        self.reader_contract = get_reader_contract(config)
        self.data_store_contract_address = (
            contract_map[self.config.chain]['datastore']['contract_address']
        )
        self.output = {
            "long": {},
            "short": {}
        }

        self._long_token_address = None
        self._short_token_address = None

    def get_data(self, to_json: bool = False, to_csv: bool = False):
        if self.filter_swap_markets:
            self._filter_swap_markets()

        data = self._get_data_processing()

        if to_json:
            parameter = data['parameter']
            save_json_file_to_datastore(
                "{}_{}_data.json".format(self.config.chain, parameter),
                data
            )

        if to_csv:
            try:
                parameter = data['parameter']
                dataframe = make_timestamped_dataframe(data['long'])
                save_csv_to_datastore(
                    "{}_long_{}_data.csv".format(self.config.chain, parameter),
                    dataframe
                )
                dataframe = make_timestamped_dataframe(data['short'])
                save_csv_to_datastore(
                    "{}_short_{}_data.csv".format(self.config.chain, parameter),
                    dataframe
                )
            except KeyError as e:

                dataframe = make_timestamped_dataframe(data)
                save_csv_to_datastore(
                    "{}_{}_data.csv".format(self.config.chain, parameter),
                    dataframe
                )

            except Exception as e:
                logging.info(e)

        return data

    def _get_data_processing(self):
        pass

    def _get_token_addresses(self, market_key: str):
        self._long_token_address = self.markets.get_long_token_address(
            market_key
        )
        self._short_token_address = self.markets.get_short_token_address(
            market_key
        )
        self.log.info(
            "Long Token Address: {}\nShort Token Address: {}".format(
                self._long_token_address, self._short_token_address
            )
        )

    def _filter_swap_markets(self):
        # TODO: Move to markets MAYBE
        keys_to_remove = []
        for market_key in self.markets.info:
            market_symbol = self.markets.get_market_symbol(market_key)
            if 'SWAP' in market_symbol:
                # Remove swap markets from dict
                keys_to_remove.append(market_key)

        [self.markets.info.pop(k) for k in keys_to_remove]

    def _get_pnl(
        self, market: list, prices_list: list, is_long: bool,
        maximize: bool = False
    ):
        open_interest_pnl = (
            self.reader_contract.functions.getOpenInterestWithPnl(
                self.data_store_contract_address,
                market,
                prices_list,
                is_long,
                maximize
            )
        )

        pnl = self.reader_contract.functions.getPnl(
            self.data_store_contract_address,
            market,
            prices_list,
            is_long,
            maximize
        )

        return open_interest_pnl, pnl

    def _get_oracle_prices(
        self,
        market_key: str,
        index_token_address: str,
        return_tuple: bool = False
    ):
        """
        For a given market get the marketInfo from the reader contract

        Parameters
        ----------
        market_key : str
            address of GMX market.
        index_token_address : str
            address of index token.
        long_token_address : str
            address of long collateral token.
        short_token_address : str
            address of short collateral token.

        Returns
        -------
        reader_contract object
            unexecuted reader contract object.

        """
        oracle_prices_dict = OraclePrices(self.config.chain).get_recent_prices()

        try:
            prices = (
                (
                    int(
                        (
                            oracle_prices_dict[index_token_address]
                            ['minPriceFull']
                        )
                    ),
                    int(
                        (
                            oracle_prices_dict[index_token_address]
                            ['maxPriceFull']
                        )
                    )
                ),
                (
                    int(
                        (
                            oracle_prices_dict[self._long_token_address]
                            ['minPriceFull']
                        )
                    ),
                    int(
                        (
                            oracle_prices_dict[self._long_token_address]
                            ['maxPriceFull']
                        )
                    )
                ),
                (
                    int(
                        (
                            oracle_prices_dict[self._short_token_address]
                            ['minPriceFull']
                        )
                    ),
                    int(
                        (
                            oracle_prices_dict[self._short_token_address]
                            ['maxPriceFull']
                        )
                    )
                ))

        # TODO - this needs to be here until GMX add stables to signed price
        # API
        except KeyError:
            prices = (
                (
                    int(
                        oracle_prices_dict[index_token_address]['minPriceFull']
                    ),
                    int(
                        oracle_prices_dict[index_token_address]['maxPriceFull']
                    )
                ),
                (
                    int(
                        (
                            oracle_prices_dict[self._long_token_address]
                            ['minPriceFull']
                        )
                    ),
                    int(
                        (
                            oracle_prices_dict[self._long_token_address]
                            ['maxPriceFull']
                        )
                    )
                ),
                (
                    int(1000000000000000000000000),
                    int(1000000000000000000000000)
                ))

        if return_tuple:
            return prices

        return self.reader_contract.functions.getMarketInfo(
            self.data_store_contract_address,
            prices,
            market_key
        )

    @staticmethod
    def _format_market_info_output(output):
        output = {
            "market_address": output[0][0],
            "index_address": output[0][1],
            "long_address": output[0][2],
            "short_address": output[0][3],

            "borrowingFactorPerSecondForLongs": output[1],
            "borrowingFactorPerSecondForShorts": output[2],

            "baseFunding_long_fundingFeeAmountPerSize_longToken": output[3][0][0][0],
            "baseFundinglong_fundingFeeAmountPerSize_shortToken": output[3][0][0][1],
            "baseFundingshort_fundingFeeAmountPerSize_longToken": output[3][0][1][0],
            "baseFundingshort_fundingFeeAmountPerSize_shortToken": output[3][0][1][1],
            "baseFundinglong_claimableFundingAmountPerSize_longToken": output[3][1][0][0],
            "baseFundinglong_claimableFundingAmountPerSize_shortToken": output[3][1][0][1],
            "baseFundingshort_claimableFundingAmountPerSize_longToken": output[3][1][1][0],
            "baseFundingshort_claimableFundingAmountPerSize_shortToken": output[3][1][1][1],

            "longsPayShorts": output[4][0],
            "fundingFactorPerSecond": output[4][1],
            "nextSavedFundingFactorPerSecond": output[4][2],

            "nextFunding_long_fundingFeeAmountPerSize_longToken": output[4][3][0][0],
            "nextFunding_long_fundingFeeAmountPerSize_shortToken": output[4][3][0][1],
            "nextFunding_baseFundingshort_fundingFeeAmountPerSize_longToken": output[4][3][1][0],
            "nextFunding_baseFundingshort_fundingFeeAmountPerSize_shortToken": output[4][3][1][1],
            "nextFunding_baseFundinglong_claimableFundingAmountPerSize_longToken": output[4][4][0][0],
            "nextFunding_baseFundinglong_claimableFundingAmountPerSize_shortToken": output[4][4][0][1],
            "nextFunding_baseFundingshort_claimableFundingAmountPerSize_longToken": output[4][4][1][0],
            "nextFunding_baseFundingshort_claimableFundingAmountPerSize_shortToken": output[4][4][1][1],

            "virtualPoolAmountForLongToken": output[5][0],
            "virtualPoolAmountForShortToken": output[5][1],
            "virtualInventoryForPositions": output[5][2],

            "isDisabled": output[6],
        }
        return output
