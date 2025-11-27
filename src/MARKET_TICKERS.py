"""
Market ticker database for full market analysis.

This file contains curated lists of tickers for different markets
that can be used to run analysis across the full market.

Usage:
    from src.MARKET_TICKERS import get_tickers_for_markets

    # Get tickers for Nordic and EU markets
    tickers = get_tickers_for_markets(["nordic", "eu"])

    # Get all tickers
    all_tickers = get_tickers_for_markets(["nordic", "eu", "us"])
"""

# Nordic Market Tickers (50 major instruments)
NORDIC_TICKERS = [
    # Swedish (Nasdaq Stockholm)
    "AAPL.ST",
    "ADDVB.ST",
    "AKSO.ST",
    "ALIV.ST",
    "AMBUU.ST",
    "ASSA.ST",
    "ATLAS.ST",
    "BIOM.ST",
    "CENTR.ST",
    "CORE.ST",
    "CORUM.ST",
    "DNSV.ST",
    "ECAD.ST",
    "ELWI.ST",
    "ENTR.ST",
    "ERIC.ST",
    "ESSITY.ST",
    "EVERGY.ST",
    "FABG.ST",
    "GARO.ST",
    "GIVA.ST",
    "GRON.ST",
    "HMAX.ST",
    "HM.ST",
    "HSBNC.ST",
    "HUMM.ST",
    "HUSON.ST",
    "INDU.ST",
    "INMR.ST",
    "INSTAL.ST",
    "INVES.ST",
    "IVSO.ST",
    "JCSE.ST",
    "KDEV.ST",
    "KNOV.ST",
    "LIFCO.ST",
    "LIND.ST",
    "LUMI.ST",
    "MKNT.ST",
    "MTG.ST",
    "MYCRP.ST",
    "MYOB.ST",
    "NAWA.ST",
    "NETF.ST",
    "NICA.ST",
    "NILOC.ST",
    "NLFB.ST",
    "NOVOB.ST",
    "NTC.ST",
    "PAXS.ST",
    "PEAB.ST",
    # Finnish (Nasdaq Helsinki)
    "KNEBV.HE",
    "NOKIA.HE",
    "RENI.HE",
    "SAMPO.HE",
    "STERV.HE",
    "TIETO.HE",
    "TRINC.HE",
    "UPM.HE",
    "WRTC.HE",
    # Danish (Nasdaq Copenhagen)
    "BANG.CO",
    "CHR.CO",
    "DXTR.CO",
    "FLS.CO",
    "GN.CO",
    "ISH.CO",
    "MAERSK.A.CO",
    "MAERSK.B.CO",
    "NWC.CO",
    "NZYMQ.CO",
    # Norwegian (Oslo Børs)
    "AEC.OSE",
    "AKRBP.OSE",
    "ASH.OSE",
    "AZURITY.OSE",
    "BAKKA.OSE",
]

# EU Market Tickers (100 major instruments)
EU_TICKERS = [
    # German (Xetra)
    "SAP.DE",
    "SIE.DE",
    "ALV.DE",
    "BMW.DE",
    "HEI.DE",
    "LHA.DE",
    "MBG.DE",
    "MUV2.DE",
    "PSM.DE",
    "RWE.DE",
    "SDF.DE",
    "VIA.DE",
    "VOW.DE",
    "ZAL.DE",
    # French (Euronext Paris)
    "MC.PA",
    "OR.PA",
    "CS.PA",
    "SAN.PA",
    "GLE.PA",
    "AI.PA",
    "AC.PA",
    "VIE.PA",
    "CAP.PA",
    "KER.PA",
    "LHYFE.PA",
    "PUB.PA",
    "WLN.PA",
    # Netherlands (Euronext Amsterdam)
    "ASML.AS",
    "ASML.AS",
    "SHELL.AS",
    "ADYEN.AS",
    "HAL.AS",
    # Italy (Borsa Italiana)
    "ENEL.MI",
    "G.MI",
    "ISP.MI",
    "MB.MI",
    "TEN.MI",
    # Spain (Bolsa de Madrid)
    "ACS.MC",
    "AIR.MC",
    "ALM.MC",
    "AMS.MC",
    "BBVA.MC",
    "CABK.MC",
    "ENG.MC",
    "FER.MC",
    # Belgium (Euronext Brussels)
    "COLR.BR",
    # Austria (Vienna Stock Exchange)
    "RHM.VI",
    "SEM.VI",
    # Switzerland (SIX Swiss Exchange)
    "NESN.SW",
    "ABBN.SW",
    "CFR.SW",
]

