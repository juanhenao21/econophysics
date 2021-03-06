'''ITCH trade sign classification

Module to implement Eq. 1,2 and 3 to classify trade signs used in the section
2.3 of the `paper
 <https://link.springer.com/content/pdf/10.1140/epjb/e2016-60818-y.pdf>`_.
The classification is made using the TotalView-ITCH 2008 data.
Finally, the acurracy of the classification is computed.

..moduleauthor:: Juan Camilo Henao Londono <www.github.com/juanhenao21>
'''

# ----------------------------------------------------------------------------
# Modules

import gzip
import numpy as np
import os
import pandas as pd

# ----------------------------------------------------------------------------


def itch_trade_classification_data(ticker, year, month, day):
    """Extracts the data to make the classification.

    Obtain the reference time, trade signs, volumes and prices from an
    TotalView-ITCH file. These data is used to test the trade sign
    classification equations.

    :param ticker: string of the abbreviation of the stock to be analyzed
     (i.e. 'AAPL').
    :param year: string of the year to be analyzed (i.e '2008').
    :param month: string of the month to be analyzed (i.e '07').
    :param day: string of the day to be analyzed (i.e '07').
    :return: tuple -- The function returns a tuple with numpy arrays.
    """

    print(f'Processing data for the stock {ticker} the {year}.{month}.{day}')
    print()

    # Load full data using cols with values time, order, type, shares and price
    data = pd.read_csv(gzip.open(''.join((
        f'../../itch_data/original_data_{year}/{year}{month}{day}_{ticker}'
        + f'.csv.gz').split()), 'rt'), usecols=(0, 2, 3, 4, 5),
        dtype={'Time': 'uint32', 'Order': 'uint64', 'T': str,
               'Shares': 'uint16', 'Price': 'float64'})

    data['Price'] = data['Price'] / 10000

    # Select only trade orders. Visible ('E' and 'F') and hidden ('T')
    trade_pos = np.array(data['T'] == 'E') + np.array(data['T'] == 'F') \
        + np.array(data['T'] == 'T')
    trade_data = data[trade_pos]

    # Converting the data in numpy arrays
    trade_data_time = trade_data['Time'].values
    trade_data_order = trade_data['Order'].values
    trade_data_types = 3 * np.array(trade_data['T'] == 'E') \
        + 4 * np.array(trade_data['T'] == 'F') \
        + 5 * np.array(trade_data['T'] == 'T')
    trade_data_volume = trade_data['Shares'].values
    trade_data_price = trade_data['Price'].values

    # Select only limit orders
    limit_pos = np.array(data['T'] == 'B') + np.array(data['T'] == 'S')
    limit_data = data[limit_pos]

    # Reduce the values to only the ones that have the same order number as
    # trade orders
    limit_data = limit_data[limit_data.Order.isin(trade_data['Order'])]

    # Converting the data in numpy arrays
    limit_data_order = limit_data['Order'].values
    limit_data_types = 1 * np.array(limit_data['T'] == 'S') \
        - 1 * np.array(limit_data['T'] == 'B')
    limit_data_volume = limit_data['Shares'].values
    limit_data_price = limit_data['Price'].values

    # Arrays to store the info of the identified trades
    length_trades = len(trade_data)
    trade_times = 1 * trade_data_time
    trade_signs = np.zeros(length_trades)
    trade_volumes = np.zeros(length_trades, dtype='uint16')
    trade_price = np.zeros(length_trades)

    # In the for loop is assigned the price, trade sign and volume of each
    # trade.
    for t_idx in range(length_trades):

        try:

            # limit orders that have the same order as the trade order
            l_idx = np.where(limit_data_order == trade_data_order[t_idx])[0][0]

            # Save values that are independent of the type

            # Price of the trade (Limit data)
            trade_price[t_idx] = limit_data_price[l_idx]

            # Trade sign identification
            trade = limit_data_types[l_idx]

            if (trade == 1):
                trade_signs[t_idx] = 1.
            else:
                trade_signs[t_idx] = -1.

            # The volume depends on the trade type. If it is 4 the
            # value is taken from the limit data and the order number
            # is deleted from the data. If it is 3 the
            # value is taken from the trade data and then the
            # value of the volume in the limit data must be
            # reduced with the value of the trade data
            volume_type = trade_data_types[t_idx]

            if (volume_type == 4):

                trade_volumes[t_idx] = limit_data_volume[l_idx]
                limit_data_order[l_idx] = 0

            else:

                trade_volumes[t_idx] = trade_data_volume[t_idx]
                diff_volumes = limit_data_volume[l_idx] \
                    - trade_data_volume[t_idx]

                assert diff_volumes > 0

                limit_data_volume[l_idx] = diff_volumes

        except IndexError:

            pass

    assert len(trade_signs != 0) == len(trade_data_types != 5)

    # To use the hidden trades, I change the values in the computed arrays with
    # the information of visible trades to have the hidden information.
    hidden_pos = trade_data_types == 5
    trade_volumes[hidden_pos] = trade_data_volume[hidden_pos]
    trade_price[hidden_pos] = trade_data_price[hidden_pos]

    # Open market time 9h40 - 15h50
    market_time = (trade_times / 3600 / 1000 >= 9.666666) & \
        (trade_times / 3600 / 1000 < 15.833333)

    trade_times_market = trade_times[market_time]
    trade_signs_market = trade_signs[market_time]
    trade_volumes_market = trade_volumes[market_time]
    trade_price_market = trade_price[market_time]

    return (trade_times_market, trade_signs_market, trade_volumes_market,
            trade_price_market)

