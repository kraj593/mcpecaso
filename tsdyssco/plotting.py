import sys
import colorlover as cl
from plotly import tools
import plotly.graph_objs as go
import warnings
import numpy as np
from tsdyssco.core.TSDyssco import TSDyssco
import plotly.plotly as py

try:
    _ = __IPYTHON__
except NameError:
    from plotly.offline import plot
else:
    if 'ipykernel' in sys.modules:
        from plotly.offline import init_notebook_mode
        from plotly.offline import iplot as plot
        from IPython.display import HTML
        HTML("""
             <script>
              var waitForPlotly = setInterval( function() {
              if( typeof(window.Plotly) !== "undefined" ){
              MathJax.Hub.Config({ SVG: { font: "STIX-Web" }, displayAlign: "center" });
              MathJax.Hub.Queue(["setRenderer", MathJax.Hub, "SVG"]);
              clearInterval(waitForPlotly);}}, 250 );
            </script>
            """)
        init_notebook_mode(connected=True)
    elif 'IPython' in sys.modules:
        from plotly.offline import plot
    else:
        warnings.warn('Unknown ipython configuration')
        from plotly.offline import plot

go = go
tools = tools
cl = cl
plot = plot


def get_colors(number_of_colors, colors=None, cl_scales=['9', 'qual', 'Set1']):
    if colors is None:
        color_scale = cl.scales[cl_scales[0]][cl_scales[1]][cl_scales[2]]
        # https://plot.ly/ipython-notebooks/color-scales/
        if number_of_colors > int(cl_scales[0]):
            print('interpolated')
            # num_pts = len(replicate_trials)
            colors = cl.interp(color_scale, 500)
            # Index the list
            # Index the list
            colors = [colors[int(x)] for x in np.arange(0, 500,
                                                        round(500 / number_of_colors))]
        else:
            colors = color_scale
    return colors


def titlemaker(title):
    list_of_words = title.split()
    linetracker = ''
    new_title = ''
    for word in list_of_words:
        if len(linetracker+word) < 20:
            new_title += word + ' '
            linetracker += word + ' '
        else:
            new_title = new_title.rstrip()
            new_title += '<br>' + word + ' '
            linetracker = word
    new_title = new_title.rstrip()
    return new_title
        

