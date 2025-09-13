# Used to plot Waffles' waveforms (to me, used in saturation jupyter notebooks)
# I just write the man functions used to create the plots, including the one that I modified to get the colorbars.


'''
plot_detectors
----- PATH -----> src/waffles/np02_plotting/PlotUtils.py
'''

def plot_detectors(wfset: WaveformSet, detector:list, plot_function: Optional[Callable] = None, **kwargs):
    for title, g in np02_gen_grids(wfset, detector, rows=kwargs.pop("rows", 0), cols=kwargs.pop("cols", 0)).items():
        # Keeping standard plotting 
        if title == "nTCO" or title == "TCO":
            if "shared_xaxes" not in kwargs:
                kwargs["shared_xaxes"] = True
            if "shared_yaxes" not in kwargs:
                kwargs["shared_yaxes"] = True

        plot_grid(chgrid=g, title=title, html=kwargs.pop("html", None), detector=detector, plot_function=plot_function, **kwargs)


'''
plot_grid
----- PATH -----> src/waffles/np02_plotting/PlotUtils.py
'''

def plot_grid(chgrid: ChannelWsGrid, title:str = "", html: Union[Path, None] = None, detector: Union[str, List[str]] = "", plot_function: Optional[Callable] = None, **kwargs):

    rows, cols= chgrid.ch_map.rows, chgrid.ch_map.columns

    showplots = kwargs.pop("showplots", False)

    subtitles = chgrid.titles

    fig = psu.make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=subtitles,
        shared_xaxes=kwargs.pop("shared_xaxes", False),
        shared_yaxes=kwargs.pop("shared_yaxes", False)
    )

    width = kwargs.pop("width", 1000)
    height = kwargs.pop("height", 800)
    if plot_function is None:
        plot_ChannelWsGrid(chgrid,
                           figure=fig,
                           share_x_scale=kwargs.pop("share_x_scale", True),
                           share_y_scale=kwargs.pop("share_y_scale", True),
                           mode=kwargs.pop("mode", "overlay"),
                           wfs_per_axes=kwargs.pop("wfs_per_axes", 2000),
                           **kwargs
                           )
    else:
        plot_CustomChannelGrid(chgrid, plot_function, figure=fig, wf_func=kwargs.pop("wf_func", None), **kwargs)

    title = title if title != "Custom" else ""
    fig.update_layout(title=title, template="plotly_white",
                      width=width, height=height, showlegend=True)
    fig.update_annotations(
        font=dict(size=14),
        align="center",
    )
    if html:
        fig.write_html(html.as_posix())
        logging.info("💾 %s", html)
        if showplots:
            fig.show()
    else:
        fig.show()


'''
plot_CustomChannelGrid
----- PATH -----> src/waffles/plotting/plot.py
'''

