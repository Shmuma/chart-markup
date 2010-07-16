// Http interface.

#import "wininet.dll"
int InternetAttemptConnect (int x);
int InternetOpenA(string sAgent, int lAccessType,
                  string sProxyName = "", string sProxyBypass = "",
                  int lFlags = 0);
int InternetOpenUrlA(int hInternetSession, string sUrl,
                     string sHeaders = "", int lHeadersLength = 0,
                     int lFlags = 0, int lContext = 0);
int InternetReadFile(int hFile, int& sBuffer[], int lNumBytesToRead,
                     int& lNumberOfBytesRead[]);
int InternetCloseHandle(int hInet);

#define INTERNET_FLAG_NO_CACHE_WRITE    0x04000000  // don't write this item to the cache
#define INTERNET_FLAG_RELOAD            0x80000000  // retrieve the original item
#import


#define E_DLL_DISABLED -1
#define E_SESSION_FAILED -2
#define E_URL_OPEN_FAILED -3


// Return size of document on success, negative value on error
int downloadFile (string url, string &txt)
{
    if (!IsDllsAllowed ())
    {
        Alert ("Cannot use http without dll load, which is currently disabled. Please enable dll.");
        return (E_DLL_DISABLED);
    }

    int hInternetSession = InternetOpenA("Microsoft Internet Explorer", 0, "", "", 0);
    if (hInternetSession <= 0)
        return (E_SESSION_FAILED);

    int hURL = InternetOpenUrlA(hInternetSession, url, "", 0, INTERNET_FLAG_RELOAD | INTERNET_FLAG_NO_CACHE_WRITE, 0);
    if (hURL <= 0) {
        InternetCloseHandle (hInternetSession);
        return (E_URL_OPEN_FAILED);
    }

    int cBuffer[256];
    int dwBytesRead[1];

    txt = "";

    while (!IsStopped ())
    {
        bool bResult = InternetReadFile (hURL, cBuffer, 1024, dwBytesRead);

        if (dwBytesRead[0] == 0)
            break;

        string text = "";
        for (int i = 0; i < 256; i++)
        {
            text = text + CharToStr(cBuffer[i] & 0x000000FF);
            if(StringLen(text) == dwBytesRead[0])
                break;
            text = text + CharToStr(cBuffer[i] >> 8 & 0x000000FF);
            if(StringLen(text) == dwBytesRead[0])
                break;
            text = text + CharToStr(cBuffer[i] >> 16 & 0x000000FF);
            if(StringLen(text) == dwBytesRead[0])
                break;
            text = text + CharToStr(cBuffer[i] >> 24 & 0x000000FF);
            if(StringLen(text) == dwBytesRead[0])
                break;
        }
        txt = txt + text;
        Sleep(1);
    }

    InternetCloseHandle(hInternetSession);

    return (StringLen (txt));
}
