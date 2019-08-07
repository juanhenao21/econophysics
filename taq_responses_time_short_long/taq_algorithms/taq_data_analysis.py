'''
TAQ data analysis

Module to compute the following data

- Midpoint price data: using the TAQ data obtain the best bid, best ask,
  quotes and midpoint price data.

- Trade signs data: using the TAQ data obtain the trade signs data.

- Self response function: using the midpoint price and the trade signs
  calculate the midpoint log returns and the self response of a stock.

- Cross response function: using the midpoint price and the trade signs
  calculate the midpoint log returns and the cross response between two
  stocks.

- Trade sign self correlator: using the trade signs of two stocks calculate
  the trade sign self correlator.

- Trade sign cross correlator: using the trade signs of two stocks calculate
  the trade sign cross correlator.

Juan Camilo Henao Londono
juan.henao-londono@stud.uni-due.de
'''

# ----------------------------------------------------------------------------
# Modules

import numpy as np
import os

import pandas as pd
import pickle

import multiprocessing as mp
from itertools import product

import taq_data_tools

# ----------------------------------------------------------------------------


def taq_self_response_day_time_short_long_tau_data(ticker, date, tau, tau_p):
    """
    Obtain the self response function using the midpoint price returns
    and trade signs of the ticker during different time lags. Return an
    array with the self response for a day and an array of the number of
    trades for each value of tau.
        :param ticker: string of the abbreviation of the midpoint stock to
         be analized (i.e. 'AAPL')
        :param date: string with the date of the data to be extracted
         (i.e. '2008-01-02')
    """

    date_sep = date.split('-')

    year = date_sep[0]
    month = date_sep[1]
    day = date_sep[2]

    function_name = taq_self_response_day_time_short_long_tau_data.__name__
    taq_data_tools.taq_function_header_print_data(function_name, ticker,
                                                  ticker, year, month, day)

    try:

        # Load data
        midpoint = pickle.load(open(''.join((
                '../../taq_data/article_reproduction_data_{1}/taq_midpoint'
                + '_full_time_data/taq_midpoint_full_time_data_midpoint_{1}'
                + '{2}{3}_{0}.pickle').split())
                .format(ticker, year, month, day), 'rb'))
        _, _, trade_sign = pickle.load(open("".join((
                '../../taq_data/article_reproduction_data_{1}/taq_trade_signs'
                + '_full_time_data/taq_trade_signs_full_time_data_{1}{2}{3}_'
                + '{0}.pickle').split())
                .format(ticker, year, month, day), 'rb'))
        # As the data is loaded from the original reproduction data from the
        # article, the data have a shift of 1 second.

        assert len(midpoint) == len(trade_sign)

        # Array of the average of each tau
        self_response= np.zeros(tau)
        num = np.zeros(tau)

        # Calculating the midpoint log return and the self response function
        # Short response
        trade_sign_tau_short = trade_sign[:-tau_p]
        trade_sign_no_0_len_short = len(trade_sign_tau_short
                                        [trade_sign_tau_short != 0])
        num[:tau_p + 1] = trade_sign_no_0_len_short * np.ones(tau_p + 1)
        # Obtain the midpoint log return. Displace the numerator tau
        # values to the right and compute the return

        # midpoint price returns

        log_return_sec_short = (midpoint[tau_p:]
                                - midpoint[:-tau_p]) \
            / midpoint[:-tau_p]

        # Obtain the self response value
        if (trade_sign_no_0_len_short != 0):
            product_short = log_return_sec_short * trade_sign_tau_short
            self_response[:tau_p + 1] = np.sum(product_short) * np.ones(tau_p + 1)

        # Depending on the tau value
        for tau_idx in range(tau):

            if (tau_idx <= tau_p):
                pass

            else:
                # Long response
                trade_sign_tau_long = trade_sign[tau_p:-tau_idx - 1]
                trade_sign_no_0_len_long = len(trade_sign_tau_long
                                                [trade_sign_tau_long != 0])
                num[tau_idx] = trade_sign_no_0_len_long + trade_sign_no_0_len_short
                # Obtain the midpoint log return. Displace the numerator tau
                # values to the right and compute the return

                # midpoint price returns

                log_return_sec_long = (midpoint[tau_idx + 1:-tau_p]
                                        - midpoint[tau_p:-tau_idx - 1]) \
                    / midpoint[tau_p:-tau_idx - 1]

                # Obtain the self response value
                if (trade_sign_no_0_len_long != 0):
                    product_long = log_return_sec_long * trade_sign_tau_long
                    self_response[tau_idx] = np.sum(product_long) + np.sum(product_short)

        return (self_response, num)

    except FileNotFoundError:
        print('No data')
        print()
        return None

