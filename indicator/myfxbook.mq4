#include "tools/sqlite.mqh"
#include "tools/http.mqh"
#include "tools/utils.mqh"

#property copyright "Max Lapan <max.lapan@gmail.com>"
#property indicator_chart_window
#property indicator_buffers 0
#property show_inputs


extern string account_id = "38016";

string db_file = "experts/files/myfxbook.db";
string orders_fields = "acc_id, pair, open_ts, close_ts, long, lots, sl, tp, open_price, close_price, pips, profit, comment";


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
    fields[2] = parse_iso_date (items[0]);
    fields[3] = parse_iso_date (items[1]);
    if (items[2] == "True")
        fields[4] = 1;
    else
        fields[4] = 0;
    fields[5] = items[3];       // lots
    fields[6] = items[4];       // sl
    fields[7] = items[5];       // tp
    fields[8] = items[6];       // open_price
    fields[9] = items[7];       // close_price
    fields[10] = items[8];       // pips
    fields[11] = items[9];       // profit
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

    return (0);
}


int start ()
{
    return (0);
}
