"""
Market ticker database for full market analysis.

This file contains curated lists of tickers for different markets
that can be used to run analysis across the full market.

Usage:
    from src.MARKET_TICKERS import get_tickers_for_markets, get_us_tickers_by_category

    # Get tickers for Nordic and EU markets
    tickers = get_tickers_for_markets(["nordic", "eu"])

    # Get US tickers by category
    tech_tickers = get_us_tickers_by_category("tech")
    small_cap = get_us_tickers_by_category("small_cap")

    # Get diversified portfolio tickers
    conservative_portfolio = get_us_tickers_by_category("us_portfolio_balanced_conservative")
    dividend_growers = get_us_tickers_by_category("us_portfolio_dividend_growth")
"""

# =============================================================================
# NORDIC MARKET TICKERS
# =============================================================================

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

# =============================================================================
# EU MARKET TICKERS
# =============================================================================

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

# =============================================================================
# US MARKET TICKERS - CATEGORIZED
# =============================================================================

# -----------------------------------------------------------------------------
# BY MARKET CAP
# -----------------------------------------------------------------------------

US_MEGA_CAP = [
    # $200B+ market cap - The largest companies
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL",  # Alphabet Class A
    "GOOG",  # Alphabet Class C
    "AMZN",  # Amazon
    "NVDA",  # NVIDIA
    "META",  # Meta Platforms
    "BRK-B",  # Berkshire Hathaway
    "LLY",  # Eli Lilly
    "TSM",  # Taiwan Semiconductor
    "V",  # Visa
    "UNH",  # UnitedHealth
    "JPM",  # JPMorgan Chase
    "XOM",  # Exxon Mobil
    "WMT",  # Walmart
    "MA",  # Mastercard
    "JNJ",  # Johnson & Johnson
    "PG",  # Procter & Gamble
    "AVGO",  # Broadcom
    "HD",  # Home Depot
    "ORCL",  # Oracle
    "CVX",  # Chevron
    "MRK",  # Merck
    "COST",  # Costco
    "ABBV",  # AbbVie
]

US_LARGE_CAP = [
    # $10B-$200B market cap
    "CRM",  # Salesforce
    "AMD",  # AMD
    "NFLX",  # Netflix
    "ADBE",  # Adobe
    "PEP",  # PepsiCo
    "KO",  # Coca-Cola
    "TMO",  # Thermo Fisher
    "CSCO",  # Cisco
    "ACN",  # Accenture
    "ABT",  # Abbott
    "MCD",  # McDonald's
    "DHR",  # Danaher
    "LIN",  # Linde
    "CMCSA",  # Comcast
    "VZ",  # Verizon
    "NKE",  # Nike
    "INTC",  # Intel
    "PM",  # Philip Morris
    "NEE",  # NextEra Energy
    "RTX",  # RTX Corporation
    "HON",  # Honeywell
    "QCOM",  # Qualcomm
    "TXN",  # Texas Instruments
    "UNP",  # Union Pacific
    "LOW",  # Lowe's
    "IBM",  # IBM
    "CAT",  # Caterpillar
    "SPGI",  # S&P Global
    "BA",  # Boeing
    "GE",  # GE Aerospace
    "INTU",  # Intuit
    "AMAT",  # Applied Materials
    "BKNG",  # Booking Holdings
    "ISRG",  # Intuitive Surgical
    "AXP",  # American Express
    "MDLZ",  # Mondelez
    "GILD",  # Gilead Sciences
    "ADI",  # Analog Devices
    "VRTX",  # Vertex Pharmaceuticals
    "REGN",  # Regeneron
    "PANW",  # Palo Alto Networks
    "LRCX",  # Lam Research
    "SYK",  # Stryker
    "KLAC",  # KLA Corporation
    "SNPS",  # Synopsys
    "CDNS",  # Cadence Design
    "MMC",  # Marsh McLennan
    "BDX",  # Becton Dickinson
    "CI",  # Cigna
    "MO",  # Altria
]

US_MID_CAP = [
    # $2B-$10B market cap
    "BILL",  # Bill Holdings
    "ROKU",  # Roku
    "ETSY",  # Etsy
    "ZS",  # Zscaler
    "DDOG",  # Datadog
    "NET",  # Cloudflare
    "CRWD",  # CrowdStrike
    "OKTA",  # Okta
    "MDB",  # MongoDB
    "SNOW",  # Snowflake
    "PATH",  # UiPath
    "VEEV",  # Veeva Systems
    "ZM",  # Zoom
    "DOCU",  # DocuSign
    "TWLO",  # Twilio
    "HUBS",  # HubSpot
    "TTD",  # Trade Desk
    "PAYC",  # Paycom
    "PCTY",  # Paylocity
    "CFLT",  # Confluent
    "ESTC",  # Elastic
    "DT",  # Dynatrace
    "GTLB",  # GitLab
    "FIVN",  # Five9
    "APPF",  # AppFolio
    "QLYS",  # Qualys
    "TENB",  # Tenable
    "RPD",  # Rapid7
    "CYBR",  # CyberArk
    "VRNS",  # Varonis
    "FTNT",  # Fortinet
    "WIX",  # Wix.com
    "GDDY",  # GoDaddy
    "GEN",  # Gen Digital
    "BSY",  # Bentley Systems
    "MANH",  # Manhattan Associates
    "TYL",  # Tyler Technologies
    "EPAM",  # EPAM Systems
    "GLOB",  # Globant
]

US_SMALL_CAP = [
    # $300M-$2B market cap
    "BIGC",  # BigCommerce
    "ALKT",  # Alkami Technology
    "BRZE",  # Braze
    "SOUN",  # SoundHound AI
    "AFRM",  # Affirm
    "UPST",  # Upstart
    "SOFI",  # SoFi Technologies
    "HOOD",  # Robinhood
    "IONQ",  # IonQ
    "RGTI",  # Rigetti Computing
    "ARQQ",  # Arqit Quantum
    "DNA",  # Ginkgo Bioworks
    "STEM",  # Stem Inc
    "ENVX",  # Enovix
    "QS",  # QuantumScape
    "LCID",  # Lucid Motors
    "RIVN",  # Rivian
    "NKLA",  # Nikola
    "GOEV",  # Canoo
    "PSNY",  # Polestar
    "FFIE",  # Faraday Future
    "WKHS",  # Workhorse
    "HYLN",  # Hyliion
    "JOBY",  # Joby Aviation
    "LILM",  # Lilium
    "ACHR",  # Archer Aviation
    "SPCE",  # Virgin Galactic
    "RKLB",  # Rocket Lab
    "ASTR",  # Astra Space
    "RDW",  # Redwire
    "MNTS",  # Momentus
    "ASTS",  # AST SpaceMobile
    "BKSY",  # BlackSky Technology
    "SATL",  # Satellogic
    "PL",  # Planet Labs
    "SPIR",  # Spire Global
    "S",  # SentinelOne
    "AI",  # C3.ai
]

# -----------------------------------------------------------------------------
# BY SECTOR
# -----------------------------------------------------------------------------

US_TECH_SOFTWARE = [
    # Software & Cloud Companies
    "MSFT",  # Microsoft
    "CRM",  # Salesforce
    "ADBE",  # Adobe
    "ORCL",  # Oracle
    "NOW",  # ServiceNow
    "INTU",  # Intuit
    "SNOW",  # Snowflake
    "DDOG",  # Datadog
    "MDB",  # MongoDB
    "CRWD",  # CrowdStrike
    "PANW",  # Palo Alto Networks
    "ZS",  # Zscaler
    "FTNT",  # Fortinet
    "NET",  # Cloudflare
    "OKTA",  # Okta
    "WDAY",  # Workday
    "VEEV",  # Veeva Systems
    "TEAM",  # Atlassian
    "ZM",  # Zoom
    "DOCU",  # DocuSign
    "TWLO",  # Twilio
    "HUBS",  # HubSpot
    "TTD",  # Trade Desk
    "BILL",  # Bill Holdings
    "PAYC",  # Paycom
    "PCTY",  # Paylocity
    "PATH",  # UiPath
    "CFLT",  # Confluent
    "ESTC",  # Elastic
    "GTLB",  # GitLab
    "DT",  # Dynatrace
    "FIVN",  # Five9
    "CYBR",  # CyberArk
    "RPD",  # Rapid7
    "TENB",  # Tenable
    "VRNS",  # Varonis
    "QLYS",  # Qualys
    "MNDY",  # Monday.com
]

US_TECH_SEMICONDUCTORS = [
    # Semiconductor & Chip Companies
    "NVDA",  # NVIDIA
    "AMD",  # AMD
    "INTC",  # Intel
    "TSM",  # Taiwan Semiconductor
    "AVGO",  # Broadcom
    "QCOM",  # Qualcomm
    "TXN",  # Texas Instruments
    "AMAT",  # Applied Materials
    "LRCX",  # Lam Research
    "KLAC",  # KLA Corporation
    "SNPS",  # Synopsys
    "CDNS",  # Cadence Design
    "ADI",  # Analog Devices
    "MU",  # Micron
    "MRVL",  # Marvell Technology
    "NXPI",  # NXP Semiconductors
    "ON",  # ON Semiconductor
    "SWKS",  # Skyworks
    "QRVO",  # Qorvo
    "MCHP",  # Microchip Technology
    "MPWR",  # Monolithic Power
    "WOLF",  # Wolfspeed
    "CRUS",  # Cirrus Logic
    "SLAB",  # Silicon Labs
    "DIOD",  # Diodes Inc
    "RMBS",  # Rambus
    "ONTO",  # Onto Innovation
    "COHR",  # Coherent Corp
    "IPGP",  # IPG Photonics
    "MKSI",  # MKS Instruments
    "FORM",  # FormFactor
    "ACLS",  # Axcelis Technologies
    "UCTT",  # Ultra Clean Holdings
    "CAMT",  # Camtek
    "ALGM",  # Allegro MicroSystems
    "AOSL",  # Alpha & Omega Semi
    "POWI",  # Power Integrations
    "SYNA",  # Synaptics
    "SITM",  # SiTime
    "SMTC",  # Semtech
]

US_TECH_HARDWARE = [
    # Hardware & Devices
    "AAPL",  # Apple
    "DELL",  # Dell Technologies
    "HPQ",  # HP Inc
    "HPE",  # Hewlett Packard Enterprise
    "NTAP",  # NetApp
    "PSTG",  # Pure Storage
    "WDC",  # Western Digital
    "STX",  # Seagate
    "SMCI",  # Super Micro Computer
    "LOGI",  # Logitech
    "CRSR",  # Corsair Gaming
    "SSYS",  # Stratasys
    "DDD",  # 3D Systems
    "NNDM",  # Nano Dimension
    "KEYS",  # Keysight Technologies
    "TER",  # Teradyne
    "ZBRA",  # Zebra Technologies
    "GRMN",  # Garmin
    "SONO",  # Sonos
    "HEAR",  # Turtle Beach
]

US_TECH_INTERNET = [
    # Internet & E-commerce
    "GOOGL",  # Alphabet
    "AMZN",  # Amazon
    "META",  # Meta Platforms
    "NFLX",  # Netflix
    "BKNG",  # Booking Holdings
    "ABNB",  # Airbnb
    "UBER",  # Uber
    "LYFT",  # Lyft
    "DASH",  # DoorDash
    "PINS",  # Pinterest
    "SNAP",  # Snap
    "SPOT",  # Spotify
    "RBLX",  # Roblox
    "U",  # Unity Software
    "MTCH",  # Match Group
    "BMBL",  # Bumble
    "ETSY",  # Etsy
    "EBAY",  # eBay
    "CPNG",  # Coupang
    "SE",  # Sea Limited
    "SHOP",  # Shopify
    "PYPL",  # PayPal
    "WIX",  # Wix.com
    "GDDY",  # GoDaddy
    "ZG",  # Zillow
    "OPEN",  # Opendoor
    "RDFN",  # Redfin
    "CARG",  # CarGurus
    "CVNA",  # Carvana
]

