import requests


class OraclePrices:
    def __init__(self, chain: str):
        self.chain = chain
        self.oracle_url = {
            "arbitrum": (
                "https://arbitrum-api.gmxinfra.io/signed_prices/latest"
            ),
            "avalanche": (
                "https://avalanche-api.gmxinfra.io/signed_prices/latest"
            )
        }

    def get_recent_prices(self):
        """
        Get raw output of the GMX rest v2 api for signed prices

        Returns
        -------
        dict
            dictionary containing raw output for each token as its keys.

        """
        raw_output = self._make_query().json()
        return self._process_output(raw_output)

    def _make_query(self):
        """
        Make request using oracle url

        Returns
        -------
        requests.models.Response
            raw request response.

        """
        url = self.oracle_url[self.chain]
        return requests.get(url)

    def _process_output(self, output: dict):
        """
        Take the API response and create a new dictionary where the index token
        addresses are the keys

        Parameters
        ----------
        output : dict
            Dictionary of rest API repsonse.

        Returns
        -------
        processed : TYPE
            DESCRIPTION.

        """
        processed = {}
        for i in output['signedPrices']:
            processed[i['tokenAddress']] = i

        return processed


if __name__ == '__main__':

    pass
