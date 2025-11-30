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
    "SMAR",  # Smartsheet
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
    "BLDE",  # Blade Air Mobility
    "SPCE",  # Virgin Galactic
    "RKLB",  # Rocket Lab
    "ASTR",  # Astra Space
    "RDW",  # Redwire
    "MNTS",  # Momentus
    "ASTS",  # AST SpaceMobile
    "BKSY",  # BlackSky Technology
    "SATL",  # Satellogic
    "PL",  # Planet Labs
    "LLAP",  # Terran Orbital
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
    "SPLK",  # Splunk
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
    "SMAR",  # Smartsheet
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
    "SQ",  # Block (Square)
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
    "SGEN",  # Seagen
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
    "SQ",  # Block (Square)
    "COIN",  # Coinbase
    "AFRM",  # Affirm
    "UPST",  # Upstart
    "SOFI",  # SoFi Technologies
    "HOOD",  # Robinhood
    "AXP",  # American Express
    "DFS",  # Discover Financial
    "COF",  # Capital One
    "SYF",  # Synchrony Financial
    "ALLY",  # Ally Financial
    "GPN",  # Global Payments
    "FIS",  # Fidelity National
    "FISV",  # Fiserv
    "FLT",  # Fleetcor
    "WEX",  # WEX Inc
    "FOUR",  # Shift4 Payments
    "TOST",  # Toast
    "MQ",  # Marqeta
    "PAYO",  # Payoneer
    "RELY",  # Remitly Global
    "BILL",  # Bill Holdings
    "NVEI",  # Nuvei Corporation
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
    "NOVA",  # Sunnova Energy
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
    "LEV",  # Lion Electric
    "FSR",  # Fisker
    "LCID",  # Lucid Motors
    "RIVN",  # Rivian
    "NIO",  # NIO Inc
    "XPEV",  # XPeng
    "LI",  # Li Auto
    "TSLA",  # Tesla
    "ALB",  # Albemarle
    "SQM",  # Sociedad Quimica
    "LAC",  # Lithium Americas
    "LTHM",  # Livent
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
    "LTHM",  # Livent
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
    "SPLK",  # Splunk
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
    "SQ",  # Block
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
    "LLAP",  # Terran Orbital
    "SPIR",  # Spire Global
    "SATL",  # Satellogic
    "JOBY",  # Joby Aviation
    "LILM",  # Lilium
    "ACHR",  # Archer Aviation
    "BLDE",  # Blade Air Mobility
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
    "FSR",  # Fisker
    "NKLA",  # Nikola
    "GOEV",  # Canoo
    "PSNY",  # Polestar
    "WKHS",  # Workhorse
    "HYLN",  # Hyliion
    "LEV",  # Lion Electric
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

    print("\n🔍 Combined analysis (Nordic + US Tech):")
    combined = get_tickers_for_analysis(
        markets=["nordic"], categories=["us_tech_software"], limit_per_category=5
    )
    print(f"   Total: {len(combined)} tickers")
    print(f"   Sample: {combined[:10]}")
