/**
 * CPTU / e-GP Tender Capacity & Joint Venture (JV) Engine
 * Implements the official Bangladesh PPR-2008 Capacity Equation:
 * Assessed Tender Capacity = (A * N * 1.5) - B
 */

class TenderCapacityEngine {
  constructor() {
    this.defaultParams = {
      turnoverA: 250000000,    // A = BDT 25 Crore (Peak annual turnover)
      durationMonths: 18,     // N = 1.5 years
      commitmentB: 120000000, // B = BDT 12 Crore (Existing ongoing contracts)
      tenderCost: 320000000,  // Target tender cost: BDT 32 Crore
      availableLiquidAssets: 45000000, // Cash / Bank Credit Line
      liquidAssetReq: 65000000         // Required Liquid Assets
    };
  }

  calculateCapacity(params = {}) {
    const config = { ...this.defaultParams, ...params };

    const A = Number(config.turnoverA) || 0;
    const N = (Number(config.durationMonths) || 12) / 12; // convert months to years
    const B = Number(config.commitmentB) || 0;
    const tenderCost = Number(config.tenderCost) || 0;
    const liquidAssets = Number(config.availableLiquidAssets) || 0;
    const liquidReq = Number(config.liquidAssetReq) || 0;

    // Official CPTU formula
    const grossPotential = A * N * 1.5;
    const assessedCapacity = grossPotential - B;
    const capacityDifference = assessedCapacity - tenderCost;
    const isCapacityEligible = assessedCapacity >= tenderCost;

    // Liquid asset check
    const isLiquidEligible = liquidAssets >= liquidReq;
    const liquidDifference = liquidAssets - liquidReq;

    // Overall qualification status
    let status = "PASS";
    let statusColor = "green";
    let summaryText = "";

    if (isCapacityEligible && isLiquidEligible) {
      status = "FULLY_QUALIFIED";
      statusColor = "emerald";
      summaryText = `Eligible to bid independently. Your assessed capacity exceeds tender value by BDT ${(capacityDifference / 10000000).toFixed(2)} Crore.`;
    } else if (!isCapacityEligible && isLiquidEligible) {
      status = "CAPACITY_DEFICIT";
      statusColor = "amber";
      summaryText = `Tender Capacity Deficit of BDT ${Math.abs(capacityDifference / 10000000).toFixed(2)} Crore. Joint Venture (JV) partner recommended.`;
    } else if (isCapacityEligible && !isLiquidEligible) {
      status = "LIQUIDITY_DEFICIT";
      statusColor = "amber";
      summaryText = `Capacity is sufficient, but Liquid Assets fall short by BDT ${Math.abs(liquidDifference / 10000000).toFixed(2)} Crore. Form e-PW2A-8 Bank Credit Line required.`;
    } else {
      status = "DUAL_DEFICIT";
      statusColor = "rose";
      summaryText = `Deficit in both Assessed Capacity (-BDT ${Math.abs(capacityDifference / 10000000).toFixed(2)} Cr) and Liquid Assets (-BDT ${Math.abs(liquidDifference / 10000000).toFixed(2)} Cr). Joint Venture or Sub-contracting mandatory.`;
    }

    // Joint Venture Requirement Analysis (PPR-2008 Rule 54 & Rule 40)
    const jvDeficit = Math.max(0, -capacityDifference);
    const minJvPartnerTurnover = jvDeficit > 0 ? Math.round(jvDeficit / (N * 1.5)) : 0;

    const recommendedPartners = this.getRecommendedJVPartners(minJvPartnerTurnover, config.category || "Civil Construction");
    const rule40Compliance = this.validateCPTURule40JV(config.leadShare || 60, config.partnerShares || [40]);

    return {
      grossPotential,
      assessedCapacity,
      capacityDifference,
      isCapacityEligible,
      isLiquidEligible,
      liquidDifference,
      status,
      statusColor,
      summaryText,
      jvDeficit,
      minJvPartnerTurnover,
      recommendedPartners,
      rule40Compliance,
      inputs: { A, N, B, tenderCost, liquidAssets, liquidReq }
    };
  }

  validateCPTURule40JV(leadShare = 60, partnerShares = [40], leadHasSimilarExp = true) {
    // Bangladesh PPR-2008 Rule 40 & CPTU STD Regulations:
    // 1. Lead Partner share must be >= 40%
    // 2. Each non-lead partner must be >= 25%
    // 3. Combined shares must equal 100%
    // 4. At least one partner must satisfy 100% of single similar contract experience
    const totalShare = leadShare + partnerShares.reduce((a, b) => a + b, 0);
    const violations = [];

    if (Math.round(totalShare) !== 100) {
      violations.push(`Total equity split must equal 100% (currently ${totalShare}%).`);
    }
    if (leadShare < 40) {
      violations.push(`Lead partner share (${leadShare}%) violates statutory CPTU minimum of 40%.`);
    }
    partnerShares.forEach((share, idx) => {
      if (share < 25) {
        violations.push(`Partner #${idx + 2} share (${share}%) falls below statutory 25% minimum under PPR-2008 Rule 40.`);
      }
    });
    if (!leadHasSimilarExp) {
      violations.push(`Neither partner meets the 100% Single Similar Contract Completion requirement.`);
    }

    return {
      isCompliant: violations.length === 0,
      badge: violations.length === 0 ? "CPTU RULE 40 COMPLIANT" : "DISQUALIFICATION RISK",
      violations
    };
  }

  getRecommendedJVPartners(minTurnoverNeeded, category) {
    const partnerPool = [
      {
        name: "Bengal MegaStructures Ltd.",
        grade: "1st Class Enlisted",
        districts: "Dhaka, Narayanganj, Gazipur",
        peakTurnover: 420000000, // 42 Cr
        completedProjects: 28,
        specialty: "RCC Bridge, Flyover, Heavy Highway",
        verified: true
      },
      {
        name: "Eastern Engineering & Consortium",
        grade: "1st Class Enlisted",
        districts: "Chattogram, Cox's Bazar, Sylhet",
        peakTurnover: 280000000, // 28 Cr
        completedProjects: 19,
        specialty: "Coastal Defense, Highway BC Carpeting",
        verified: true
      },
      {
        name: "Apex InfraTech Solutions Ltd.",
        grade: "Special Class",
        districts: "Khulna, Jashore, Barishal",
        peakTurnover: 190000000, // 19 Cr
        completedProjects: 14,
        specialty: "Multistoried Hospital, Institutional Building",
        verified: true
      },
      {
        name: "Padma River Dredging & Hydro Works",
        grade: "1st Class",
        districts: "Rajshahi, Pabna, Sirajganj",
        peakTurnover: 310000000, // 31 Cr
        completedProjects: 22,
        specialty: "Dredging, CC Block Riverbank Revetment",
        verified: true
      }
    ];

    return partnerPool.filter(p => p.peakTurnover >= minTurnoverNeeded);
  }
}

// Global Singleton
window.capacityEngine = new TenderCapacityEngine();
