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
                                                        int(np.floor(500 / number_of_colors)))]
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
        if num_of_conditions <= 7:
            fig['layout']['showlegend'] = True
        else:
            fig['layout']['showlegend'] = False
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
            if dyssco.objective_name not in ['productivity', 'yield', 'titer', 'dupont metric']:

                attribute_names = ['batch_productivity', 'batch_yield', 'batch_titer',
                                   'dupont_metric', 'objective_value']
                characteristics = ['productivity', 'yield', 'titer', 'dupont metric',
                                   'objective value']
            else:
                attribute_names = ['batch_productivity', 'batch_yield', 'batch_titer',
                                   'dupont_metric', 'linear_combination']
                characteristics = ['productivity', 'yield', 'titer', 'dupont metric',
                                   'objective value']

            units = ['(mmol/L.h)', '(mmol product/mmol substrate)', '(mmol/L)', '(a.u.)', '(a.u.)']
            titles = [str(target_metabolite) + ' ' + characteristic + " distribution for two stage fermentation in "
                      + str(dyssco.model.id) + '. Objective: ' + str(dyssco.objective_name)
                      for characteristic in characteristics]
            for row, characteristic in enumerate(characteristics):
                tracelist = list()
                tracelist.append(go.Scatter(x=np.linspace(0, max(dyssco.two_stage_characteristics
                                                                 ['stage_one_growth_rate']), 10),
                                            y=np.linspace(0, max(dyssco.two_stage_characteristics
                                                                 ['stage_two_growth_rate']), 10), mode='lines',
                                            name='One Stage Points',
                                            line={'color': 'rgb(255, 218, 68)', 'dash': 'dash'},
                                            showlegend=True))
                tracelist.append(go.Contour(z=dyssco.two_stage_characteristics[characteristic],
                                            x=dyssco.two_stage_characteristics['stage_one_growth_rate'],
                                            y=dyssco.two_stage_characteristics['stage_two_growth_rate'],
                                            hoverinfo='text',
                                            text=['Stage 1 growth rate: ' +
                                                  str(round(
                                                      dyssco.two_stage_characteristics['stage_one_growth_rate'][i],
                                                      3)) +
                                                  '<br>Stage 2 growth rate: ' +
                                                  str(round(
                                                      dyssco.two_stage_characteristics['stage_two_growth_rate'][i],
                                                      3)) +
                                                  '<br>' + characteristic.title() + ': ' +
                                                  str(round(dyssco.two_stage_characteristics[characteristic][i], 3))
                                                  for i in
                                                  range(len(dyssco.two_stage_characteristics[characteristic]))],
                                            showlegend=False,
                                            ncontours=20,
                                            contours=dict(coloring='heatmap', showlabels=True,
                                                          labelfont=dict(size=12, color='white')),
                                            colorbar=dict(title=characteristic.title() + '<br>' + units[row],
                                                          titleside='right',
                                                          titlefont=dict(size=14),
                                                          nticks=15,
                                                          ticks='outside',
                                                          tickfont=dict(size=12),
                                                          thickness=15,
                                                          showticklabels=True,
                                                          thicknessmode='pixels',
                                                          len=1.05,
                                                          lenmode='fraction',
                                                          outlinewidth=1)))
                tracelist.append(go.Scatter(x=[dyssco.two_stage_best_batch.stage_one_fluxes[0]],
                                            y=[dyssco.two_stage_best_batch.stage_two_fluxes[0]],
                                            mode='markers', hoverinfo='text', showlegend=True,
                                            name='Best Two Stage Point',
                                            text=['Best Two Stage Point<br>' + characteristic.title() + ': ' +
                                                  str(round(getattr(dyssco.two_stage_best_batch,
                                                                    attribute_names[row]), 3))],
                                            marker=dict(color='rgb(81, 206, 59)',
                                                        size=10)))
                tracelist.append(go.Scatter(x=[dyssco.one_stage_best_batch.fluxes[0]],
                                            y=[dyssco.one_stage_best_batch.fluxes[0]],
                                            name='Best One Stage Point',
                                            mode='markers', hoverinfo='text', showlegend=True,
                                            text=['Best One Stage Point<br>' + characteristic.title() + ': ' +
                                                  str(round(getattr(dyssco.one_stage_best_batch,
                                                                    attribute_names[row]), 3))],
                                            marker=dict(color='rgb(252, 217, 17)',
                                                        size=10)))
                tracelist.append(go.Scatter(x=[dyssco.two_stage_suboptimal_batch.stage_one_fluxes[0]],
                                            y=[dyssco.two_stage_suboptimal_batch.stage_two_fluxes[0]],
                                            name='Max Growth to Min Growth Point',
                                            mode='markers', hoverinfo='text', showlegend=True,
                                            text=['Max Growth to Min Growth Point<br>' +
                                                  characteristic.title() + ': ' +
                                                  str(round(getattr(dyssco.one_stage_best_batch,
                                                                    attribute_names[row]), 3))],
                                            marker=dict(color='rgb(255, 0, 0)',
                                                        size=10)))

                fig = go.Figure(data=tracelist)
                fig['layout']['xaxis']['range'] = [0, np.around(((max(dyssco.two_stage_characteristics
                                                                      ['stage_one_growth_rate']))+0.05), 1)]
                fig['layout']['xaxis']['dtick'] = np.around((max(dyssco.two_stage_characteristics
                                                                 ['stage_one_growth_rate'])) / 5, 2)
                fig['layout']['yaxis']['range'] = [0, np.around(((max(dyssco.two_stage_characteristics
                                                                      ['stage_two_growth_rate']))+0.05), 1)]
                fig['layout']['yaxis']['dtick'] = np.around((max(dyssco.two_stage_characteristics
                                                                 ['stage_two_growth_rate'])) / 5, 2)
                fig['layout']['yaxis']['title'] = 'Stage 2 Growth Rate<br>(1/h)'
                fig['layout']['xaxis']['title'] = 'Stage 1 Growth Rate<br>(1/h)'
                fig['layout']['xaxis']['ticks'] = 'outside'
                fig['layout']['yaxis']['ticks'] = 'outside'
                fig['layout']['hovermode'] = 'closest'
                fig['layout']['height'] = 575
                fig['layout']['width'] = 500
                fig['layout']['showlegend'] = True
                fig['layout']['legend']['x'] = 0
                fig['layout']['legend']['y'] = -0.25
                fig['layout']['legend']['orientation'] = 'h'
                fig['layout']['title'] = titlemaker(titles[row], 50)

                plot(fig)
        else:
            warnings.warn('The given dyssco model does not contain two stage fermentations.')

    else:
        warnings.warn('The given object is not a tsdyssco object.')