# ----------------------------------------------------------------------------


def itch_trade_classification_eq1_data(ticker, trade_signs, price_signs, year,
                                       month, day):
    """Implementation Eq. 1.

    Implementation of Eq. 1 of the
    `paper
    <https://link.springer.com/content/pdf/10.1140/epjb/e2016-60818-y.pdf>`_.
    Obtain the experimental trade signs based on the change of prices. To
    compute the trades signs are used consecutive trades in the ITCH data.

    :param ticker: string of the abbreviation of the stock to be analyzed
     (i.e. 'AAPL').
    :param trade_signs: array of empirical trade signs from ITCH data.
    :param price_signs: array of the price of the trades.
    :param year: string of the year to be analyzed (i.e '2008').
    :param month: string of the month to be analyzed (i.e '07').
    :param day: string of the day to be analyzed (i.e '07').
    :return: array -- The function returns a numpy array.
    """

    print('Implementation of Eq. 1.')
    print(f'Processing data for the stock {ticker} the {year}.{month}.{day}')
    print()

    identified_trades = np.zeros(len(trade_signs))

    # Implementation of Eq 1. Sign of the price change between consecutive
    # trades
    for t_idx, t_val in enumerate(trade_signs):

        diff = price_signs[t_idx] - price_signs[t_idx - 1]

        if (diff):

            identified_trades[t_idx] = np.sign(diff)

        else:

            identified_trades[t_idx] = identified_trades[t_idx - 1]

    trades_pos = trade_signs != 0
    identified_trades = identified_trades[trades_pos]

    return identified_trades

# ----------------------------------------------------------------------------


def itch_trade_classification_eq2_data(ticker, times_signs, trade_signs,
                                       identified_trades, year, month, day):
    """Implementation Eq. 2.

    Implementation of the Eq. 2 of the
    `paper
    <https://link.springer.com/content/pdf/10.1140/epjb/e2016-60818-y.pdf>`_.
    Obtain the experimental trade signs based on Eq. 1 classification using
    the ITCH data.
    :param ticker: string of the abbreviation of the stock to be analyzed
     (i.e. 'AAPL').
    :param times_signs: array of the time of the trades.
    :param trade_signs: array of the empirical trade signs from ITCH data.
    :param identified_trades: array of the trade signs from Eq. 1.
    :param year: string of the year to be analyzed (i.e '2008').
    :param month: string of the month to be analyzed (i.e '07').
    :param day: string of the day to be analyzed (i.e '07').
    :return: tuple -- The function returns a tuple with numpy arrays.
    """

    print('Implementation of Eq. 2.')
    print(f'Processing data for the stock {ticker} the {year}.{month}.{day}')
    print()

    trade_signs_no_0 = trade_signs != 0
    trade_signs = trade_signs[trade_signs_no_0]
    times_signs = times_signs[trade_signs_no_0]

    assert len(trade_signs) == len(identified_trades)

    full_time = np.array(range(34800, 57000))
    trades_emp_s = 0. * full_time
    trades_exp_s = 0. * full_time

    # Implementation of equation (2). Trade sign in each second
    for t_idx, t_val in enumerate(full_time):

        condition = (times_signs / 1000 >= t_val) \
                    * (times_signs / 1000 < t_val + 1)
        # Experimental
        trades_same_t_exp = identified_trades[condition]
        sign_exp = np.sign(np.sum(trades_same_t_exp))
        trades_exp_s[t_idx] = sign_exp

        # Empirical
        trades_same_t_emp = trade_signs[condition]
        sign_emp = np.sign(np.sum(trades_same_t_emp))
        trades_emp_s[t_idx] = sign_emp

    return (trades_emp_s, trades_exp_s)

# ----------------------------------------------------------------------------


