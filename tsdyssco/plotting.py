import sys
import colorlover as cl
from plotly import tools
import plotly.graph_objs as go
import warnings
import numpy as np
from tsdyssco.core.TSDyssco import TSDyssco

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
        if number_of_colors > int(cl_scales[0]):
            print('interpolated')
            colors = cl.interp(color_scale, 500)
            colors = [colors[int(x)] for x in np.arange(0, 500,
                                                        round(500 / number_of_colors))]
        else:
            colors = color_scale
    return colors


def titlemaker(title, line_length):
    list_of_words = title.split()
    linetracker = ''
    new_title = ''
    for word in list_of_words:
        if len(linetracker+word) < line_length:
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
        condition_list = [dyssco.condition for dyssco in dyssco_list]

        if len(set(condition_list)) != len(condition_list):
            warnings.warn("You have duplicate conditions in your list of dyssco objects. Please ensure that the "
                          "conditions are unique in the list of dyssco objects and try again.")
            return

        envelope_check_list = [dyssco.production_envelope is None for dyssco in dyssco_list]

        if any(envelope_check_list):
            warnings.warn("One or more of the dyssco objects do not have a production envelope. Please ensure"
                          "that all your dyssco models are complete and that they have production envelopes.")
            return

        envelope_dict = {condition: dyssco.production_envelope
                         for condition, dyssco in zip(condition_list, dyssco_list)}
        colors = get_colors(len(condition_list))
        max_growth = max([max(envelope['growth_rates']) for envelope in list(envelope_dict.values())])
        max_uptake = max([max(envelope['substrate_uptake_rates']) for envelope in list(envelope_dict.values())])
        max_flux = max([max(envelope['production_rates_ub']) for envelope in list(envelope_dict.values())])
        max_yield = max([max(envelope['yield_ub']) for envelope in list(envelope_dict.values())])

        if num_of_conditions <= 4:
            fig = tools.make_subplots(rows=3, cols=num_of_conditions,
                                      subplot_titles=[titlemaker(condition, 20) for condition in condition_list],
                                      vertical_spacing=0.1, print_grid=False)

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
            for row in range(3):
                for col in range(num_of_conditions):
                    fig['layout']['xaxis'+str(row*num_of_conditions+col+1)]['ticks'] = 'outside'
                    fig['layout']['yaxis'+str(row*num_of_conditions+col+1)]['ticks'] = 'outside'
                    fig['layout']['xaxis' + str(row*num_of_conditions+col+1)]['range'] = [0, np.around((max_growth +
                                                                                          0.05), 1)]
                    fig['layout']['xaxis' + str(row*num_of_conditions+col+1)]['dtick'] = np.around(max_growth / 5, 2)

                    if row == 0:
                        fig['layout']['yaxis' + str(row*num_of_conditions+1)]['title'] = 'Substrate Uptake<br>' \
                                                                                         '(mmol/gdw.h)'
                        fig['layout']['xaxis'+str(row*num_of_conditions+col+1)]['title'] = 'Growth Rate (1/h)'
                        fig['layout']['yaxis'+str(row*num_of_conditions+col+1)]['range'] = [0, 1.2*max_uptake]

                    if row == 1:
                        fig['layout']['yaxis' + str(row*num_of_conditions+1)]['title'] = 'Product Flux<br>' \
                                                                                         '(mmol/gdw.h)'
                        fig['layout']['xaxis'+str(row*num_of_conditions+col+1)]['title'] = 'Growth Rate (1/h)'
                        fig['layout']['yaxis'+str(row*num_of_conditions+col+1)]['range'] = [0, 1.2*max_flux]

                    if row == 2:
                        fig['layout']['yaxis' + str(row*num_of_conditions+1)]['title'] = 'Product Yield<br>' \
                                                                                         '(mmol/mmol substrate)'
                        fig['layout']['xaxis'+str(row*num_of_conditions+col+1)]['title'] = 'Growth Rate (1/h)'
                        fig['layout']['yaxis'+str(row*num_of_conditions+col+1)]['range'] = [0, 1.2*max_yield]

            fig['layout']['showlegend'] = False
            fig['layout']['title'] = 'Production Characteristics'
            fig['layout']['height'] = 850
            fig['layout']['width'] = 150 + num_of_conditions * 200
            plot(fig)

        else:
            warnings.warn("You are trying to plot more than 4 conditions. All conditions can only be plotted on the"
                          " same graph for each item.")

        fig = tools.make_subplots(rows=1, cols=3, subplot_titles=
                                  ['Substrate Uptake Rate', 'Product Flux', 'Product Yield'],
                                  print_grid=False, horizontal_spacing=0.1)

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
            fig['layout']['yaxis'+str(col+1)]['ticks'] = 'outside'
            fig['layout']['xaxis'+str(col+1)]['title'] = 'Growth Rate (1/h)'
            fig['layout']['xaxis' + str(col+1)]['range'] = [0, np.around((max_growth + 0.05), 1)]
            fig['layout']['xaxis' + str(col+1)]['dtick'] = np.around(max_growth / 5, 2)
        fig['layout']['yaxis1']['range'] = [0, 1.2 * max_uptake]
        fig['layout']['yaxis2']['range'] = [0, 1.2 * max_flux]
        fig['layout']['yaxis3']['range'] = [0, 1.2 * max_yield]
        fig['layout']['yaxis1']['title'] = 'Substrate Uptake<br>(mmol/gdw.h)'
        fig['layout']['yaxis2']['title'] = 'Product Flux<br>(mmol/gdw.h)'
        fig['layout']['yaxis3']['title'] = 'Product Yield<br>(mmol/mmol substrate)'
        fig['layout']['legend']['orientation'] = 'h'
        fig['layout']['legend']['x'] = 0
        fig['layout']['legend']['y'] = -0.25
        fig['layout']['showlegend'] = True
        fig['layout']['title'] = 'Production Characteristics'
        fig['layout']['width'] = 950
        fig['layout']['height'] = 425
        plot(fig)

    else:
        warnings.warn('The given object is not a tsdyssco object.')