def multi_two_stage_char_contours(dyssco_list):
    if sum([type(dyssco) == TSDyssco for dyssco in dyssco_list]) == len(dyssco_list):
        num_of_conditions = len(dyssco_list)
        condition_list = [dyssco.condition for dyssco in dyssco_list]
        if len(set(condition_list)) != len(condition_list):
            warnings.warn("You have duplicate conditions in your list of dyssco objects. Please ensure that the "
                          "conditions are unique in the list of dyssco objects and try again.")
            return

        ts_ferm_check_list = [len(dyssco.two_stage_fermentation_list) == 0 for dyssco in dyssco_list]

        if any(ts_ferm_check_list):
            warnings.warn("One or more of the dyssco objects do not have a production envelope. Please ensure"
                          "that all your dyssco models are complete and that they have production envelopes.")
            return

        ts_char_dict = {condition: dyssco.two_stage_characteristics
                        for condition, dyssco in zip(condition_list, dyssco_list)}
        max_stage_one_growth = max([max(ts_char['stage_one_growth_rate']) for ts_char in list(ts_char_dict.values())])
        max_stage_two_growth = max([max(ts_char['stage_two_growth_rate']) for ts_char in list(ts_char_dict.values())])

        if num_of_conditions <= 3:

            attribute_names = ['batch_productivity', 'batch_yield', 'batch_titer',
                               'dupont_metric', 'objective_value']
            characteristics = ['productivity', 'yield', 'titer', 'dupont metric',
                               'objective value']
            units = ['(mmol/L.h)', '(mmol product/mmol substrate)', '(mmol/L)', '(a.u.)', '(a.u.)']
            titles = [characteristic.title() + " distribution for two stage fermentation"
                      for characteristic in characteristics]

            for row, characteristic in enumerate(characteristics):
                max_characteristic = max(
                    [max(dyssco.two_stage_characteristics[characteristic]) for dyssco in dyssco_list])
                min_characteristic = min(
                    [min(dyssco.two_stage_characteristics[characteristic]) for dyssco in dyssco_list])
                fig = tools.make_subplots(rows=1, cols=len(dyssco_list),
                                          subplot_titles=[dyssco.condition for dyssco in dyssco_list],
                                          horizontal_spacing=0.05, print_grid=False)

                for col, dyssco in enumerate(dyssco_list):
                    fig.append_trace(go.Scatter(x=np.linspace(0, max(dyssco.two_stage_characteristics
                                                                     ['stage_one_growth_rate']), 10),
                                                y=np.linspace(0, max(dyssco.two_stage_characteristics
                                                                     ['stage_two_growth_rate']), 10), mode='lines',
                                                name='One Stage Points',
                                                line={'color': 'rgb(255, 218, 68)', 'dash': 'dash'},
                                                showlegend=True if col == len(dyssco_list)-1 else False,
                                                legendgroup='One Stage Points'), 1, col + 1)
                    fig.append_trace(go.Contour(z=dyssco.two_stage_characteristics[characteristic],
                                                x=dyssco.two_stage_characteristics['stage_one_growth_rate'],
                                                y=dyssco.two_stage_characteristics['stage_two_growth_rate'],
                                                showlegend=False, hoverinfo='text',
                                                text=['Stage 1 growth rate: ' +
                                                      str(dyssco.two_stage_characteristics['stage_one_growth_rate'][
                                                              i]) +
                                                      '<br>Stage 2 growth rate: ' +
                                                      str(dyssco.two_stage_characteristics['stage_two_growth_rate'][
                                                              i]) +
                                                      '<br>' + characteristic.title() + ': ' +
                                                      str(round(dyssco.two_stage_characteristics[characteristic][i], 3))
                                                      for i in
                                                      range(len(dyssco.two_stage_characteristics[characteristic]))],
                                                contours=dict(coloring='heatmap', showlabels=True,
                                                              labelfont=dict(size=12, color='white')),
                                                colorscale='RdBu',
                                                colorbar=dict(title=characteristic.title() + '<br>' + units[row],
                                                              titleside='right',
                                                              titlefont=dict(size=14),
                                                              nticks=10,
                                                              tick0=0,
                                                              ticks='outside',
                                                              tickfont=dict(size=12),
                                                              thickness=15,
                                                              showticklabels=True,
                                                              thicknessmode='pixels',
                                                              len=1.05,
                                                              lenmode='fraction',
                                                              outlinewidth=1),
                                                zmin=min_characteristic, zmax=max_characteristic, ncontours=20), 1,
                                     col + 1)
                    fig.append_trace(go.Scatter(x=[dyssco.one_stage_best_batch.fluxes[0]],
                                                y=[dyssco.one_stage_best_batch.fluxes[0]],
                                                name='Best One Stage Point',
                                                mode='markers', hoverinfo='text',
                                                showlegend=True if col == len(dyssco_list)-1 else False,
                                                text=['Best One Stage Point<br>' + characteristic.title() + ': ' +
                                                      str(round(getattr(dyssco.one_stage_best_batch,
                                                                        attribute_names[row]), 3))],
                                                marker=dict(color='rgb(252, 217, 17)',
                                                            size=10),
                                                legendgroup='Best One Stage Point'), 1, col+1)
                    fig.append_trace(go.Scatter(x=[dyssco.two_stage_suboptimal_batch.stage_one_fluxes[0]],
                                                y=[dyssco.two_stage_suboptimal_batch.stage_two_fluxes[0]],
                                                name='Max Growth to Min Growth Point',
                                                mode='markers', hoverinfo='text',
                                                showlegend=True if col == len(dyssco_list) - 1 else False,
                                                text=['Max Growth to Min Growth Point<br>' +
                                                      characteristic.title() + ': ' +
                                                      str(round(getattr(dyssco.one_stage_best_batch,
                                                                        attribute_names[row]), 3))],
                                                marker=dict(color='rgb(255, 0, 0)',
                                                            size=10),
                                                legendgroup='Max Growth to Min Growth Point'), 1, col + 1)
                    fig.append_trace(go.Scatter(x=[dyssco.two_stage_best_batch.stage_one_fluxes[0]],
                                                y=[dyssco.two_stage_best_batch.stage_two_fluxes[0]],
                                                mode='markers', hoverinfo='text',
                                                showlegend=True if col == len(dyssco_list) - 1 else False,
                                                name='Best Two Stage Point',
                                                text=['Best Two Stage Point<br>' + characteristic.title() + ': ' +
                                                      str(round(getattr(dyssco.two_stage_best_batch,
                                                                        attribute_names[row]), 3))],
                                                marker=dict(color='rgb(81, 206, 59)',
                                                            size=10),
                                                legendgroup='Best Two Stage Point'), 1, col + 1)

                    fig['layout']['xaxis'+str(col+1)]['range'] = [0, np.around((max_stage_one_growth + 0.05), 1)]
                    fig['layout']['xaxis'+str(col+1)]['dtick'] = np.around(max_stage_one_growth / 5, 2)
                    fig['layout']['yaxis'+str(col+1)]['range'] = [0, np.around((max_stage_two_growth + 0.05), 1)]
                    fig['layout']['yaxis'+str(col+1)]['dtick'] = np.around(max_stage_two_growth / 5, 2)

                    fig['layout']['yaxis1']['title'] = 'Stage 2<br>Growth Rate(1/h)'
                    fig['layout']['xaxis' + str(col + 1)]['title'] = 'Stage 1<br>Growth Rate(1/h)'
                    fig['layout']['xaxis' + str(col + 1)]['ticks'] = 'outside'
                    fig['layout']['yaxis' + str(col + 1)]['ticks'] = 'outside'
                fig['layout']['height'] = 490
                fig['layout']['width'] = 100 + len(dyssco_list) * 285
                fig['layout']['title'] = titlemaker(titles[row], 100)
                fig['layout']['hovermode'] = 'closest'
                fig['layout']['legend']['orientation'] = 'h'
                fig['layout']['legend']['x'] = 0
                fig['layout']['legend']['y'] = -0.45
                plot(fig)

        else:
            warnings.warn('There are too many dyssco objects in this list. This function can handle a maximum of 3'
                          ' objects')

    else:
        warnings.warn('One or more of the objects in this list are not Dyssco objects.')


