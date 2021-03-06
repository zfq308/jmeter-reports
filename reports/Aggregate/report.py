import datetime
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
from matplotlib import rc
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
import pandas
from lxml import etree
from mpltools import style

from lib.basereport import BaseReport
from lib.utils import percentile90


class AggregateReport(BaseReport):
    """Aggregate JMeter report.
    Calculate Mean, Median, 90% Line, Max, Min and Throughput by label.
    """

    def _generate_html_data(self):
        if not hasattr(self, 'df') or self.df.empty:
            return ''

        # group data by 'label' field. this data use in plot generation.
        self._group_by_operation = self.df.groupby('label')
        # calc statistic by operation: mean, median, 90% line
        result = self._group_by_operation['Latency'].agg([np.mean, np.median, percentile90, np.min, np.max, np.std, np.sum])
        size = self._group_by_operation.size()

        # Calc throughput for every group
        result['sum'] = result['sum'].astype(float)
        for i in size.index:
            result['sum'][i] = float(size[i]) / float(result['sum'][i]) * 1000

        result = result.applymap(lambda x: round(x, 2))

        # rename columns
        result.rename(columns={'mean': 'Mean, msec',
                               'median': 'Median, msec',
                               'percentile90': '90% Line, msec',
                               'amin': 'Min, msec',
                               'amax': 'Max, msec',
                               'sum': 'Throughput, req/sec',
                               'std': 'StDev, msec'}, inplace=True)

        xml = etree.XML(result.to_html())
        xml.set('class', 'table table-hover table-condensed table-responsive table-bordered')
        xml.set('id', 'data')

        paths = {'mean': ['//table[@id="data"]/tbody/tr/td[1]', '//table[@id="data"]/thead/tr/th[2]'],
                 'median': ['//table[@id="data"]/tbody/tr/td[2]', '//table[@id="data"]/thead/tr/th[3]'],
                 '90line': ['//table[@id="data"]/tbody/tr/td[3]', '//table[@id="data"]/thead/tr/th[4]'],
                 'min': ['//table[@id="data"]/tbody/tr/td[4]', '//table[@id="data"]/thead/tr/th[5]'],
                 'max': ['//table[@id="data"]/tbody/tr/td[5]', '//table[@id="data"]/thead/tr/th[6]'],
                 'std': ['//table[@id="data"]/tbody/tr/td[6]', '//table[@id="data"]/thead/tr/th[7]'],
                 'throughput': ['//table[@id="data"]/tbody/tr/td[7]', '//table[@id="data"]/thead/tr/th[8]']}

        for k in paths:
            for path in paths[k]:
                tags = xml.xpath(path)
                for t in tags:
                    t.set('class', k)

        for t in xml.xpath('//table[@id="data"]/tbody/tr'):
            req_name = self._normalize_test_name(t[0].text)
            t.set('data-toggle', 'collapse')
            t.set('data-target', '#' + req_name)
            t.set('class', 'accordion-toggle')
            t.addnext(etree.XML('<tr>' +
                                '<td colspan="8" class="hiddenRow nohover">' +
                                '<div id="' + req_name + '" class="accordian-body collapse">' +

                                '<img src="plots/' + req_name + '_hist_prob_all.png"/>' +
                                '<img src="plots/' + req_name + '_hist_prob_90line.png"/>' +
                                '<img src="plots/' + req_name + '_requests.png"/>' +
                                '<img src="plots/' + req_name + '_percentiles.png"/>' +

                                '</div>' +
                                '</td>' +
                                '</tr>'))

        return etree.tostring(xml)

    def _generate_plots(self, report_name):
        """

        :param report_name:
        """
        font = {'size': '8'}
        #'family' : 'monospace',
        #'weight' : 'bold',
        rc('font', **font)
        style.use('ggplot')

        #if self.perfmon:
        #     for (name, param) in self.perfmon.items():
        #         with pandas.plot_params.use('x_compat', True):
        #             plt.figure(figsize=(12, 8), dpi=150)
        #
        #             fig, host = plt.subplots()
        #             #axes = [host] + [host.twinx() for i in xrange(0, len(param['input']) - 1)]
        #             axes = [host, host]
        #
        #             for i in xrange(0, len(param['input'])):
        #                 input_file = param['input'].keys()[i]
        #                 input_param = param['input'][input_file]
        #                 ax = axes[i]
        #                 df = pandas.read_csv(input_file)
        #
        #                 if 'real-date' in input_param:
        #                     df['timeStamp'] = df['timeStamp'].apply(lambda x: datetime.datetime.fromtimestamp(int(str(x)[:-3])).strftime('%Y-%m-%d %H:%M:%S'))
        #                 else:
        #                     start_time = datetime.datetime.fromtimestamp(int(str(df['timeStamp'][0])[:-3]))
        #                     df['timeStamp'] = df['timeStamp'].apply(lambda x: str(datetime.datetime.fromtimestamp(int(str(x)[:-3])) - start_time))
        #
        #                 if 'group-by' in input_param:
        #                     grp = df.groupby(input_param['group-by'])
        #
        #                     for g in grp:
        #                         if g[0] in input_param['groups']:
        #                             for column_name, column_param in input_param['columns'].items():
        #                                 if not 'as_is' in column_param or not column_param['as_is']:
        #                                     g[1][column_name] = g[1][column_name].apply(lambda x: float(x) / 1000)
        #
        #                                 c = g[1].set_index('timeStamp').unstack()[column_name]
        #                                 c.plot(label=g[0], ax=ax)
        #
        #                 else:
        #                     for column in input_param['columns']:
        #                         c = df.set_index('timeStamp').unstack()[column]
        #                         #c.plot(label=column, ax=ax)
        #
        #             #ax1 = plt.subplot(111)
        #             # box = host.get_position()
        #             # host.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        #             # host.legend(axes, loc='center left', bbox_to_anchor=(1, 0.5))
        #
        #             plt.xticks(rotation=70)
        #             plt.xlabel('')
        #             plt.ylabel('Metrics')
        #
        #             plt.tight_layout(rect=[0.02, 0, 0.8, 1])
        #             plt.savefig('test.png')
        #             plt.close()
        #
        # exit(0)

        # i = 1
        # for df in self.perfmon:
        #     grp = df.groupby('label')
        #     plt.figure(figsize=(12, 8), dpi=150)
        #     ax = plt.subplot(111)
        #
        #     for g in grp:
        #         elapsed = g[1].set_index('timeStamp').unstack()['elapsed']
        #         elapsed.plot(label=g[0])
        #
        #     font_prop = FontProperties()
        #     font_prop.set_size('small')
        #
        #     box = ax.get_position()
        #     ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        #     ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), prop=font_prop)
        #
        #     plt.xticks(rotation=70)
        #     for tick in ax.xaxis.get_major_ticks():
        #         tick.label.set_fontsize(10)
        #     plt.xlabel('')
        #     plt.ylabel('Metrics')
        #
        #     plt.tight_layout(rect=[0.02, -0.02, 0.8, 1])
        #     plt.savefig('results/' + report_name + '/plots/perfmon{0}.png'.format(i))
        #     i += 1
        #     plt.close()

        l = self.df['Latency']
        from scipy.stats import gaussian_kde

        plt.figure(figsize=(8, 5), dpi=150)
        l.hist(normed=True, alpha=0.2)
        l.plot(kind='kde')
        plt.fill(color='0.8')

        #density = gaussian_kde(l)
        #plt.plot(density)
        #plt.fill(l.index, density(l.index), alpha=.5, zorder=5, antialiased=True, color="#E01B6A")
        #plt.fill()
        plt.xlabel('Response time', fontsize=9)
        plt.ylabel('Probability', fontsize=9)
        plt.title('Histogram of all response time', fontsize=10)
        plt.tick_params(axis='both', which='major', labelsize=8)
        plt.tick_params(axis='both', which='minor', labelsize=6)
        plt.tight_layout()
        plt.savefig('results/' + report_name + '/plots/hist_prob_all.png')
        plt.close()

        plt.figure(figsize=(8, 5), dpi=150)
        l[l < np.percentile(l, 90)].hist(normed=True, alpha=0.2)
        l[l < np.percentile(l, 90)].plot(kind='kde')
        plt.xlabel('Response time', fontsize=9)
        plt.ylabel('Probability', fontsize=9)
        plt.title('Histogram of 90% line response time', fontsize=10)
        plt.tick_params(axis='both', which='major', labelsize=8)
        plt.tick_params(axis='both', which='minor', labelsize=6)
        plt.tight_layout()
        plt.savefig('results/' + report_name + '/plots/hist_prob_line90.png')
        plt.close()

        # percentile plot
        d = np.sort(l).cumsum()
        p = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        perc = mlab.prctile(d, p=p)
        plt.figure(figsize=(8, 5), dpi=150)
        plt.plot(d)
        plt.plot((len(d) - 1) * p / 100., perc, 'r.')
        plt.xticks((len(d) - 1) * p / 100., map(str, p))
        plt.xlabel('Percentile', fontsize=9)
        plt.ylabel('Response time', fontsize=9)
        plt.title('Percentiles', fontsize=10)
        plt.tick_params(axis='both', which='major', labelsize=8)
        plt.tick_params(axis='both', which='minor', labelsize=6)
        plt.tight_layout()
        plt.savefig('results/' + report_name + '/plots/percentiles.png')
        plt.close()

        for label, data in self._group_by_operation:
            file_name = self._normalize_test_name(label)
            d = data['Latency']

            # histogram of all response time
            plt.figure(figsize=(6, 4))
            d.hist(normed=True, alpha=0.2)
            try:
                d.plot(kind='kde')
            except np.linalg.linalg.LinAlgError:
                pass
                # if singular matrix - no plot
            except:
                raise
            plt.xlabel('Response time', fontsize=9)
            plt.ylabel('Probability', fontsize=9)
            plt.title('Histogram of all response time', fontsize=10)
            plt.tick_params(axis='both', which='major', labelsize=8)
            plt.tick_params(axis='both', which='minor', labelsize=6)
            plt.tight_layout()
            plt.savefig('results/' + report_name + '/plots/' + file_name + '_hist_prob_all.png')
            plt.close()

            # histogram of 90% line response time
            plt.figure(figsize=(6, 4), dpi=150)
            d[d < np.percentile(d, 90)].hist(normed=True, alpha=0.2)
            try:
                d[d < np.percentile(d, 90)].plot(kind='kde')
            except np.linalg.linalg.LinAlgError:
                pass
                # if singular matrix - no plot
            except:
                raise
            plt.xlabel('Response time', fontsize=9)
            plt.ylabel('Probability', fontsize=9)
            plt.title('Histogram of 90% line response time', fontsize=10)
            plt.tick_params(axis='both', which='major', labelsize=8)
            plt.tick_params(axis='both', which='minor', labelsize=6)
            plt.tight_layout()
            plt.savefig('results/' + report_name + '/plots/' + file_name + '_hist_prob_90line.png')
            plt.close()

            # scatterplot
            plt.figure(figsize=(6, 4), dpi=150)
            a = data['Latency']
            plt.plot(range(1, len(a) + 1), a, 'ro', color='g', alpha=0.50)
            plt.xlabel('Request', fontsize=9)
            plt.ylabel('Response time', fontsize=9)
            plt.title('Requests times', fontsize=10)
            plt.tick_params(axis='both', which='major', labelsize=8)
            plt.tick_params(axis='both', which='minor', labelsize=6)
            plt.tight_layout()
            plt.savefig('results/' + report_name + '/plots/' + file_name + '_requests.png')
            plt.close()

            # percentile plot
            pd = np.sort(d).cumsum()
            p = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
            perc = mlab.prctile(pd, p=p)
            plt.figure(figsize=(6, 4), dpi=150)
            plt.plot(pd)
            plt.plot((len(pd) - 1) * p / 100., perc, 'r.')
            plt.xticks((len(pd) - 1) * p / 100., map(str, p))
            plt.xlabel('Percentile', fontsize=9)
            plt.ylabel('Response time', fontsize=9)
            plt.title('Percentiles', fontsize=10)
            plt.tick_params(axis='both', which='major', labelsize=8)
            plt.tick_params(axis='both', which='minor', labelsize=6)
            plt.tight_layout()
            plt.savefig('results/' + report_name + '/plots/' + file_name + '_percentiles.png')
            plt.close()