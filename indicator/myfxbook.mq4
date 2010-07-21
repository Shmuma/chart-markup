#include "tools/sqlite.mqh"
#include "tools/http.mqh"
#include "tools/utils.mqh"

#property copyright "Max Lapan <max.lapan@gmail.com>"
#property indicator_chart_window
#property indicator_buffers 0
#property show_inputs

extern string account_id = "38016";
extern bool show_lines = true;

string db_file = "experts/files/myfxbook.db";
string orders_fields = "acc_id, pair, open_ts, close_ts, long, lots, sl, tp, open_price, close_price, pips, profit, comment";

int objects_count = 0;          // Amount of created objects. Used in destruction.


void create_schema ()
{
    sqlite_exec (db_file, "create table orders (" + orders_fields + ")");
}


int query_orders_count (string acc_id, string pair)
{
    string res;
    int bytes = downloadFile ("http://chart-markup.appspot.com/fxbook?id=" + acc_id + "&pair=" + pair + "&count=1", res);

    if (bytes > 0) {
        res = StringTrimRight (res);
        return (StrToInteger (res));
    }
    else
        return (-1);
}


bool is_data_expired (string acc_id, string pair)
{
    int cols[1];
    int handle = sqlite_query (db_file, "select count(*) from orders where acc_id = '" + acc_id + "' and pair = '" + pair + "'", cols);
    bool res = true;
    int count;
    
    if (sqlite_next_row (handle) == 1) {
        count = query_orders_count (acc_id, pair);
        if (count < 0)
            res = false;        // if we failed to fetch actual count, do not update information
        res = StrToInteger (sqlite_get_col (handle, 0)) != count;
    }

    sqlite_free_query (handle);

    return (res);
}

void insert_order (string acc_id, string pair, string line)
{
    int count;
    string items[1];

    count = split (line, ",", items);

    if (count < 11)
        return;

    string comm = items[10];

    for (int i = 11; i < count; i++)
        comm = comm + "," + items[i];

    string fields[13];

    fields[0] = acc_id;
    fields[1] = pair;
    fields[2] = parse_iso_date (items[0], 2*60*60);
    fields[3] = parse_iso_date (items[1], 2*60*60);
    if (items[2] == "True")
        fields[4] = 1;
    else
        fields[4] = 0;
    fields[5] = items[3];       // lots
    fields[6] = items[4];       // sl
    fields[7] = items[5];       // tp
    fields[8] = items[6];       // open_price
    fields[9] = items[7];       // close_price
    fields[10] = items[8];      // pips
    fields[11] = items[9];      // profit
    fields[12] = comm;

    sqlite_exec (db_file, "insert into orders (" + orders_fields + ") values (" + 
                 build_insert_list (fields) + ")");
}


void update_data (string acc_id, string pair)
{
    string res;
    int bytes = downloadFile ("http://chart-markup.appspot.com/fxbook?id=" + acc_id + "&pair=" + pair, res);

    if (bytes <= 0)
        return;

    string lines[1];
    int rows;

    // clean old data. It's much faster to wipe all old orders than mess with incremental update.
    sqlite_exec (db_file, "delete from orders where acc_id = '" + acc_id + "' and pair = '" + pair + "'");

    rows = split (res, "\n", lines);

    for (int i = 1; i < rows; i++) {
        string line = StringTrimRight (lines[i]);
        if (StringLen (line) > 0)
            insert_order (acc_id, pair, lines[i]);
    }
}


string obj_name (int index)
{
    return ("myfx-" + account_id + "-" + Symbol () + "-" + index);
}


void make_object_for_order (string open_ts, string close_ts, string is_long_str, string lots, string sl, string tp,
                            string open_price, string close_price, string pips, string profit, string comment)
{
    bool res, is_long = is_long_str == "1";
    string name = obj_name (objects_count);
    string comm;

    // Open object
    res = ObjectCreate (name, OBJ_ARROW, 0, StrToInteger (open_ts), StrToDouble (open_price));
    if (!res)
        return;
    if (is_long) {
        ObjectSet (name, OBJPROP_ARROWCODE, SYMBOL_ARROWUP);
        ObjectSet (name, OBJPROP_COLOR, Green);
        comm = "Long, ";
    }
    else {
        ObjectSet (name, OBJPROP_ARROWCODE, SYMBOL_ARROWDOWN);
        ObjectSet (name, OBJPROP_COLOR, Red);
        comm = "Short, ";
    }
    ObjectSetText (name, comm + lots + " lots, sl @" + sl + ", tp @" + tp + ", comment '" + comment + "'");

    objects_count++;
    name = obj_name (objects_count);

    // Close object
    ObjectCreate (name, OBJ_ARROW, 0, StrToInteger (close_ts), StrToDouble (close_price));

    if (StrToDouble (profit) > 0) {
        ObjectSet (name, OBJPROP_ARROWCODE, SYMBOL_CHECKSIGN);
        ObjectSet (name, OBJPROP_COLOR, Green);
    }
    else {
        ObjectSet (name, OBJPROP_ARROWCODE, SYMBOL_STOPSIGN);
        ObjectSet (name, OBJPROP_COLOR, Red);
    }
    ObjectSetText (name, "Profit $" + profit + " (" + pips + " pips)");
    objects_count++;
}


void make_objects ()
{
    int cols[1];
    int handle = sqlite_query (db_file, "select " + orders_fields + " from orders where acc_id = '" + account_id +
                               "' and pair = '" + Symbol () + "'", cols);

    while (sqlite_next_row (handle) == 1) {
        make_object_for_order (sqlite_get_col (handle, 2),
                               sqlite_get_col (handle, 3),
                               sqlite_get_col (handle, 4),
                               sqlite_get_col (handle, 5),
                               sqlite_get_col (handle, 6),
                               sqlite_get_col (handle, 7),
                               sqlite_get_col (handle, 8),
                               sqlite_get_col (handle, 9),
                               sqlite_get_col (handle, 10),
                               sqlite_get_col (handle, 11),
                               sqlite_get_col (handle, 12));
    }

    sqlite_free_query (handle);
}


int init ()
{
    string pair = Symbol ();

    if (!sqlite_table_exists (db_file, "orders"))
        create_schema ();

    if (StringLen (account_id) == 0) {
        Print ("Account ID is required, failed");
        return (-1);
    }

    // check for data update needed
    if (is_data_expired (account_id, pair)) {
        Print ("Data is expired, fetch data for account " + account_id + " and pair " + pair);
        update_data (account_id, pair);
    }

    // create symbols according to data in DB.
    make_objects ();

    return (0);
}


int start ()
{
    if (!show_lines)
        return (0);

    int counted_bars = IndicatorCounted ();

    for (int i = 0; i < Bars - counted_bars - 1; i++) {
        // Interpolate, interpolate, interpolate!
    }

    return (0);
}


int deinit ()
{
    while (objects_count > 0) {
        objects_count--;
        ObjectDelete (obj_name (objects_count));
    }

    return (0);
}
