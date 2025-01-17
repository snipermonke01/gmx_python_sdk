from utils import _set_paths

_set_paths()

from gmx_python_sdk.scripts.v2.get.get_available_liquidity import (
    GetAvailableLiquidity
)
from gmx_python_sdk.scripts.v2.get.get_borrow_apr import GetBorrowAPR
from gmx_python_sdk.scripts.v2.get.get_claimable_fees import GetClaimableFees
from gmx_python_sdk.scripts.v2.get.get_contract_balance import (
    GetPoolTVL as ContractTVL
)
from gmx_python_sdk.scripts.v2.get.get_funding_apr import GetFundingFee
from gmx_python_sdk.scripts.v2.get.get_gm_prices import GMPrices
from gmx_python_sdk.scripts.v2.get.get_markets import Markets
from gmx_python_sdk.scripts.v2.get.get_open_interest import OpenInterest
from gmx_python_sdk.scripts.v2.get.get_oracle_prices import OraclePrices
from gmx_python_sdk.scripts.v2.get.get_pool_tvl import GetPoolTVL
from gmx_python_sdk.scripts.v2.get.get_glv_stats import GlvStats

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager


class GetGMXv2Stats:

    def __init__(self, config, to_json, to_csv):
        self.config = config
        self.to_json = to_json
        self.to_csv = to_csv

    def get_available_liquidity(self):

        return GetAvailableLiquidity(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_borrow_apr(self):

        return GetBorrowAPR(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_claimable_fees(self):

        return GetClaimableFees(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_contract_tvl(self):

        return ContractTVL(
            self.config
        ).get_pool_balances(
            to_json=self.to_json
        )

    def get_funding_apr(self):

        return GetFundingFee(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_gm_price(self):

        return GMPrices(
            self.config
        ).get_price_traders(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_available_markets(self):

        return Markets(
            self.config
        ).get_available_markets()

    def get_open_interest(self):

        return OpenInterest(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_oracle_prices(self):

        return OraclePrices(
            self.config.chain
        ).get_recent_prices()

    def get_pool_tvl(self):

        return GetPoolTVL(
            self.config
        ).get_pool_balances(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_glv_stats(self):

        return GlvStats(
            self.config
        ).get_glv_stats()


if __name__ == "__main__":

    to_json = True
    to_csv = True

    config = ConfigManager(chain='arbitrum')
    config.set_config()

    stats_object = GetGMXv2Stats(
        config=config,
        to_json=to_json,
        to_csv=to_csv
    )

    markets = stats_object.get_available_markets()
    liquidity = stats_object.get_available_liquidity()
    borrow_apr = stats_object.get_borrow_apr()
    claimable_fees = stats_object.get_claimable_fees()
    contract_tvl = stats_object.get_contract_tvl()
    funding_apr = stats_object.get_funding_apr()
    gm_prices = stats_object.get_gm_price()
    open_interest = stats_object.get_open_interest()
    oracle_prices = stats_object.get_oracle_prices()
    pool_tvl = stats_object.get_pool_tvl()
    glv_price = stats_object.get_glv_stats()