US_HEALTHCARE_PHARMA = [
    # Pharmaceuticals & Biotech
    "JNJ",  # Johnson & Johnson
    "LLY",  # Eli Lilly
    "PFE",  # Pfizer
    "MRK",  # Merck
    "ABBV",  # AbbVie
    "BMY",  # Bristol-Myers Squibb
    "AMGN",  # Amgen
    "GILD",  # Gilead Sciences
    "VRTX",  # Vertex Pharmaceuticals
    "REGN",  # Regeneron
    "BIIB",  # Biogen
    "MRNA",  # Moderna
    "BNTX",  # BioNTech
    "AZN",  # AstraZeneca
    "GSK",  # GSK plc
    "NVO",  # Novo Nordisk
    "SNY",  # Sanofi
    "ZTS",  # Zoetis
    "ALNY",  # Alnylam Pharmaceuticals
    "BMRN",  # BioMarin
    "INCY",  # Incyte
    "SRPT",  # Sarepta Therapeutics
    "EXEL",  # Exelixis
    "UTHR",  # United Therapeutics
    "JAZZ",  # Jazz Pharmaceuticals
    "NBIX",  # Neurocrine Biosciences
    "PCVX",  # Vaxcyte
    "IONS",  # Ionis Pharmaceuticals
    "ARWR",  # Arrowhead Pharmaceuticals
]

US_HEALTHCARE_DEVICES = [
    # Medical Devices & Equipment
    "ABT",  # Abbott Laboratories
    "TMO",  # Thermo Fisher Scientific
    "DHR",  # Danaher
    "MDT",  # Medtronic
    "ISRG",  # Intuitive Surgical
    "SYK",  # Stryker
    "BDX",  # Becton Dickinson
    "BSX",  # Boston Scientific
    "EW",  # Edwards Lifesciences
    "ZBH",  # Zimmer Biomet
    "HOLX",  # Hologic
    "DXCM",  # DexCom
    "PODD",  # Insulet
    "ALGN",  # Align Technology
    "IDXX",  # IDEXX Laboratories
    "IQV",  # IQVIA
    "A",  # Agilent Technologies
    "MTD",  # Mettler-Toledo
    "WAT",  # Waters Corporation
    "TFX",  # Teleflex
    "STVN",  # Stevanato Group
    "GMED",  # Globus Medical
    "NUVA",  # NuVasive
    "LIVN",  # LivaNova
    "SWAV",  # Shockwave Medical
    "NVST",  # Envista Holdings
    "XRAY",  # Dentsply Sirona
    "INSP",  # Inspire Medical
    "SILK",  # Silk Road Medical
    "PRCT",  # PROCEPT BioRobotics
]

US_FINANCIALS_BANKS = [
    # Banks & Financial Institutions
    "JPM",  # JPMorgan Chase
    "BAC",  # Bank of America
    "WFC",  # Wells Fargo
    "C",  # Citigroup
    "GS",  # Goldman Sachs
    "MS",  # Morgan Stanley
    "USB",  # US Bancorp
    "PNC",  # PNC Financial
    "TFC",  # Truist Financial
    "SCHW",  # Charles Schwab
    "BK",  # Bank of New York Mellon
    "STT",  # State Street
    "FITB",  # Fifth Third Bancorp
    "HBAN",  # Huntington Bancshares
    "KEY",  # KeyCorp
    "RF",  # Regions Financial
    "CFG",  # Citizens Financial
    "MTB",  # M&T Bank
    "ZION",  # Zions Bancorporation
    "CMA",  # Comerica
    "FHN",  # First Horizon
    "EWBC",  # East West Bancorp
    "SIVB",  # SVB Financial
    "SBNY",  # Signature Bank
    "WAL",  # Western Alliance
    "PACW",  # PacWest Bancorp
    "FRC",  # First Republic Bank
    "FFBC",  # First Financial Bancorp
    "BOKF",  # BOK Financial
    "UMBF",  # UMB Financial
]

US_FINANCIALS_FINTECH = [
    # Fintech & Payment Processing
    "V",  # Visa
    "MA",  # Mastercard
    "PYPL",  # PayPal
    "COIN",  # Coinbase
    "AFRM",  # Affirm
    "UPST",  # Upstart
    "SOFI",  # SoFi Technologies
    "HOOD",  # Robinhood
    "AXP",  # American Express
    "COF",  # Capital One
    "SYF",  # Synchrony Financial
    "ALLY",  # Ally Financial
    "GPN",  # Global Payments
    "FIS",  # Fidelity National
    "FISV",  # Fiserv
    "WEX",  # WEX Inc
    "FOUR",  # Shift4 Payments
    "TOST",  # Toast
    "MQ",  # Marqeta
    "PAYO",  # Payoneer
    "RELY",  # Remitly Global
    "BILL",  # Bill Holdings
    "FLYW",  # Flywire
    "PSFE",  # Paysafe
    "LMND",  # Lemonade
    "ROOT",  # Root Inc
]

US_FINANCIALS_ASSET_MGMT = [
    # Asset Management & Insurance
    "BLK",  # BlackRock
    "BX",  # Blackstone
    "KKR",  # KKR & Co
    "APO",  # Apollo Global
    "CG",  # Carlyle Group
    "ARES",  # Ares Management
    "OWL",  # Blue Owl Capital
    "BAM",  # Brookfield Asset Mgmt
    "IVZ",  # Invesco
    "TROW",  # T. Rowe Price
    "BEN",  # Franklin Resources
    "AMG",  # Affiliated Managers
    "VCTR",  # Victory Capital
    "FHI",  # Federated Hermes
    "WDR",  # Waddell & Reed
    "CNS",  # Cohen & Steers
    "EV",  # Eaton Vance
    "JHG",  # Janus Henderson
    "SEIC",  # SEI Investments
    "LPLA",  # LPL Financial
    "RJF",  # Raymond James
    "SF",  # Stifel Financial
    "EVR",  # Evercore
    "LAZ",  # Lazard
    "PJT",  # PJT Partners
    "MC",  # Moelis & Company
    "HLI",  # Houlihan Lokey
    "PIPR",  # Piper Sandler
    "MKTX",  # MarketAxess
    "VIRT",  # Virtu Financial
]

US_CONSUMER_RETAIL = [
    # Retail & Consumer Discretionary
    "WMT",  # Walmart
    "COST",  # Costco
    "TGT",  # Target
    "HD",  # Home Depot
    "LOW",  # Lowe's
    "TJX",  # TJX Companies
    "ROST",  # Ross Stores
    "DG",  # Dollar General
    "DLTR",  # Dollar Tree
    "KR",  # Kroger
    "WBA",  # Walgreens
    "CVS",  # CVS Health
    "BBY",  # Best Buy
    "ULTA",  # Ulta Beauty
    "LULU",  # Lululemon
    "NKE",  # Nike
    "GPS",  # Gap Inc
    "ANF",  # Abercrombie & Fitch
    "AEO",  # American Eagle
    "URBN",  # Urban Outfitters
    "FL",  # Foot Locker
    "M",  # Macy's
    "KSS",  # Kohl's
    "JWN",  # Nordstrom
    "BURL",  # Burlington Stores
    "FIVE",  # Five Below
    "OLLI",  # Ollie's Bargain
    "BJ",  # BJ's Wholesale
    "PSMT",  # PriceSmart
    "CASY",  # Casey's General
]

US_CONSUMER_FOOD_BEV = [
    # Food & Beverage
    "PEP",  # PepsiCo
    "KO",  # Coca-Cola
    "MDLZ",  # Mondelez
    "PM",  # Philip Morris
    "MO",  # Altria
    "GIS",  # General Mills
    "K",  # Kellogg
    "CPB",  # Campbell Soup
    "SJM",  # J.M. Smucker
    "HSY",  # Hershey
    "MNST",  # Monster Beverage
    "KDP",  # Keurig Dr Pepper
    "STZ",  # Constellation Brands
    "BF-B",  # Brown-Forman
    "TAP",  # Molson Coors
    "SAM",  # Boston Beer
    "HRL",  # Hormel Foods
    "TSN",  # Tyson Foods
    "CAG",  # Conagra Brands
    "KHC",  # Kraft Heinz
    "CLX",  # Clorox
    "CL",  # Colgate-Palmolive
    "EL",  # Estee Lauder
    "PG",  # Procter & Gamble
    "KMB",  # Kimberly-Clark
    "CHD",  # Church & Dwight
    "SYY",  # Sysco
    "USFD",  # US Foods
    "PFGC",  # Performance Food
    "CHEF",  # Chefs' Warehouse
]

US_CONSUMER_RESTAURANTS = [
    # Restaurants & Hospitality
    "MCD",  # McDonald's
    "SBUX",  # Starbucks
    "YUM",  # Yum! Brands
    "CMG",  # Chipotle
    "DRI",  # Darden Restaurants
    "QSR",  # Restaurant Brands
    "WING",  # Wingstop
    "CAVA",  # Cava Group
    "SHAK",  # Shake Shack
    "TXRH",  # Texas Roadhouse
    "BJRI",  # BJ's Restaurants
    "BLMN",  # Bloomin' Brands
    "EAT",  # Brinker International
    "DIN",  # Dine Brands
    "CAKE",  # Cheesecake Factory
    "DENN",  # Denny's
    "JACK",  # Jack in the Box
    "PZZA",  # Papa John's
    "DPZ",  # Domino's Pizza
    "WEN",  # Wendy's
    "ARCO",  # Arcos Dorados
    "PLAY",  # Dave & Buster's
    "BOWL",  # Bowlero Corp
    "BROS",  # Dutch Bros
    "LOCO",  # El Pollo Loco
    "NDLS",  # Noodles & Company
    "PLNT",  # Planet Fitness
    "XPOF",  # Xponential Fitness
    "FRSH",  # Freshpet
    "HAIN",  # Hain Celestial
]

US_INDUSTRIALS = [
    # Industrial & Manufacturing
    "CAT",  # Caterpillar
    "DE",  # Deere & Company
    "BA",  # Boeing
    "GE",  # GE Aerospace
    "RTX",  # RTX Corporation
    "HON",  # Honeywell
    "LMT",  # Lockheed Martin
    "NOC",  # Northrop Grumman
    "GD",  # General Dynamics
    "TXT",  # Textron
    "HWM",  # Howmet Aerospace
    "TDG",  # TransDigm
    "HEI",  # Heico Corp
    "AXON",  # Axon Enterprise
    "OSK",  # Oshkosh Corp
    "PCAR",  # PACCAR
    "CMI",  # Cummins
    "EMR",  # Emerson Electric
    "ETN",  # Eaton Corporation
    "ROK",  # Rockwell Automation
    "PH",  # Parker-Hannifin
    "ITW",  # Illinois Tool Works
    "SWK",  # Stanley Black Decker
    "DOV",  # Dover Corp
    "AME",  # AMETEK
    "FTV",  # Fortive
    "IR",  # Ingersoll Rand
    "GGG",  # Graco Inc
    "GNRC",  # Generac Holdings
    "AGCO",  # AGCO Corporation
]

