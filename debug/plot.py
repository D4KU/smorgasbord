import matplotlib.pyplot as plt


def save_barplot(
        xvals,
        yvals,
        barwidth=0.8,
        xmax=None,
        title="",
        filename="plot",
        ):
    """
    Save a pyplot barplot to disk as a png image.
    :param xvals: Values along the x-axis
    :param yvals: Values along the y-axis
    :param barwidth: Width of one bar
    :param xmax: Maximum x-value drawn. If None, the maximum value
        found in 'xvals' is used.
    :param title: String printed under the plot.
    :param filename: Name of the file to save without file extension.
        Can be a relative or absolute path.
    """
    plt.clf()
    if xmax is not None:
        plt.xlim(right=xmax)
    plt.title(title)
    plt.bar(xvals, yvals, barwidth)
    plt.savefig(filename + ".png")