def plot_CustomChannelGrid(
    channel_ws_grid: ChannelWsGrid,  
    plot_function: Callable, 
    figure: Optional[pgo.Figure] = None,  
    share_x_scale: bool = False,  
    share_y_scale: bool = False,  
    wfs_per_axes: Optional[int] = 1,  
    x_axis_title: Optional[str] = None,  
    y_axis_title: Optional[str] = None,  
    figure_title: Optional[str] = None,  
    show_ticks_only_on_edges: bool = False,  
    wf_func: Optional[Callable] = None,
    log_x_axis: bool = False,
    yannotation: Optional[float] = 1.25
) -> pgo.Figure:
    """
    This function returns a plotly.graph_objects.Figure with a grid of subplots arranged according to the 
    channel_ws_grid.ch_map attribute.

    Parameters:
    - channel_ws_grid (ChannelWsGrid): A grid containing waveform sets and channels.
    - plot_function (Callable): The function used to plot the waveforms.
    - figure (Optional[pgo.Figure]): An optional existing Plotly figure to add subplots to.
    - share_x_scale (bool): Whether to share the X-axis scale across subplots.
    - share_y_scale (bool): Whether to share the Y-axis scale across subplots.
    - wfs_per_axes (Optional[int]): Number of waveforms to plot per axis.
    - x_axis_title (Optional[str]): The title of the X-axis.
    - y_axis_title (Optional[str]): The title of the Y-axis.
    - figure_title (Optional[str]): The title of the entire figure.
    - show_ticks_only_on_edges (bool): Whether to show ticks only on the edges of the plot.
    - wf_func (Optional[Callable]): Optional function for additional waveform processing.
    - yannotation (Optional[float]): Y-coordinate for the top annotation of each subplot.
    """

    # Create a new figure if one is not provided
    if figure is not None:
        wpu.check_dimensions_of_suplots_figure(figure, channel_ws_grid.ch_map.rows, channel_ws_grid.ch_map.columns)
        figure_ = figure
    else:
        figure_ = psu.make_subplots(rows=channel_ws_grid.ch_map.rows, cols=channel_ws_grid.ch_map.columns)

    # Configure shared axes if needed
    wpu.update_shared_axes_status(figure_, share_x=share_x_scale, share_y=share_y_scale)
    
    # Add unique channel annotations at the top
    wpu.__add_unique_channels_top_annotations(  
        channel_ws_grid,
        figure_,
        also_add_run_info=True,
        yannotation=yannotation
    )

    # Add title to the figure if provided
    if figure_title:
        figure_.update_layout(title=figure_title)

    # Iterate over the grid of subplots
    total_rows = channel_ws_grid.ch_map.rows
    total_cols = channel_ws_grid.ch_map.columns
    
    for i in range(total_rows):
        for j in range(total_cols):
            try:
                # Get the channel and endpoint for the current subplot
                channel_ws = channel_ws_grid.ch_wf_sets[channel_ws_grid.ch_map.data[i][j].endpoint][
                    channel_ws_grid.ch_map.data[i][j].channel]
            except KeyError:
                # If there's no data, add a "No data" annotation
                wpu.__add_no_data_annotation(figure_, i + 1, j + 1)
                continue

            # Get the indices of the waveforms to process
            if wfs_per_axes is not None:
                aux_idcs = range(min(wfs_per_axes, len(channel_ws.waveforms)))
                
            else:
                aux_idcs = range(len(channel_ws.waveforms))

            # Apply the user-defined plot function to each selected waveform
            for idx in aux_idcs:
                if wf_func is None:
                    plot_function(channel_ws, figure_, i + 1, j + 1)
                else:
                    plot_function(channel_ws, figure_, i + 1, j + 1, wf_func)
                
            # Configure axes based on the option to show ticks only on edges
            if show_ticks_only_on_edges:
                figure_.update_xaxes(
                    title_text=x_axis_title if i == total_rows - 1 else '',
                    showticklabels=(i == total_rows - 1),
                    row=i + 1, col=j + 1
                )
                figure_.update_yaxes(
                    title_text=y_axis_title if j == 0 else '',
                    showticklabels=(j == 0),
                    row=i + 1, col=j + 1
                )
            else:
                if x_axis_title is not None and i == total_rows - 1:
                    figure_.update_xaxes(title_text=x_axis_title, row=i + 1, col=j + 1)
                if y_axis_title is not None and j == 0:
                    figure_.update_yaxes(title_text=y_axis_title, row=i + 1, col=j + 1)

            # Set the X-axis to logarithmic scale if the title is 'Frequency [MHz]'
            if x_axis_title == 'Frequency [MHz]':
                figure_.update_xaxes(
                    type='log',  # Sets the X-axis to a logarithmic scale
                    row=i + 1, col=j + 1
                )
            if log_x_axis:
                figure_.update_xaxes(
                    type='log',  # Aplica escala logarítmica al eje X
                    row=i + 1, col=j + 1
                )
                
    return figure_



'''
__subplot_heatmap
----- PATH -----> src/waffles/plotting/plot_utils.py
(modified by me to get colorbars)
'''

