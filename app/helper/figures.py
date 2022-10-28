def radar_chart(data):
    import pygal
    from pygal.style import Style
    from pygal import Config

    categories = ["energy", "liveness", "speechiness",	"acousticness",	"instrumentalness", "danceability",	"valence"]
    
    r = data.mean()
    # Avg audio features of the TOP 500 Rolling Stones Magazine
    r2 = [0.601546, 0.215710, 0.064273, 0.345752, 0.037234, 0.554010, 0.638210]
    # Avg audio features of the TOP Tracks 2020 Germany
    r3 = [0.658820, 0.169402, 0.148086, 0.223102, 0.019515, 0.737580, 0.539320]

    config = Config()

    config.show_legend = True
    config.include_x_axis = False
    

    costum_style = Style(   
        font_family='googlefont:Raleway', 
        background = 'transparent',
        plot_background = 'transparent',
        foreground = '#fff',
        foreground_strong = '#fff',
        foreground_subtle = '#555',
        opacity = '.1',
        opacity_hover = '.75',
        transition = '1s ease-out',
        colors = ('#ff5995', '#b6e354', '#feed6c'))

    radar_chart = pygal.Radar(config, fill=True,
                              dots_size=8,
                              margin_top=50,
                              margin_bottom=50,
                              show_y_guides=False,
                              interpolate='cubic', 
                              legend_at_bottom=True,
                              legend_at_bottom_columns=3,
                              style=costum_style)
    
    costum_style.label_font_size = 24
    costum_style.legend_font_size = 24

    #radar_chart.title = 'Your music profile'
    radar_chart.x_labels = categories
    radar_chart.add('TOP 500 US', r2)
    radar_chart.add('Your profile', r)
    radar_chart.add('TOP Tracks 2020', r3)

    return radar_chart.render_data_uri()
