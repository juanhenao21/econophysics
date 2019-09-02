'''Self- and cross responses figures

Plot the short and long self- and cross responses for the stocks AAPL, CVX,
GS, JPM, MSFT, and XOM.
'''

# ----------------------------------------------------------------------------
# Modules
from matplotlib import pyplot as plt
import numpy as np
import os
import pickle

# ----------------------------------------------------------------------------


def taq_self_response_year_avg_shift_plot(ticker, year, taus):
    """Plots the self-response average for a year in event scale and time scale.

    :param ticker: string of the abbreviation of the stock to be analized
     (i.e. 'AAPL').
    :param year: string of the year to be analized (i.e '2008').
    :param taus: list of integers greater than zero (i.e. [1, 10, 50]).
    :return: None -- The function saves the plot in a file and does not return
     a value.
    """

    try:
        figure = plt.figure(figsize=(16, 9))

        # Figure with different plots for different taus
        for tau_idx, tau_val in enumerate(taus):

            ax1 = plt.subplot(2, len(taus), tau_idx + 1)
            ax2 = plt.subplot(2, len(taus), tau_idx + len(taus) + 1)

            times = np.array(range(- 10 * tau_val, 10 * tau_val, 1))

            # Load data
            self_event = pickle.load(open(''.join((
                               '../../project/taq_data/event_shift_data_{1}/taq_self'
                               + '_response_year_event_shift_data_tau_{2}/taq'
                               + '_self_response_year_event_shift_data_tau_{2}'
                               + '_{1}_{0}.pickle').split())
                               .format(ticker, year, tau_val), 'rb'))


            print(self_event)
            max_pos = np.where(max(self_event) == self_event)[0][0]

            ax1.plot(times, self_event, linewidth=5, label=r'{}'.format(ticker))
            # Plot line in the peak of the figure
            ax1.plot((times[max_pos], times[max_pos]), (0, self_event[max_pos]),
                    '--', label=r'Max position $t$ = {}'
                    .format(max_pos - 10 * tau_val))
            ax1.legend(loc='best', fontsize=15)
            # ax.set_title(r'$\tau$ = {}'.format(tau_val), fontsize=20)
            ax1.set_xlabel(r'Time shift $[s]$', fontsize=15)
            ax1.set_ylabel(r'$R_{ii}(\tau)$', fontsize=15)
            ax1.grid(True)

            self_time = pickle.load(open(''.join((
                               '../../project/taq_data/time_shift_data_{1}/taq_self'
                               + '_response_year_time_shift_data_tau_{2}/taq'
                               + '_self_response_year_time_shift_data_tau_{2}'
                               + '_{1}_{0}.pickle').split())
                               .format(ticker, year, tau_val), 'rb'))

            max_pos = np.where(max(self_time) == self_time)[0][0]


            ax2.plot(times, self_time, linewidth=5, label=r'{}'.format(ticker))
            # Plot line in the peak of the figure
            ax2.plot((times[max_pos], times[max_pos]), (0, self_time[max_pos]),
                    '--', label=r'Max position $t$ = {}'
                    .format(max_pos - 10 * tau_val))
            ax2.legend(loc='best', fontsize=15)
            # ax2.set_title(r'$\tau$ = {}'.format(tau_val), fontsize=20)
            ax2.set_xlabel(r'Time shift $[s]$', fontsize=15)
            ax2.set_ylabel(r'$R_{ii}(\tau)$', fontsize=15)
            ax2.grid(True)

        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        plt.tight_layout()
        plt.show()


        # Save plot

        return None

    except FileNotFoundError as e:
        print('No data')
        print(e)
        print()
        return None

# ----------------------------------------------------------------------------


def main():

    taus = [1, 10, 100, 1000]
    year = '2008'

    taq_self_response_year_avg_shift_plot('AAPL', year, taus)

    return None

# ----------------------------------------------------------------------------


if __name__ == "__main__":
    main()
