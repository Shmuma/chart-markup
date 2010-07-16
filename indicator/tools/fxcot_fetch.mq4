#include "sqlite.mqh"
#include "http.mqh"
#include "utils.mqh"


string db_file = "experts/files/fxcot.db";

string data_fields = "symbol, date, oi, non_comm_long, non_comm_short, non_comm_spread, comm_long, comm_short, non_repr_long, non_repr_short, cnt_non_comm_long, cnt_non_comm_short, cnt_non_comm_spread, cnt_comm_long, cnt_comm_short";


void create_schema ()
{
    sqlite_exec (db_file, "create table items (symbol, last_update)");
    sqlite_exec (db_file, "create table data (" + data_fields + ")");
}


datetime get_item_last_update (string symbol)
{
    int cols[1], rows = 0;
    int handle = sqlite_query (db_file, "select last_update from items where symbol='" + symbol + "'", cols);
    datetime ts = 0;

    while (sqlite_next_row (handle) == 1) {
        ts = parse_iso_date (sqlite_get_col (handle, 0));
        rows++;
    }
    sqlite_free_query (handle);

    if (rows == 0)
        sqlite_exec (db_file, "insert into items (symbol, last_update) values ('" + symbol + "', '1970-01-01')");

    return (ts);
}


int update_item_last_update (string symbol, string date)
{
    return (sqlite_exec (db_file, "update items set last_update = '" + date + "'where symbol = '" + symbol + "'"));
}



int fetch_cot_items (string& data[][])
{
    // get list of available instruments in GAE service
    Print ("Download list of COT instruments...");

    string res;
    int err = downloadFile ("http://quote-tracker.appspot.com/cot-list?csv=1", res);
    int result_rows = 0;

    if (err > 0) {
        string lines[1];
        int rows;

        rows = split (res, "\n", lines);
        for (int i = 1; i < rows; i++)
            if (lines[i] != "") {
                // each line has symbol and last update date in ISO format (YYYY-MM-DD)
                // Pack them in array
                int pos = StringFind (lines[i], ",");
                if (pos >= 0) {
                    ArrayResize (data, result_rows+1);
                    data[result_rows][0] = StringSubstr (lines[i], 0, pos);
                    data[result_rows][1] = parse_iso_date (StringSubstr (lines[i], pos+1, StringLen (lines[i])));
                    result_rows = result_rows + 1;
                }
            }
        return (result_rows);
    }
    else {
        Print ("Failed to download COT instruments list. Error code " + err);
        return (0);
    }
}



int update_cot_item (string symbol, string url)
{
    string data;
    int err = downloadFile (url, data);
    int entries = 0;
    string last_date = "";

    if (err > 0) {
        string lines[1];
        int rows;

        rows = split (data, "\n", lines);
        for (int i = 1; i < rows; i++) {
            if (lines[i] != "") {
                string items[1];
                int cols;

                cols = split (lines[i], ",", items);

                if (cols != 14)
                    continue;

                string query = "insert into data (" + data_fields + ") values ('" + symbol + "','" + items[0] + "',";

                for (int j = 1; j < cols; j++) {
                    query = query + items[j];
                    if (j != cols-1)
                        query = query + ",";
                }

                query = query + ")";
                sqlite_exec (db_file, query);
                entries++;
                if (items[0] > last_date)
                    last_date = items[0];
            }
        }
        Print (symbol, " processed, handled ", entries, " reports");
        update_item_last_update (symbol, last_date);
        return (entries);
    }

    return (0);
}


int start ()
{
    // check for fresh database
    if (!sqlite_table_exists (db_file, "items"))
        create_schema ();

    int items_count;
    string items[1][2];

    items_count = fetch_cot_items (items);

    if (items_count <= 0)
        return (0);

    // for each cot item, check for update needed
    for (int i = 0; i < items_count; i++) {
        string symbol = items[i][0];
        string date = items[i][1];
        datetime ts = get_item_last_update (symbol);
        if (ts < StrToInteger (date)) {
            string from = format_iso_date (ts);
            string to   = format_iso_date (StrToInteger (date));
            Print ("Fetch ", symbol, " from date ", from, " to date ", to);
            string url = "http://quote-tracker.appspot.com/cot/" + symbol + "?";

            if (ts > 0)
                url = url + "from=" + from + "&";
            url = url + "to=" + to;
            update_cot_item (symbol, url);
        }
    }
}