def plot_envelope(dyssco):
    if type(dyssco) == TSDyssco:
        envelope = dyssco.production_envelope
        if envelope is not None:
            target_metabolite = list(dyssco.target_rxn.metabolites.keys())[0].name
            k_m = dyssco.k_m
            fig = tools.make_subplots(rows=1, cols=3, subplot_titles=['Substrate Uptake Rate', 'Product Flux',
                                                                      'Product Yield'],
                                      horizontal_spacing=0.1, print_grid=False)
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
                fig['layout']['xaxis' + str(col + 1)]['range'] = [0, np.around(((max(envelope['growth_rates'])) +
                                                                                0.05), 1)]
                fig['layout']['xaxis' + str(col + 1)]['dtick'] = np.around((max(envelope['growth_rates'])) / 5, 2)
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


def two_stage_char_contour(dyssco):
    if type(dyssco) == TSDyssco:
        ts_fermentations = dyssco.two_stage_fermentation_list

        if ts_fermentations:
            target_metabolite = list(dyssco.target_rxn.metabolites.keys())[0].name
            characteristics = ['productivity', 'yield', 'titer', 'dupont metric', 'objective value']
            units = ['mmol/L.h', 'mmol product/mmol substrate', 'mmol/L', 'a.u.', 'a.u.']
            titles = [str(target_metabolite) + ' ' + characteristic + " distribution for two stage fermentations in "
                      + str(dyssco.model.id) for characteristic in characteristics]
            for row, characteristic in enumerate(characteristics):
                trace = go.Contour(z=dyssco.two_stage_characteristics[characteristic],
                                   x=dyssco.two_stage_characteristics['stage_one_growth_rate'],
                                   y=dyssco.two_stage_characteristics['stage_two_growth_rate'],
                                   contours=dict(coloring='heatmap', showlabels=True,
                                                 labelfont=dict(size=10, color='white')),
                                   colorbar=dict(title=characteristic + '<br>' + units[row],
                                                 titleside='right',
                                                 titlefont=dict(size=14),
                                                 nticks=15,
                                                 ticks='outside',
                                                 tickfont=dict(size=10),
                                                 thickness=20,
                                                 showticklabels=True,
                                                 thicknessmode='pixels',
                                                 len=1.05,
                                                 lenmode='fraction',
                                                 outlinewidth=1))
                fig = go.Figure(data=[trace])
                fig['layout']['yaxis']['title'] = 'Stage 2<br>Growth Rate(1/h)'
                fig['layout']['xaxis']['title'] = 'Stage 1<br>Growth Rate(1/h)'
                fig['layout']['xaxis']['ticks'] = 'outside'
                fig['layout']['yaxis']['ticks'] = 'outside'
                fig['layout']['height'] = 600
                fig['layout']['width'] = 600
                for item in fig['layout']['annotations']:
                    item['font'] = dict(size=14)
                fig['layout']['showlegend'] = True
                fig['layout']['title'] = titlemaker(titles[row], 50)

                plot(fig)
        else:
            warnings.warn('The given dyssco model does not contain two stage fermentations.')

    else:
        warnings.warn('The given object is not a tsdyssco object.')