US_ENERGY = [
    # Oil, Gas & Energy
    "XOM",  # Exxon Mobil
    "CVX",  # Chevron
    "COP",  # ConocoPhillips
    "SLB",  # Schlumberger
    "EOG",  # EOG Resources
    "PXD",  # Pioneer Natural
    "MPC",  # Marathon Petroleum
    "PSX",  # Phillips 66
    "VLO",  # Valero Energy
    "OXY",  # Occidental Petroleum
    "HAL",  # Halliburton
    "BKR",  # Baker Hughes
    "DVN",  # Devon Energy
    "FANG",  # Diamondback Energy
    "HES",  # Hess Corporation
    "APA",  # APA Corporation
    "MRO",  # Marathon Oil
    "OVV",  # Ovintiv
    "CTRA",  # Coterra Energy
    "EQT",  # EQT Corporation
    "AR",  # Antero Resources
    "RRC",  # Range Resources
    "SWN",  # Southwestern Energy
    "CHK",  # Chesapeake Energy
    "WMB",  # Williams Companies
    "KMI",  # Kinder Morgan
    "ET",  # Energy Transfer
    "EPD",  # Enterprise Products
    "MPLX",  # MPLX LP
    "PAA",  # Plains All American
]

US_CLEAN_ENERGY = [
    # Renewable & Clean Energy
    "NEE",  # NextEra Energy
    "ENPH",  # Enphase Energy
    "SEDG",  # SolarEdge
    "FSLR",  # First Solar
    "RUN",  # Sunrun
    "ARRY",  # Array Technologies
    "MAXN",  # Maxeon Solar
    "JKS",  # JinkoSolar
    "CSIQ",  # Canadian Solar
    "DQ",  # Daqo New Energy
    "PLUG",  # Plug Power
    "BLDP",  # Ballard Power
    "BE",  # Bloom Energy
    "FCEL",  # FuelCell Energy
    "CHPT",  # ChargePoint
    "BLNK",  # Blink Charging
    "EVGO",  # EVgo Inc
    "LCID",  # Lucid Motors
    "RIVN",  # Rivian
    "NIO",  # NIO Inc
    "XPEV",  # XPeng
    "LI",  # Li Auto
    "TSLA",  # Tesla
    "ALB",  # Albemarle
    "SQM",  # Sociedad Quimica
    "LAC",  # Lithium Americas
]

US_UTILITIES = [
    # Utilities
    "NEE",  # NextEra Energy
    "DUK",  # Duke Energy
    "SO",  # Southern Company
    "D",  # Dominion Energy
    "AEP",  # American Electric Power
    "EXC",  # Exelon
    "XEL",  # Xcel Energy
    "SRE",  # Sempra
    "ED",  # Consolidated Edison
    "WEC",  # WEC Energy
    "ES",  # Eversource Energy
    "DTE",  # DTE Energy
    "PEG",  # Public Service Enterprise
    "EIX",  # Edison International
    "FE",  # FirstEnergy
    "PPL",  # PPL Corporation
    "CMS",  # CMS Energy
    "AEE",  # Ameren
    "LNT",  # Alliant Energy
    "EVRG",  # Evergy
    "AES",  # AES Corporation
    "NI",  # NiSource
    "NRG",  # NRG Energy
    "VST",  # Vistra Corp
    "CEG",  # Constellation Energy
    "AWK",  # American Water Works
    "WTRG",  # Essential Utilities
    "CWT",  # California Water
    "SJW",  # SJW Group
    "YORW",  # York Water
]

US_REAL_ESTATE = [
    # REITs & Real Estate
    "PLD",  # Prologis
    "AMT",  # American Tower
    "EQIX",  # Equinix
    "CCI",  # Crown Castle
    "PSA",  # Public Storage
    "DLR",  # Digital Realty
    "O",  # Realty Income
    "SPG",  # Simon Property Group
    "WELL",  # Welltower
    "AVB",  # AvalonBay Communities
    "EQR",  # Equity Residential
    "VTR",  # Ventas
    "ARE",  # Alexandria Real Estate
    "BXP",  # Boston Properties
    "SLG",  # SL Green Realty
    "VNO",  # Vornado Realty
    "KIM",  # Kimco Realty
    "REG",  # Regency Centers
    "FRT",  # Federal Realty
    "NNN",  # NNN REIT
    "STOR",  # STORE Capital
    "WPC",  # W. P. Carey
    "ADC",  # Agree Realty
    "ESS",  # Essex Property
    "MAA",  # Mid-America Apartment
    "UDR",  # UDR Inc
    "CPT",  # Camden Property
    "INVH",  # Invitation Homes
    "AMH",  # American Homes
    "EXR",  # Extra Space Storage
]

US_MATERIALS = [
    # Basic Materials & Mining
    "LIN",  # Linde
    "APD",  # Air Products
    "SHW",  # Sherwin-Williams
    "ECL",  # Ecolab
    "DD",  # DuPont
    "DOW",  # Dow Inc
    "FCX",  # Freeport-McMoRan
    "NEM",  # Newmont Mining
    "GOLD",  # Barrick Gold
    "NUE",  # Nucor
    "STLD",  # Steel Dynamics
    "CLF",  # Cleveland-Cliffs
    "X",  # United States Steel
    "AA",  # Alcoa
    "CENX",  # Century Aluminum
    "RS",  # Reliance Steel
    "CMC",  # Commercial Metals
    "ATI",  # ATI Inc
    "MLM",  # Martin Marietta
    "VMC",  # Vulcan Materials
    "CX",  # Cemex
    "SUM",  # Summit Materials
    "EXP",  # Eagle Materials
    "USLM",  # United States Lime
    "ALB",  # Albemarle
    "EMN",  # Eastman Chemical
    "CE",  # Celanese
    "HUN",  # Huntsman
    "WLK",  # Westlake Chemical
]

US_COMMUNICATION = [
    # Telecom & Media
    "VZ",  # Verizon
    "T",  # AT&T
    "TMUS",  # T-Mobile
    "CMCSA",  # Comcast
    "CHTR",  # Charter Communications
    "DIS",  # Walt Disney
    "WBD",  # Warner Bros Discovery
    "PARA",  # Paramount Global
    "NFLX",  # Netflix
    "FOX",  # Fox Corp
    "FOXA",  # Fox Corp Class A
    "NWS",  # News Corp
    "NWSA",  # News Corp Class A
    "OMC",  # Omnicom
    "IPG",  # Interpublic
    "MGNI",  # Magnite
    "ROKU",  # Roku
    "TTD",  # Trade Desk
    "PUBM",  # PubMatic
    "ZD",  # Ziff Davis
    "IAC",  # IAC Inc
    "MTCH",  # Match Group
    "ANGI",  # Angi Inc
    "VZIO",  # Vizio
    "SIRI",  # SiriusXM
    "LYV",  # Live Nation
    "MSGS",  # MSG Sports
    "MSGE",  # MSG Entertainment
    "LBRDK",  # Liberty Broadband
    "FWONK",  # Liberty Formula One
]

US_TRANSPORTATION = [
    # Transportation & Logistics
    "UNP",  # Union Pacific
    "CSX",  # CSX Corporation
    "NSC",  # Norfolk Southern
    "UPS",  # United Parcel Service
    "FDX",  # FedEx
    "EXPD",  # Expeditors
    "CHRW",  # C.H. Robinson
    "XPO",  # XPO Inc
    "JBHT",  # J.B. Hunt
    "ODFL",  # Old Dominion Freight
    "SAIA",  # Saia Inc
    "WERN",  # Werner Enterprises
    "KNX",  # Knight-Swift
    "SNDR",  # Schneider National
    "HTLD",  # Heartland Express
    "ARCB",  # ArcBest Corp
    "LSTR",  # Landstar System
    "DAL",  # Delta Air Lines
    "UAL",  # United Airlines
    "AAL",  # American Airlines
    "LUV",  # Southwest Airlines
    "ALK",  # Alaska Air
    "JBLU",  # JetBlue
    "SAVE",  # Spirit Airlines
    "HA",  # Hawaiian Holdings
    "SKYW",  # SkyWest
    "MESA",  # Mesa Air Group
    "RYAAY",  # Ryanair
    "KEX",  # Kirby Corp
    "MATX",  # Matson Inc
]

# -----------------------------------------------------------------------------
# BY INVESTMENT THEME
# -----------------------------------------------------------------------------

US_AI_ML = [
    # Artificial Intelligence & Machine Learning
    "NVDA",  # NVIDIA
    "MSFT",  # Microsoft
    "GOOGL",  # Alphabet
    "AMZN",  # Amazon
    "META",  # Meta Platforms
    "AMD",  # AMD
    "INTC",  # Intel
    "IBM",  # IBM
    "CRM",  # Salesforce
    "SNOW",  # Snowflake
    "MDB",  # MongoDB
    "DDOG",  # Datadog
    "PLTR",  # Palantir
    "AI",  # C3.ai
    "PATH",  # UiPath
    "UPST",  # Upstart
    "SOUN",  # SoundHound AI
    "BBAI",  # BigBear.ai
    "PRCT",  # PROCEPT BioRobotics
    "ISRG",  # Intuitive Surgical
    "VEEV",  # Veeva Systems
    "NOW",  # ServiceNow
    "ADBE",  # Adobe
    "INTU",  # Intuit
    "PANW",  # Palo Alto Networks
    "CRWD",  # CrowdStrike
    "ZS",  # Zscaler
    "S",  # SentinelOne
    "HUBS",  # HubSpot
    "TTD",  # Trade Desk
]

US_CYBERSECURITY = [
    # Cybersecurity
    "CRWD",  # CrowdStrike
    "PANW",  # Palo Alto Networks
    "ZS",  # Zscaler
    "FTNT",  # Fortinet
    "NET",  # Cloudflare
    "S",  # SentinelOne
    "OKTA",  # Okta
    "CYBR",  # CyberArk
    "RPD",  # Rapid7
    "TENB",  # Tenable
    "VRNS",  # Varonis
    "QLYS",  # Qualys
    "GEN",  # Gen Digital
    "CHKP",  # Check Point
    "MIME",  # Mimecast
    "FEYE",  # FireEye
    "SAIL",  # SailPoint
    "AVGO",  # Broadcom (acquired Symantec)
    "CSCO",  # Cisco
    "IBM",  # IBM Security
    "MSFT",  # Microsoft Security
    "GOOGL",  # Google Cloud Security
    "AMZN",  # AWS Security
    "AKAM",  # Akamai
    "FFIV",  # F5 Networks
    "A10",  # A10 Networks
    "RDWR",  # Radware
    "NLOK",  # NortonLifeLock
    "OSPN",  # OneSpan
]

US_CLOUD_COMPUTING = [
    # Cloud Computing & Infrastructure
    "AMZN",  # Amazon (AWS)
    "MSFT",  # Microsoft (Azure)
    "GOOGL",  # Alphabet (GCP)
    "ORCL",  # Oracle Cloud
    "IBM",  # IBM Cloud
    "CRM",  # Salesforce
    "NOW",  # ServiceNow
    "SNOW",  # Snowflake
    "DDOG",  # Datadog
    "NET",  # Cloudflare
    "MDB",  # MongoDB
    "CFLT",  # Confluent
    "ESTC",  # Elastic
    "SUMO",  # Sumo Logic
    "DT",  # Dynatrace
    "NEWR",  # New Relic
    "GTLB",  # GitLab
    "ZM",  # Zoom
    "TWLO",  # Twilio
    "FSLY",  # Fastly
    "DOCN",  # DigitalOcean
    "AYX",  # Alteryx
    "HUBS",  # HubSpot
    "SHOP",  # Shopify
    "WDAY",  # Workday
    "VEEV",  # Veeva Systems
    "TEAM",  # Atlassian
    "ADBE",  # Adobe
    "INTU",  # Intuit
]

