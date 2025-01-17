from .get import GetData
from ..gmx_utils import execute_threading


class GetBorrowAPR(GetData):
    def __init__(self, chain: str):
        super().__init__(chain)

    def _get_data_processing(self):
        """
        Generate the dictionary of borrow APR data

        Returns
        -------
        funding_apr : dict
            dictionary of borrow data.

        """
        output_list = []
        mapper = []
        for market_key in self.markets.info:
            index_token_address = self.markets.get_index_token_address(
                market_key
            )

            self._get_token_addresses(market_key)
            output = self._get_oracle_prices(
                market_key,
                index_token_address,
            )

            output_list.append(output)
            mapper.append(self.markets.get_market_symbol(market_key))

        threaded_output = execute_threading(output_list)

        for key, output in zip(mapper, threaded_output):
            self.output["long"][key] = (
                output[1] / 10 ** 28
            ) * 3600
            self.output["short"][key] = (
                output[2] / 10 ** 28
            ) * 3600

            self.log.info(
                (
                    "{}\nLong Borrow Hourly Rate: -{:.5f}%\n"
                    "Short Borrow Hourly Rate: -{:.5f}%\n"
                ).format(
                    key,
                    self.output["long"][key],
                    self.output["short"][key]
                )
            )

        self.output['parameter'] = "borrow_apr"

        return self.output


if __name__ == "__main__":
    data = GetBorrowAPR(chain='arbitrum').get_data(to_csv=False)