def multi_two_stage_char_contours(dyssco_list):
    if sum([type(dyssco) == TSDyssco for dyssco in dyssco_list]) == len(dyssco_list):
        ts_fermentations = dyssco.two_stage_fermentation_list

        if ts_fermentations:
            target_metabolite = list(dyssco.target_rxn.metabolites.keys())[0].name
            characteristics = ['productivity', 'yield', 'titer', 'dupont metric', 'objective value']
            units = ['mmol/L.h', 'mmol product/mmol substrate', 'mmol/L', 'a.u.', 'a.u.']
            titles = [str(target_metabolite) + ' ' + characteristic + " distribution for two stage fermentations in "
                      + str(dyssco.model.id) for characteristic in characteristics]
            for row, characteristic in enumerate(characteristics):
                max_characteristic = max(
                    [max(dyssco.two_stage_characteristics[characteristic]) for dyssco in dyssco_list])
                min_characteristic = min(
                    [min(dyssco.two_stage_characteristics[characteristic]) for dyssco in dyssco_list])
                fig = tools.make_subplots(rows=1, cols=len(dyssco_list),
                                          subplot_titles=[dyssco.condition for dyssco in dyssco_list],
                                          horizontal_spacing=0.07, print_grid=False)
                for col, dyssco in enumerate(dyssco_list):
                    fig.append_trace(go.Contour(z=dyssco.two_stage_characteristics[characteristic],
                                                x=dyssco.two_stage_characteristics['stage_one_growth_rate'],
                                                y=dyssco.two_stage_characteristics['stage_two_growth_rate'],
                                                contours=dict(coloring='heatmap', showlabels=True,
                                                              labelfont=dict(size=10, color='white')),
                                                colorscale='RdBu',
                                                colorbar=dict(title=characteristic + '<br>' + units[row],
                                                              titleside='right',
                                                              titlefont=dict(size=14),
                                                              nticks=10,
                                                              tick0=0,
                                                              ticks='outside',
                                                              tickfont=dict(size=10),
                                                              thickness=20,
                                                              showticklabels=True,
                                                              thicknessmode='pixels',
                                                              len=1.05,
                                                              lenmode='fraction',
                                                              outlinewidth=1),
                                                zmin=min_characteristic, zmax=max_characteristic, ncontours=20), 1,
                                     col + 1)

                    fig['layout']['yaxis1']['title'] = 'Stage 2<br>Growth Rate(1/h)'
                    fig['layout']['xaxis' + str(col + 1)]['title'] = 'Stage 1<br>Growth Rate(1/h)'
                    fig['layout']['xaxis' + str(col + 1)]['ticks'] = 'outside'
                    fig['layout']['yaxis' + str(col + 1)]['ticks'] = 'outside'
                fig['layout']['height'] = 425
                fig['layout']['width'] = 100 + len(dyssco_list) * 300
                # for item in fig['layout']['annotations']:
                #    item['font'] = dict(size=14)
                # fig['layout']['showlegend'] = True
                fig['layout']['title'] = titlemaker(titles[row], 50)

                plot(fig)

        else:
            warnings.warn('The given dyssco model does not contain two stage fermentations.')

    else:
        warnings.warn('The given object is not a tsdyssco object.')