US_SPACE_DEFENSE = [
    # Space & Defense
    "LMT",  # Lockheed Martin
    "RTX",  # RTX Corporation
    "NOC",  # Northrop Grumman
    "GD",  # General Dynamics
    "BA",  # Boeing
    "TXT",  # Textron
    "LHX",  # L3Harris Technologies
    "HWM",  # Howmet Aerospace
    "TDG",  # TransDigm
    "HEI",  # Heico Corp
    "AXON",  # Axon Enterprise
    "KTOS",  # Kratos Defense
    "PLTR",  # Palantir
    "SPCE",  # Virgin Galactic
    "RKLB",  # Rocket Lab
    "ASTR",  # Astra Space
    "RDW",  # Redwire
    "MNTS",  # Momentus
    "ASTS",  # AST SpaceMobile
    "BKSY",  # BlackSky Technology
    "PL",  # Planet Labs
    "SPIR",  # Spire Global
    "SATL",  # Satellogic
    "JOBY",  # Joby Aviation
    "LILM",  # Lilium
    "ACHR",  # Archer Aviation
    "LDOS",  # Leidos Holdings
    "BAH",  # Booz Allen Hamilton
]

US_EV_AUTONOMOUS = [
    # Electric Vehicles & Autonomous Driving
    "TSLA",  # Tesla
    "RIVN",  # Rivian
    "LCID",  # Lucid Motors
    "NIO",  # NIO Inc
    "XPEV",  # XPeng
    "LI",  # Li Auto
    "NKLA",  # Nikola
    "GOEV",  # Canoo
    "PSNY",  # Polestar
    "WKHS",  # Workhorse
    "HYLN",  # Hyliion
    "FFIE",  # Faraday Future
    "MULN",  # Mullen Automotive
    "CHPT",  # ChargePoint
    "BLNK",  # Blink Charging
    "EVGO",  # EVgo Inc
    "QCOM",  # Qualcomm (automotive)
    "MRVL",  # Marvell (automotive)
    "NVDA",  # NVIDIA (automotive AI)
    "INTC",  # Intel (Mobileye)
    "MBLY",  # Mobileye
    "LAZR",  # Luminar Technologies
    "OUST",  # Ouster
    "INVZ",  # Innoviz Technologies
    "AEVA",  # Aeva Technologies
    "VLDR",  # Velodyne Lidar
    "CPTN",  # Cepton
    "APTV",  # Aptiv
]

US_BIOTECH_GENOMICS = [
    # Biotechnology & Genomics
    "ILMN",  # Illumina
    "TMO",  # Thermo Fisher
    "DHR",  # Danaher
    "REGN",  # Regeneron
    "VRTX",  # Vertex
    "MRNA",  # Moderna
    "BNTX",  # BioNTech
    "CRSP",  # CRISPR Therapeutics
    "EDIT",  # Editas Medicine
    "NTLA",  # Intellia Therapeutics
    "BEAM",  # Beam Therapeutics
    "VERV",  # Verve Therapeutics
    "DNA",  # Ginkgo Bioworks
    "TWST",  # Twist Bioscience
    "CDNA",  # CareDx
    "GH",  # Guardant Health
    "EXAS",  # Exact Sciences
    "NTRA",  # Natera
    "NVTA",  # Invitae
    "ME",  # 23andMe
    "TXG",  # 10x Genomics
    "SEER",  # Seer
    "OLINK",  # Olink Holding
    "NUVB",  # Nuvation Bio
    "FATE",  # Fate Therapeutics
    "BLUE",  # Bluebird Bio
    "RCKT",  # Rocket Pharmaceuticals
    "SGMO",  # Sangamo Therapeutics
    "PRTX",  # Protagonist Therapeutics
    "KYMR",  # Kymera Therapeutics
]

US_QUANTUM_COMPUTING = [
    # Quantum Computing
    "IONQ",  # IonQ
    "RGTI",  # Rigetti Computing
    "ARQQ",  # Arqit Quantum
    "IBM",  # IBM (Quantum)
    "GOOGL",  # Alphabet (Quantum AI)
    "MSFT",  # Microsoft (Azure Quantum)
    "AMZN",  # Amazon (Braket)
    "HON",  # Honeywell (Quantinuum)
    "NVDA",  # NVIDIA (Quantum Simulation)
    "AMD",  # AMD
    "INTC",  # Intel
    "QUBT",  # Quantum Computing Inc
]

# -----------------------------------------------------------------------------
# ETFs BY CATEGORY
# -----------------------------------------------------------------------------

US_ETFS_BROAD_MARKET = [
    # Broad Market ETFs
    "SPY",  # SPDR S&P 500
    "VOO",  # Vanguard S&P 500
    "IVV",  # iShares Core S&P 500
    "VTI",  # Vanguard Total Stock Market
    "ITOT",  # iShares Core Total Market
    "SCHB",  # Schwab Total Stock Market
    "SPTM",  # SPDR Portfolio Total Market
    "DIA",  # SPDR Dow Jones Industrial
    "QQQ",  # Invesco QQQ Trust (Nasdaq-100)
    "QQQM",  # Invesco NASDAQ 100
    "IWM",  # iShares Russell 2000
    "IWB",  # iShares Russell 1000
    "IWV",  # iShares Russell 3000
    "VXF",  # Vanguard Extended Market
    "IJH",  # iShares Core S&P Mid-Cap
    "IJR",  # iShares Core S&P Small-Cap
    "RSP",  # Invesco S&P 500 Equal Weight
    "SPLG",  # SPDR Portfolio S&P 500
    "VV",  # Vanguard Large-Cap
    "VO",  # Vanguard Mid-Cap
    "VB",  # Vanguard Small-Cap
    "MGK",  # Vanguard Mega Cap Growth
    "MGV",  # Vanguard Mega Cap Value
    "VUG",  # Vanguard Growth
    "VTV",  # Vanguard Value
    "IWF",  # iShares Russell 1000 Growth
    "IWD",  # iShares Russell 1000 Value
    "SCHG",  # Schwab U.S. Large-Cap Growth
    "SCHV",  # Schwab U.S. Large-Cap Value
    "SCHX",  # Schwab U.S. Large-Cap
]

US_ETFS_SECTOR = [
    # Sector ETFs
    "XLK",  # Technology Select Sector
    "XLF",  # Financial Select Sector
    "XLV",  # Health Care Select Sector
    "XLE",  # Energy Select Sector
    "XLI",  # Industrial Select Sector
    "XLY",  # Consumer Discretionary
    "XLP",  # Consumer Staples
    "XLU",  # Utilities Select Sector
    "XLB",  # Materials Select Sector
    "XLRE",  # Real Estate Select Sector
    "XLC",  # Communication Services
    "VGT",  # Vanguard Information Tech
    "VFH",  # Vanguard Financials
    "VHT",  # Vanguard Health Care
    "VDE",  # Vanguard Energy
    "VIS",  # Vanguard Industrials
    "VCR",  # Vanguard Consumer Disc
    "VDC",  # Vanguard Consumer Staples
    "VPU",  # Vanguard Utilities
    "VAW",  # Vanguard Materials
    "VNQ",  # Vanguard Real Estate
    "VOX",  # Vanguard Communication
    "SMH",  # VanEck Semiconductor
    "SOXX",  # iShares Semiconductor
    "IBB",  # iShares Biotechnology
    "XBI",  # SPDR S&P Biotech
    "ARKK",  # ARK Innovation
    "ARKW",  # ARK Next Generation Internet
    "ARKG",  # ARK Genomic Revolution
    "ARKF",  # ARK Fintech Innovation
]

US_ETFS_FIXED_INCOME = [
    # Fixed Income ETFs
    "AGG",  # iShares Core U.S. Aggregate Bond
    "BND",  # Vanguard Total Bond Market
    "SCHZ",  # Schwab U.S. Aggregate Bond
    "TLT",  # iShares 20+ Year Treasury
    "IEF",  # iShares 7-10 Year Treasury
    "SHY",  # iShares 1-3 Year Treasury
    "GOVT",  # iShares U.S. Treasury Bond
    "VGIT",  # Vanguard Intermediate Treasury
    "VGLT",  # Vanguard Long-Term Treasury
    "VGSH",  # Vanguard Short-Term Treasury
    "LQD",  # iShares Investment Grade Corp
    "VCIT",  # Vanguard Intermediate Corp
    "VCSH",  # Vanguard Short-Term Corp
    "VCLT",  # Vanguard Long-Term Corp
    "HYG",  # iShares High Yield Corp
    "JNK",  # SPDR Bloomberg High Yield
    "SJNK",  # SPDR Short Term High Yield
    "EMB",  # iShares Emerging Markets Bond
    "BNDX",  # Vanguard Total Intl Bond
    "MUB",  # iShares National Muni Bond
    "TIP",  # iShares TIPS Bond
    "SCHP",  # Schwab U.S. TIPS
    "VTIP",  # Vanguard Short-Term TIPS
    "FLOT",  # iShares Floating Rate Bond
    "SHV",  # iShares Short Treasury Bond
    "BIL",  # SPDR 1-3 Month T-Bill
    "MINT",  # PIMCO Enhanced Short Maturity
    "NEAR",  # iShares Short Maturity Bond
    "BSV",  # Vanguard Short-Term Bond
    "BIV",  # Vanguard Intermediate-Term Bond
]

US_ETFS_INTERNATIONAL = [
    # International ETFs
    "VEA",  # Vanguard FTSE Developed Markets
    "VWO",  # Vanguard FTSE Emerging Markets
    "IEFA",  # iShares Core MSCI EAFE
    "IEMG",  # iShares Core MSCI Emerging
    "EFA",  # iShares MSCI EAFE
    "EEM",  # iShares MSCI Emerging Markets
    "VXUS",  # Vanguard Total International
    "IXUS",  # iShares Core MSCI Total Intl
    "VGK",  # Vanguard FTSE Europe
    "VPL",  # Vanguard FTSE Pacific
    "AAXJ",  # iShares MSCI All Country Asia ex Japan
    "FXI",  # iShares China Large-Cap
    "MCHI",  # iShares MSCI China
    "KWEB",  # KraneShares CSI China Internet
    "EWJ",  # iShares MSCI Japan
    "EWZ",  # iShares MSCI Brazil
    "EWY",  # iShares MSCI South Korea
    "INDA",  # iShares MSCI India
    "EWT",  # iShares MSCI Taiwan
    "EWG",  # iShares MSCI Germany
    "EWU",  # iShares MSCI United Kingdom
    "EWQ",  # iShares MSCI France
    "EWP",  # iShares MSCI Spain
    "EWI",  # iShares MSCI Italy
    "EWL",  # iShares MSCI Switzerland
    "EWA",  # iShares MSCI Australia
    "EWC",  # iShares MSCI Canada
    "EWW",  # iShares MSCI Mexico
    "ERUS",  # iShares MSCI Russia (suspended)
    "TUR",  # iShares MSCI Turkey
]

US_ETFS_THEMATIC = [
    # Thematic & Innovation ETFs
    "ARKK",  # ARK Innovation
    "ARKW",  # ARK Next Generation Internet
    "ARKG",  # ARK Genomic Revolution
    "ARKF",  # ARK Fintech Innovation
    "ARKQ",  # ARK Autonomous Tech & Robotics
    "BOTZ",  # Global X Robotics & AI
    "ROBO",  # ROBO Global Robotics & Automation
    "HACK",  # ETFMG Prime Cyber Security
    "BUG",  # Global X Cybersecurity
    "CIBR",  # First Trust NASDAQ Cybersecurity
    "CLOU",  # Global X Cloud Computing
    "WCLD",  # WisdomTree Cloud Computing
    "SKYY",  # First Trust Cloud Computing
    "FINX",  # Global X FinTech
    "IPAY",  # ETFMG Prime Mobile Payments
    "ICLN",  # iShares Global Clean Energy
    "QCLN",  # First Trust NASDAQ Clean Edge
    "TAN",  # Invesco Solar
    "FAN",  # First Trust Global Wind Energy
    "LIT",  # Global X Lithium & Battery
    "DRIV",  # Global X Autonomous & Electric
    "IDRV",  # iShares Self-Driving EV
    "KARS",  # KraneShares Electric Vehicles
    "ESPO",  # VanEck Video Gaming & eSports
    "HERO",  # Global X Video Games & Esports
    "SOCL",  # Global X Social Media
    "BLOK",  # Amplify Transformational Data
    "BITO",  # ProShares Bitcoin Strategy
    "GNOM",  # Global X Genomics & Biotech
    "HELX",  # Franklin Genomic Advancements
]

