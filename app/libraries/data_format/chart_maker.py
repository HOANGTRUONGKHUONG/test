import io

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator


def export_bar_chart(data, ingredients, total, chart_name):
    fig, ax1 = plt.subplots(figsize=(10, 8))
    fig.subplots_adjust(left=0.115, right=0.88)

    pos = np.arange(len(ingredients))

    rects = ax1.barh(pos, data, align='center', height=0.5, tick_label=ingredients)

    ax1.set_title(chart_name)
    ax1.set_xlim([0, (total + total / 10) if total != 0 else 10])
    ax1.xaxis.set_major_locator(MaxNLocator(11))
    ax1.xaxis.grid(True, linestyle='--', which='major', color='grey', alpha=0.5)
    for rect in rects:
        width = int(rect.get_width())
        rank_str = width
        x_loc = 5
        clr = 'black'
        align = 'left'
        y_loc = rect.get_y() + rect.get_height() / 2
        label = ax1.annotate(rank_str, xy=(width, y_loc), xytext=(x_loc, 0), textcoords="offset points", ha=align,
                             va='center', color=clr, weight='bold', clip_on=True)
    sio = io.BytesIO()
    fig.savefig(sio, format="png", bbox_inches='tight')
    return sio


def export_pie_chart(data, ingredients, chart_name):
    if data == [] and ingredients == []:
        data = [1]
        ingredients = ['No Data']
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(aspect="equal"))

    def format_data(pct, all_vals):
        if pct > 1:
            absolute = int(pct / 100. * np.sum(all_vals))
            return "{:.1f}%".format(pct, absolute)
        else:
            return ""

    wedges, texts, auto_texts = ax.pie(data, autopct=lambda pct: format_data(pct, data), textprops=dict(color="w"))

    ax.legend(wedges, ingredients, title=chart_name, loc="center left", bbox_to_anchor=(1, 0, 0, 1))
    plt.setp(auto_texts, size=6, weight="bold")
    sio = io.BytesIO()
    plt.savefig(sio, format="png", bbox_inches='tight')
    return sio