def itch_trade_classification_eq3_data(ticker, times_signs, trade_signs,
                                       volume_signs, identified_trades, year,
                                       month, day):
    """Implementation Eq. 3.

    Implementation of the Eq. 3 of the
    `paper
    <https://link.springer.com/content/pdf/10.1140/epjb/e2016-60818-y.pdf>`_.
    Obtain the experimental trade signs based on Eq. 1 classification using
    the ITCH data.
    :param ticker: string of the abbreviation of the stock to be analyzed
     (i.e. 'AAPL').
    :param times_signs: array of the time of the trades.
    :param trade_signs: array of the theoric trade signs from ITCH data.
    :param volume_signs: array of the volume of the trades.
    :param identified_trades: array of the trades signs from Eq. 1.
    :param year: string of the year to be analyzed (i.e '2008').
    :param month: string of the month to be analyzed (i.e '07').
    :param day: string of the day to be analyzed (i.e '07').
    :return: tuple -- The function returns a tuple with numpy arrays.
    """

    print('Implementation of Eq. 3.')
    print(f'Processing data for the stock {ticker} the {year}.{month}.{day}')
    print()

    trade_signs_no_0 = trade_signs != 0
    trade_signs = trade_signs[trade_signs_no_0]
    times_signs = times_signs[trade_signs_no_0]
    volume_signs = volume_signs[trade_signs_no_0]

    assert (len(trade_signs) == len(identified_trades))

    full_time = np.array(range(34800, 57000))
    trades_emp_s = 0. * full_time
    trades_exp_s = 0. * full_time

    # Implementation of equation (3). Trade sign in each second
    for t_idx, t_val in enumerate(full_time):

        condition = (times_signs / 1000 >= t_val) \
                    * (times_signs / 1000 < t_val + 1)
        # Experimental
        trades_same_t_exp = identified_trades[condition]
        volumes_same_t = volume_signs[condition]
        sign_exp = np.sign(np.sum(trades_same_t_exp * volumes_same_t))
        trades_exp_s[t_idx] = sign_exp

        # Empirical
        trades_same_t_emp = trade_signs[condition]
        sign_emp = np.sign(np.sum(trades_same_t_emp))
        trades_emp_s[t_idx] = sign_emp

    return (trades_emp_s, trades_exp_s)

# ----------------------------------------------------------------------------


def main():
    """Main function of the script.

    The main function extract the data and classify the trade signs using
    different equations

    :return: None.
    """

    ticker = ['AAPL', 'AAPL', 'GS', 'GS', 'XOM', 'XOM']
    year = '2008'
    month = ['01', '06', '10', '12', '02', '08']
    day = ['07', '02', '07', '10', '11', '04']
    full_time = np.array(range(34800, 57000))

    file = open('../stats_trade_sign_classification.csv', 'a+')
    file.write('Ticker, Date, No_Id_Trades, No_Matches, Accuracy, '
               + 'No_Id_Trades, Matches_eq_2, Acc_eq_2, Matches_eq_3, '
               + 'Acc_eq_3, Trades_zero_eq2, Trades_zero_eq_3\n')

    for (t, m, d) in zip(ticker, month, day):

        (times_signs, trade_signs,
         volume_signs, price_signs) = itch_trade_classification_data(t, year,
                                                                     m, d)

        identified_trades = \
            itch_trade_classification_eq1_data(t, trade_signs, price_signs,
                                               year, m, d)

        emp_eq2_s, exp_eq2_s = \
            itch_trade_classification_eq2_data(t, times_signs, trade_signs,
                                               identified_trades, year, m, d)

        emp_eq3_s, exp_eq3_s = \
            itch_trade_classification_eq3_data(t, times_signs, trade_signs,
                                               volume_signs, identified_trades,
                                               year, m, d)

        count = 0
        for t_idx, t_val in enumerate(full_time):

            if(not emp_eq2_s[t_idx]
               and not exp_eq2_s[t_idx]
               and not exp_eq3_s[t_idx]):

                emp_eq2_s[t_idx] = float('nan')
                exp_eq2_s[t_idx] = float('nan')
                exp_eq3_s[t_idx] = float('nan')

                count += 1

        emp_eq2_s = emp_eq2_s[~np.isnan(emp_eq2_s)]
        exp_eq2_s = exp_eq2_s[~np.isnan(exp_eq2_s)]
        exp_eq3_s = exp_eq3_s[~np.isnan(exp_eq3_s)]

        assert len(emp_eq2_s) == len(exp_eq2_s)
        assert len(emp_eq2_s) == len(exp_eq3_s)

        date = year + m + d
        id_trades_trades_num = len(trade_signs[trade_signs != 0])
        trade_matches = np.sum(
            trade_signs[trade_signs != 0] == identified_trades)
        accuracy_trades = round(trade_matches / id_trades_trades_num, 4)
        id_trades_physical_num = len(emp_eq2_s)
        physical_matches_eq2 = np.sum(emp_eq2_s == exp_eq2_s)
        accuracy_physical_eq2 = round(physical_matches_eq2 / id_trades_physical_num,
                                    4)
        physical_matches_eq3 = np.sum(emp_eq2_s == exp_eq3_s)
        accuracy_physical_eq3 = round(physical_matches_eq3 / id_trades_physical_num,
                                    4)
        zeros_eq2 = np.sum(exp_eq2_s == 0) + count
        zeros_eq3 = np.sum(exp_eq3_s == 0) + count
        file.write(f'{t}, {date}, {id_trades_trades_num}, {trade_matches}, '
                   + f'{accuracy_trades}, '
                   + f'{id_trades_physical_num}, {physical_matches_eq2}, '
                   + f'{accuracy_physical_eq2}, '
                   + f'{physical_matches_eq3}, {accuracy_physical_eq3}, '
                   + f'{zeros_eq2}, {zeros_eq3}\n')

    file.close()

    return None

# ----------------------------------------------------------------------------


if __name__ == '__main__':
    main()