# ----------------------------------------------------------------------------


def taq_self_response_year_time_short_long_tau_data(ticker, year, tau, tau_p):
    """
    Obtain the year average self response function using the midpoint
    price returns and trade signs of the ticker during different time
    lags. Return an array with the year average self response.
        :param ticker: string of the abbreviation of the midpoint stock to
         be analized (i.e. 'AAPL')
        :param year: string of the year to be analized (i.e '2016')
    """

    function_name = taq_self_response_year_time_short_long_tau_data.__name__
    taq_data_tools.taq_function_header_print_data(function_name, ticker,
                                                  ticker, year, '',
                                                  '')

    dates = taq_data_tools.taq_bussiness_days(year)

    self_response = np.zeros(tau)
    num = []

    for date in dates:

        try:

            data, avg_num = \
                 taq_self_response_day_time_short_long_tau_data(ticker, date, tau,
                                                            tau_p)

            self_response += data
            num.append(avg_num)

        except TypeError:
            pass

    num = np.asarray(num)
    num_t = np.sum(num, axis=0)

    # Saving data
    taq_data_tools.taq_save_data('{}_tau_{}_tau_p_{}'.format(function_name, tau, tau_p),
                                 self_response / num_t,
                                 ticker, ticker, year, '', '')

    return self_response / num_t

# ----------------------------------------------------------------------------