US_ETFS_DIVIDEND = [
    # Dividend & Income ETFs
    "VYM",  # Vanguard High Dividend Yield
    "SCHD",  # Schwab U.S. Dividend Equity
    "DVY",  # iShares Select Dividend
    "HDV",  # iShares Core High Dividend
    "SPHD",  # Invesco S&P 500 High Dividend
    "VIG",  # Vanguard Dividend Appreciation
    "DGRO",  # iShares Core Dividend Growth
    "NOBL",  # ProShares S&P 500 Dividend Aristocrats
    "SDY",  # SPDR S&P Dividend
    "DGRW",  # WisdomTree U.S. Quality Dividend Growth
    "RDVY",  # First Trust Rising Dividend
    "FDVV",  # Fidelity High Dividend
    "SPYD",  # SPDR Portfolio S&P 500 High Dividend
    "DIV",  # Global X SuperDividend
    "SRET",  # Global X SuperDividend REIT
    "DHS",  # WisdomTree High Dividend
    "DON",  # WisdomTree MidCap Dividend
    "DES",  # WisdomTree SmallCap Dividend
    "DIVI",  # Franklin U.S. Core Dividend
    "KBWD",  # Invesco KBW High Dividend Yield
    "QDIV",  # Global X S&P 500 Quality Dividend
    "LVHD",  # Franklin Low Volatility High Dividend
    "DTD",  # WisdomTree U.S. Total Dividend
    "FDL",  # First Trust Morningstar Dividend Leaders
    "PEY",  # Invesco High Yield Equity Dividend
    "REGL",  # ProShares S&P MidCap 400 Dividend
    "SMDV",  # ProShares Russell 2000 Dividend Growers
    "XSHD",  # Invesco S&P SmallCap High Dividend
    "WDIV",  # SPDR S&P Global Dividend
    "IDV",  # iShares International Select Dividend
]

# =============================================================================
# DIVERSIFIED PORTFOLIO CATEGORIES
# =============================================================================

# -----------------------------------------------------------------------------
# BALANCED PORTFOLIOS
# -----------------------------------------------------------------------------

US_PORTFOLIO_BALANCED_CONSERVATIVE = [
    # A conservative balanced portfolio: 40% equities, 60% bonds mindset
    # Focus on dividend-paying blue chips, utilities, and defensive stocks
    # Equities - Mega Cap Dividend Aristocrats
    "JNJ",  # Healthcare - Johnson & Johnson
    "PG",  # Consumer Staples - Procter & Gamble
    "KO",  # Consumer Staples - Coca-Cola
    "PEP",  # Consumer Staples - PepsiCo
    "WMT",  # Consumer Staples - Walmart
    "MCD",  # Consumer Discretionary - McDonald's
    "VZ",  # Telecom - Verizon
    "T",  # Telecom - AT&T
    # Utilities
    "NEE",  # Utilities - NextEra Energy
    "DUK",  # Utilities - Duke Energy
    "SO",  # Utilities - Southern Company
    "D",  # Utilities - Dominion Energy
    # REITs
    "O",  # REIT - Realty Income (Monthly Dividend)
    "VNQ",  # REIT ETF - Vanguard Real Estate
    # Bonds / Fixed Income ETFs
    "BND",  # Total Bond Market ETF
    "AGG",  # Aggregate Bond ETF
    "TLT",  # 20+ Year Treasury
    "VCIT",  # Intermediate Corporate Bond
    "LQD",  # Investment Grade Corporate
    "SCHD",  # Dividend Equity ETF
]

US_PORTFOLIO_BALANCED_MODERATE = [
    # Moderate balanced: 60% equities, 40% bonds mindset
    # Mix of growth and value with some income
    # Large Cap Core
    "AAPL",  # Tech - Apple
    "MSFT",  # Tech - Microsoft
    "GOOGL",  # Tech - Alphabet
    "JPM",  # Financials - JPMorgan
    "V",  # Financials - Visa
    "UNH",  # Healthcare - UnitedHealth
    "HD",  # Consumer - Home Depot
    "PG",  # Consumer Staples - P&G
    # Mid Cap Growth
    "DDOG",  # Tech - Datadog
    "CRWD",  # Cybersecurity - CrowdStrike
    # Dividend Payers
    "COST",  # Consumer - Costco
    "ABBV",  # Healthcare - AbbVie
    "MO",  # Consumer - Altria (High Yield)
    # International Exposure
    "VEA",  # Developed Markets ETF
    "VWO",  # Emerging Markets ETF
    # Fixed Income
    "BND",  # Total Bond
    "VCIT",  # Corporate Bonds
    "TIP",  # TIPS
    # Broad Market
    "VOO",  # S&P 500 ETF
    "VTV",  # Value ETF
]

US_PORTFOLIO_BALANCED_AGGRESSIVE = [
    # Aggressive balanced: 80% equities, 20% alternatives
    # Higher risk tolerance, long-term growth focus
    # Tech Leaders
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL",  # Alphabet
    "AMZN",  # Amazon
    "NVDA",  # NVIDIA
    "META",  # Meta
    # High Growth Tech
    "TSLA",  # Tesla
    "CRWD",  # CrowdStrike
    "SNOW",  # Snowflake
    "DDOG",  # Datadog
    "NET",  # Cloudflare
    # Financials Growth
    "COIN",  # Coinbase
    # Healthcare Innovation
    "LLY",  # Eli Lilly (GLP-1)
    "ISRG",  # Intuitive Surgical
    "MRNA",  # Moderna
    # Consumer Growth
    "ABNB",  # Airbnb
    "UBER",  # Uber
    # Small/Mid Cap Growth
    "PLTR",  # Palantir
    "SOFI",  # SoFi
    # Growth ETFs
    "QQQ",  # Nasdaq 100
    "VUG",  # Vanguard Growth
    "ARKK",  # ARK Innovation
]

# -----------------------------------------------------------------------------
# INCOME-FOCUSED PORTFOLIOS
# -----------------------------------------------------------------------------

US_PORTFOLIO_DIVIDEND_ARISTOCRATS = [
    # S&P 500 Dividend Aristocrats - 25+ years of dividend increases
    "JNJ",  # Healthcare
    "PG",  # Consumer Staples
    "KO",  # Beverages
    "PEP",  # Beverages
    "MMM",  # Industrials
    "ABT",  # Healthcare
    "ABBV",  # Healthcare
    "MCD",  # Restaurants
    "WMT",  # Retail
    "TGT",  # Retail
    "LOW",  # Retail
    "CL",  # Consumer Staples
    "CLX",  # Consumer Staples
    "GD",  # Defense
    "ITW",  # Industrials
    "EMR",  # Industrials
    "APD",  # Materials
    "SHW",  # Materials
    "ED",  # Utilities
    "ATO",  # Utilities
]

US_PORTFOLIO_HIGH_YIELD_INCOME = [
    # High dividend yield focus (5%+ yields)
    # REITs
    "O",  # Realty Income - 5%+
    "AGNC",  # AGNC Investment - 14%+
    "NLY",  # Annaly Capital - 13%+
    "STWD",  # Starwood Property - 9%+
    "ARCC",  # Ares Capital - 9%+
    "MAIN",  # Main Street Capital - 6%+
    # MLPs/Energy
    "ET",  # Energy Transfer - 8%+
    "EPD",  # Enterprise Products - 7%+
    "MPLX",  # MPLX LP - 8%+
    # Telecom
    "VZ",  # Verizon - 6%+
    "T",  # AT&T - 6%+
    # Tobacco
    "MO",  # Altria - 8%+
    "BTI",  # British American Tobacco - 9%+
    # BDCs
    "HTGC",  # Hercules Capital - 10%+
    "TPVG",  # TriplePoint Venture - 12%+
    # High Yield ETFs
    "JEPI",  # JPMorgan Equity Premium Income
    "JEPQ",  # JPMorgan Nasdaq Equity Premium
    "RYLD",  # Global X Russell 2000 Covered Call
    "QYLD",  # Global X Nasdaq 100 Covered Call
    "SDIV",  # Global X SuperDividend
]

US_PORTFOLIO_DIVIDEND_GROWTH = [
    # Companies with strong dividend growth rates (10%+ CAGR)
    "AVGO",  # Broadcom - 15%+ growth
    "MSFT",  # Microsoft - 10%+ growth
    "V",  # Visa - 15%+ growth
    "MA",  # Mastercard - 15%+ growth
    "HD",  # Home Depot - 15%+ growth
    "LOW",  # Lowe's - 20%+ growth
    "COST",  # Costco - 12%+ growth
    "UNH",  # UnitedHealth - 15%+ growth
    "TMO",  # Thermo Fisher - 15%+ growth
    "AAPL",  # Apple - 8%+ growth
    "TXN",  # Texas Instruments - 20%+ growth
    "QCOM",  # Qualcomm - 10%+ growth
    "LMT",  # Lockheed Martin - 8%+ growth
    "CAT",  # Caterpillar - 10%+ growth
    "SBUX",  # Starbucks - 10%+ growth
    "NKE",  # Nike - 10%+ growth
    "ADP",  # ADP - 12%+ growth
    "ACN",  # Accenture - 10%+ growth
    "SPGI",  # S&P Global - 10%+ growth
    "AMT",  # American Tower - 15%+ growth
]

# -----------------------------------------------------------------------------
# GROWTH PORTFOLIOS
# -----------------------------------------------------------------------------

US_PORTFOLIO_TECH_GROWTH = [
    # Pure technology growth portfolio
    # Mega Cap Tech
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL",  # Alphabet
    "AMZN",  # Amazon
    "NVDA",  # NVIDIA
    "META",  # Meta
    # Cloud & SaaS
    "CRM",  # Salesforce
    "NOW",  # ServiceNow
    "SNOW",  # Snowflake
    "DDOG",  # Datadog
    "MDB",  # MongoDB
    "CRWD",  # CrowdStrike
    "ZS",  # Zscaler
    "NET",  # Cloudflare
    # Semiconductors
    "AMD",  # AMD
    "AVGO",  # Broadcom
    "QCOM",  # Qualcomm
    "MRVL",  # Marvell
    "AMAT",  # Applied Materials
    "LRCX",  # Lam Research
]

US_PORTFOLIO_NEXT_GEN_TECH = [
    # Emerging technology themes - AI, quantum, robotics
    # AI Leaders
    "NVDA",  # NVIDIA - AI chips
    "MSFT",  # Microsoft - OpenAI partner
    "GOOGL",  # Google - AI research
    "META",  # Meta - AI models
    "AMD",  # AMD - AI accelerators
    "PLTR",  # Palantir - AI analytics
    "AI",  # C3.ai
    "SOUN",  # SoundHound AI
    "PATH",  # UiPath - RPA
    # Quantum Computing
    "IONQ",  # IonQ
    "RGTI",  # Rigetti Computing
    "IBM",  # IBM Quantum
    # Robotics & Automation
    "ISRG",  # Intuitive Surgical
    "ROK",  # Rockwell Automation
    "TER",  # Teradyne
    "ZBRA",  # Zebra Technologies
    # Edge Computing
    "ANET",  # Arista Networks
    "SMCI",  # Super Micro Computer
    # ETFs
    "BOTZ",  # Global X Robotics & AI
    "ROBO",  # ROBO Global Robotics
]

