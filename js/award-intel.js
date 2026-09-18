/**
 * TenderPulse 4IR - Historical Contract Award & Competitor Intelligence ("Who Won?")
 * Deltek GovWin / Stotles tier intelligence for Bangladesh Public Procurement.
 */

class AwardIntelligenceManager {
  constructor() {
    this.awards = [];
    this.init();
  }

  init() {
    // Seed historical awards
    this.awards = [
      {
        awardId: "AWD-982104",
        tenderId: "982104",
        refNo: "RHD/DHK/2025/W-401",
        title: "Construction of 4-Lane Pre-Stressed Girder Bridge over Shitalakshya River with Approach Road",
        agency: "Roads and Highways Department (RHD)",
        district: "Gazipur",
        division: "Dhaka",
        category: "Civil Construction",
        stdType: "e-PW3",
        officialEstimate: 485000000,
        awardedAmount: 437227500,
        discountPercent: -9.85,
        awardDate: "2026-02-14",
        winner: {
          companyName: "Eastern Engineering & Consortium Ltd.",
          cptuId: "BDR-90142",
          leadEngineer: "Engr. Tanvir Ahmed, FIEB",
          score: 98.4
        },
        competitors: [
          {
            companyName: "Bengal MegaStructures Ltd.",
            bidAmount: 441350000,
            discount: -9.00,
            status: "Technically Responsive (2nd Lowest)",
            disqualificationReason: "Price variance: Higher bid price than lowest responsive bidder."
          },
          {
            companyName: "Apex InfraTech Solutions Ltd.",
            bidAmount: 421950000,
            discount: -13.00,
            status: "NON-RESPONSIVE (DISQUALIFIED)",
            disqualificationReason: "Breached CPTU PPR-2008 Rule 98 10% Rate Cap; bid exceeded -10% discount and rejected as Abnormally Low Tender (ALT)."
          },
          {
            companyName: "Padma Builders & Trading Co.",
            bidAmount: 448625000,
            discount: -7.50,
            status: "NON-RESPONSIVE (DISQUALIFIED)",
            disqualificationReason: "Failed Form e-PW3-3A Turnover: Peak annual turnover demonstrated was BDT 28 Cr vs mandatory BDT 35 Cr."
          }
        ]
      },
      {
        awardId: "AWD-979402",
        tenderId: "979402",
        refNo: "LGED/SYL/2025/RD-88",
        title: "Widening and Asphalt Overlay Improvement of Golapganj-Beanibazar Upazila Connecting Road",
        agency: "Local Government Engineering Department (LGED)",
        district: "Sylhet",
        division: "Sylhet",
        category: "Road Infrastructure",
        stdType: "e-PW2A",
        officialEstimate: 125000000,
        awardedAmount: 112625000,
        discountPercent: -9.90,
        awardDate: "2026-01-28",
        winner: {
          companyName: "Surma Infrastructure Development Ltd.",
          cptuId: "BDR-78192",
          leadEngineer: "Engr. K. M. Hossain",
          score: 99.0
        },
        competitors: [
          {
            companyName: "Green Valley Construction Ltd.",
            bidAmount: 112875000,
            discount: -9.70,
            status: "Technically Responsive (2nd Lowest)",
            disqualificationReason: "Evaluated 2nd lowest tenderer by margin of BDT 2.50 Lakh."
          },
          {
            companyName: "Sylhet Highway Builders",
            bidAmount: 110000000,
            discount: -12.00,
            status: "NON-RESPONSIVE (DISQUALIFIED)",
            disqualificationReason: "Exceeded -10% maximum permissible discount cap under LGED procurement regulations."
          }
        ]
      },
      {
        awardId: "AWD-975109",
        tenderId: "975109",
        refNo: "PWD/RAJ/2025/BLD-12",
        title: "Construction of 10-Storied District Judicial Court Complex with Central HVAC and Solar Rooftop",
        agency: "Public Works Department (PWD)",
        district: "Rajshahi",
        division: "Rajshahi",
        category: "Building Construction",
        stdType: "e-PW3",
        officialEstimate: 310000000,
        awardedAmount: 292020000,
        discountPercent: -5.80,
        awardDate: "2025-12-19",
        winner: {
          companyName: "National Builders & Engineers Consortium",
          cptuId: "BDR-44201",
          leadEngineer: "Engr. Rezaul Karim",
          score: 97.8
        },
        competitors: [
          {
            companyName: "Prime Infrastructure Ltd.",
            bidAmount: 296050000,
            discount: -4.50,
            status: "Technically Responsive",
            disqualificationReason: "Evaluated higher than lowest responsive bidder."
          },
          {
            companyName: "Barendra Construction Co.",
            bidAmount: 288300000,
            discount: -7.00,
            status: "NON-RESPONSIVE (DISQUALIFIED)",
            disqualificationReason: "Failed Form e-PW2A-8: Bank credit line commitment letter was conditional and lacked SWIFT verification."
          }
        ]
      },
      {
        awardId: "AWD-971044",
        tenderId: "971044",
        refNo: "BWDB/KHL/2025/DR-99",
        title: "Emergency Riverbank Revetment with Geo-Textile Bags and CC Blocks along Rupsha River",
        agency: "Bangladesh Water Development Board (BWDB)",
        district: "Khulna",
        division: "Khulna",
        category: "Civil Construction",
        stdType: "e-PW3",
        officialEstimate: 220000000,
        awardedAmount: 204600000,
        discountPercent: -7.00,
        awardDate: "2025-11-04",
        winner: {
          companyName: "Delta Hydro-Tech Dredging Ltd.",
          cptuId: "BDR-65011",
          leadEngineer: "Engr. S. M. Faruq",
          score: 96.5
        },
        competitors: [
          {
            companyName: "Khulna Marine Infra",
            bidAmount: 206800000,
            discount: -6.00,
            status: "Technically Responsive",
            disqualificationReason: "Price variance."
          },
          {
            companyName: "Sundarbans Coastal Works",
            bidAmount: 200200000,
            discount: -9.00,
            status: "NON-RESPONSIVE (DISQUALIFIED)",
            disqualificationReason: "Failed equipment schedule: Did not possess mandatory 2 hydraulic long-boom excavators."
          }
        ]
      }
    ];
  }

