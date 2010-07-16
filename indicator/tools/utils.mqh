int split (string data, string substr, string& res[])
{
    int pos = 0, ppos = 0;
    int rows = 0;

    while (true) {
        pos = StringFind (data, substr, ppos);
        string line;

        if (pos >= 0)
            line = StringSubstr (data, ppos, pos-ppos);
        else
            line = StringSubstr (data, ppos, StringLen (data));
        ppos = pos + 1;
        ArrayResize (res, rows+1);
        res[rows] = line;
        rows = rows + 1;
        if (pos < 0)
            break;
    }

    return (rows);
}


/*
 * replaces every occurence of a with b
 */
string str_replace (string data, string a, string b)
{
    string res = "";
    string arr[1];
    int count;

    count = split (data, a, arr);
    for (int i = 0; i < count; i++)
        if (res != "")
            res = res + b + arr[i];
        else
            res = arr[i];

    return (res);
}



datetime parse_iso_date (string val, int delta)
{
    string a = str_replace (val, "-", ".");
    return (StrToTime (a) + delta);
}


string format_iso_date (datetime val)
{
    return (str_replace (TimeToStr (val, TIME_DATE), ".", "-"));
}


string build_insert_list (string items[])
{
    string res = "";
    
    for (int i = 0; i < ArraySize (items); i++) {
        if (i > 0)
            res = res + ",";
        res = res + "'" + items[i] + "'";
    }

    return (res);
}
