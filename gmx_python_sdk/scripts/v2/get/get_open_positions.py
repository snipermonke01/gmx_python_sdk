import logging
import numpy as np

from .get import GetData
from .get_oracle_prices import OraclePrices

from ..gmx_utils import (get_tokens_address_dict, convert_to_checksum_address)

chain = 'arbitrum'


class GetOpenPositions(GetData):
    def __init__(self, config: str, address: str):
        super().__init__(config)
        self.address = convert_to_checksum_address(config, address)

    def get_data(self):
        """
        Get all open positions for a given address on the chain defined in
        class init

        Parameters
        ----------
        address : str
            evm address .

        Returns
        -------
        processed_positions : dict
            a dictionary containing the open positions, where asset and
            direction are the keys.

        """
        raw_positions = self.reader_contract.functions.getAccountPositions(
            self.data_store_contract_address,
            self.address,
            0,
            10
        ).call()

        if len(raw_positions) == 0:
            logging.info(
                'No positions open for address: "{}"" on {}.'.format(
                    self.address,
                    self.config.chain.title()
                )
            )
        processed_positions = {}

        for raw_position in raw_positions:
            try:
                processed_position = self._get_data_processing(raw_position)

                # TODO - maybe a better way of building the key?
                if processed_position['is_long']:
                    direction = 'long'
                else:
                    direction = 'short'

                key = "{}_{}".format(
                    processed_position['market_symbol'][0],
                    direction
                )
                processed_positions[key] = processed_position
            except KeyError as e:
                logging.error(f"Incompatible market: {e}")

        return processed_positions

    def _get_data_processing(self, raw_position: tuple):
        """
        A tuple containing the raw information return from the reader contract
        query GetAccountPositions

        Parameters
        ----------
        raw_position : tuple
            raw information return from the reader contract .

        Returns
        -------
        dict
            a processed dictionary containing info on the positions.
        """
        market_info = self.markets.info[raw_position[0][1]]

        chain_tokens = get_tokens_address_dict(chain)

        entry_price = (
            raw_position[1][0] / raw_position[1][1]
        ) / 10 ** (
            30 - chain_tokens[market_info['index_token_address']]['decimals']
        )

        leverage = (
            raw_position[1][0] / 10 ** 30
        ) / (
            raw_position[1][2] / 10 ** chain_tokens[
                raw_position[0][2]
            ]['decimals']
        )
        prices = OraclePrices(chain=chain).get_recent_prices()
        mark_price = np.median(
            [
                float(
                    prices[market_info['index_token_address']]['maxPriceFull']
                ),
                float(
                    prices[market_info['index_token_address']]['minPriceFull']
                )
            ]
        ) / 10 ** (
            30 - chain_tokens[market_info['index_token_address']]['decimals']
        )

        return {
            "account": raw_position[0][0],
            "market": raw_position[0][1],
            "market_symbol": (
                self.markets.info[raw_position[0][1]]['market_symbol'],
            ),
            "collateral_token": chain_tokens[raw_position[0][2]]['symbol'],
            "position_size": raw_position[1][0] / 10**30,
            "size_in_tokens": raw_position[1][1],
            "entry_price": (
                (
                    raw_position[1][0] / raw_position[1][1]
                ) / 10 ** (
                    30 - chain_tokens[
                        market_info['index_token_address']
                    ]['decimals']
                )
            ),
            "inital_collateral_amount": raw_position[1][2],
            "inital_collateral_amount_usd": (
                raw_position[1][2]
                / 10 ** chain_tokens[raw_position[0][2]]['decimals'],
            ),
            "leverage": leverage,
            "borrowing_factor": raw_position[1][3],
            "funding_fee_amount_per_size": raw_position[1][4],
            "long_token_claimable_funding_amount_per_size": raw_position[1][5],
            "short_token_claimable_funding_amount_per_size": raw_position[1][6],
            "position_modified_at": "",
            "is_long": raw_position[2][0],
            "percent_profit": (
                (
                    1 - (mark_price / entry_price)
                ) * leverage
            ) * 100,
            "mark_price": mark_price
        }


if __name__ == "__main__":
    address = "0x99f5585dcc32e2238634f11f32d9be9bd5e98b49"
    positions = GetOpenPositions(chain='arbitrum', address=address).get_data()

    for position in positions:
        print(positions[position])