def multiplot_envelopes(dyssco_list):

    if sum([type(dyssco) == TSDyssco for dyssco in dyssco_list]) == len(dyssco_list):
        num_of_conditions = len(dyssco_list)

        if num_of_conditions > 4:
            warnings.warn("You are trying to plot more than 4 conditions on the same plot. This function can handle a "
                          "maximum of 4 conditions. Please retry with a list of 4 dyssco objects.")
            return 0

        condition_list = [dyssco.condition for dyssco in dyssco_list]

        if len(set(condition_list)) != len(condition_list):
            warnings.warn("You have duplicate conditions in your list of dyssco objects. Please ensure that the "
                          "conditions are unique in the list of dyssco objects and try again.")
            return 0

        envelope_check_list = [dyssco.production_envelope is None for dyssco in dyssco_list]

        if any(envelope_check_list):
            warnings.warn("One or more of the dyssco objects do not have a production envelope. Please ensure"
                          "that all your dyssco models are complete and that they have production envelopes.")
            return 0

        envelope_dict = {condition: dyssco.production_envelope
                         for condition, dyssco in zip(condition_list, dyssco_list)}
        colors = get_colors(len(condition_list))

        fig = tools.make_subplots(rows=3, cols=num_of_conditions,
                                  subplot_titles=[titlemaker(condition) for condition in condition_list],
                                  vertical_spacing=0.05)
        max_growth = 0
        max_uptake = 0
        max_flux = 0
        max_yield = 0

        for col, condition in enumerate(envelope_dict):

            fig.append_trace(go.Scatter(x=envelope_dict[condition]['growth_rates'],
                                        y=envelope_dict[condition]['substrate_uptake_rates'],
                                        line={'color': colors[col]}, name='Glucose Uptake Rate',
                                        mode='lines'), 1, col+1)
            fig.append_trace(go.Scatter(x=list(reversed(envelope_dict[condition]['growth_rates']))
                                        + list(envelope_dict[condition]['growth_rates']),
                                        y=list(reversed(envelope_dict[condition]['production_rates_lb']))
                                        + list(envelope_dict[condition]['production_rates_ub']),
                                        line={'color': colors[col]}, name='Product Flux',
                                        mode='lines'), 2, col+1)
            fig.append_trace(go.Scatter(x=list(reversed(list(envelope_dict[condition]['growth_rates'])))
                                        + list(envelope_dict[condition]['growth_rates']),
                                        y=list(reversed(list(envelope_dict[condition]['yield_lb'])))
                                        + list(envelope_dict[condition]['yield_ub']),
                                        line={'color': colors[col]}, name='Product Yield',
                                        mode='lines'), 3, col+1)

            max_growth = max(max(envelope_dict[condition]['growth_rates']), max_growth)
            max_uptake = max(max(envelope_dict[condition]['substrate_uptake_rates']), max_uptake)
            max_flux = max(max(envelope_dict[condition]['production_rates_ub']), max_flux)
            max_yield = max(max(envelope_dict[condition]['yield_ub']), max_yield)

        for row in range(3):
            for col in range(num_of_conditions):
                fig['layout']['xaxis'+str(row*num_of_conditions+col+1)]['ticks'] = 'outside'
                fig['layout']['yaxis'+str(row*num_of_conditions+col+1)]['ticks'] = 'outside'

                if row == 0:
                    fig['layout']['yaxis' + str(row + num_of_conditions)]['title'] = 'Substrate Uptake (mmol/gdw.h)'
                    fig['layout']['xaxis'+str(row*num_of_conditions+col+1)]['title'] = 'Growth Rate (1/h)'
                    fig['layout']['yaxis'+str(row*num_of_conditions+col+1)]['range'] = [0, 1.2*max_uptake]

                if row == 1:
                    fig['layout']['yaxis' + str(row + num_of_conditions)]['title'] = 'Product Flux (mmol/gdw.h)'
                    fig['layout']['xaxis'+str(row*num_of_conditions+col+1)]['title'] = 'Growth Rate (1/h)'
                    fig['layout']['yaxis'+str(row*num_of_conditions+col+1)]['range'] = [0, 1.2*max_flux]

                if row == 2:
                    fig['layout']['yaxis' + str(row + num_of_conditions)]['title'] = 'Product Yield<br>' \
                                                                                     '(mmol/mmol substrate)'
                    fig['layout']['xaxis'+str(row*num_of_conditions+col+1)]['title'] = 'Growth Rate (1/h)'
                    fig['layout']['yaxis'+str(row*num_of_conditions+col+1)]['range'] = [0, 1.2*max_yield]

        fig['layout']['showlegend'] = False
        fig['layout']['title'] = 'Production Characteristics'
        fig['layout']['height'] = 1000
        fig['layout']['width'] = 1000
        plot(fig)

        fig = tools.make_subplots(rows=1, cols=3, subplot_titles=
                                  ['Substrate Uptake Rate', 'Product Flux', 'Product Yield'])

        for i, condition in enumerate(envelope_dict):
            fig.append_trace(go.Scatter(x=list(envelope_dict[condition]['growth_rates']),
                                        y=list(envelope_dict[condition]['substrate_uptake_rates']),
                                        line={'color': colors[i]}, name=condition,
                                        mode='lines', legendgroup=condition), 1, 1)
            fig.append_trace(go.Scatter(x=list(reversed(envelope_dict[condition]['growth_rates']))
                                        + list(envelope_dict[condition]['growth_rates']),
                                        y=list(reversed(envelope_dict[condition]['production_rates_lb']))
                                        + list(envelope_dict[condition]['production_rates_ub']),
                                        line={'color': colors[i]},
                                        mode='lines', showlegend=False, legendgroup=condition, name=condition), 1, 2)
            fig.append_trace(go.Scatter(x=list(reversed(list(envelope_dict[condition]['growth_rates'])))
                                        + list(envelope_dict[condition]['growth_rates']),
                                        y=list(reversed(list(envelope_dict[condition]['yield_lb'])))
                                        + list(envelope_dict[condition]['yield_ub']),
                                        line={'color': colors[i]},
                                        mode='lines', showlegend=False, legendgroup=condition, name=condition), 1, 3)

        for col in range(3):
            fig['layout']['xaxis'+str(col+1)]['ticks'] = 'outside'
            fig['layout']['yaxis']['range'] = [0, 1.2*max_uptake]
            fig['layout']['yaxis'+str(col+1)]['ticks'] = 'outside'
            fig['layout']['xaxis'+str(col+1)]['title'] = 'Growth Rate (1/h)'
        fig['layout']['yaxis1']['title'] = 'Substrate Uptake<br>(mmol/gdw.h)'
        fig['layout']['yaxis2']['title'] = 'Product Flux<br>(mmol/gdw.h)'
        fig['layout']['yaxis3']['title'] = 'Product Yield<br>(mmol/mmol substrate)'
        fig['layout']['legend']['orientation'] = 'h'
        fig['layout']['legend']['x'] = 0
        fig['layout']['legend']['y'] = -0.25
        fig['layout']['showlegend'] = True
        fig['layout']['title'] = 'Production Characteristics'
        fig['layout']['height'] = 500
        fig['layout']['width'] = 1000
        plot(fig)

    else:
        warnings.warn('The given object is not a tsdyssco object.')