def __subplot_heatmap(
    waveform_set: WaveformSet,
    figure: pgo.Figure,
    name: str,
    row: int,
    col: int,
    wf_idcs: List[int],
    analysis_label: str,
    time_bins: int,
    adc_bins: int,
    ranges: np.ndarray,
    show_color_bar: bool = False,
    filtering: float = 0,
    zlog: bool = False,
) -> pgo.Figure:
    """This is a helper function for the 
    plot_WaveformSet() function. It should only
    be called by that one, where the 
    data-availability and the well-formedness 
    checks of the input have already been 
    performed. No checks are performed in
    this function. For each subplot in the grid 
    plot generated by the plot_WaveformSet()
    function when its 'mode' parameter is
    set to 'heatmap', such function delegates
    plotting the heatmap to the current function.
    This function takes the given figure, and 
    plots on it the heatmap of the union of 
    the waveforms whose indices are contained 
    within the given 'wf_idcs' list. The 
    position of the subplot where this heatmap 
    is plotted is given by the 'row' and 'col' 
    parameters. Finally, this function returns 
    the figure.

    Parameters
    ----------
    waveform_set: WaveformSet
        The WaveformSet object whose waveforms
        will be plotted in the heatmap
    figure: pgo.Figure
        The figure where the heatmap will be
        plotted
    name: str
        The name of the heatmap. It is given
        to the 'name' parameter of
        plotly.graph_objects.Heatmap().
    row (resp. col): int
        The row (resp. column) where the
        heatmap will be plotted. These values
        are expected to be 1-indexed, so they
        are directly passed to the 'row' and
        'col' parameters of the figure.add_trace()
        method.
    wf_idcs: list of int
        Indices of the waveforms, with respect
        to the waveform_set.waveforms list,
        which will be added to the heatmap.
    analysis_label: str
        For each considered Waveform, it is the
        key for its analyses attribute which gives
        the WfAna object whose computed baseline
        is subtracted from the Waveform prior to
        addition to the heatmap. The baseline is
        grabbed from the 'baseline' key in the
        result attribute of the specified WfAna
        object. I.e. such information must be
        available. If it is not, an exception will
        be raised.
    time_bins: int
        The number of bins for the horizontal axis
        of the heatmap
    adc_bins: int
        The number of bins for the vertical axis
        of the heatmap
    ranges: np.ndarray
        A 2x2 integer numpy array where ranges[0,0]
        (resp. ranges[0,1]) gives the lower (resp.
        upper) bound of the horizontal axis of the
        heatmap, and ranges[1,0] (resp. ranges[1,1])
        gives the lower (resp. upper) bound of the
        vertical axis of the heatmap.
    show_color_bar: bool
        It is given to the 'showscale' parameter of
        plotly.graph_objects.Heatmap(). If True, a
        bar with the color scale of the plotted 
        heatmap is shown. If False, it is not.
    filtering: float
        It is given to the Denoise.apply_denoise()
        method. If it is greater than 0, then the
        waveforms will be denoised before being
        added to the heatmap. If it is 0, then no
        denoising will be applied.
    zlog: bool
        If True, the z-axis of the heatmap will be
        logarithmically scaled. 

    Returns
    ----------
    figure_: plotly.graph_objects.Figure
        The figure whose subplot at position 
        (row, col) has been filled with the heatmap
    """

    figure_ = figure

    time_step = (ranges[0, 1] - ranges[0, 0]) / time_bins
    adc_step = (ranges[1, 1] - ranges[1, 0]) / adc_bins

    aux_x = np.hstack([np.arange(
        0,
        waveform_set.points_per_wf,
        dtype=np.float32) + waveform_set.waveforms[idx].time_offset for idx in wf_idcs])

    denoiser = Denoise()
    try:
        if filtering>0:
            aux_y = np.hstack([
                denoiser.apply_denoise((waveform_set.waveforms[idx].adcs).astype(np.float32) -
                waveform_set.waveforms[idx].analyses[analysis_label].result['baseline'], filter=filtering) for idx in wf_idcs])
        else:
            aux_y = np.hstack([
                waveform_set.waveforms[idx].adcs -
                waveform_set.waveforms[idx].analyses[analysis_label].result['baseline'] for idx in wf_idcs])

    except KeyError:
        raise Exception(GenerateExceptionMessage(
            1,
            '__subplot_heatmap()',
            f"Either an analysis with the given analysis_label ({analysis_label}) does not exist for the waveforms in the given WaveformSet, or the analysis exists but it does not compute the baseline under the 'baseline' key."))

    aux = wun.histogram2d(
        np.vstack((aux_x, aux_y)),
        np.array((time_bins, adc_bins)),
        ranges)
    
    aux = aux.astype(float)
    aux[aux == 0] = np.nan
    if zlog:
        aux = np.log10(aux)
    
    heatmap = pgo.Heatmap(
        z=aux,
        x0=ranges[0, 0],
        dx=time_step,
        y0=ranges[1, 0],
        dy=adc_step,
        name=name,
        transpose=True,
        # ------------------------ SHOWING COLORBAR --------------------------
        showscale=True,
        colorbar=dict(
            title='Wf(s) [log10]',
            title_font=dict(size=9),
            tickfont=dict(size=10),
            x=0.45+0.55*(col-1),
            y=0.205+0.62*(row-1),
            len=0.43,
        ),
        # --------------------------------------------------------------------
    )
    
    figure_.add_trace(heatmap,
                      row=row,
                      col=col)
    figure_.update_xaxes(title_text="Time [ticks]", row=row, col=col)
    figure_.update_yaxes(title_text="Amplitude [ADCs]", row=row, col=1)
    return figure_
