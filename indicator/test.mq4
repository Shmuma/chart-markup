
#property copyright "Max Lapan <max.lapan@gmail.com>"
#property indicator_chart_window
#property indicator_buffers 1

double data[];


int from_shift, mid_shift, to_shift;

int init ()
{
    from_shift = iBarShift (NULL, 0, D'2010.07.20 11:00');
    mid_shift  = iBarShift (NULL, 0, D'2010.07.20 23:00');
    to_shift   = iBarShift (NULL, 0, D'2010.07.21 11:00');

    SetIndexStyle (0, DRAW_SECTION, STYLE_SOLID, 2, Red);
    SetIndexBuffer (0, data);

    return (0);
}


int start ()
{
    int counted_bars = IndicatorCounted ();

    for (int i = 0; i < Bars - counted_bars - 1; i++) {
        if (i == from_shift || i == to_shift || i == mid_shift)
            data[i] = Close[i];
        else
            data[i] = EMPTY_VALUE;
    }
    return (0);
}


int deinit ()
{
    return (0);
}