def taq_cross_response_day_time_short_long_tau_data(ticker_i, ticker_j, date, tau,
                                                tau_p):
    """
    Obtain the cross response function using the midpoint price returns of
    ticker i and trade signs of ticker j during different time lags. The data
    is adjusted to use only the values each second. Return an array with the
    cross response function for a day.
        :param ticker_i: string of the abbreviation of the midpoint stock to
         be analized (i.e. 'AAPL')
        :param ticker_j: string of the abbreviation of the trade sign stock to
         be analized (i.e. 'AAPL')
        :param date: string with the date of the data to be extracted
         (i.e. '2008-01-02')
    """

    date_sep = date.split('-')

    year = date_sep[0]
    month = date_sep[1]
    day = date_sep[2]

    if (ticker_i == ticker_j):

        # Self-response

        return None

    else:

        try:

            function_name = taq_cross_response_day_time_short_long_tau_data. \
                            __name__
            taq_data_tools.taq_function_header_print_data(function_name,
                                                          ticker_i, ticker_j,
                                                          year, month, day)

            # Load data
            midpoint_i = pickle.load(open(''.join((
                    '../../taq_data/article_reproduction_data_{1}/taq'
                    + '_midpoint_full_time_data/taq_midpoint_full_time_data'
                    + '_midpoint_{1}{2}{3}_{0}.pickle').split())
                    .format(ticker_i, year, month, day), 'rb'))
            _, _, trade_sign_j = pickle.load(open("".join((
                    '../../taq_data/article_reproduction_data_2008/taq_trade_'
                    + 'signs_full_time_data/taq_trade_signs_full_time_data'
                    + '_{1}{2}{3}_{0}.pickle').split())
                    .format(ticker_j, year, month, day), 'rb'))
            # As the data is loaded from the original reproduction data from
            # the article, the data have a shift of 1 second.

            assert len(midpoint_i) == len(trade_sign_j)

            # Array of the average of each tau. 10^3 s used by Wang
            cross_response = np.zeros(tau)
            num = np.zeros(tau)

            # Calculating the midpoint return and the cross response function
            # Short response
            trade_sign_tau_short = trade_sign_j[:-tau_p]
            trade_sign_no_0_len_short = \
                len(trade_sign_tau_short[trade_sign_tau_short != 0])
            num[:tau_p + 1] = trade_sign_no_0_len_short * np.ones(tau_p + 1)
            # Obtain the midpoint log return. Displace the numerator
            # tau values to the right and compute the return

            log_return_i_sec_short = (midpoint_i[tau_p:]
                                        - midpoint_i[:-tau_p]) \
                / midpoint_i[:-tau_p]

            # Obtain the cross response value
            if (trade_sign_no_0_len_short != 0):
                product_short = log_return_i_sec_short \
                                * trade_sign_tau_short
                cross_response[:tau_p + 1] = np.sum(product_short) * np.ones(tau_p + 1)

            # Depending on the tau value
            for tau_idx in range(tau):

                if (tau_idx <= tau_p):
                    pass

                else:
                    # Long response
                    trade_sign_tau_long = trade_sign_j[tau_p:-tau_idx - 1]
                    trade_sign_no_0_len_long = len(trade_sign_tau_long
                                                    [trade_sign_tau_long != 0])
                    num[tau_idx] = trade_sign_no_0_len_long + trade_sign_no_0_len_short
                    # Obtain the midpoint log return. Displace the numerator
                    # tau values to the right and compute the return

                    log_return_i_sec_long = (midpoint_i[tau_idx + 1:-tau_p]
                                                - midpoint_i[tau_p:-tau_idx - 1])\
                        / midpoint_i[tau_p:-tau_idx - 1]

                    # Obtain the cross response value
                    if (trade_sign_no_0_len_long != 0):
                        product_long = log_return_i_sec_long \
                                        * trade_sign_tau_long
                        cross_response[tau_idx] = np.sum(product_long) + np.sum(product_short)

            return (cross_response, num)

        except FileNotFoundError:
            print('No data')
            print()
            return None

# ----------------------------------------------------------------------------


def taq_cross_response_year_time_short_long_tau_data(ticker_i, ticker_j, year, tau,
                                                 tau_p):
    """
    Obtain the year average cross response function using the midpoint
    price returns and trade signs of the tickers during different time
    lags. Return an array with the year average cross response.
        :param ticker_i: string of the abbreviation of the midpoint stock to
         be analized (i.e. 'AAPL')
        :param ticker_j: string of the abbreviation of the trade sign stock to
         be analized (i.e. 'AAPL')
        :param year: string of the year to be analized (i.e '2016')
    """

    if (ticker_i == ticker_j):

        # Self-response

        return None

    else:

        function_name = taq_cross_response_year_time_short_long_tau_data.__name__
        taq_data_tools.taq_function_header_print_data(function_name, ticker_i,
                                                      ticker_j, year, '',
                                                      '')

        dates = taq_data_tools.taq_bussiness_days(year)

        cross_response = np.zeros(tau)
        num = []

        for date in dates:

            try:

                data, avg_num = \
                    taq_cross_response_day_time_short_long_tau_data(ticker_i,
                                                                ticker_j, date,
                                                                tau, tau_p)

                cross_response += data
                num.append(avg_num)

            except TypeError:
                pass

        num = np.asarray(num)
        num_t = np.sum(num, axis=0)

        # Saving data
        taq_data_tools.taq_save_data('{}_tau_{}_tau_p_{}'.format(function_name, tau, tau_p),
                                     cross_response / num_t,
                                     ticker_i, ticker_j, year, '', '')

        return cross_response / num_t

# ----------------------------------------------------------------------------


def main():

    tickers = ['AAPL', 'MSFT']
    year = '2008'

    taq_cross_response_year_time_short_long_tau_data('AAPL', 'MSFT', '2008', 1000,
                                                 10)


if __name__ == "__main__":
    main()