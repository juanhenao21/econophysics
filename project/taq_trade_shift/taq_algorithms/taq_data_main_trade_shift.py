'''TAQ data main module.

The functions in the module run the complete analysis and plot of the TAQ data
for the trade shift between returns and trade signs. To run this module it
is necessary to have the files of the midpoint prices for trade time scale
from the TAQ Responses Physical module and the trade signs for trade time scale
from the TAQ Responses Trade module.

This script requires the following modules:
    * itertools.product
    * multiprocessing
    * pandas
    * taq_data_analysis_trade_shift
    * taq_data_plot_trade_shift
    * taq_data_tools_trade_shift

The module contains the following functions:
    * taq_data_plot_generator - generates all the analysis and plots from the
      TAQ data.
    * main - the main function of the script.

.. moduleauthor:: Juan Camilo Henao Londono <www.github.com/juanhenao21>
'''

# -----------------------------------------------------------------------------
# Modules

from itertools import product as iprod
import multiprocessing as mp
import os
import pandas as pd
import pickle

import taq_data_analysis_trade_shift
import taq_data_plot_trade_shift
import taq_data_tools_trade_shift

# -----------------------------------------------------------------------------


def taq_data_plot_generator(tickers, year, taus):
    """Generates all the analysis and plots from the TAQ data.

    :param tickers: list of the string abbreviation of the stocks to be
     analized (i.e. ['AAPL', 'MSFT']).
    :param year: string of the year to be analized (i.e '2016').
    :param taus: list of integers greater than zero (i.e. [1, 10, 50]).
    :return: None -- The function saves the data in a file and does not return
     a value.
    """

    # Especific functions
    # Self-response
    for ticker in tickers:
        for tau in taus:

            taq_data_analysis_trade_shift \
                .taq_self_response_year_trade_shift_data(ticker, year, tau)

    ticker_prod = iprod(tickers, tickers)

    # Cross-response
    for ticks in ticker_prod:
        for tau in taus:

            taq_data_analysis_trade_shift \
                .taq_cross_response_year_trade_shift_data(ticks[0], ticks[1],
                                                          year, tau)
    # Parallel computing
    with mp.Pool(processes=mp.cpu_count()) as pool:
        # Plot
        pool.starmap(taq_data_plot_trade_shift
                     .taq_self_response_year_avg_trade_shift_plot,
                     iprod(tickers, [year], [taus]))
        pool.starmap(taq_data_plot_trade_shift
                     .taq_cross_response_year_avg_trade_shift_plot,
                     iprod(tickers, tickers, [year], [taus]))

    return None

# -----------------------------------------------------------------------------


def main():
    """The main function of the script.

    The main function is used to test the functions in the script.

    :return: None.
    """

    # Tickers and days to analyze
    year, tickers, taus = taq_data_tools_trade_shift.taq_initial_data()

    # Basic folders
    # taq_data_tools_trade_shift.taq_start_folders('2008')

    # Run analysis
    # Analysis and plot
    taq_data_plot_generator(tickers, year, taus)

    print('Ay vamos!!')

    return None

# -----------------------------------------------------------------------------


if __name__ == '__main__':
    main()