US_PORTFOLIO_DISRUPTIVE_INNOVATION = [
    # ARK-style disruptive innovation across sectors
    # Fintech Disruption
    "COIN",  # Coinbase
    "AFRM",  # Affirm
    "SOFI",  # SoFi
    "HOOD",  # Robinhood
    # Healthcare Disruption
    "TDOC",  # Teladoc
    "DXCM",  # DexCom
    "ILMN",  # Illumina
    "CRSP",  # CRISPR Therapeutics
    "BEAM",  # Beam Therapeutics
    # EV & Autonomous
    "TSLA",  # Tesla
    "RIVN",  # Rivian
    "LCID",  # Lucid
    "LAZR",  # Luminar Technologies
    # Space & Aerospace
    "RKLB",  # Rocket Lab
    "SPCE",  # Virgin Galactic
    "JOBY",  # Joby Aviation
    # 3D Printing
    "DDD",  # 3D Systems
    "SSYS",  # Stratasys
    # Disruptive ETF
    "ARKK",  # ARK Innovation
]

# -----------------------------------------------------------------------------
# VALUE PORTFOLIOS
# -----------------------------------------------------------------------------

US_PORTFOLIO_DEEP_VALUE = [
    # Classic value investing - low P/E, high book value
    # Financials (traditionally value)
    "BRK-B",  # Berkshire Hathaway
    "WFC",  # Wells Fargo
    "C",  # Citigroup
    "BAC",  # Bank of America
    "USB",  # US Bancorp
    # Energy (cyclical value)
    "XOM",  # Exxon Mobil
    "CVX",  # Chevron
    "COP",  # ConocoPhillips
    "SLB",  # Schlumberger
    "HAL",  # Halliburton
    # Industrials
    "GE",  # GE Aerospace
    "MMM",  # 3M
    "CAT",  # Caterpillar
    "DE",  # Deere
    # Healthcare Value
    "PFE",  # Pfizer
    "BMY",  # Bristol-Myers Squibb
    "GILD",  # Gilead
    "CVS",  # CVS Health
    # Telecom Value
    "VZ",  # Verizon
    "T",  # AT&T
    # Value ETFs
    "VTV",  # Vanguard Value
    "SCHV",  # Schwab US Large-Cap Value
]

US_PORTFOLIO_GARP = [
    # Growth at Reasonable Price - blend of growth and value
    "AAPL",  # Apple - Reasonable P/E with growth
    "MSFT",  # Microsoft - Quality at fair price
    "GOOGL",  # Alphabet - Undervalued tech
    "META",  # Meta - Value with AI upside
    "V",  # Visa - Steady compounder
    "MA",  # Mastercard - Steady compounder
    "JPM",  # JPMorgan - Quality bank
    "UNH",  # UnitedHealth - Healthcare compounder
    "LLY",  # Eli Lilly - Growth pharma
    "HD",  # Home Depot - Quality retailer
    "COST",  # Costco - Defensive growth
    "TXN",  # Texas Instruments - Quality semi
    "AVGO",  # Broadcom - Value semi with growth
    "ACN",  # Accenture - Steady IT services
    "ADP",  # ADP - Steady business services
    "SPGI",  # S&P Global - Moat business
    "MCO",  # Moody's - Duopoly
    "CME",  # CME Group - Exchange moat
    "ICE",  # Intercontinental Exchange
    "BLK",  # BlackRock - Asset management leader
]

US_PORTFOLIO_QUALITY_VALUE = [
    # High-quality companies at reasonable valuations
    "BRK-B",  # Berkshire Hathaway
    "JNJ",  # Johnson & Johnson
    "PG",  # Procter & Gamble
    "KO",  # Coca-Cola
    "PEP",  # PepsiCo
    "WMT",  # Walmart
    "COST",  # Costco
    "HD",  # Home Depot
    "TGT",  # Target
    "MCD",  # McDonald's
    "NKE",  # Nike
    "UPS",  # UPS
    "CAT",  # Caterpillar
    "HON",  # Honeywell
    "LMT",  # Lockheed Martin
    "RTX",  # RTX Corporation
    "NEE",  # NextEra Energy
    "DUK",  # Duke Energy
    "AMT",  # American Tower
    "PLD",  # Prologis
]

# -----------------------------------------------------------------------------
# SECTOR ROTATION PORTFOLIOS
# -----------------------------------------------------------------------------

US_PORTFOLIO_ECONOMIC_EXPANSION = [
    # Cyclical stocks that outperform during economic expansion
    # Consumer Discretionary
    "AMZN",  # Amazon
    "TSLA",  # Tesla
    "HD",  # Home Depot
    "NKE",  # Nike
    "SBUX",  # Starbucks
    "MCD",  # McDonald's
    # Financials
    "JPM",  # JPMorgan
    "GS",  # Goldman Sachs
    "MS",  # Morgan Stanley
    "BLK",  # BlackRock
    # Industrials
    "CAT",  # Caterpillar
    "DE",  # Deere
    "BA",  # Boeing
    "UNP",  # Union Pacific
    # Materials
    "FCX",  # Freeport-McMoRan
    "NEM",  # Newmont
    "NUE",  # Nucor
    # Technology
    "NVDA",  # NVIDIA
    "AMD",  # AMD
    "AVGO",  # Broadcom
]

US_PORTFOLIO_ECONOMIC_CONTRACTION = [
    # Defensive stocks for economic slowdown
    # Consumer Staples
    "PG",  # Procter & Gamble
    "KO",  # Coca-Cola
    "PEP",  # PepsiCo
    "WMT",  # Walmart
    "COST",  # Costco
    "CL",  # Colgate-Palmolive
    # Healthcare
    "JNJ",  # Johnson & Johnson
    "UNH",  # UnitedHealth
    "ABBV",  # AbbVie
    "PFE",  # Pfizer
    "MRK",  # Merck
    # Utilities
    "NEE",  # NextEra Energy
    "DUK",  # Duke Energy
    "SO",  # Southern Company
    "D",  # Dominion
    # Telecom
    "VZ",  # Verizon
    "T",  # AT&T
    # Bonds/Defensive
    "TLT",  # Long-term Treasury
    "BND",  # Total Bond
    "GLD",  # Gold ETF
]

US_PORTFOLIO_INFLATION_HEDGE = [
    # Assets that tend to perform well during inflation
    # Commodities & Materials
    "XOM",  # Exxon - Oil
    "CVX",  # Chevron - Oil
    "FCX",  # Freeport - Copper
    "NEM",  # Newmont - Gold miner
    "GOLD",  # Barrick Gold
    "NUE",  # Nucor - Steel
    "CF",  # CF Industries - Fertilizer
    "MOS",  # Mosaic - Fertilizer
    # Real Assets
    "PLD",  # Prologis - Logistics REIT
    "AMT",  # American Tower - Cell tower REIT
    "O",  # Realty Income - Triple net REIT
    # TIPS & Real Assets
    "TIP",  # TIPS ETF
    "DBC",  # Commodity Index ETF
    "GLD",  # Gold ETF
    "SLV",  # Silver ETF
    # Inflation Pass-through
    "COST",  # Costco - Pricing power
    "HD",  # Home Depot - Pricing power
    "WMT",  # Walmart - Scale advantage
    "BRK-B",  # Berkshire - Diversified
]

# -----------------------------------------------------------------------------
# THEMATIC PORTFOLIOS
# -----------------------------------------------------------------------------

US_PORTFOLIO_AGING_POPULATION = [
    # Companies benefiting from demographic aging trends
    # Senior Healthcare
    "UNH",  # UnitedHealth
    "HCA",  # HCA Healthcare
    "THC",  # Tenet Healthcare
    "ELV",  # Elevance Health
    "HUM",  # Humana
    "CI",  # Cigna
    # Pharma for Chronic Conditions
    "LLY",  # Eli Lilly (Diabetes/Obesity)
    "NVO",  # Novo Nordisk (Diabetes)
    "ABBV",  # AbbVie (Immunology)
    "PFE",  # Pfizer
    "JNJ",  # Johnson & Johnson
    # Medical Devices
    "MDT",  # Medtronic
    "ABT",  # Abbott
    "BSX",  # Boston Scientific
    "ZBH",  # Zimmer Biomet
    "SYK",  # Stryker
    # Senior Living REITs
    "WELL",  # Welltower
    "VTR",  # Ventas
    # Life Insurance
    "PRU",  # Prudential
    "MET",  # MetLife
]

US_PORTFOLIO_MILLENNIAL_FAVORITES = [
    # Companies popular with younger demographics
    # Social & Entertainment
    "META",  # Meta (Instagram)
    "SNAP",  # Snapchat
    "SPOT",  # Spotify
    "NFLX",  # Netflix
    "DIS",  # Disney
    "RBLX",  # Roblox
    # E-commerce & Services
    "AMZN",  # Amazon
    "ETSY",  # Etsy
    "ABNB",  # Airbnb
    "UBER",  # Uber
    "DASH",  # DoorDash
    # Fitness & Wellness
    "LULU",  # Lululemon
    "NKE",  # Nike
    "PTON",  # Peloton
    "PLNT",  # Planet Fitness
    # Fintech
    "PYPL",  # PayPal/Venmo
    "SOFI",  # SoFi
    "HOOD",  # Robinhood
    # Food & Beverage
    "SBUX",  # Starbucks
    "CMG",  # Chipotle
]

US_PORTFOLIO_INFRASTRUCTURE_SPENDING = [
    # Beneficiaries of infrastructure investment
    # Construction & Materials
    "CAT",  # Caterpillar
    "DE",  # Deere
    "VMC",  # Vulcan Materials
    "MLM",  # Martin Marietta
    "NUE",  # Nucor Steel
    "STLD",  # Steel Dynamics
    # Engineering & Construction
    "PWR",  # Quanta Services
    "EME",  # EMCOR
    "MTZ",  # MasTec
    "J",  # Jacobs Solutions
    "ACM",  # AECOM
    # Rail & Transport
    "UNP",  # Union Pacific
    "CSX",  # CSX
    "NSC",  # Norfolk Southern
    # Utilities Infrastructure
    "NEE",  # NextEra Energy
    "ETN",  # Eaton
    "EMR",  # Emerson Electric
    # 5G/Broadband Infrastructure
    "AMT",  # American Tower
    "CCI",  # Crown Castle
    "T",  # AT&T
    "VZ",  # Verizon
]

US_PORTFOLIO_RESHORING_USA = [
    # Companies benefiting from US manufacturing reshoring
    # US Manufacturers
    "CAT",  # Caterpillar
    "DE",  # Deere
    "EMR",  # Emerson
    "ROK",  # Rockwell Automation
    "TER",  # Teradyne
    # US Semiconductors
    "INTC",  # Intel (US fabs)
    "TXN",  # Texas Instruments
    "AMAT",  # Applied Materials
    "LRCX",  # Lam Research
    "KLAC",  # KLA
    # Construction
    "VMC",  # Vulcan Materials
    "MLM",  # Martin Marietta
    "BLDR",  # Builders FirstSource
    # Utilities (Industrial Power)
    "NEE",  # NextEra
    "DUK",  # Duke
    # Steel & Materials
    "NUE",  # Nucor
    "STLD",  # Steel Dynamics
    "CLF",  # Cleveland-Cliffs
    # Packaging
    "PKG",  # Packaging Corp
    "IP",  # International Paper
]

US_PORTFOLIO_WATER_SCARCITY = [
    # Water infrastructure and management
    # Water Utilities
    "AWK",  # American Water Works
    "WTRG",  # Essential Utilities
    "CWT",  # California Water
    "SJW",  # SJW Group
    # Water Technology
    "XYL",  # Xylem
    "IEX",  # IDEX Corporation
    "WTS",  # Watts Water Technologies
    "FELE",  # Franklin Electric
    # Infrastructure
    "VMC",  # Vulcan Materials (Pipes)
    "APG",  # APi Group
    # Diversified Water Exposure
    "ECL",  # Ecolab
    "DHR",  # Danaher (Water quality)
    "A",  # Agilent (Testing)
    # Water ETFs
    "PHO",  # Invesco Water Resources
    "FIW",  # First Trust Water
]