def plot_envelope(dyssco):
    display(TSDyssco)
    if type(dyssco) == TSDyssco:
        envelope = dyssco.production_envelope
        if envelope is not None:
            target_metabolite = list(dyssco.target_rxn.metabolites.keys())[0].name
            k_m = dyssco.k_m
            fig = tools.make_subplots(rows=1, cols=3, subplot_titles=['Substrate Uptake Rate', 'Product Flux', 'Product Yield'],
                                      horizontal_spacing=0.1)
            colors = get_colors(1)
            fig.append_trace(go.Scatter(x=envelope['growth_rates'],
                                        y=envelope['substrate_uptake_rates'],
                                        line={'color': colors[0]},
                                        mode='lines'), 1, 1)

            fig.append_trace(go.Scatter(x=list(reversed(envelope['growth_rates']))
                                        + list(envelope['growth_rates']),
                                        y=list(reversed(envelope['production_rates_lb']))
                                        + list(envelope['production_rates_ub']),
                                        line={'color': colors[0]},
                                        mode='lines', showlegend=False), 1, 2)

            fig.append_trace(go.Scatter(x=list(reversed(envelope['growth_rates']))
                                        + list(envelope['growth_rates']),
                                        y=list(reversed(envelope['yield_lb']))
                                        + list(envelope['yield_ub']),
                                        line={'color': colors[0]},
                                        mode='lines', showlegend=False), 1, 3)

            for col in range(3):
                fig['layout']['xaxis' + str(col + 1)]['ticks'] = 'outside'
                fig['layout']['xaxis' + str(col + 1)]['zeroline'] = True
                fig['layout']['yaxis' + str(col + 1)]['ticks'] = 'outside'
                fig['layout']['xaxis' + str(col + 1)]['title'] = 'Growth Rate (1/h)'
                fig['layout']['xaxis' + str(col + 1)]['range'] = [0, np.around(((max(envelope['growth_rates'])) + 0.05 - 0), 1)]
                fig['layout']['xaxis' + str(col + 1)]['dtick'] = np.around(((max(envelope['growth_rates'])) - 0) / 5, 2)
                fig['layout']['xaxis' + str(col + 1)]['tick0'] = 0

            fig['layout']['yaxis1']['title'] = 'Substrate Uptake<br>(mmol/gdw.h)'
            fig['layout']['yaxis2']['title'] = 'Product Flux<br>(mmol/gdw.h)'
            fig['layout']['yaxis3']['title'] = 'Product Yield<br>(mmol/mmol substrate)'
            fig['layout']['showlegend'] = False
            fig['layout']['title'] = str(target_metabolite) + ' production characteristics in ' + str(dyssco.model.id) \
                                     + ' with substrate uptake penalty: ' + str(k_m)
            fig['layout']['yaxis1']['range'] = [0,
                                                1.2 * max(envelope['substrate_uptake_rates'])]
            fig['layout']['yaxis2']['range'] = [min(envelope['production_rates_lb']),
                                                1.2 * max(envelope['production_rates_ub'])]
            fig['layout']['yaxis3']['range'] = [min(envelope['yield_lb']),
                                                1.2 * max(envelope['yield_ub'])]
            fig['layout']['height'] = 425
            fig['layout']['width'] = 950

            plot(fig)

        else:
            warnings.warn('The given dyssco model does not contain a production envelope.')

    else:
        warnings.warn('The given object is not a tsdyssco object.')
