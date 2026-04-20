import os

# Path to your secrets env file
SECRETS_ENV_PATH = os.path.expanduser('/Users/sharayu/CodeLab/Local Secrets/secrets.local.env')

# Base directory for this project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory to store page snapshots
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")

# Directory for logs
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Directory to store per-page JSON history files
HISTORY_DIR = os.path.join(BASE_DIR, "history")

# URLs to monitor with friendly names
MONITORED_PAGES = [
    {
        "company": "OtterBox",
        "name": "OtterBox Terms of Use",
        "url": "https://www.otterbox.com/en-us/terms-of-use.html",
    },
    {
        "company": "47Brand",
        "name": "47Brand Rewards Terms and Conditions",
        "url": "https://www.47brand.com/pages/47-brand-rewards-terms-and-conditions",
    },
    {
        "company": "47Brand",
        "name": "47Brand Terms and Conditions",
        "url": "https://www.47brand.com/pages/terms-conditions-47brand-com",
    },
    {
        "company": "DoorDash",
        "name": "DoorDash Consumer Terms and Conditions",
        "url": "https://help.doordash.com/legal/document?type=cx-terms-and-conditions&region=US&locale=en-US",
    },
    {
        "company": "DoorDash",
        "name": "DoorDash Consumer Terms and Conditions US English Section 12-14",
        "url": "https://help.doordash.com/dashers/s/news/consumer-terms-and-conditions-us-english-section-12-14-MCB5IXJMLM2RDULADEXG3OFNGWMA",
    },
    {
        "company": "DoorDash",
        "name": "DoorDash Consumer Terms and Conditions AU English",
        "url": "https://help.doordash.com/dashers/s/news/consumer-terms-and-conditions-au-english-MCHRSFWWK4TFBJHCOTRE2QVVCN2I?language=de",
    },
    {
        "company": "DoorDash",
        "name": "DoorDash Promotional Terms and Conditions English",
        "url": "https://help.doordash.com/consumers/s/promotional-terms-and-conditions-english?language=en_US&ctry=IN&divcode=MH",
    },
    {
        "company": "Royal Caribbean",
        "name": "Royal Caribbean Promotions Terms and Conditions",
        "url": "https://www.royalcaribbean.com/terms-and-conditions/promotions",
    },
    {
        "company": "Royal Caribbean",
        "name": "Royal Caribbean UAE Terms and Conditions",
        "url": "https://www.royalcaribbean.ae/terms-and-conditions/",
    },
    {
        "company": "Royal Caribbean",
        "name": "Royal Caribbean UK Terms and Conditions",
        "url": "https://www.royalcaribbean.com/gbr/en/terms-and-conditions.co.uk?country=GBR",
    },
    {
        "company": "Paperless Post",
        "name": "Paperless Post Party Shop Terms and Conditions",
        "url": "https://partyshop.paperlesspost.com/pages/terms-conditions",
    },
    {
        "company": "Carhartt",
        "name": "Carhartt Terms and Conditions",
        "url": "https://www.carhartt.com/terms-conditions",
    },
    {
        "company": "Carhartt",
        "name": "Carhartt WIP US Terms",
        "url": "https://us.carhartt-wip.com/en-us/terms",
    },
    {
        "company": "Carhartt",
        "name": "Carhartt WIP DE Terms",
        "url": "https://www.carhartt-wip.com/en-de/i/terms?srsltid=AfmBOopT5OKdNNxy7LmKCduP3dzn6PBKj0oDMtqhb7bfGIt_LDebrOrl",
    },
    {
        "company": "Carhartt",
        "name": "Carhartt Company Gear Terms and Conditions",
        "url": "https://companygear.carhartt.com/terms-and-conditions/",
    },
    {
        "company": "Yahoo",
        "name": "Yahoo Terms of Service",
        "url": "https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html",
    },
    {
        "company": "Yahoo",
        "name": "Yahoo Advertising Terms",
        "url": "https://legal.yahoo.com/us/en/yahoo/terms/advertising-322/index.html",
    },
    {
        "company": "eBay",
        "name": "eBay Coded Coupons Buyer Terms",
        "url": "https://pages.ebay.com/specialoffers/codedcoupons_buyerterms.html",
    },
    {
        "company": "eBay",
        "name": "eBay Social Sharing Terms",
        "url": "https://pages.ebay.com/social/sharing/terms.html",
    },
    {
        "company": "eBay",
        "name": "eBay International Shipping Program Buyer Terms",
        "url": "https://pages.ebay.com/internationalshippingprogram/buyer/terms/",
    },
    {
        "company": "Discord",
        "name": "Discord Terms",
        "url": "https://discord.com/terms",
    },
    {
        "company": "Activision",
        "name": "Activision Terms of Use",
        "url": "https://www.activision.com/legal/terms-of-use",
    },
    {
        "company": "Formula 1",
        "name": "Formula 1 Official F1 Race Guide App Terms and Conditions",
        "url": "https://www.formula1.com/en/information/official-f1-race-guide-app-terms-and-conditions.6vXQ9RT3vCLLDDeyRSUPe7",
    },
    {
        "company": "Nintendo",
        "name": "Nintendo US Terms of Use",
        "url": "https://www.nintendo.com/us/terms-of-use/",
    },
    {
        "company": "Nintendo",
        "name": "Nintendo US Purchase Terms",
        "url": "https://www.nintendo.com/us/purchase-terms/",
    },
    {
        "company": "Nintendo",
        "name": "Nintendo UK Terms of Service",
        "url": "https://www.nintendo.com/en-gb/Legal-information/Terms-of-service-570453.html",
    },
    {
        "company": "Nintendo",
        "name": "Nintendo Canada Gift Card Terms",
        "url": "https://www.nintendo.com/en-ca/giftcards/terms/",
    },
    {
        "company": "Redfin",
        "name": "Redfin Terms of Use",
        "url": "https://www.redfin.com/about/terms-of-use",
    },
    {
        "company": "Redfin",
        "name": "Redfin Terms and Conditions",
        "url": "https://support.redfin.com/hc/en-us/articles/360001454551-Terms-and-Conditions",
    },
    {
        "company": "Hoopla",
        "name": "Hoopla Terms",
        "url": "https://www.hoopladigital.com/terms",
    },
    {
        "company": "Hoopla",
        "name": "Hoopla Audiobook Terms and Conditions Lauren Asher",
        "url": "https://www.hoopladigital.com/audiobook/terms-and-conditions-lauren-asher/15210357",
    },
    {
        "company": "Hoopla",
        "name": "Hoopla UK Terms of Use",
        "url": "https://hoopladigital.co.uk/terms-of-use/",
    },
    {
        "company": "305 Fitness",
        "name": "305 Fitness Terms of Service",
        "url": "https://www.305fitness.com/terms-of-service",
    },
    {
        "company": "Bandai Namco",
        "name": "Bandai Namco Terms",
        "url": "https://www.bandainamcoent.com/legal/terms",
    },
    {
        "company": "Baseball America",
        "name": "Baseball America Terms of Use",
        "url": "https://www.baseballamerica.com/terms-of-use/",
    },
    {
        "company": "Birds and Blooms",
        "name": "Birds and Blooms Hidden Object Official Rules",
        "url": "https://www.birdsandblooms.com/birds-blooms-hidden-object-official-rules/",
    },
    {
        "company": "CorePower Yoga",
        "name": "CorePower Yoga Terms of Use",
        "url": "https://www.corepoweryoga.com/content/terms-use",
    },
    {
        "company": "CorePower Yoga",
        "name": "CorePower Yoga Student Terms and Conditions",
        "url": "https://www.corepoweryoga.com/content/student-terms-conditions",
    },
    {
        "company": "Criterion",
        "name": "Criterion Terms",
        "url": "https://www.criterion.com/terms?srsltid=AfmBOoqHIf_tHIBfLgXJCw-OBaUsLcBm5suDfiCDBavrhMIeTHWQU6OF",
    },
    {
        "company": "Criterion",
        "name": "Criterion Channel Terms of Service",
        "url": "https://www.criterionchannel.com/tos",
    },
    {
        "company": "DKOldies",
        "name": "DKOldies Terms and Conditions",
        "url": "https://www.dkoldies.com/terms-and-conditions/",
    },
    {
        "company": "Electronic Arts",
        "name": "EA User Agreement",
        "url": "https://www.ea.com/legal/user-agreement",
    },
    {
        "company": "Electronic Arts",
        "name": "EA Terms of Sale",
        "url": "https://www.ea.com/legal/terms-of-sale",
    },
    {
        "company": "Electronic Arts",
        "name": "EA Play Terms",
        "url": "https://www.ea.com/legal/ea-play-terms",
    },
    {
        "company": "Game Over Videogames",
        "name": "Game Over Videogames Terms of Use",
        "url": "https://gameovergames.com/terms-of-use/",
    },
    {
        "company": "GameFly",
        "name": "GameFly Terms of Use",
        "url": "https://www.gamefly.com/terms-of-use?srsltid=AfmBOopNrKpQyLUcGwbRwLj6xJ6vsCLufM2Qm_TNO5nMNWmR7r5RbvQY",
    },
    {
        "company": "Google Assistant",
        "name": "Google Assistant Community Terms",
        "url": "https://developers.google.com/assistant/community/terms",
    },
    {
        "company": "Google Assistant",
        "name": "Google Assistant Product Terms",
        "url": "https://transparency.google/intl/en/our-policies/product-terms/google-assistant/",
    },
    {
        "company": "iam8bit",
        "name": "iam8bit Terms Conditions Policy",
        "url": "https://www.iam8bit.com/pages/terms-conditions-policy",
    },
    {
        "company": "iam8bit",
        "name": "iam8bit Policies",
        "url": "https://www.iam8bit.com/pages/policies",
    },
    {
        "company": "iam8bit",
        "name": "iam8bit Privacy Policy",
        "url": "https://www.iam8bit.com/pages/privacy-policy",
    },
    {
        "company": "Kick",
        "name": "Kick Terms of Service",
        "url": "https://kick.com/terms-of-service",
    },
    {
        "company": "Kick",
        "name": "Kick Partner Terms and Conditions",
        "url": "https://kick.com/partner-terms-and-conditions",
    },
    {
        "company": "Microsoft/Xbox",
        "name": "Xbox Subscription Terms",
        "url": "https://www.xbox.com/en-IN/legal/subscription-terms",
    },
    {
        "company": "Microsoft/Xbox",
        "name": "Xbox Web Purchase Terms",
        "url": "https://www.xbox.com/en-US/legal/web-purchase",
    },
    {
        "company": "PGA TOUR",
        "name": "PGA TOUR Tickets and Merchandise Terms and Conditions",
        "url": "https://www.pgatour.com/company/terms-conditions-tickets-and-merchandise",
    },
    {
        "company": "PGA TOUR",
        "name": "PGA TOUR Terms of Use",
        "url": "https://www.pgatour.com/company/terms-of-use",
    },
    {
        "company": "Pvolve",
        "name": "Pvolve Terms of Service",
        "url": "https://www.pvolve.com/policies/terms-of-service?srsltid=AfmBOoqMxgGLW17FSojeSIBgMvuQApDx-G0oX10TWbOGLJ-XtagqbxH2",
    },
    {
        "company": "Pvolve",
        "name": "Pvolve Terms of Service Page 2",
        "url": "https://www.pvolve.com/policies/terms-of-service?page=2&srsltid=AfmBOora5D6RkYgBsrQzHBqTr0DdaxYGlPgiSm77Nipr3y4v8rvpEHuK",
    },
    {
        "company": "Pvolve",
        "name": "Pvolve Ultimate Giveaway 2025 Terms and Conditions",
        "url": "https://www.pvolve.com/pages/terms-conditions-ultimate-giveaway-2025?srsltid=AfmBOorXYZAWGpkB85_Cmz6VuPZ7b5YnyImKsRyiHp7c5MGcRQrUnOsp",
    },
    {
        "company": "Quince",
        "name": "Quince Privacy Policy",
        "url": "https://www.quince.com/privacy-policy?srsltid=AfmBOorDGXgSLYQALnnpy2FCZsaA5J8pzdUK74zfteFSaQZMpnpJgvd0",
    },
    {
        "company": "Quince",
        "name": "Quince Terms",
        "url": "https://www.quince.com/terms?srsltid=AfmBOopmxy-iYsOpaSa17WxlmBwrvPClfouahF7_qgwm6ElqSLk6DcyH",
    },
    {
        "company": "Reader's Digest",
        "name": "Reader's Digest Terms of Use",
        "url": "https://www.readersdigest.in/terms-of-use",
    },
    {
        "company": "Reader's Digest",
        "name": "Reader's Digest Gift Rules",
        "url": "https://subscription.readersdigest.in/rdindia/giftedm/s100rules.html",
    },
    {
        "company": "SiriusXM",
        "name": "SiriusXM Media Terms",
        "url": "https://www.siriusxmmedia.com/terms",
    },
    {
        "company": "SiriusXM",
        "name": "SiriusXM Customer Agreement",
        "url": "https://www.siriusxm.com/customer-agreement",
    },
    {
        "company": "Starz",
        "name": "Starz Terms of Use",
        "url": "https://www.starz.com/us/en/termsofuse",
    },
    {
        "company": "Starz",
        "name": "Starz SPI Terms Web BR EN",
        "url": "https://resources.starz.com/legal/spi-terms-web-br-en.html",
    },
    {
        "company": "Starz",
        "name": "Starz SPI Terms Web FI EN",
        "url": "https://resources.starz.com/legal/spi-terms-web-fi-en.html",
    },
    {
        "company": "TaxAct",
        "name": "TaxAct Terms of Service",
        "url": "https://www.taxact.com/terms-of-service",
    },
    {
        "company": "TaxAct",
        "name": "TaxAct Terms of Service Printable",
        "url": "https://www.taxact.com/terms-of-service/printable",
    },
    {
        "company": "TaxAct",
        "name": "TaxAct Free File Terms of Service",
        "url": "https://www.taxact.com/ffa/free-file/terms-of-service",
    },
    {
        "company": "TaxAct",
        "name": "TaxAct VITA Terms of Service",
        "url": "https://www.taxact.com/ffa/vita/terms-of-service",
    },
    {
        "company": "TaxAct",
        "name": "TaxAct Refer Terms",
        "url": "https://refer.taxact.com/zone/terms?campaign_id=6766300849289157074",
    },
]