# -----------------------------------------------------------------------------
# INTERNATIONAL EXPOSURE PORTFOLIOS
# -----------------------------------------------------------------------------

US_PORTFOLIO_GLOBAL_LEADERS = [
    # ADRs and US-listed global companies
    # European ADRs
    "ASML",  # ASML (Netherlands) - Semis
    "NVO",  # Novo Nordisk (Denmark) - Pharma
    "SAP",  # SAP (Germany) - Software
    "TM",  # Toyota (Japan) - Auto
    "SONY",  # Sony (Japan) - Electronics
    "NVS",  # Novartis (Switzerland) - Pharma
    "AZN",  # AstraZeneca (UK) - Pharma
    "GSK",  # GSK (UK) - Pharma
    "UL",  # Unilever (UK) - Consumer
    "BP",  # BP (UK) - Energy
    "SHEL",  # Shell (UK) - Energy
    "RIO",  # Rio Tinto (UK) - Mining
    "BHP",  # BHP Group (Australia) - Mining
    # Asian ADRs
    "BABA",  # Alibaba (China)
    "TSM",  # TSMC (Taiwan)
    "SE",  # Sea Limited (Singapore)
    # International ETFs
    "VEA",  # Developed Markets
    "VWO",  # Emerging Markets
    "EFA",  # MSCI EAFE
    "IEMG",  # Core Emerging Markets
]

US_PORTFOLIO_EMERGING_MARKETS_GROWTH = [
    # Emerging market exposure via ADRs and ETFs
    # China
    "BABA",  # Alibaba
    "JD",  # JD.com
    "PDD",  # PDD Holdings
    "BIDU",  # Baidu
    "NIO",  # NIO
    "XPEV",  # XPeng
    "LI",  # Li Auto
    # India (Limited ADRs)
    "IBN",  # ICICI Bank
    "HDB",  # HDFC Bank
    "INFY",  # Infosys
    "WIT",  # Wipro
    # Latin America
    "NU",  # Nu Holdings (Brazil Fintech)
    "MELI",  # MercadoLibre (Argentina)
    # Taiwan/Korea
    "TSM",  # TSMC
    # Southeast Asia
    "SE",  # Sea Limited
    "GRAB",  # Grab Holdings
    # EM ETFs
    "VWO",  # Vanguard Emerging Markets
    "IEMG",  # iShares Core EM
    "EEM",  # iShares MSCI EM
]

# -----------------------------------------------------------------------------
# RISK-PARITY INSPIRED PORTFOLIOS
# -----------------------------------------------------------------------------

US_PORTFOLIO_ALL_WEATHER = [
    # Ray Dalio All-Weather inspired - balanced across economic environments
    # Stocks (30%)
    "VTI",  # Total US Stock Market
    "VEA",  # Developed International
    "VWO",  # Emerging Markets
    # Long-term Bonds (40%)
    "TLT",  # 20+ Year Treasury
    "VGLT",  # Vanguard Long-Term Treasury
    "EDV",  # Extended Duration Treasury
    # Intermediate Bonds (15%)
    "IEF",  # 7-10 Year Treasury
    "VGIT",  # Intermediate Treasury
    # Commodities (7.5%)
    "GLD",  # Gold
    "IAU",  # iShares Gold
    # TIPS (7.5%)
    "TIP",  # TIPS
    "SCHP",  # Schwab TIPS
]

US_PORTFOLIO_PERMANENT = [
    # Harry Browne Permanent Portfolio inspired - 25% each category
    # Stocks (25%)
    "VTI",  # Total US Stock Market
    "VOO",  # S&P 500
    # Long-term Bonds (25%)
    "TLT",  # 20+ Year Treasury
    "VGLT",  # Long-Term Treasury
    # Gold (25%)
    "GLD",  # Gold
    "IAU",  # iShares Gold
    # Cash/Short-term (25%)
    "SHV",  # Short Treasury
    "BIL",  # 1-3 Month T-Bill
    "SGOV",  # 0-3 Month Treasury
]

US_PORTFOLIO_GOLDEN_BUTTERFLY = [
    # Modified permanent portfolio with small cap value tilt
    # Large Cap (20%)
    "VTI",  # Total Market
    # Small Cap Value (20%)
    "VBR",  # Vanguard Small Cap Value
    "IJS",  # iShares S&P SmallCap Value
    # Long-term Bonds (20%)
    "TLT",  # 20+ Year Treasury
    # Short-term Bonds (20%)
    "SHY",  # 1-3 Year Treasury
    "VGSH",  # Short-Term Treasury
    # Gold (20%)
    "GLD",  # Gold
    "IAU",  # iShares Gold
]

# -----------------------------------------------------------------------------
# LEGACY COMBINED LIST (for backward compatibility)
# -----------------------------------------------------------------------------