# US Market Tickers (200 major instruments)
US_TICKERS = [
    # Tech giants
    "AAPL",
    "MSFT",
    "GOOGL",
    "GOOG",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "NFLX",
    "CRWD",
    "CRM",
    "ADBE",
    "INTU",
    "PYPL",
    "ABNB",
    "UBER",
    "SPOT",
    "DDOG",
    "SNOW",
    "NET",
    "OKTA",
    "WDAY",
    "ZM",
    "COIN",
    "MSTR",
    "PLTR",
    "U",
    "IBM",
    "INTC",
    "AMD",
    "QCOM",
    "AVGO",
    "LRCX",
    "ASML",
    "KLAC",
    "MRVL",
    "SNPS",
    "CDNS",
    "AMAT",
    "MU",
    "NXPI",
    "STX",
    "WDC",
    "ASGN",
    "CRWD",
    "CSCO",
    # Financials
    "JPM",
    "BAC",
    "WFC",
    "GS",
    "MS",
    "BLK",
    "SCHW",
    "COIN",
    "RBLX",
    "VZ",
    "T",
    "CMCSA",
    "CHTR",
    "DISH",
    "FOX",
    "FOXA",
    "DIS",
    "NWSA",
    "NEWS",
    "GRMN",
    "EA",
    "TTWO",
    "ATVI",
    "ROBLOX",
    "UMC",
    "TSM",
    "AIMT",
    "AMAT",
    "ASML",
    "LRCX",
    "NFLX",
    # Healthcare
    "JNJ",
    "PFE",
    "MRNA",
    "BNTX",
    "AZN",
    "LLY",
    "ABT",
    "ABBV",
    "TMO",
    "AMGN",
    "GILD",
    "BERY",
    "VRTX",
    "ILMN",
    "REGN",
    "BIIB",
    "EXAS",
    "ELLI",
    "FLGT",
    "VEEV",
    "ALRM",
    "AEZS",
    "AEGN",
    "AGIO",
    "ALKS",
    "ALLT",
    "AMPH",
    "AMTI",
    "AMWL",
    "AMZN",
    # Consumer
    "WMT",
    "HD",
    "LOW",
    "MCD",
    "SBUX",
    "NKE",
    "VFC",
    "KMX",
    "KR",
    "COST",
    "TGT",
    "BBY",
    "ULTA",
    "LULU",
    "RH",
    "DECK",
    "CPRT",
    "PTON",
    "FIVE",
    "GEVO",
    "HLT",
    "MAR",
    "IAG",
    "RCL",
    "CCL",
    "NCLH",
    "PSHW",
    "DPZ",
    "BLKB",
    "BLMN",
    # Industrial
    "BA",
    "GE",
    "CAT",
    "DE",
    "MMM",
    "SPY",
    "XLF",
    "XLI",
    "XLK",
    "XLY",
    "XLV",
    "XLRE",
    "XLU",
    "XLRE",
    "RSP",
    "VTI",
    "VTV",
    "VUG",
    "VOE",
    "VOT",
    "VB",
    "VO",
    "VBR",
    "VSS",
    "VEA",
    "VWO",
    "BND",
    "AGG",
    "BSV",
    "BIV",
    "LQD",
    "EMB",
    "HYG",
    "ANGL",
    "VCIT",
    "VCSH",
    "VCRT",
    "VNQ",
    "VGSLX",
    "VMMSX",
    # ETFs
    "SPY",
    "VOO",
    "VTI",
    "IVV",
    "SCHX",
    "VTSAX",
    "VFIAX",
    "VSTAX",
    "AGG",
    "BND",
    "SCHB",
    "RSP",
    "EUSA",
    "VV",
    "VFIAX",
    "SPLG",
    "IWV",
    "SCHB",
    "VONE",
    "VTV",
    # More sectors
    "XOM",
    "CVX",
    "SLB",
    "EOG",
    "MPC",
    "PSX",
    "VLO",
    "TSO",
    "WMB",
    "NS",
    "NEE",
    "DUK",
    "SO",
    "AEP",
    "EXC",
    "EQIX",
    "DLR",
    "PLD",
    "PSA",
    "AMT",
]


def get_tickers_for_markets(markets: list[str], limit: int = None) -> list[str]:
    """
    Get ticker list for specified markets.

    Args:
        markets: List of market codes ('nordic', 'eu', 'us')
        limit: Optional limit on number of tickers per market

    Returns:
        List of tickers for the specified markets

    Examples:
        >>> get_tickers_for_markets(['nordic', 'eu'])
        ['AAPL.ST', 'NOVOB.ST', ..., 'SAP.DE', 'ASML.AS', ...]

        >>> get_tickers_for_markets(['us'], limit=50)
        ['AAPL', 'MSFT', 'GOOGL', ..., ]  # First 50 US tickers
    """
    tickers = []

    market_map = {
        "nordic": NORDIC_TICKERS,
        "eu": EU_TICKERS,
        "us": US_TICKERS,
    }

    for market in markets:
        if market.lower() in market_map:
            market_tickers = market_map[market.lower()]
            if limit:
                tickers.extend(market_tickers[:limit])
            else:
                tickers.extend(market_tickers)

    return tickers


def get_market_stats() -> dict:
    """Get statistics about available tickers per market."""
    return {
        "nordic": len(NORDIC_TICKERS),
        "eu": len(EU_TICKERS),
        "us": len(US_TICKERS),
        "total": len(NORDIC_TICKERS) + len(EU_TICKERS) + len(US_TICKERS),
    }


if __name__ == "__main__":
    # Example usage
    stats = get_market_stats()
    print("Available tickers per market:")
    for market, count in stats.items():
        print(f"  {market}: {count}")

    # Get some tickers
    nordic_tickers = get_tickers_for_markets(["nordic"], limit=10)
    print(f"\nFirst 10 Nordic tickers: {nordic_tickers}")

    # Get all markets
    all_tickers = get_tickers_for_markets(["nordic", "eu", "us"])
    print(f"\nTotal tickers available: {len(all_tickers)}")