  getAwards(filters = {}) {
    return this.awards.filter(item => {
      if (filters.agency && filters.agency !== "All" && item.agency !== filters.agency) return false;
      if (filters.district && filters.district !== "All" && item.district !== filters.district) return false;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        const matchTitle = item.title.toLowerCase().includes(q);
        const matchWinner = item.winner.companyName.toLowerCase().includes(q);
        const matchId = item.tenderId.includes(q);
        if (!matchTitle && !matchWinner && !matchId) return false;
      }
      return true;
    });
  }

  getTopCompetitors() {
    return [
      {
        name: "Eastern Engineering & Consortium Ltd.",
        grade: "1st Class Super-Special Enlisted",
        totalWins: 34,
        totalValueWon: 1420000000, // 142 Cr
        avgDiscount: -9.80,
        dominantAgencies: "RHD, BWDB",
        topDistricts: "Dhaka, Gazipur, Chattogram",
        disqualificationRate: 4.2
      },
      {
        name: "Surma Infrastructure Development Ltd.",
        grade: "1st Class Enlisted",
        totalWins: 22,
        totalValueWon: 580000000, // 58 Cr
        avgDiscount: -9.90,
        dominantAgencies: "LGED, RHD",
        topDistricts: "Sylhet, Sunamganj, Moulvibazar",
        disqualificationRate: 2.1
      },
      {
        name: "National Builders & Engineers Consortium",
        grade: "Special Class PWD",
        totalWins: 19,
        totalValueWon: 890000000, // 89 Cr
        avgDiscount: -5.60,
        dominantAgencies: "PWD, EED",
        topDistricts: "Rajshahi, Dhaka, Rangpur",
        disqualificationRate: 6.8
      },
      {
        name: "Delta Hydro-Tech Dredging Ltd.",
        grade: "Special Class BWDB",
        totalWins: 15,
        totalValueWon: 740000000, // 74 Cr
        avgDiscount: -7.10,
        dominantAgencies: "BWDB, BIWTA",
        topDistricts: "Khulna, Barishal, Chandpur",
        disqualificationRate: 5.0
      }
    ];
  }

  getDisqualificationStats() {
    return {
      rateCapExceeded: 41,     // 41% of rejections: bid > -10% below estimate
      turnoverDeficit: 28,     // 28%: failed Form e-PW3-3A
      creditLineDeficit: 18,   // 18%: invalid/conditional bank letter (e-PW2A-8)
      machineryMissing: 13     // 13%: failed equipment ownership schedule
    };
  }
}

// Global Singleton
window.awardIntel = new AwardIntelligenceManager();