US_TICKERS = list(
    set(
        US_MEGA_CAP
        + US_LARGE_CAP
        + US_MID_CAP[:40]
        + US_SMALL_CAP[:30]
        + US_TECH_SOFTWARE[:30]
        + US_TECH_SEMICONDUCTORS[:30]
        + US_FINANCIALS_BANKS[:20]
        + US_HEALTHCARE_PHARMA[:20]
        + US_CONSUMER_RETAIL[:20]
        + US_ENERGY[:20]
        + US_ETFS_BROAD_MARKET
        + US_ETFS_SECTOR
    )
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


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

    return list(set(tickers))


def get_us_tickers_by_category(category: str, limit: int = None) -> list[str]:
    """
    Get US tickers filtered by category.

    Args:
        category: Category name (see US_CATEGORIES for options)
        limit: Optional limit on number of tickers

    Returns:
        List of tickers for the specified category

    Examples:
        >>> get_us_tickers_by_category('us_tech_software', limit=10)
        ['MSFT', 'CRM', 'ADBE', ...]

        >>> get_us_tickers_by_category('us_small_cap')
        ['BIGC', 'ALKT', 'BRZE', ...]
    """
    category_map = {
        # By Market Cap
        "us_mega_cap": US_MEGA_CAP,
        "us_large_cap": US_LARGE_CAP,
        "us_mid_cap": US_MID_CAP,
        "us_small_cap": US_SMALL_CAP,
        # By Sector - Technology
        "us_tech": US_TECH_SOFTWARE + US_TECH_SEMICONDUCTORS + US_TECH_HARDWARE + US_TECH_INTERNET,
        "us_tech_software": US_TECH_SOFTWARE,
        "us_tech_semiconductors": US_TECH_SEMICONDUCTORS,
        "us_tech_hardware": US_TECH_HARDWARE,
        "us_tech_internet": US_TECH_INTERNET,
        # By Sector - Healthcare
        "us_healthcare": US_HEALTHCARE_PHARMA + US_HEALTHCARE_DEVICES,
        "us_healthcare_pharma": US_HEALTHCARE_PHARMA,
        "us_healthcare_devices": US_HEALTHCARE_DEVICES,
        # By Sector - Financials
        "us_financials": US_FINANCIALS_BANKS + US_FINANCIALS_FINTECH + US_FINANCIALS_ASSET_MGMT,
        "us_financials_banks": US_FINANCIALS_BANKS,
        "us_financials_fintech": US_FINANCIALS_FINTECH,
        "us_financials_asset_mgmt": US_FINANCIALS_ASSET_MGMT,
        # By Sector - Consumer
        "us_consumer": US_CONSUMER_RETAIL + US_CONSUMER_FOOD_BEV + US_CONSUMER_RESTAURANTS,
        "us_consumer_retail": US_CONSUMER_RETAIL,
        "us_consumer_food_bev": US_CONSUMER_FOOD_BEV,
        "us_consumer_restaurants": US_CONSUMER_RESTAURANTS,
        # By Sector - Other
        "us_industrials": US_INDUSTRIALS,
        "us_energy": US_ENERGY,
        "us_clean_energy": US_CLEAN_ENERGY,
        "us_utilities": US_UTILITIES,
        "us_real_estate": US_REAL_ESTATE,
        "us_materials": US_MATERIALS,
        "us_communication": US_COMMUNICATION,
        "us_transportation": US_TRANSPORTATION,
        # By Theme
        "us_ai_ml": US_AI_ML,
        "us_cybersecurity": US_CYBERSECURITY,
        "us_cloud_computing": US_CLOUD_COMPUTING,
        "us_space_defense": US_SPACE_DEFENSE,
        "us_ev_autonomous": US_EV_AUTONOMOUS,
        "us_biotech_genomics": US_BIOTECH_GENOMICS,
        "us_quantum_computing": US_QUANTUM_COMPUTING,
        # ETFs
        "us_etfs": US_ETFS_BROAD_MARKET
        + US_ETFS_SECTOR
        + US_ETFS_FIXED_INCOME
        + US_ETFS_INTERNATIONAL
        + US_ETFS_THEMATIC
        + US_ETFS_DIVIDEND,
        "us_etfs_broad_market": US_ETFS_BROAD_MARKET,
        "us_etfs_sector": US_ETFS_SECTOR,
        "us_etfs_fixed_income": US_ETFS_FIXED_INCOME,
        "us_etfs_international": US_ETFS_INTERNATIONAL,
        "us_etfs_thematic": US_ETFS_THEMATIC,
        "us_etfs_dividend": US_ETFS_DIVIDEND,
        # Balanced Portfolios
        "us_portfolio_balanced_conservative": US_PORTFOLIO_BALANCED_CONSERVATIVE,
        "us_portfolio_balanced_moderate": US_PORTFOLIO_BALANCED_MODERATE,
        "us_portfolio_balanced_aggressive": US_PORTFOLIO_BALANCED_AGGRESSIVE,
        # Income Portfolios
        "us_portfolio_dividend_aristocrats": US_PORTFOLIO_DIVIDEND_ARISTOCRATS,
        "us_portfolio_high_yield": US_PORTFOLIO_HIGH_YIELD_INCOME,
        "us_portfolio_dividend_growth": US_PORTFOLIO_DIVIDEND_GROWTH,
        # Growth Portfolios
        "us_portfolio_tech_growth": US_PORTFOLIO_TECH_GROWTH,
        "us_portfolio_next_gen_tech": US_PORTFOLIO_NEXT_GEN_TECH,
        "us_portfolio_disruptive": US_PORTFOLIO_DISRUPTIVE_INNOVATION,
        # Value Portfolios
        "us_portfolio_deep_value": US_PORTFOLIO_DEEP_VALUE,
        "us_portfolio_garp": US_PORTFOLIO_GARP,
        "us_portfolio_quality_value": US_PORTFOLIO_QUALITY_VALUE,
        # Economic Cycle
        "us_portfolio_expansion": US_PORTFOLIO_ECONOMIC_EXPANSION,
        "us_portfolio_contraction": US_PORTFOLIO_ECONOMIC_CONTRACTION,
        "us_portfolio_inflation_hedge": US_PORTFOLIO_INFLATION_HEDGE,
        # Thematic
        "us_portfolio_aging_population": US_PORTFOLIO_AGING_POPULATION,
        "us_portfolio_millennial": US_PORTFOLIO_MILLENNIAL_FAVORITES,
        "us_portfolio_infrastructure": US_PORTFOLIO_INFRASTRUCTURE_SPENDING,
        "us_portfolio_reshoring": US_PORTFOLIO_RESHORING_USA,
        "us_portfolio_water": US_PORTFOLIO_WATER_SCARCITY,
        # International
        "us_portfolio_global_leaders": US_PORTFOLIO_GLOBAL_LEADERS,
        "us_portfolio_emerging_markets": US_PORTFOLIO_EMERGING_MARKETS_GROWTH,
        # Risk Parity
        "us_portfolio_all_weather": US_PORTFOLIO_ALL_WEATHER,
        "us_portfolio_permanent": US_PORTFOLIO_PERMANENT,
        "us_portfolio_golden_butterfly": US_PORTFOLIO_GOLDEN_BUTTERFLY,
    }

    if category.lower() not in category_map:
        available = ", ".join(sorted(category_map.keys()))
        raise ValueError(f"Unknown category '{category}'. Available: {available}")

    tickers = category_map[category.lower()]
    if limit:
        return tickers[:limit]
    return list(set(tickers))


def get_us_categories() -> dict[str, int]:
    """Get all available US ticker categories and their counts."""
    return {
        # Market Cap
        "us_mega_cap": len(US_MEGA_CAP),
        "us_large_cap": len(US_LARGE_CAP),
        "us_mid_cap": len(US_MID_CAP),
        "us_small_cap": len(US_SMALL_CAP),
        # Technology
        "us_tech_software": len(US_TECH_SOFTWARE),
        "us_tech_semiconductors": len(US_TECH_SEMICONDUCTORS),
        "us_tech_hardware": len(US_TECH_HARDWARE),
        "us_tech_internet": len(US_TECH_INTERNET),
        # Healthcare
        "us_healthcare_pharma": len(US_HEALTHCARE_PHARMA),
        "us_healthcare_devices": len(US_HEALTHCARE_DEVICES),
        # Financials
        "us_financials_banks": len(US_FINANCIALS_BANKS),
        "us_financials_fintech": len(US_FINANCIALS_FINTECH),
        "us_financials_asset_mgmt": len(US_FINANCIALS_ASSET_MGMT),
        # Consumer
        "us_consumer_retail": len(US_CONSUMER_RETAIL),
        "us_consumer_food_bev": len(US_CONSUMER_FOOD_BEV),
        "us_consumer_restaurants": len(US_CONSUMER_RESTAURANTS),
        # Other Sectors
        "us_industrials": len(US_INDUSTRIALS),
        "us_energy": len(US_ENERGY),
        "us_clean_energy": len(US_CLEAN_ENERGY),
        "us_utilities": len(US_UTILITIES),
        "us_real_estate": len(US_REAL_ESTATE),
        "us_materials": len(US_MATERIALS),
        "us_communication": len(US_COMMUNICATION),
        "us_transportation": len(US_TRANSPORTATION),
        # Themes
        "us_ai_ml": len(US_AI_ML),
        "us_cybersecurity": len(US_CYBERSECURITY),
        "us_cloud_computing": len(US_CLOUD_COMPUTING),
        "us_space_defense": len(US_SPACE_DEFENSE),
        "us_ev_autonomous": len(US_EV_AUTONOMOUS),
        "us_biotech_genomics": len(US_BIOTECH_GENOMICS),
        "us_quantum_computing": len(US_QUANTUM_COMPUTING),
        # ETFs
        "us_etfs_broad_market": len(US_ETFS_BROAD_MARKET),
        "us_etfs_sector": len(US_ETFS_SECTOR),
        "us_etfs_fixed_income": len(US_ETFS_FIXED_INCOME),
        "us_etfs_international": len(US_ETFS_INTERNATIONAL),
        "us_etfs_thematic": len(US_ETFS_THEMATIC),
        "us_etfs_dividend": len(US_ETFS_DIVIDEND),
        # Balanced Portfolios
        "us_portfolio_balanced_conservative": len(US_PORTFOLIO_BALANCED_CONSERVATIVE),
        "us_portfolio_balanced_moderate": len(US_PORTFOLIO_BALANCED_MODERATE),
        "us_portfolio_balanced_aggressive": len(US_PORTFOLIO_BALANCED_AGGRESSIVE),
        # Income Portfolios
        "us_portfolio_dividend_aristocrats": len(US_PORTFOLIO_DIVIDEND_ARISTOCRATS),
        "us_portfolio_high_yield": len(US_PORTFOLIO_HIGH_YIELD_INCOME),
        "us_portfolio_dividend_growth": len(US_PORTFOLIO_DIVIDEND_GROWTH),
        # Growth Portfolios
        "us_portfolio_tech_growth": len(US_PORTFOLIO_TECH_GROWTH),
        "us_portfolio_next_gen_tech": len(US_PORTFOLIO_NEXT_GEN_TECH),
        "us_portfolio_disruptive": len(US_PORTFOLIO_DISRUPTIVE_INNOVATION),
        # Value Portfolios
        "us_portfolio_deep_value": len(US_PORTFOLIO_DEEP_VALUE),
        "us_portfolio_garp": len(US_PORTFOLIO_GARP),
        "us_portfolio_quality_value": len(US_PORTFOLIO_QUALITY_VALUE),
        # Economic Cycle
        "us_portfolio_expansion": len(US_PORTFOLIO_ECONOMIC_EXPANSION),
        "us_portfolio_contraction": len(US_PORTFOLIO_ECONOMIC_CONTRACTION),
        "us_portfolio_inflation_hedge": len(US_PORTFOLIO_INFLATION_HEDGE),
        # Thematic
        "us_portfolio_aging_population": len(US_PORTFOLIO_AGING_POPULATION),
        "us_portfolio_millennial": len(US_PORTFOLIO_MILLENNIAL_FAVORITES),
        "us_portfolio_infrastructure": len(US_PORTFOLIO_INFRASTRUCTURE_SPENDING),
        "us_portfolio_reshoring": len(US_PORTFOLIO_RESHORING_USA),
        "us_portfolio_water": len(US_PORTFOLIO_WATER_SCARCITY),
        # International
        "us_portfolio_global_leaders": len(US_PORTFOLIO_GLOBAL_LEADERS),
        "us_portfolio_emerging_markets": len(US_PORTFOLIO_EMERGING_MARKETS_GROWTH),
        # Risk Parity
        "us_portfolio_all_weather": len(US_PORTFOLIO_ALL_WEATHER),
        "us_portfolio_permanent": len(US_PORTFOLIO_PERMANENT),
        "us_portfolio_golden_butterfly": len(US_PORTFOLIO_GOLDEN_BUTTERFLY),
    }


def get_market_stats() -> dict:
    """Get statistics about available tickers per market."""
    us_unique = len(set(US_TICKERS))
    us_categories = get_us_categories()
    total_us_categorized = sum(us_categories.values())

    return {
        "nordic": len(NORDIC_TICKERS),
        "eu": len(EU_TICKERS),
        "us_combined": us_unique,
        "us_categorized_total": total_us_categorized,
        "us_categories": us_categories,
        "total": len(NORDIC_TICKERS) + len(EU_TICKERS) + us_unique,
    }


def get_tickers_for_analysis(
    markets: list[str] = None, categories: list[str] = None, limit_per_category: int = None
) -> list[str]:
    """
    Get a comprehensive ticker list for analysis combining markets and categories.

    Args:
        markets: List of market codes ('nordic', 'eu', 'us')
        categories: List of US category codes (e.g., 'tech_software', 'financials_banks')
        limit_per_category: Optional limit per category

    Returns:
        Deduplicated list of tickers

    Examples:
        >>> get_tickers_for_analysis(markets=['nordic'], categories=['tech_software', 'ai_ml'])
        ['AAPL.ST', ..., 'MSFT', 'CRM', 'NVDA', ...]
    """
    tickers = []

    if markets:
        tickers.extend(get_tickers_for_markets(markets))

    if categories:
        for cat in categories:
            try:
                tickers.extend(get_us_tickers_by_category(cat, limit=limit_per_category))
            except ValueError:
                print(f"Warning: Unknown category '{cat}', skipping...")

    return list(set(tickers))


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Example usage
    stats = get_market_stats()

    print("=" * 60)
    print("MARKET TICKERS DATABASE")
    print("=" * 60)

    print("\n📊 Overview:")
    print(f"  Nordic tickers: {stats['nordic']}")
    print(f"  EU tickers: {stats['eu']}")
    print(f"  US tickers (combined): {stats['us_combined']}")
    print(f"  Total unique: {stats['total']}")

    print("\n🇺🇸 US Categories:")
    categories = stats["us_categories"]

    # Group by type
    print("\n  Market Cap:")
    for cat in ["us_mega_cap", "us_large_cap", "us_mid_cap", "us_small_cap"]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Technology:")
    for cat in [
        "us_tech_software",
        "us_tech_semiconductors",
        "us_tech_hardware",
        "us_tech_internet",
    ]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Healthcare:")
    for cat in ["us_healthcare_pharma", "us_healthcare_devices"]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Financials:")
    for cat in ["us_financials_banks", "us_financials_fintech", "us_financials_asset_mgmt"]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Themes:")
    for cat in [
        "us_ai_ml",
        "us_cybersecurity",
        "us_cloud_computing",
        "us_ev_autonomous",
        "us_biotech_genomics",
    ]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  ETFs:")
    for cat in ["us_etfs_broad_market", "us_etfs_sector", "us_etfs_dividend", "us_etfs_thematic"]:
        print(f"    {cat}: {categories[cat]}")

    print("\n💼 Portfolio Categories:")

    print("\n  Balanced Portfolios:")
    for cat in [
        "us_portfolio_balanced_conservative",
        "us_portfolio_balanced_moderate",
        "us_portfolio_balanced_aggressive",
    ]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Income Portfolios:")
    for cat in [
        "us_portfolio_dividend_aristocrats",
        "us_portfolio_high_yield",
        "us_portfolio_dividend_growth",
    ]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Growth Portfolios:")
    for cat in [
        "us_portfolio_tech_growth",
        "us_portfolio_next_gen_tech",
        "us_portfolio_disruptive",
    ]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Value Portfolios:")
    for cat in ["us_portfolio_deep_value", "us_portfolio_garp", "us_portfolio_quality_value"]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Economic Cycle:")
    for cat in [
        "us_portfolio_expansion",
        "us_portfolio_contraction",
        "us_portfolio_inflation_hedge",
    ]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Thematic:")
    for cat in [
        "us_portfolio_aging_population",
        "us_portfolio_millennial",
        "us_portfolio_infrastructure",
        "us_portfolio_reshoring",
        "us_portfolio_water",
    ]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  International:")
    for cat in ["us_portfolio_global_leaders", "us_portfolio_emerging_markets"]:
        print(f"    {cat}: {categories[cat]}")

    print("\n  Risk Parity:")
    for cat in [
        "us_portfolio_all_weather",
        "us_portfolio_permanent",
        "us_portfolio_golden_butterfly",
    ]:
        print(f"    {cat}: {categories[cat]}")

    # Example queries
    print("\n" + "=" * 60)
    print("EXAMPLE QUERIES")
    print("=" * 60)

    print("\n🔍 Top 5 AI/ML tickers:")
    ai_tickers = get_us_tickers_by_category("us_ai_ml", limit=5)
    print(f"   {ai_tickers}")

    print("\n🔍 Top 5 Small Cap tickers:")
    small_caps = get_us_tickers_by_category("us_small_cap", limit=5)
    print(f"   {small_caps}")

    print("\n🔍 Balanced Conservative Portfolio:")
    conservative = get_us_tickers_by_category("us_portfolio_balanced_conservative")
    print(f"   Total: {len(conservative)} tickers")
    print(f"   Sample: {conservative[:5]}")

    print("\n🔍 Combined analysis (Nordic + US Tech):")
    combined = get_tickers_for_analysis(
        markets=["nordic"], categories=["us_tech_software"], limit_per_category=5
    )
    print(f"   Total: {len(combined)} tickers")
    print(f"   Sample: {combined[:10]}")