def plot_dyssco_dfba(dyssco):

    if type(dyssco) == TSDyssco:
        ts_fermentations = dyssco.two_stage_fermentation_list

        if ts_fermentations:
            ts_suboptimal = dyssco.two_stage_suboptimal_batch
            os_best = dyssco.one_stage_best_batch
            ts_best = dyssco.two_stage_best_batch
            titles = ['Traditional Two Stage Batch', 'Best One Stage Batch', 'Best Two Stage Batch']
            ferm_list = [ts_suboptimal, os_best, ts_best]
            fig = tools.make_subplots(rows=1, cols=3, subplot_titles=[titlemaker(title, 25) for title in titles],
                                      print_grid=False)
            max_conc = max([(max([max(data) for data in ferm.data])) for ferm in ferm_list])
            max_t = max([max(ferm.time) for ferm in ferm_list])
            for col, ferm in enumerate(ferm_list):
                fig.append_trace(go.Scatter(x=ferm.time, y=ferm.data[0], name='Biomass Concentration',
                                            line={'color': '#8c564b'}, legendgroup='Biomass',
                                            showlegend=True if col == 2 else False, mode='lines'), 1, col+1)
                fig.append_trace(go.Scatter(x=ferm.time, y=ferm.data[1], name='Substrate Concentration',
                                            line={'color': '#1f77b4'}, legendgroup='Substrate',
                                            showlegend=True if col == 2 else False, mode='lines'), 1, col + 1)
                fig.append_trace(go.Scatter(x=ferm.time, y=ferm.data[2], name='Product Concentration',
                                            line={'color': '#e377c2'}, legendgroup='Product',
                                            showlegend=True if col == 2 else False, mode='lines'), 1, col + 1)
                if col != 1:
                    fig.append_trace(go.Scatter(x=[ferm.optimal_switch_time]*30,
                                                y=np.linspace(0, 0.8*max_conc, 30),
                                                name='Optimal Switch Time', mode='lines',
                                                line={'color': 'black',
                                                        'width': 3,
                                                        'dash': 'dot'},
                                                showlegend=True if col == 2 else False), 1, col+1)
                fig['layout']['xaxis'+str(col+1)]['range'] = [0, max_t]
                fig['layout']['yaxis'+str(col+1)]['range'] = [0, 1.2*max_conc]
                fig['layout']['annotations'] = list(fig['layout']['annotations']) + \
                                               [go.layout.Annotation
                                                (dict(x=max_t / 3,
                                                      y=1.05*max_conc,
                                                      xref='x'+str(col+1), yref='y'+str(col+1),
                                                      text='Productivity=' + str(round(ferm.batch_productivity, 3)) +
                                                      '<br>Yield=' + str(round(ferm.batch_yield, 3)) +
                                                      '<br>End Titer=' + str(round(ferm.batch_titer,3)),
                                                      showarrow=False,
                                                      ax=-0, ay=-0))]
                fig['layout']['xaxis'+str(col+1)]['title'] = 'Time (h)'

            target_metabolite = list(dyssco.target_rxn.metabolites.keys())[0].name
            fig['layout']['yaxis']['title'] = 'Concentration (mmol/L or g/L)'
            fig['layout']['xaxis']['ticks'] = 'outside'
            fig['layout']['yaxis']['ticks'] = 'outside'
            fig['layout']['hovermode'] = 'closest'
            fig['layout']['height'] = 500
            fig['layout']['width'] = 1000
            fig['layout']['showlegend'] = True
            fig['layout']['legend']['x'] = 0
            fig['layout']['legend']['y'] = -0.25
            fig['layout']['legend']['orientation'] = 'h'
            fig['layout']['title'] = 'Production Strategies for ' + target_metabolite + ' in ' + dyssco.model.id + \
                                     '. Objective: ' + dyssco.objective_name.title()
            plot(fig)
        else:
            warnings.warn('The given dyssco model does not contain two stage fermentations.')

    else:
        warnings.warn('The given object is not a tsdyssco object.')
